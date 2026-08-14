"""Loads ``config/bhava.toml`` into a validated ``BhavaConfig`` (SPEC §28).

TOML is authoritative; every default is declared in the file (no hidden
defaults); a missing file yields the validated dataclass defaults; there
are no environment-variable overrides (determinism). Unknown enum values
anywhere raise ``InvalidBhavaConfigError``.
"""

from __future__ import annotations

import enum
import tomllib
from pathlib import Path

from jyotish import HouseSystem

from .errors import InvalidBhavaConfigError
from .models import (
    BhavaConfig,
    RelativeHouseFrame,
    UnplacedBodyBehavior,
    validate,
)

DEFAULT_CONFIG_PATH: Path = Path("config/bhava.toml")


def load_config(path: str | Path | None = None) -> BhavaConfig:
    """Load and validate JRE-005 defaults from a TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return validate(BhavaConfig())
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("bhava", {})

    house_systems_raw = section.get("house_systems", ["WHOLE_SIGN"])
    if not isinstance(house_systems_raw, list):
        raise InvalidBhavaConfigError(
            f"house_systems must be an array, got {house_systems_raw!r}"
        )

    house_systems = tuple(
        _parse_enum(HouseSystem, item, "house_system", HouseSystem.WHOLE_SIGN)
        for item in house_systems_raw
    )

    config = BhavaConfig(
        cusp_proximity_orb_deg=float(section.get("cusp_proximity_orb_deg", 3.0)),
        house_systems=house_systems,
        include_empty_houses=bool(section.get("include_empty_houses", True)),
        unplaced_body_behavior=_parse_enum(
            UnplacedBodyBehavior,
            section.get("unplaced_body_behavior"),
            "unplaced_body_behavior",
            UnplacedBodyBehavior.RAISE,
        ),
        anchor_frame=_parse_enum(
            RelativeHouseFrame,
            section.get("anchor_frame"),
            "anchor_frame",
            RelativeHouseFrame.HOUSE_OCCUPANCY,
        ),
        derivation_version=str(section.get("derivation_version", "0.2.0")),
        # tradition_profile intentionally omitted: TOML has no null.
    )
    return validate(config)


def _parse_enum[EnumT: enum.Enum](
    enum_cls: type[EnumT], raw: object, field: str, default: EnumT
) -> EnumT:
    if raw is None:
        return default
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise InvalidBhavaConfigError(f"unknown {field} value {raw!r}") from exc

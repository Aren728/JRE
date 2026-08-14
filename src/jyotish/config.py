"""Loads ``config/jyotish.toml`` into a validated ``JyotishConfig``.

Defaults mirror the Specialist spec §19. Validation at load: enum values
known (unknown → ``InvalidConfigError``), orb values positive, aspect table
complete, ``conjunction_orb_deg`` consistent with
``aspect_orbs_deg["CONJUNCTION"]``, ``coordinate_precision`` in 0–3. No
environment-variable overrides (determinism).

TOML authority (SPEC §19): every default declared in ``config/jyotish.toml``
(``zodiac_mode``, ``ayanamsa``, ``house_system``, ``node_model``,
``position_type``, ``timezone``, orbs, precision, transit parameters) is read
from the file; ``provider_id``/``ephemeris_version`` are intentionally
omitted there (TOML has no null) and keep their ``None`` defaults.
"""

from __future__ import annotations

import enum
import tomllib
from pathlib import Path

from astronomy.models import Ayanamsa, NodeType, PositionType

from .errors import InvalidConfigError, InvalidOrbError
from .models import (
    DEFAULT_ASPECT_ORBS,
    AspectKind,
    HouseSystem,
    JyotishConfig,
    ZodiacMode,
)

DEFAULT_CONFIG_PATH: Path = Path("config/jyotish.toml")

_VALID_PRECISION_RANGE = range(0, 4)


#: Enum-typed JyotishConfig fields (SPEC §19: unknown enum values →
#: ``InvalidConfigError``). ``ayanamsa`` may be None (Ayanamsa | None).
_ENUM_FIELDS: tuple[tuple[str, type[enum.Enum] | None], ...] = (
    ("zodiac_mode", ZodiacMode),
    ("ayanamsa", Ayanamsa),
    ("house_system", HouseSystem),
    ("node_model", NodeType),
    ("position_type", PositionType),
)


def _parse_enum[EnumT: enum.Enum](
    enum_cls: type[EnumT], raw: str | None, field: str, default: EnumT
) -> EnumT:
    """Parse a TOML/JSON string into an enum; unknown values raise
    ``InvalidConfigError`` (SPEC §19/§20)."""
    if raw is None:
        return default
    try:
        return enum_cls(raw)
    except ValueError as exc:
        raise InvalidConfigError(
            f"unknown {field} value {raw!r}"
        ) from exc


def load_config(path: str | Path | None = None) -> JyotishConfig:
    """Load and validate JRE-003 defaults from a TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return validate(JyotishConfig())
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("jyotish", {})

    orbs_raw = section.get("aspect_orbs", {})
    aspect_orbs: dict[AspectKind, float] = {}
    for kind in AspectKind:
        value = orbs_raw.get(kind.value)
        aspect_orbs[kind] = DEFAULT_ASPECT_ORBS[kind] if value is None else float(value)

    config = JyotishConfig(
        zodiac_mode=_parse_enum(
            ZodiacMode, section.get("zodiac_mode"), "zodiac_mode", ZodiacMode.SIDEREAL
        ),
        ayanamsa=_parse_enum(
            Ayanamsa, section.get("ayanamsa"), "ayanamsa", Ayanamsa.LAHIRI
        ),
        house_system=_parse_enum(
            HouseSystem,
            section.get("house_system"),
            "house_system",
            HouseSystem.WHOLE_SIGN,
        ),
        node_model=_parse_enum(
            NodeType, section.get("node_model"), "node_model", NodeType.MEAN
        ),
        position_type=_parse_enum(
            PositionType, section.get("position_type"), "position_type", PositionType.APPARENT
        ),
        timezone=str(section.get("timezone", "UTC")),
        coordinate_precision=int(section.get("coordinate_precision", 1)),
        conjunction_orb_deg=float(section.get("conjunction_orb_deg", 8.0)),
        aspect_orbs_deg=aspect_orbs,
        station_speed_epsilon=float(section.get("station_speed_epsilon", 1e-9)),
        transit_sample_step_hours=float(section.get("transit_sample_step_hours", 6.0)),
        transit_tolerance_jd=float(section.get("transit_tolerance_jd", 1e-4)),
    )
    return validate(config)


def validate(config: JyotishConfig) -> JyotishConfig:
    """Validate a ``JyotishConfig``; raises typed errors for invalid values."""
    # SPEC §19/§20: unknown enum values (incl. raw strings where an enum is
    # expected) → ``InvalidConfigError``.
    for field, enum_cls in _ENUM_FIELDS:
        value = getattr(config, field)
        if enum_cls is not None and value is not None and not isinstance(value, enum_cls):
            raise InvalidConfigError(f"unknown {field} value {value!r}")
    if config.coordinate_precision not in _VALID_PRECISION_RANGE:
        raise InvalidConfigError(
            f"coordinate_precision must be in [0, 3], got {config.coordinate_precision}"
        )
    if config.conjunction_orb_deg <= 0.0:
        raise InvalidOrbError(
            f"conjunction_orb_deg must be positive, got {config.conjunction_orb_deg}"
        )
    known = set(AspectKind)
    supplied = set(config.aspect_orbs_deg)
    if supplied != known:
        missing = known - supplied
        extra = supplied - known

        def _label(key: object) -> str:
            return key.value if isinstance(key, AspectKind) else str(key)

        raise InvalidOrbError(
            f"aspect_orbs_deg must cover all 7 kinds; missing={sorted(map(_label, missing))} "
            f"extra={sorted(map(_label, extra))}"
        )
    for kind, orb in config.aspect_orbs_deg.items():
        if orb <= 0.0:
            raise InvalidOrbError(f"orb for {kind.value!r} must be positive, got {orb}")
    if config.aspect_orbs_deg[AspectKind.CONJUNCTION] != config.conjunction_orb_deg:
        raise InvalidOrbError(
            "aspect_orbs_deg[CONJUNCTION] must equal conjunction_orb_deg: "
            f"{config.aspect_orbs_deg[AspectKind.CONJUNCTION]} != {config.conjunction_orb_deg}"
        )
    if config.transit_sample_step_hours <= 0.0:
        raise InvalidConfigError(
            f"transit_sample_step_hours must be positive, got {config.transit_sample_step_hours}"
        )
    if config.transit_tolerance_jd <= 0.0:
        raise InvalidConfigError(
            f"transit_tolerance_jd must be positive, got {config.transit_tolerance_jd}"
        )
    return config

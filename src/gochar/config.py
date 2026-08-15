"""Loads ``config/gochar.toml`` into a validated ``GocharConfig`` (SPEC §5).

TOML authority (SPEC §22): ``config/gochar.toml`` is the single source of
defaults; per-request config overrides win; everything else is the TOML
value. No environment-variable configuration. A config missing any
declared field is a load error (``InvalidGocharConfigError``); a missing
file yields the validated dataclass defaults.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidGocharConfigError
from .models import GOCHAR_VERSION, GocharConfig, validate

DEFAULT_CONFIG_PATH: Path = Path("config/gochar.toml")

#: Every field the TOML must declare (SPEC §5; ``tradition_profile`` is
#: intentionally omitted — TOML has no null — and keeps its ``None`` default).
_DECLARED_FIELDS: tuple[str, ...] = (
    "reference_point",
    "house_system",
    "sample_step_hours",
    "aspect_echo",
    "natal_house_series",
    "version",
)


def load_config(path: str | Path | None = None) -> GocharConfig:
    """Load and validate JRE-006 defaults from a TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return validate(GocharConfig())
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("gochar", {})
    if not isinstance(section, dict):
        raise InvalidGocharConfigError(f"[gochar] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidGocharConfigError(
            "config/gochar.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    config = GocharConfig(
        reference_point=str(section["reference_point"]),
        house_system=str(section["house_system"]),
        sample_step_hours=float(section["sample_step_hours"]),
        aspect_echo=_as_bool(section["aspect_echo"], "aspect_echo"),
        natal_house_series=_as_bool(section["natal_house_series"], "natal_house_series"),
        # tradition_profile is intentionally omitted (TOML has no null).
        version=str(section.get("version", GOCHAR_VERSION)),
    )
    return validate(config)


def _as_bool(raw: object, field: str) -> bool:
    if not isinstance(raw, bool):
        raise InvalidGocharConfigError(f"{field} must be a boolean, got {raw!r}")
    return raw

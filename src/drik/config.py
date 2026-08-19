"""Loads ``config/drik.toml`` into a validated ``DrikConfig``.

TOML authority: ``config/drik.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidDrikConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidDrikConfigError
from .models import DrikConfig, validate

DEFAULT_CONFIG_PATH: Path = Path("config/drik.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "default_orb_deg",
    "aspect_houses",
)


def load_config(path: str | Path | None = None) -> DrikConfig:
    """Load and validate JRE-012 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidDrikConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/drik.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("drik", {})
    if not isinstance(section, dict):
        raise InvalidDrikConfigError(f"[drik] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidDrikConfigError(
            "config/drik.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    houses_raw = section.get("aspect_houses", {})
    if not isinstance(houses_raw, dict) or not houses_raw:
        raise InvalidDrikConfigError(
            f"aspect_houses must be a non-empty table, got {houses_raw!r}"
        )
    aspect_houses = {
        str(k): tuple(int(vi) for vi in v) if isinstance(v, list) else (int(v),)
        for k, v in houses_raw.items()
    }

    config = DrikConfig(
        version=str(section["version"]),
        default_orb_deg=float(section["default_orb_deg"]),
        aspect_houses=aspect_houses,
    )
    return validate(config)

"""Loads ``config/varga.toml`` into a validated ``VargaConfig`` (§18).

TOML authority: ``config/varga.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidVargaConfigError`` is raised deterministically (no
hidden fallback defaults). Programmatic ``VargaConfig`` values supplied by
a caller remain valid. No environment-variable configuration.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidVargaConfigError
from .models import VargaConfig, validate

DEFAULT_CONFIG_PATH: Path = Path("config/varga.toml")

#: Every field the TOML must declare (default_ayanamsa is optional — it
#: may be omitted and keeps its declared default; TOML has no null).
_DECLARED_FIELDS: tuple[str, ...] = (
    "catalog_version",
    "version",
    "default_boundary_convention",
    "default_zodiac_mode",
    "default_ayanamsa",
)


def load_config(path: str | Path | None = None) -> VargaConfig:
    """Load and validate JRE-008 defaults from the authoritative TOML file.

    The authoritative file (``config/varga.toml`` by default) MUST exist
    and MUST declare every default field; otherwise
    ``InvalidVargaConfigError`` is raised deterministically.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidVargaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/varga.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("varga", {})
    if not isinstance(section, dict):
        raise InvalidVargaConfigError(f"[varga] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidVargaConfigError(
            "config/varga.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    config = VargaConfig(
        catalog_version=str(section["catalog_version"]),
        version=str(section["version"]),
        default_boundary_convention=str(section["default_boundary_convention"]),
        default_zodiac_mode=str(section["default_zodiac_mode"]),
        default_ayanamsa=str(section["default_ayanamsa"]),
    )
    return validate(config)

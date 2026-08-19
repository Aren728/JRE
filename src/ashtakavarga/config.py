"""Loads ``config/ashtakavarga.toml`` into a validated ``AshtakavargaConfig``.

TOML authority: ``config/ashtakavarga.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidAshtakavargaConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidAshtakavargaConfigError
from .models import AshtakavargaConfig

DEFAULT_CONFIG_PATH: Path = Path("config/ashtakavarga.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
)


def load_config(path: str | Path | None = None) -> AshtakavargaConfig:
    """Load and validate JRE-016 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidAshtakavargaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/ashtakavarga.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("ashtakavarga", {})
    if not isinstance(section, dict):
        raise InvalidAshtakavargaConfigError(
            f"[ashtakavarga] section must be a table, got {section!r}"
        )

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidAshtakavargaConfigError(
            "config/ashtakavarga.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    config = AshtakavargaConfig(
        version=str(section["version"]),
    )
    return config

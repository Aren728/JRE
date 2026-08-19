"""Loads ``config/tajika.toml`` into a validated ``TajikaConfig``.

TOML authority: ``config/tajika.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidTajikaConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidTajikaConfigError
from .models import SahamType, TajikaConfig

DEFAULT_CONFIG_PATH: Path = Path("config/tajika.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "enabled_sahams",
)


def load_config(path: str | Path | None = None) -> TajikaConfig:
    """Load and validate JRE-017 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidTajikaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/tajika.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("tajika", {})
    if not isinstance(section, dict):
        raise InvalidTajikaConfigError(
            f"[tajika] section must be a table, got {section!r}"
        )

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidTajikaConfigError(
            "config/tajika.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    raw_sahams = section.get("enabled_sahams", [])
    if isinstance(raw_sahams, list) and raw_sahams:
        enabled = tuple(SahamType(s) for s in raw_sahams)
    else:
        enabled = tuple(SahamType)

    config = TajikaConfig(
        version=str(section["version"]),
        enabled_sahams=enabled,
    )
    return config

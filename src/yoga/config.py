"""Loads ``config/yoga.toml`` into a validated ``YogaConfig``.

TOML authority: ``config/yoga.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidYogaConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidYogaConfigError
from .models import YogaConfig, YogaId, validate

DEFAULT_CONFIG_PATH: Path = Path("config/yoga.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "min_bala_ratio",
)


def load_config(path: str | Path | None = None) -> YogaConfig:
    """Load and validate JRE-013 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidYogaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/yoga.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("yoga", {})
    if not isinstance(section, dict):
        raise InvalidYogaConfigError(f"[yoga] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidYogaConfigError(
            "config/yoga.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    enabled_raw = section.get("enabled_yogas")
    if isinstance(enabled_raw, list) and enabled_raw:
        enabled = tuple(YogaId(str(v)) for v in enabled_raw)
    else:
        enabled = tuple(YogaId)

    config = YogaConfig(
        version=str(section["version"]),
        min_bala_ratio=float(section["min_bala_ratio"]),
        enabled_yogas=enabled,
    )
    return validate(config)

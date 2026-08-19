"""Loads ``config/avastha.toml`` into a validated ``AvasthaConfig``.

TOML authority: ``config/avastha.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidAvasthaConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidAvasthaConfigError
from .models import AvasthaConfig, validate

DEFAULT_CONFIG_PATH: Path = Path("config/avastha.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "jagradadi",
    "jagradadi_multipliers",
    "deeptadi_multipliers",
)


def load_config(path: str | Path | None = None) -> AvasthaConfig:
    """Load and validate JRE-015 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidAvasthaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/avastha.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("avastha", {})
    if not isinstance(section, dict):
        raise InvalidAvasthaConfigError(f"[avastha] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidAvasthaConfigError(
            "config/avastha.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    jag_raw = section.get("jagradadi_multipliers", {})
    jag = {str(k): float(v) for k, v in jag_raw.items()} if isinstance(jag_raw, dict) else {}
    deep_raw = section.get("deeptadi_multipliers", {})
    deep = {str(k): float(v) for k, v in deep_raw.items()} if isinstance(deep_raw, dict) else {}

    config = AvasthaConfig(
        version=str(section["version"]),
        jagradadi_multipliers=jag,
        deeptadi_multipliers=deep,
    )
    return validate(config)

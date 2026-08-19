"""Loads ``config/dasha.toml`` into a validated ``DashaConfig``.

TOML authority: ``config/dasha.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidDashaConfigError`` is raised deterministically (no
hidden fallback defaults).  Programmatic ``DashaConfig`` values supplied
by a caller remain valid.  No environment-variable configuration.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidDashaConfigError
from .models import DashaConfig, DashaSystem, validate

DEFAULT_CONFIG_PATH: Path = Path("config/dasha.toml")

#: Every field the TOML must declare.
_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "default_system",
    "max_depth",
    "vimshottari_years",
)


def load_config(path: str | Path | None = None) -> DashaConfig:
    """Load and validate JRE-010 defaults from the authoritative TOML file.

    The authoritative file (``config/dasha.toml`` by default) MUST exist
    and MUST declare every default field; otherwise
    ``InvalidDashaConfigError`` is raised deterministically.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidDashaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/dasha.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("dasha", {})
    if not isinstance(section, dict):
        raise InvalidDashaConfigError(f"[dasha] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidDashaConfigError(
            "config/dasha.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    vy_raw = section.get("vimshottari_years", {})
    if not isinstance(vy_raw, dict) or not vy_raw:
        raise InvalidDashaConfigError(
            f"vimshottari_years must be a non-empty table, got {vy_raw!r}"
        )
    vy = {str(k): int(v) for k, v in vy_raw.items()}

    config = DashaConfig(
        version=str(section["version"]),
        default_system=DashaSystem(str(section["default_system"])),
        max_depth=int(section["max_depth"]),
        vimshottari_years=vy,
    )
    return validate(config)

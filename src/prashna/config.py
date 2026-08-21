"""Loads ``config/prashna.toml`` into a validated ``PrashnaConfig``.

TOML authority: ``config/prashna.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidPrashnaConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidPrashnaConfigError
from .models import DEFAULT_HOUSE_MAPPINGS, PrashnaConfig

DEFAULT_CONFIG_PATH: Path = Path("config/prashna.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "default_category",
    "house_mappings",
)


def load_config(path: str | Path | None = None) -> PrashnaConfig:
    """Load and validate JRE-019 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidPrashnaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/prashna.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("prashna", {})
    if not isinstance(section, dict):
        raise InvalidPrashnaConfigError(
            f"[prashna] section must be a table, got {section!r}"
        )

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidPrashnaConfigError(
            "config/prashna.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    version = section.get("version", "0.1.0")
    if not isinstance(version, str) or version == "":
        raise InvalidPrashnaConfigError(
            f"version must be a non-empty string, got {version!r}"
        )

    default_category = section.get("default_category", "GENERAL")
    if not isinstance(default_category, str) or default_category == "":
        raise InvalidPrashnaConfigError(
            f"default_category must be a non-empty string, got {default_category!r}"
        )

    raw_mappings = section.get("house_mappings", {})
    house_mappings: dict[str, tuple[int, int]] = {}
    if isinstance(raw_mappings, dict):
        for cat_name, cat_val in raw_mappings.items():
            if isinstance(cat_val, dict):
                primary = cat_val.get("primary")
                secondary = cat_val.get("secondary")
                if (isinstance(primary, int) and isinstance(secondary, int)
                        and 1 <= primary <= 12 and 1 <= secondary <= 12):
                    house_mappings[str(cat_name)] = (primary, secondary)
                    continue
            raise InvalidPrashnaConfigError(
                f"house_mappings[{cat_name!r}] must be "
                f"{{primary: int(1-12), secondary: int)}}, got {cat_val!r}"
            )

    # Merge with defaults for any missing categories
    merged = dict(DEFAULT_HOUSE_MAPPINGS)
    merged.update(house_mappings)

    return PrashnaConfig(
        version=version,
        default_category=default_category,
        house_mappings=merged,
    )

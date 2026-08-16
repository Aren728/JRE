"""Loads ``config/context.toml`` into a validated ``ContextConfig`` (SPEC §5).

TOML authority (SPEC §22): ``config/context.toml`` is the single source of
defaults; per-request config overrides win; everything else is the TOML
value. No environment-variable configuration. A config missing any
declared field is a load error (``InvalidContextConfigError``); a missing
file is likewise a load error — there are NO hidden fallback defaults.
Programmatic ``ContextConfig`` values supplied by a caller remain valid.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidContextConfigError
from .models import ContextConfig, validate

DEFAULT_CONFIG_PATH: Path = Path("config/context.toml")

#: Every field the TOML must declare (SPEC §5; ``tradition_profile`` is
#: intentionally omitted — TOML has no null — and keeps its ``None`` default).
_DECLARED_FIELDS: tuple[str, ...] = (
    "snapshot_version",
    "default_time_precision",
    "house_system",
    "version",
)


def load_config(path: str | Path | None = None) -> ContextConfig:
    """Load and validate JRE-007 defaults from the authoritative TOML file.

    The authoritative file (``config/context.toml`` by default) MUST exist
    and MUST declare every default field; otherwise
    ``InvalidContextConfigError`` is raised deterministically (no hidden
    fallback defaults).
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidContextConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/context.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("context", {})
    if not isinstance(section, dict):
        raise InvalidContextConfigError(f"[context] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidContextConfigError(
            "config/context.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    config = ContextConfig(
        snapshot_version=str(section["snapshot_version"]),
        default_time_precision=str(section["default_time_precision"]),
        house_system=str(section["house_system"]),
        # tradition_profile is intentionally omitted (TOML has no null).
        version=str(section["version"]),
    )
    return validate(config)

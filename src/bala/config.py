"""Loads ``config/bala.toml`` into a validated ``BalaConfig``.

TOML authority: ``config/bala.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidBalaConfigError`` is raised deterministically (no
hidden fallback defaults).  Programmatic ``BalaConfig`` values supplied
by a caller remain valid.  No environment-variable configuration.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidBalaConfigError
from .models import BalaConfig, validate

DEFAULT_CONFIG_PATH: Path = Path("config/bala.toml")

#: Every field the TOML must declare.
_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "max_depth",
    "minimum_rupas",
    "naisargika_virupas",
)


def load_config(path: str | Path | None = None) -> BalaConfig:
    """Load and validate JRE-011 defaults from the authoritative TOML file.

    The authoritative file (``config/bala.toml`` by default) MUST exist
    and MUST declare every default field; otherwise
    ``InvalidBalaConfigError`` is raised deterministically.
    """
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidBalaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/bala.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("bala", {})
    if not isinstance(section, dict):
        raise InvalidBalaConfigError(f"[bala] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidBalaConfigError(
            "config/bala.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    min_raw = section.get("minimum_rupas", {})
    if not isinstance(min_raw, dict) or not min_raw:
        raise InvalidBalaConfigError(
            f"minimum_rupas must be a non-empty table, got {min_raw!r}"
        )
    min_rupas = {str(k): float(v) for k, v in min_raw.items()}

    nais_raw = section.get("naisargika_virupas", {})
    if not isinstance(nais_raw, dict) or not nais_raw:
        raise InvalidBalaConfigError(
            f"naisargika_virupas must be a non-empty table, got {nais_raw!r}"
        )
    nais_virupas = {str(k): float(v) for k, v in nais_raw.items()}

    config = BalaConfig(
        version=str(section["version"]),
        max_depth=int(section["max_depth"]),
        minimum_rupas=min_rupas,
        naisargika_virupas=nais_virupas,
    )
    return validate(config)

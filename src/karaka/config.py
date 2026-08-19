"""Loads ``config/karaka.toml`` into a validated ``KarakaConfig``.

TOML authority: ``config/karaka.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidKarakaConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidKarakaConfigError
from .models import KarakaConfig, validate

DEFAULT_CONFIG_PATH: Path = Path("config/karaka.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "chara_planet_count",
    "naisargika",
    "sthira",
)


def load_config(path: str | Path | None = None) -> KarakaConfig:
    """Load and validate JRE-014 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidKarakaConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/karaka.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("karaka", {})
    if not isinstance(section, dict):
        raise InvalidKarakaConfigError(f"[karaka] section must be a table, got {section!r}")

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidKarakaConfigError(
            "config/karaka.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    nais_raw = section.get("naisargika", {})
    nais = {str(k): str(v) for k, v in nais_raw.items()} if isinstance(nais_raw, dict) else {}
    sthi_raw = section.get("sthira", {})
    sthi = {str(k): str(v) for k, v in sthi_raw.items()} if isinstance(sthi_raw, dict) else {}

    config = KarakaConfig(
        version=str(section["version"]),
        chara_planet_count=int(section["chara_planet_count"]),
        naisargika=nais,
        sthira=sthi,
    )
    return validate(config)

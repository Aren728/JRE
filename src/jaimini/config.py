"""Loads ``config/jaimini.toml`` into a validated ``JaiminiConfig``.

TOML authority: ``config/jaimini.toml`` is the single source of defaults;
the authoritative file MUST exist and MUST declare every default field —
otherwise ``InvalidJaiminiConfigError`` is raised deterministically (no
hidden fallback defaults).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .errors import InvalidJaiminiConfigError
from .models import JaiminiConfig

DEFAULT_CONFIG_PATH: Path = Path("config/jaimini.toml")

_DECLARED_FIELDS: tuple[str, ...] = (
    "version",
    "default_period_years",
    "chara_dasha_start_sign",
    "argala",
)


def load_config(path: str | Path | None = None) -> JaiminiConfig:
    """Load and validate JRE-018 defaults from the authoritative TOML file."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        raise InvalidJaiminiConfigError(
            f"missing authoritative default configuration {config_path} "
            "(config/jaimini.toml is required; no hidden fallback defaults)"
        )
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("jaimini", {})
    if not isinstance(section, dict):
        raise InvalidJaiminiConfigError(
            f"[jaimini] section must be a table, got {section!r}"
        )

    missing = [field for field in _DECLARED_FIELDS if field not in section]
    if missing:
        raise InvalidJaiminiConfigError(
            "config/jaimini.toml must declare every default (no hidden defaults); "
            f"missing fields: {missing}"
        )

    period_years = section.get("default_period_years", 7)
    if not isinstance(period_years, int) or period_years < 1:
        raise InvalidJaiminiConfigError(
            f"default_period_years must be a positive int, got {period_years!r}"
        )

    raw_start = section.get("chara_dasha_start_sign", {})
    start_sign: dict[str, int] = {}
    if isinstance(raw_start, dict):
        for key, val in raw_start.items():
            if not isinstance(val, int) or val < 1:
                raise InvalidJaiminiConfigError(
                    f"chara_dasha_start_sign[{key!r}] must be a positive int, got {val!r}"
                )
            start_sign[str(key)] = int(val)

    raw_argala = section.get("argala", {})
    intervening: tuple[int, ...] = (2, 4, 5, 11)
    obstructing: tuple[int, ...] = (12, 10, 9, 3)
    if isinstance(raw_argala, dict):
        raw_int = raw_argala.get("intervening_houses")
        if isinstance(raw_int, list) and raw_int:
            intervening = tuple(int(x) for x in raw_int)
        raw_obs = raw_argala.get("obstructing_houses")
        if isinstance(raw_obs, list) and raw_obs:
            obstructing = tuple(int(x) for x in raw_obs)

    return JaiminiConfig(
        version=str(section["version"]),
        default_period_years=period_years,
        chara_dasha_start_sign=start_sign or {"MOVABLE": 9, "FIXED": 10, "DUAL": 11},
        argala_intervening_houses=intervening,
        argala_obstructing_houses=obstructing,
    )

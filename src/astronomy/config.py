"""Loads ``config/astronomy.toml`` into a ``CalculationConfig``.

If the file is absent or a key is missing, hardcoded defaults are used, so the
core always has a deterministic configuration. There are no environment-variable
overrides: ambient inputs are a determinism risk and are intentionally absent.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from .models import Ayanamsa, CalculationConfig, EphemerisMode, NodeType, PositionType

DEFAULT_CONFIG_PATH: Path = Path("config/astronomy.toml")


def load_config(path: str | Path | None = None) -> CalculationConfig:
    """Load calculation defaults from a TOML file (see ``config/astronomy.toml``)."""
    config_path = Path(path) if path is not None else DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return CalculationConfig()
    with config_path.open("rb") as handle:
        data = tomllib.load(handle)
    section = data.get("astronomy", {})
    return CalculationConfig(
        ayanamsa=None if section.get("ayanamsa") is None else Ayanamsa(section["ayanamsa"]),
        ephemeris_mode=EphemerisMode(section.get("ephemeris_mode", EphemerisMode.SWIEPH.value)),
        position_type=PositionType(section.get("position_type", PositionType.APPARENT.value)),
        node_type=NodeType(section.get("node_type", NodeType.MEAN.value)),
        ephemeris_path=section.get("ephemeris_path"),
        allow_fallback=bool(section.get("allow_fallback", True)),
    )

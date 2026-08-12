"""Unit tests for the configuration loader."""

import tomllib
from pathlib import Path

from astronomy.config import DEFAULT_CONFIG_PATH, load_config
from astronomy.models import Ayanamsa, EphemerisMode, NodeType, PositionType

# tests/unit/astronomy/test_config.py -> parents[0..2]=astronomy/unit/tests -> parents[3]=repo root
REPO_ROOT = Path(__file__).resolve().parents[3]


def test_repo_config_file_exists_and_parses():
    path = REPO_ROOT / DEFAULT_CONFIG_PATH
    assert path.is_file(), f"expected {path}"
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    assert "astronomy" in data


def test_load_config_reads_repo_defaults():
    config = load_config(REPO_ROOT / DEFAULT_CONFIG_PATH)
    assert config.ayanamsa is Ayanamsa.LAHIRI
    assert config.ephemeris_mode is EphemerisMode.SWIEPH
    assert config.position_type is PositionType.APPARENT
    assert config.node_type is NodeType.MEAN
    assert config.allow_fallback is True


def test_load_config_missing_file_uses_defaults(tmp_path):
    config = load_config(tmp_path / "nope.toml")
    assert config == load_config(REPO_ROOT / DEFAULT_CONFIG_PATH)


def test_load_config_overrides(tmp_path):
    path = tmp_path / "custom.toml"
    path.write_text(
        "[astronomy]\nayanamsa = 'RAMAN'\nephemeris_mode = 'MOSEPH'\nallow_fallback = false\n"
    )
    config = load_config(path)
    assert config.ayanamsa is Ayanamsa.RAMAN
    assert config.ephemeris_mode is EphemerisMode.MOSEPH
    assert config.allow_fallback is False
    assert config.position_type is PositionType.APPARENT  # untouched default

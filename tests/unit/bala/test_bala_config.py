"""JRE-011 BalaConfig tests.

Tests for config loading, validation, and TOML parsing.
"""

from __future__ import annotations

import pytest

from bala.config import load_config
from bala.errors import InvalidBalaConfigError
from bala.models import BalaConfig, validate


class TestLoadConfig:
    """Test TOML config loading."""

    def test_loads_default(self) -> None:
        config = load_config()
        assert config.version == "0.1.0"
        assert config.max_depth == 1

    def test_minimum_rupas_loaded(self) -> None:
        config = load_config()
        assert "SUN" in config.minimum_rupas
        assert config.minimum_rupas["SUN"] == 5.0

    def test_naisargika_loaded(self) -> None:
        config = load_config()
        assert "SUN" in config.naisargika_virupas
        assert config.naisargika_virupas["SUN"] == 60.0

    def test_missing_file(self) -> None:
        with pytest.raises(InvalidBalaConfigError):
            load_config(path="/nonexistent/bala.toml")


class TestBalaConfigFromDict:
    """Test BalaConfig.from_dict."""

    def test_from_dict_full(self) -> None:
        data = {
            "version": "0.2.0",
            "max_depth": 2,
            "minimum_rupas": {"SUN": 6.0, "MOON": 7.0},
            "naisargika_virupas": {"SUN": 70.0, "MOON": 60.0},
        }
        config = BalaConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert config.max_depth == 2
        assert config.minimum_rupas["SUN"] == 6.0

    def test_from_dict_defaults(self) -> None:
        config = BalaConfig.from_dict({})
        assert config.version == "0.1.0"
        assert config.max_depth == 1


class TestValidate:
    """Test BalaConfig validation."""

    def test_valid_config(self) -> None:
        config = BalaConfig()
        validated = validate(config)
        assert validated is config

    def test_empty_version(self) -> None:
        config = BalaConfig(version="")
        with pytest.raises(InvalidBalaConfigError):
            validate(config)

    def test_invalid_max_depth(self) -> None:
        config = BalaConfig(max_depth=0)
        with pytest.raises(InvalidBalaConfigError):
            validate(config)

    def test_empty_minimum_rupas(self) -> None:
        config = BalaConfig(minimum_rupas={})
        with pytest.raises(InvalidBalaConfigError):
            validate(config)

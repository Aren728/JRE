"""JRE-012 DrikConfig tests."""

from __future__ import annotations

import pytest

from drik.config import load_config
from drik.errors import InvalidDrikConfigError
from drik.models import DrikConfig, validate


class TestLoadConfig:
    def test_loads_default(self) -> None:
        config = load_config()
        assert config.version == "0.1.0"
        assert config.default_orb_deg == 6.0

    def test_aspect_houses_loaded(self) -> None:
        config = load_config()
        assert "SUN" in config.aspect_houses
        assert 7 in config.aspect_houses["SUN"]

    def test_mars_special_loaded(self) -> None:
        config = load_config()
        mars_houses = config.aspect_houses.get("MARS", ())
        assert 4 in mars_houses
        assert 8 in mars_houses

    def test_missing_file(self) -> None:
        with pytest.raises(InvalidDrikConfigError):
            load_config(path="/nonexistent/drik.toml")


class TestDrikConfigFromDict:
    def test_from_dict_full(self) -> None:
        data = {
            "version": "0.2.0",
            "default_orb_deg": 10.0,
            "aspect_houses": {"SUN": [7], "MARS": [4, 7, 8]},
        }
        config = DrikConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert config.default_orb_deg == 10.0

    def test_from_dict_defaults(self) -> None:
        config = DrikConfig.from_dict({})
        assert config.version == "0.1.0"
        assert config.default_orb_deg == 6.0


class TestValidate:
    def test_valid_config(self) -> None:
        config = DrikConfig()
        validated = validate(config)
        assert validated is config

    def test_empty_version(self) -> None:
        config = DrikConfig(version="")
        with pytest.raises(InvalidDrikConfigError):
            validate(config)

    def test_negative_orb(self) -> None:
        config = DrikConfig(default_orb_deg=-1.0)
        with pytest.raises(InvalidDrikConfigError):
            validate(config)

    def test_empty_aspect_houses(self) -> None:
        config = DrikConfig(aspect_houses={})
        with pytest.raises(InvalidDrikConfigError):
            validate(config)

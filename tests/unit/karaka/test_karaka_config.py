"""JRE-014 KarakaConfig tests."""

from __future__ import annotations

import pytest

from karaka.config import load_config
from karaka.errors import InvalidKarakaConfigError
from karaka.models import KarakaConfig, validate


class TestLoadConfig:
    def test_loads_default(self) -> None:
        config = load_config()
        assert config.version == "0.1.0"
        assert config.chara_planet_count == 7

    def test_naisargika_loaded(self) -> None:
        config = load_config()
        assert "SUN" in config.naisargika

    def test_sthira_loaded(self) -> None:
        config = load_config()
        assert "ATMA" in config.sthira

    def test_missing_file(self) -> None:
        with pytest.raises(InvalidKarakaConfigError):
            load_config(path="/nonexistent/karaka.toml")


class TestKarakaConfigFromDict:
    def test_from_dict_full(self) -> None:
        data = {
            "version": "0.2.0",
            "chara_planet_count": 8,
            "naisargika": {"SUN": "ATMA"},
            "sthira": {"ATMA": "SUN"},
        }
        config = KarakaConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert config.chara_planet_count == 8

    def test_from_dict_defaults(self) -> None:
        config = KarakaConfig.from_dict({})
        assert config.version == "0.1.0"
        assert config.chara_planet_count == 7


class TestValidate:
    def test_valid_config(self) -> None:
        config = KarakaConfig()
        validated = validate(config)
        assert validated is config

    def test_empty_version(self) -> None:
        config = KarakaConfig(version="")
        with pytest.raises(InvalidKarakaConfigError):
            validate(config)

    def test_negative_chara_count(self) -> None:
        config = KarakaConfig(chara_planet_count=-1)
        with pytest.raises(InvalidKarakaConfigError):
            validate(config)

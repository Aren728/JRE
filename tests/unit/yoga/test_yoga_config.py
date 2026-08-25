"""JRE-013 YogaConfig tests."""

from __future__ import annotations

import pytest

from yoga.config import load_config
from yoga.errors import InvalidYogaConfigError
from yoga.models import YogaConfig, YogaId, validate


class TestLoadConfig:
    def test_loads_default(self) -> None:
        config = load_config()
        assert config.version == "0.1.0"
        assert config.min_bala_ratio == 0.5

    def test_enabled_yogas_loaded(self) -> None:
        config = load_config()
        assert len(config.enabled_yogas) == len(YogaId)

    def test_missing_file(self) -> None:
        with pytest.raises(InvalidYogaConfigError):
            load_config(path="/nonexistent/yoga.toml")


class TestYogaConfigFromDict:
    def test_from_dict_full(self) -> None:
        data = {
            "version": "0.2.0",
            "min_bala_ratio": 0.8,
            "enabled_yogas": ["GAJAKESARI_YOGA", "RAJA_YOGA"],
        }
        config = YogaConfig.from_dict(data)
        assert config.version == "0.2.0"
        assert len(config.enabled_yogas) == 2

    def test_from_dict_defaults(self) -> None:
        config = YogaConfig.from_dict({})
        assert config.version == "0.1.0"
        assert len(config.enabled_yogas) == len(YogaId)


class TestValidate:
    def test_valid_config(self) -> None:
        config = YogaConfig()
        validated = validate(config)
        assert validated is config

    def test_empty_version(self) -> None:
        config = YogaConfig(version="")
        with pytest.raises(InvalidYogaConfigError):
            validate(config)

    def test_negative_bala(self) -> None:
        config = YogaConfig(min_bala_ratio=-1.0)
        with pytest.raises(InvalidYogaConfigError):
            validate(config)

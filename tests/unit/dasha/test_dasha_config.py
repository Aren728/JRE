"""JRE-010 Dasha config unit tests.

Tests loading from the authoritative TOML file, validation, and error
handling for missing/malformed configurations.
"""

from __future__ import annotations

import pytest

from dasha.config import load_config
from dasha.errors import InvalidDashaConfigError
from dasha.models import DashaConfig, DashaSystem


class TestLoadConfig:
    """Test loading from config/dasha.toml."""

    def test_load_default_config(self) -> None:
        config = load_config()
        assert isinstance(config, DashaConfig)
        assert config.version == "0.1.0"
        assert config.default_system == DashaSystem.VIMSHOTTARI
        assert config.max_depth == 3

    def test_load_config_custom_path(self, tmp_path: object) -> None:
        """Test loading from a custom path."""
        import tomllib
        from pathlib import Path

        config_path = Path(str(tmp_path)) / "custom.toml"
        config_path.write_text(
            '[dasha]\n'
            'version = "0.2.0"\n'
            'default_system = "VIMSHOTTARI"\n'
            'max_depth = 2\n'
            '[dasha.vimshottari_years]\n'
            'KETU = 7\nVENUS = 20\nSUN = 6\nMOON = 10\n'
            'MARS = 7\nRAHU = 18\nJUPITER = 16\nSATURN = 19\nMERCURY = 17\n',
            encoding="utf-8",
        )
        config = load_config(config_path)
        assert config.version == "0.2.0"
        assert config.max_depth == 2

    def test_missing_config_raises(self, tmp_path: object) -> None:
        from pathlib import Path

        config_path = Path(str(tmp_path)) / "missing.toml"
        with pytest.raises(InvalidDashaConfigError, match="missing"):
            load_config(config_path)


class TestValidate:
    """Test DashaConfig validation."""

    def test_valid_config(self) -> None:
        from dasha.models import validate

        config = DashaConfig()
        validated = validate(config)
        assert validated is config

    def test_invalid_version(self) -> None:
        from dasha.models import validate

        config = DashaConfig(version="")
        with pytest.raises(InvalidDashaConfigError, match="version"):
            validate(config)

    def test_invalid_max_depth(self) -> None:
        from dasha.models import validate

        config = DashaConfig(max_depth=0)
        with pytest.raises(InvalidDashaConfigError, match="max_depth"):
            validate(config)

    def test_invalid_max_depth_too_high(self) -> None:
        from dasha.models import validate

        config = DashaConfig(max_depth=4)
        with pytest.raises(InvalidDashaConfigError, match="max_depth"):
            validate(config)

    def test_invalid_vimshottari_sum(self) -> None:
        from dasha.models import validate

        config = DashaConfig(
            vimshottari_years={"KETU": 7, "VENUS": 20, "SUN": 6, "MOON": 10,
                               "MARS": 7, "RAHU": 18, "JUPITER": 16, "SATURN": 19, "MERCURY": 18}
        )
        with pytest.raises(InvalidDashaConfigError, match="sum"):
            validate(config)

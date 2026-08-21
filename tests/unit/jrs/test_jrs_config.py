"""Unit tests for JRS configuration loading."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from jrs.config import load_jrs_config
from jrs.errors import InvalidJRSConfigError


class TestLoadJRSConfig:
    """Tests for the load_jrs_config function."""

    def test_loads_default_config(self) -> None:
        config = load_jrs_config()
        assert config.version == "1.0"
        assert "CAREER" in config.routing
        assert "WEALTH" in config.routing

    def test_career_routing_loaded(self) -> None:
        config = load_jrs_config()
        career = config.routing["CAREER"]
        assert "bhava" in career.required_engines
        assert 10 in career.required_houses

    def test_marriage_routing_loaded(self) -> None:
        config = load_jrs_config()
        marriage = config.routing["MARRIAGE"]
        assert "drik" in marriage.required_engines
        assert "avastha" in marriage.required_engines
        assert 7 in marriage.required_houses

    def test_all_categories_present(self) -> None:
        config = load_jrs_config()
        expected = {"CAREER", "WEALTH", "MARRIAGE", "HEALTH", "EDUCATION",
                    "PROPERTY", "CHILDREN", "LITIGATION", "TRAVEL", "GENERAL"}
        assert set(config.routing.keys()) == expected

    def test_engine_hints_loaded(self) -> None:
        config = load_jrs_config()
        assert config.engine_hints.get("tajika_if_annual") is True
        assert config.engine_hints.get("jaimini_if_lagna_known") is True

    def test_missing_file_raises(self) -> None:
        with pytest.raises(InvalidJRSConfigError, match="not found"):
            load_jrs_config(Path("/nonexistent/jrs.toml"))

    def test_invalid_toml_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write("this is not valid toml [[[")
            f.flush()
            with pytest.raises(InvalidJRSConfigError, match="Invalid TOML"):
                load_jrs_config(Path(f.name))

    def test_missing_jrs_section_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[other]\nversion = "1.0"\n')
            f.flush()
            with pytest.raises(InvalidJRSConfigError, match="Missing top-level"):
                load_jrs_config(Path(f.name))

    def test_unknown_field_raises(self) -> None:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
            f.write('[jrs]\nunknown_field = true\n')
            f.flush()
            with pytest.raises(InvalidJRSConfigError, match="Unknown config fields"):
                load_jrs_config(Path(f.name))

    def test_all_routing_rules_have_engines(self) -> None:
        config = load_jrs_config()
        for category, rule in config.routing.items():
            assert len(rule.required_engines) > 0, f"{category} has no engines"

    def test_all_routing_rules_have_houses(self) -> None:
        config = load_jrs_config()
        for category, rule in config.routing.items():
            assert len(rule.required_houses) > 0, f"{category} has no houses"

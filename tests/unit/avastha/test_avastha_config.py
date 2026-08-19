"""Unit tests for AvasthaConfig."""

from __future__ import annotations

from avastha.config import load_config


class TestAvasthaConfig:
    def test_load_default(self) -> None:
        cfg = load_config()
        assert cfg is not None
        assert cfg.version == "0.1.0"

    def test_deterministic(self) -> None:
        cfg1 = load_config()
        cfg2 = load_config()
        assert cfg1.version == cfg2.version

    def test_has_multipliers(self) -> None:
        cfg = load_config()
        assert len(cfg.jagradadi_multipliers) >= 3
        assert len(cfg.deeptadi_multipliers) >= 6

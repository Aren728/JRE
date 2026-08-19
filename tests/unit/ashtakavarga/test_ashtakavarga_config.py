"""Unit tests for AshtakavargaConfig."""

from __future__ import annotations

from ashtakavarga.config import load_config


class TestAshtakavargaConfig:
    def test_load_default(self) -> None:
        cfg = load_config()
        assert cfg is not None
        assert cfg.version == "0.1.0"

    def test_deterministic(self) -> None:
        cfg1 = load_config()
        cfg2 = load_config()
        assert cfg1.version == cfg2.version

    def test_to_dict(self) -> None:
        cfg = load_config()
        d = cfg.to_dict()
        assert d["version"] == "0.1.0"

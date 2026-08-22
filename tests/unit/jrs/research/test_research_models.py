"""Unit tests for research module models."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.research.conftest import make_rule_citation

from jrs.research.models import ResearchConfig, RuleCitation


class TestRuleCitation:
    """Tests for the RuleCitation model."""

    def test_creation(self) -> None:
        citation = make_rule_citation(rule_id="R-TEST")
        assert citation.rule_id == "R-TEST"
        assert citation.source == "BPHS"

    def test_frozen(self) -> None:
        citation = make_rule_citation()
        with pytest.raises(AttributeError):
            citation.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        citation = make_rule_citation(
            rule_id="R-100",
            source="Phaladeepika",
            claim="Test claim for dict",
        )
        d = citation.to_dict()
        assert d["rule_id"] == "R-100"
        assert d["source"] == "Phaladeepika"
        assert d["claim"] == "Test claim for dict"

    def test_to_dict_deterministic(self) -> None:
        citation = make_rule_citation()
        d1 = citation.to_dict()
        d2 = citation.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_to_citation_string(self, sample_citation: RuleCitation) -> None:
        s = sample_citation.to_citation_string()
        assert "Brihat Parashara Hora Shastra" in s
        assert "Chapter 14, Verse 5" in s
        assert "2nd lord in 11th" in s

    def test_to_citation_string_deterministic(
        self, sample_citation: RuleCitation,
    ) -> None:
        s1 = sample_citation.to_citation_string()
        s2 = sample_citation.to_citation_string()
        assert s1 == s2


class TestResearchConfig:
    """Tests for the ResearchConfig model."""

    def test_defaults(self) -> None:
        config = ResearchConfig()
        assert config.version == "1.0"

    def test_frozen(self) -> None:
        config = ResearchConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

"""Unit tests for spirituality domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.spirituality.conftest import make_spirituality_rule

from jrs.domains.spirituality.models import (
    SpiritualityConfig,
    SpiritualityOutcomeTaxonomy,
    SpiritualityRule,
    SpiritualityRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestSpiritualityOutcomeTaxonomy:
    """Tests for the SpiritualityOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in SpiritualityOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(SpiritualityOutcomeTaxonomy) == 6

    def test_outcome_from_value(self) -> None:
        awk = SpiritualityOutcomeTaxonomy("SPIRITUAL_AWAKENING")
        assert awk is SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING
        ren = SpiritualityOutcomeTaxonomy("RENUNCIATION")
        assert ren is SpiritualityOutcomeTaxonomy.RENUNCIATION

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            SpiritualityOutcomeTaxonomy("INVALID")


class TestSpiritualityRule:
    """Tests for the SpiritualityRule model."""

    def test_creation(self) -> None:
        rule = make_spirituality_rule(rule_id="R-TEST")
        assert rule.rule_id == "R-TEST"
        assert rule.outcome is SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING

    def test_frozen(self) -> None:
        rule = make_spirituality_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_spirituality_rule(
            rule_id="R-100",
            outcome=SpiritualityOutcomeTaxonomy.RENUNCIATION,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "R-100"
        assert d["outcome"] == "RENUNCIATION"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_spirituality_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestSpiritualityRuleCatalog:
    """Tests for the SpiritualityRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = SpiritualityRuleCatalog(rules=(make_spirituality_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(
        self, sample_catalog: SpiritualityRuleCatalog,
    ) -> None:
        awk = sample_catalog.get_rules_by_outcome(
            SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING,
        )
        assert len(awk) == 1

    def test_get_rule_by_id(self, sample_catalog: SpiritualityRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-TEST-002")
        assert rule is not None
        assert rule.rule_id == "R-TEST-002"

    def test_get_rule_by_id_not_found(
        self, sample_catalog: SpiritualityRuleCatalog,
    ) -> None:
        rule = sample_catalog.get_rule_by_id("R-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: SpiritualityRuleCatalog) -> None:
        d = sample_catalog.to_dict()
        assert d["rule_count"] == 5
        assert len(d["rules"]) == 5


class TestEvaluateCondition:
    """Tests for the evaluate_condition function."""

    def test_truthy_check(self) -> None:
        assert evaluate_condition("flag_a", {"flag_a": True}) is True
        assert evaluate_condition("flag_a", {"flag_a": False}) is False
        assert evaluate_condition("flag_a", {}) is False

    def test_equality(self) -> None:
        assert evaluate_condition("x=5", {"x": 5}) is True
        assert evaluate_condition("x=5", {"x": 4}) is False
        assert evaluate_condition("x=hello", {"x": "hello"}) is True

    def test_inequality(self) -> None:
        assert evaluate_condition("x!=5", {"x": 4}) is True
        assert evaluate_condition("x!=5", {"x": 5}) is False

    def test_greater_than(self) -> None:
        assert evaluate_condition("x>5", {"x": 6}) is True
        assert evaluate_condition("x>5", {"x": 5}) is False

    def test_less_than(self) -> None:
        assert evaluate_condition("x<5", {"x": 4}) is True
        assert evaluate_condition("x<5", {"x": 5}) is False

    def test_membership(self) -> None:
        assert evaluate_condition("x in (1,2,3)", {"x": 2}) is True
        assert evaluate_condition("x in (1,2,3)", {"x": 4}) is False

    def test_missing_fact(self) -> None:
        assert evaluate_condition("x>5", {}) is False


class TestEvaluateRule:
    """Tests for the evaluate_rule function."""

    def test_single_condition_match(self) -> None:
        rule = make_spirituality_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING.value

    def test_single_condition_no_match(self) -> None:
        rule = make_spirituality_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_spirituality_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_spirituality_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_spirituality_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(
        self, sample_rules: tuple[SpiritualityRule, ...],
    ) -> None:
        facts = {
            "ketu_strong": True,
            "jupiter_strong": True,
            "saturn_in_8th": True,
            "ketu_8th_connection": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 2

    def test_no_rules_match(
        self, sample_rules: tuple[SpiritualityRule, ...],
    ) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(
        self, sample_rules: tuple[SpiritualityRule, ...],
    ) -> None:
        facts = {"ketu_strong": True, "jupiter_strong": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure 'spiritual awakening' doesn't trigger 'renunciation'."""
        rules = (
            make_spirituality_rule(
                rule_id="R-AWK",
                outcome=SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING,
                condition_facts=("ketu_strong=true",),
            ),
            make_spirituality_rule(
                rule_id="R-REN",
                outcome=SpiritualityOutcomeTaxonomy.RENUNCIATION,
                condition_facts=("ketu_in_1st=true",),
            ),
        )
        records = evaluate_facts(rules, {"ketu_strong": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING.value

    def test_numeric_comparison(self) -> None:
        rules = (
            make_spirituality_rule(
                rule_id="R-BALA",
                outcome=SpiritualityOutcomeTaxonomy.OCCULT_INTEREST,
                condition_facts=("jupiter_bala>6.0",),
            ),
        )
        records = evaluate_facts(rules, {"jupiter_bala": 7.5})
        assert len(records) == 1


class TestSpiritualityConfig:
    """Tests for the SpiritualityConfig model."""

    def test_defaults(self) -> None:
        config = SpiritualityConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = SpiritualityConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

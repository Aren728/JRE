"""Unit tests for traits domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.traits.conftest import make_trait_rule

from jrs.domains.traits.models import (
    TraitOutcomeTaxonomy,
    TraitRule,
    TraitRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength


class TestTraitOutcomeTaxonomy:
    """Tests for the TraitOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in TraitOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(TraitOutcomeTaxonomy) == 6

    def test_outcome_from_value(self) -> None:
        assert (
            TraitOutcomeTaxonomy("INTELLECTUAL_DEPTH")
            is TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH
        )
        assert (
            TraitOutcomeTaxonomy("EMOTIONAL_VOLATILITY")
            is TraitOutcomeTaxonomy.EMOTIONAL_VOLATILITY
        )

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            TraitOutcomeTaxonomy("INVALID")

    def test_all_six_taxonomies(self) -> None:
        expected = {
            "INTELLECTUAL_DEPTH",
            "EMOTIONAL_VOLATILITY",
            "PRACTICAL_GROUNDEDNESS",
            "SPIRITUAL_INCLINATION",
            "LEADERSHIP_TENDENCY",
            "ADAPTABILITY",
        }
        actual = {o.value for o in TraitOutcomeTaxonomy}
        assert actual == expected


class TestTraitRule:
    """Tests for the TraitRule model."""

    def test_creation(self) -> None:
        rule = make_trait_rule(rule_id="R-TEST")
        assert rule.rule_id == "R-TEST"
        assert rule.outcome is TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH

    def test_frozen(self) -> None:
        rule = make_trait_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_trait_rule(
            rule_id="R-100",
            outcome=TraitOutcomeTaxonomy.EMOTIONAL_VOLATILITY,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "R-100"
        assert d["outcome"] == "EMOTIONAL_VOLATILITY"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_trait_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_defaults(self) -> None:
        rule = TraitRule(
            rule_id="R-001",
            description="Test",
            condition_facts=("fact_a",),
            outcome=TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH,
            direction=EvidenceDirection.SUPPORT,
        )
        assert rule.strength is EvidenceStrength.MODERATE
        assert rule.source_id == "BPHS"


class TestTraitRuleCatalog:
    """Tests for the TraitRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = TraitRuleCatalog(rules=(make_trait_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: TraitRuleCatalog) -> None:
        # Only one rule with INTELLECTUAL_DEPTH in sample
        depth = sample_catalog.get_rules_by_outcome(
            TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH,
        )
        assert len(depth) == 1

    def test_get_rule_by_id(self, sample_catalog: TraitRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-TEST-002")
        assert rule is not None
        assert rule.rule_id == "R-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: TraitRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: TraitRuleCatalog) -> None:
        d = sample_catalog.to_dict()
        assert d["rule_count"] == 6
        assert len(d["rules"]) == 6


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
        assert evaluate_condition("x>5", {"x": 4}) is False

    def test_less_than(self) -> None:
        assert evaluate_condition("x<5", {"x": 4}) is True
        assert evaluate_condition("x<5", {"x": 5}) is False

    def test_greater_or_equal(self) -> None:
        assert evaluate_condition("x>=5", {"x": 5}) is True
        assert evaluate_condition("x>=5", {"x": 6}) is True
        assert evaluate_condition("x>=5", {"x": 4}) is False

    def test_less_or_equal(self) -> None:
        assert evaluate_condition("x<=5", {"x": 5}) is True
        assert evaluate_condition("x<=5", {"x": 4}) is True
        assert evaluate_condition("x<=5", {"x": 6}) is False

    def test_membership(self) -> None:
        assert evaluate_condition("x in (1,2,3)", {"x": 2}) is True
        assert evaluate_condition("x in (1,2,3)", {"x": 4}) is False
        assert evaluate_condition("x in (a,b)", {"x": "a"}) is True

    def test_membership_string_values(self) -> None:
        assert (
            evaluate_condition(
                "nakshatra in (ASHWINI,MOOLA)", {"nakshatra": "ASHWINI"}
            )
            is True
        )
        assert (
            evaluate_condition(
                "nakshatra in (ASHWINI,MOOLA)", {"nakshatra": "ROHINI"}
            )
            is False
        )

    def test_missing_fact(self) -> None:
        assert evaluate_condition("x>5", {}) is False
        assert evaluate_condition("flag", {}) is False

    def test_string_comparison(self) -> None:
        assert evaluate_condition("x=hello", {"x": "hello"}) is True
        assert evaluate_condition("x!=hello", {"x": "world"}) is True

    def test_equality_case_insensitive_boolean(self) -> None:
        assert evaluate_condition("flag=true", {"flag": True}) is True
        assert evaluate_condition("flag=false", {"flag": False}) is True


class TestEvaluateRule:
    """Tests for the evaluate_rule function."""

    def test_single_condition_match(self) -> None:
        rule = make_trait_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH.value

    def test_single_condition_no_match(self) -> None:
        rule = make_trait_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_trait_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_trait_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_trait_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None

    def test_record_fields_populated(self) -> None:
        rule = make_trait_rule(
            rule_id="R-POP",
            condition_facts=("x>5",),
        )
        record = evaluate_rule(rule, {"x": 10})
        assert record is not None
        assert record.rule_id == "R-POP"
        assert record.source_id == "BPHS"


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[TraitRule, ...]) -> None:
        facts = {"hora": "MERCURY"}
        records = evaluate_facts(sample_rules, facts)
        # Should match R-TEST-001 (INTELLECTUAL_DEPTH)
        assert len(records) >= 1
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH.value in outcomes

    def test_no_rules_match(self, sample_rules: tuple[TraitRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[TraitRule, ...]) -> None:
        facts = {"hora": "MERCURY"}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure an INTELLECTUAL_DEPTH rule doesn't trigger LEADERSHIP_TENDENCY."""
        rules = (
            make_trait_rule(
                rule_id="R-INTEL",
                outcome=TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH,
                condition_facts=("hora=MERCURY",),
            ),
            make_trait_rule(
                rule_id="R-LEAD",
                outcome=TraitOutcomeTaxonomy.LEADERSHIP_TENDENCY,
                condition_facts=("hora=SUN",),
            ),
        )
        records = evaluate_facts(rules, {"hora": "MERCURY"})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH.value

    def test_membership_condition(self) -> None:
        rules = (
            make_trait_rule(
                rule_id="R-NAK",
                outcome=TraitOutcomeTaxonomy.SPIRITUAL_INCLINATION,
                condition_facts=("nakshatra in (ASHWINI,MOOLA)",),
            ),
        )
        records = evaluate_facts(rules, {"nakshatra": "ASHWINI"})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == TraitOutcomeTaxonomy.SPIRITUAL_INCLINATION.value

"""Unit tests for marriage domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest

from tests.unit.jrs.domains.marriage.conftest import make_marriage_rule
from jrs.domains.marriage.models import (
    MarriageConfig,
    MarriageOutcomeTaxonomy,
    MarriageRule,
    MarriageRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength


class TestMarriageOutcomeTaxonomy:
    """Tests for the MarriageOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in MarriageOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(MarriageOutcomeTaxonomy) == 14

    def test_outcome_from_value(self) -> None:
        assert MarriageOutcomeTaxonomy("MARRIAGE_FORMATION") is MarriageOutcomeTaxonomy.MARRIAGE_FORMATION
        assert MarriageOutcomeTaxonomy("DELAYED_MARRIAGE") is MarriageOutcomeTaxonomy.DELAYED_MARRIAGE

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            MarriageOutcomeTaxonomy("INVALID")

    def test_remarrige_divorce_vs_spouse_death(self) -> None:
        """Verify divorce and spouse death are distinct taxonomies."""
        assert MarriageOutcomeTaxonomy.REMARRIAGE_AFTER_DIVORCE is not MarriageOutcomeTaxonomy.REMARRIAGE_AFTER_SPOUSE_DEATH
        assert MarriageOutcomeTaxonomy.REMARRIAGE_AFTER_DIVORCE.value != MarriageOutcomeTaxonomy.REMARRIAGE_AFTER_SPOUSE_DEATH.value


class TestMarriageRule:
    """Tests for the MarriageRule model."""

    def test_creation(self) -> None:
        rule = make_marriage_rule(rule_id="R-TEST")
        assert rule.rule_id == "R-TEST"
        assert rule.outcome is MarriageOutcomeTaxonomy.MARRIAGE_FORMATION

    def test_frozen(self) -> None:
        rule = make_marriage_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_marriage_rule(
            rule_id="R-100",
            outcome=MarriageOutcomeTaxonomy.DELAYED_MARRIAGE,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "R-100"
        assert d["outcome"] == "DELAYED_MARRIAGE"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_marriage_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_defaults(self) -> None:
        rule = MarriageRule(
            rule_id="R-001",
            description="Test",
            condition_facts=("fact_a",),
            outcome=MarriageOutcomeTaxonomy.MARRIAGE_FORMATION,
            direction=EvidenceDirection.SUPPORT,
        )
        assert rule.strength is EvidenceStrength.MODERATE
        assert rule.source_id == "BPHS"


class TestMarriageRuleCatalog:
    """Tests for the MarriageRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = MarriageRuleCatalog(rules=(make_marriage_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: MarriageRuleCatalog) -> None:
        formation = sample_catalog.get_rules_by_outcome(
            MarriageOutcomeTaxonomy.MARRIAGE_FORMATION,
        )
        assert len(formation) == 2  # R-TEST-001 and R-TEST-006

    def test_get_rule_by_id(self, sample_catalog: MarriageRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-TEST-002")
        assert rule is not None
        assert rule.rule_id == "R-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: MarriageRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: MarriageRuleCatalog) -> None:
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

    def test_missing_fact(self) -> None:
        assert evaluate_condition("x>5", {}) is False
        assert evaluate_condition("flag", {}) is False

    def test_string_comparison(self) -> None:
        assert evaluate_condition("x=hello", {"x": "hello"}) is True
        assert evaluate_condition("x!=hello", {"x": "world"}) is True


class TestEvaluateRule:
    """Tests for the evaluate_rule function."""

    def test_single_condition_match(self) -> None:
        rule = make_marriage_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == MarriageOutcomeTaxonomy.MARRIAGE_FORMATION.value

    def test_single_condition_no_match(self) -> None:
        rule = make_marriage_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_marriage_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_marriage_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_marriage_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None

    def test_record_fields_populated(self) -> None:
        rule = make_marriage_rule(
            rule_id="R-POP",
            condition_facts=("x>5",),
        )
        record = evaluate_rule(rule, {"x": 10})
        assert record is not None
        assert record.rule_id == "R-POP"
        assert record.source_id == "BPHS"


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[MarriageRule, ...]) -> None:
        facts = {
            "7th_lord_in_kendra_or_trikona": True,
            "saturn_aspects_7th_lord": True,
            "venus_bala": 7.0,
        }
        records = evaluate_facts(sample_rules, facts)
        # Should match R-TEST-001 (formation), R-TEST-002 (delay), R-TEST-006 (formation)
        assert len(records) >= 2

    def test_no_rules_match(self, sample_rules: tuple[MarriageRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[MarriageRule, ...]) -> None:
        facts = {"7th_lord_in_kendra_or_trikona": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_mitigation_rule(self, sample_rules: tuple[MarriageRule, ...]) -> None:
        """Test that mitigation rules fire alongside support rules."""
        facts = {
            "saturn_aspects_7th_lord": True,
            "jupiter_aspects_7th": True,
        }
        records = evaluate_facts(sample_rules, facts)
        directions = {r.direction for r in records}
        assert EvidenceDirection.SUPPORT in directions
        assert EvidenceDirection.MITIGATE in directions

    def test_no_false_cross_contamination(self) -> None:
        """Ensure a 'second marriage' rule doesn't trigger 'multiple spouses'."""
        rules = (
            make_marriage_rule(
                rule_id="R-DIVORCE",
                outcome=MarriageOutcomeTaxonomy.REMARRIAGE_AFTER_DIVORCE,
                condition_facts=("divorce_indicator=true",),
            ),
            make_marriage_rule(
                rule_id="R-MULTI",
                outcome=MarriageOutcomeTaxonomy.MULTIPLE_SIMULTANEOUS_SPOUSES,
                condition_facts=("multiple_partners=true",),
            ),
        )
        records = evaluate_facts(rules, {"divorce_indicator": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == MarriageOutcomeTaxonomy.REMARRIAGE_AFTER_DIVORCE.value

    def test_numeric_comparison(self) -> None:
        rules = (
            make_marriage_rule(
                rule_id="R-BALA",
                outcome=MarriageOutcomeTaxonomy.MARRIAGE_FORMATION,
                condition_facts=("venus_bala>6.0",),
            ),
        )
        records = evaluate_facts(rules, {"venus_bala": 7.5})
        assert len(records) == 1

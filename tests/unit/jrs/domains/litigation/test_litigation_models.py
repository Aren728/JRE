"""Unit tests for litigation domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.litigation.conftest import make_litigation_rule

from jrs.domains.litigation.models import (
    LitigationConfig,
    LitigationOutcomeTaxonomy,
    LitigationRule,
    LitigationRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestLitigationOutcomeTaxonomy:
    """Tests for the LitigationOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in LitigationOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(LitigationOutcomeTaxonomy) == 6

    def test_outcome_from_value(self) -> None:
        vic = LitigationOutcomeTaxonomy("LEGAL_VICTORY")
        assert vic is LitigationOutcomeTaxonomy.LEGAL_VICTORY
        crm = LitigationOutcomeTaxonomy("CRIMINAL_LITIGATION")
        assert crm is LitigationOutcomeTaxonomy.CRIMINAL_LITIGATION

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            LitigationOutcomeTaxonomy("INVALID")

    def test_all_six_outcomes_exist(self) -> None:
        assert LitigationOutcomeTaxonomy.LEGAL_VICTORY.value == "LEGAL_VICTORY"
        assert LitigationOutcomeTaxonomy.LEGAL_DEFEAT.value == "LEGAL_DEFEAT"
        assert LitigationOutcomeTaxonomy.PROLONGED_LITIGATION.value == "PROLONGED_LITIGATION"
        assert LitigationOutcomeTaxonomy.SETTLEMENT_OUT_OF_COURT.value == "SETTLEMENT_OUT_OF_COURT"
        assert LitigationOutcomeTaxonomy.FALSE_ACCUSATION.value == "FALSE_ACCUSATION"
        assert LitigationOutcomeTaxonomy.CRIMINAL_LITIGATION.value == "CRIMINAL_LITIGATION"


class TestLitigationRule:
    """Tests for the LitigationRule model."""

    def test_creation(self) -> None:
        rule = make_litigation_rule(rule_id="LIT-TEST")
        assert rule.rule_id == "LIT-TEST"
        assert rule.outcome is LitigationOutcomeTaxonomy.LEGAL_VICTORY

    def test_frozen(self) -> None:
        rule = make_litigation_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_litigation_rule(
            rule_id="LIT-100",
            outcome=LitigationOutcomeTaxonomy.LEGAL_DEFEAT,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "LIT-100"
        assert d["outcome"] == "LEGAL_DEFEAT"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_litigation_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestLitigationRuleCatalog:
    """Tests for the LitigationRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = LitigationRuleCatalog(rules=(make_litigation_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: LitigationRuleCatalog) -> None:
        vic = sample_catalog.get_rules_by_outcome(LitigationOutcomeTaxonomy.LEGAL_VICTORY)
        assert len(vic) == 1

    def test_get_rule_by_id(self, sample_catalog: LitigationRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("LIT-TEST-002")
        assert rule is not None
        assert rule.rule_id == "LIT-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: LitigationRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("LIT-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: LitigationRuleCatalog) -> None:
        d = sample_catalog.to_dict()
        assert d["rule_count"] == 7
        assert len(d["rules"]) == 7


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
        rule = make_litigation_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == LitigationOutcomeTaxonomy.LEGAL_VICTORY.value

    def test_single_condition_no_match(self) -> None:
        rule = make_litigation_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_litigation_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_litigation_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_litigation_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[LitigationRule, ...]) -> None:
        facts = {
            "6th_lord_strong": True,
            "benefic_aspects_6th": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 1

    def test_no_rules_match(self, sample_rules: tuple[LitigationRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[LitigationRule, ...]) -> None:
        facts = {"6th_lord_strong": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure a 'victory' rule doesn't trigger 'defeat'."""
        rules = (
            make_litigation_rule(
                rule_id="LIT-VIC",
                outcome=LitigationOutcomeTaxonomy.LEGAL_VICTORY,
                condition_facts=("6th_lord_strong=true",),
            ),
            make_litigation_rule(
                rule_id="LIT-DEF",
                outcome=LitigationOutcomeTaxonomy.LEGAL_DEFEAT,
                condition_facts=("6th_lord_debilitated=true",),
            ),
        )
        records = evaluate_facts(rules, {"6th_lord_strong": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == LitigationOutcomeTaxonomy.LEGAL_VICTORY.value

    def test_prolonged_vs_settlement_distinction(self) -> None:
        """Ensure prolonged litigation ≠ settlement out of court."""
        rules = (
            make_litigation_rule(
                rule_id="LIT-PRO",
                outcome=LitigationOutcomeTaxonomy.PROLONGED_LITIGATION,
                condition_facts=("saturn_aspecting_7th=true",),
            ),
            make_litigation_rule(
                rule_id="LIT-SET",
                outcome=LitigationOutcomeTaxonomy.SETTLEMENT_OUT_OF_COURT,
                condition_facts=("venus_strong=true",),
            ),
        )
        # Saturn fact triggers prolonged, not settlement
        records = evaluate_facts(rules, {"saturn_aspecting_7th": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == LitigationOutcomeTaxonomy.PROLONGED_LITIGATION.value
        # Venus fact triggers settlement, not prolonged
        records = evaluate_facts(rules, {"venus_strong": True})
        assert len(records) == 1
        expected = LitigationOutcomeTaxonomy.SETTLEMENT_OUT_OF_COURT.value
        assert records[0].outcome_taxonomy == expected

    def test_criminal_vs_false_accusation_distinction(self) -> None:
        """Ensure criminal litigation ≠ false accusation."""
        rules = (
            make_litigation_rule(
                rule_id="LIT-CRI",
                outcome=LitigationOutcomeTaxonomy.CRIMINAL_LITIGATION,
                condition_facts=("mars_saturn_conjunction_6th=true",),
            ),
            make_litigation_rule(
                rule_id="LIT-FAL",
                outcome=LitigationOutcomeTaxonomy.FALSE_ACCUSATION,
                condition_facts=("rahu_afflicting_6th_lord=true",),
            ),
        )
        records = evaluate_facts(rules, {"mars_saturn_conjunction_6th": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == LitigationOutcomeTaxonomy.CRIMINAL_LITIGATION.value


class TestLitigationConfig:
    """Tests for the LitigationConfig model."""

    def test_defaults(self) -> None:
        config = LitigationConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = LitigationConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

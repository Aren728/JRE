"""Unit tests for progeny domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.progeny.conftest import make_progeny_rule

from jrs.domains.progeny.models import (
    ProgenyConfig,
    ProgenyOutcomeTaxonomy,
    ProgenyRule,
    ProgenyRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestProgenyOutcomeTaxonomy:
    """Tests for the ProgenyOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in ProgenyOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(ProgenyOutcomeTaxonomy) == 8

    def test_outcome_from_value(self) -> None:
        easy = ProgenyOutcomeTaxonomy("EASY_CONCEPTION")
        assert easy is ProgenyOutcomeTaxonomy.EASY_CONCEPTION
        delay = ProgenyOutcomeTaxonomy("DELAYED_PROGENY")
        assert delay is ProgenyOutcomeTaxonomy.DELAYED_PROGENY

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            ProgenyOutcomeTaxonomy("INVALID")


class TestProgenyRule:
    """Tests for the ProgenyRule model."""

    def test_creation(self) -> None:
        rule = make_progeny_rule(rule_id="R-TEST")
        assert rule.rule_id == "R-TEST"
        assert rule.outcome is ProgenyOutcomeTaxonomy.EASY_CONCEPTION

    def test_frozen(self) -> None:
        rule = make_progeny_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_progeny_rule(
            rule_id="R-100",
            outcome=ProgenyOutcomeTaxonomy.MISCARRIAGE_RISK,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "R-100"
        assert d["outcome"] == "MISCARRIAGE_RISK"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_progeny_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestProgenyRuleCatalog:
    """Tests for the ProgenyRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = ProgenyRuleCatalog(rules=(make_progeny_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: ProgenyRuleCatalog) -> None:
        easy = sample_catalog.get_rules_by_outcome(ProgenyOutcomeTaxonomy.EASY_CONCEPTION)
        assert len(easy) == 1

    def test_get_rule_by_id(self, sample_catalog: ProgenyRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-TEST-002")
        assert rule is not None
        assert rule.rule_id == "R-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: ProgenyRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: ProgenyRuleCatalog) -> None:
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
        rule = make_progeny_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == ProgenyOutcomeTaxonomy.EASY_CONCEPTION.value

    def test_single_condition_no_match(self) -> None:
        rule = make_progeny_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_progeny_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_progeny_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_progeny_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[ProgenyRule, ...]) -> None:
        facts = {
            "jupiter_strong": True,
            "5th_lord_in_kendra": True,
            "saturn_in_5th": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 2

    def test_no_rules_match(self, sample_rules: tuple[ProgenyRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[ProgenyRule, ...]) -> None:
        facts = {"jupiter_strong": True, "5th_lord_in_kendra": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure 'challenges' rule doesn't trigger 'miscarriage'."""
        rules = (
            make_progeny_rule(
                rule_id="R-CHAL",
                outcome=ProgenyOutcomeTaxonomy.CHALLENGES_WITH_CHILDREN,
                condition_facts=("malefic_in_5th=true",),
            ),
            make_progeny_rule(
                rule_id="R-MISC",
                outcome=ProgenyOutcomeTaxonomy.MISCARRIAGE_RISK,
                condition_facts=("mars_in_5th=true",),
            ),
        )
        records = evaluate_facts(rules, {"malefic_in_5th": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == ProgenyOutcomeTaxonomy.CHALLENGES_WITH_CHILDREN.value

    def test_numeric_comparison(self) -> None:
        rules = (
            make_progeny_rule(
                rule_id="R-BALA",
                outcome=ProgenyOutcomeTaxonomy.CHILDREN_SUCCESS,
                condition_facts=("jupiter_bala>6.0",),
            ),
        )
        records = evaluate_facts(rules, {"jupiter_bala": 7.5})
        assert len(records) == 1


class TestProgenyConfig:
    """Tests for the ProgenyConfig model."""

    def test_defaults(self) -> None:
        config = ProgenyConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = ProgenyConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

"""Unit tests for wealth domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.wealth.conftest import make_wealth_rule

from jrs.domains.wealth.models import (
    WealthConfig,
    WealthOutcomeTaxonomy,
    WealthRule,
    WealthRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestWealthOutcomeTaxonomy:
    """Tests for the WealthOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in WealthOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(WealthOutcomeTaxonomy) == 14

    def test_outcome_from_value(self) -> None:
        acc = WealthOutcomeTaxonomy("WEALTH_ACCUMULATION")
        assert acc is WealthOutcomeTaxonomy.WEALTH_ACCUMULATION
        biz = WealthOutcomeTaxonomy("BUSINESS_WEALTH")
        assert biz is WealthOutcomeTaxonomy.BUSINESS_WEALTH

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            WealthOutcomeTaxonomy("INVALID")


class TestWealthRule:
    """Tests for the WealthRule model."""

    def test_creation(self) -> None:
        rule = make_wealth_rule(rule_id="R-TEST")
        assert rule.rule_id == "R-TEST"
        assert rule.outcome is WealthOutcomeTaxonomy.WEALTH_ACCUMULATION

    def test_frozen(self) -> None:
        rule = make_wealth_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_wealth_rule(
            rule_id="R-100",
            outcome=WealthOutcomeTaxonomy.DEBT_BURDEN,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "R-100"
        assert d["outcome"] == "DEBT_BURDEN"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_wealth_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestWealthRuleCatalog:
    """Tests for the WealthRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = WealthRuleCatalog(rules=(make_wealth_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: WealthRuleCatalog) -> None:
        acc = sample_catalog.get_rules_by_outcome(WealthOutcomeTaxonomy.WEALTH_ACCUMULATION)
        assert len(acc) == 1

    def test_get_rule_by_id(self, sample_catalog: WealthRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-TEST-002")
        assert rule is not None
        assert rule.rule_id == "R-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: WealthRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: WealthRuleCatalog) -> None:
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
        rule = make_wealth_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == WealthOutcomeTaxonomy.WEALTH_ACCUMULATION.value

    def test_single_condition_no_match(self) -> None:
        rule = make_wealth_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_wealth_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_wealth_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_wealth_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[WealthRule, ...]) -> None:
        facts = {
            "2nd_lord_in_11th": True,
            "saturn_afflicts_2nd_lord": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 2

    def test_no_rules_match(self, sample_rules: tuple[WealthRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[WealthRule, ...]) -> None:
        facts = {"2nd_lord_in_11th": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure a 'business wealth' rule doesn't trigger 'debt burden'."""
        rules = (
            make_wealth_rule(
                rule_id="R-BIZ",
                outcome=WealthOutcomeTaxonomy.BUSINESS_WEALTH,
                condition_facts=("mercury_strong=true",),
            ),
            make_wealth_rule(
                rule_id="R-DEBT",
                outcome=WealthOutcomeTaxonomy.DEBT_BURDEN,
                condition_facts=("saturn_in_2nd=true",),
            ),
        )
        records = evaluate_facts(rules, {"mercury_strong": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == WealthOutcomeTaxonomy.BUSINESS_WEALTH.value

    def test_numeric_comparison(self) -> None:
        rules = (
            make_wealth_rule(
                rule_id="R-BALA",
                outcome=WealthOutcomeTaxonomy.WEALTH_ACCUMULATION,
                condition_facts=("jupiter_bala>6.0",),
            ),
        )
        records = evaluate_facts(rules, {"jupiter_bala": 7.5})
        assert len(records) == 1


class TestWealthConfig:
    """Tests for the WealthConfig model."""

    def test_defaults(self) -> None:
        config = WealthConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = WealthConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

"""Unit tests for business domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.business.conftest import make_business_rule

from jrs.domains.business.models import (
    BusinessConfig,
    BusinessOutcomeTaxonomy,
    BusinessRule,
    BusinessRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestBusinessOutcomeTaxonomy:
    """Tests for the BusinessOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in BusinessOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(BusinessOutcomeTaxonomy) == 6

    def test_outcome_from_value(self) -> None:
        ent = BusinessOutcomeTaxonomy("SUCCESSFUL_ENTREPRENEURSHIP")
        assert ent is BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP
        biz = BusinessOutcomeTaxonomy("BUSINESS_PARTNERSHIP")
        assert biz is BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            BusinessOutcomeTaxonomy("INVALID")

    def test_all_six_outcomes_exist(self) -> None:
        ent = BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP
        assert ent.value == "SUCCESSFUL_ENTREPRENEURSHIP"
        biz = BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP
        assert biz.value == "BUSINESS_PARTNERSHIP"
        fail = BusinessOutcomeTaxonomy.BUSINESS_FAILURE
        assert fail.value == "BUSINESS_FAILURE"
        self_emp = BusinessOutcomeTaxonomy.SELF_EMPLOYMENT
        assert self_emp.value == "SELF_EMPLOYMENT"
        franchise = BusinessOutcomeTaxonomy.FRANCHISE_AGENCY
        assert franchise.value == "FRANCHISE_AGENCY"
        fam = BusinessOutcomeTaxonomy.FAMILY_BUSINESS
        assert fam.value == "FAMILY_BUSINESS"


class TestBusinessRule:
    """Tests for the BusinessRule model."""

    def test_creation(self) -> None:
        rule = make_business_rule(rule_id="BIZ-TEST")
        assert rule.rule_id == "BIZ-TEST"
        assert rule.outcome is BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP

    def test_frozen(self) -> None:
        rule = make_business_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_business_rule(
            rule_id="BIZ-100",
            outcome=BusinessOutcomeTaxonomy.BUSINESS_FAILURE,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "BIZ-100"
        assert d["outcome"] == "BUSINESS_FAILURE"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_business_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestBusinessRuleCatalog:
    """Tests for the BusinessRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = BusinessRuleCatalog(rules=(make_business_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: BusinessRuleCatalog) -> None:
        ent = BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP
        rules = sample_catalog.get_rules_by_outcome(ent)
        assert len(rules) == 1

    def test_get_rule_by_id(self, sample_catalog: BusinessRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("BIZ-TEST-002")
        assert rule is not None
        assert rule.rule_id == "BIZ-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: BusinessRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("BIZ-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: BusinessRuleCatalog) -> None:
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

    def test_less_than(self) -> None:
        assert evaluate_condition("x<5", {"x": 4}) is True
        assert evaluate_condition("x<5", {"x": 5}) is False

    def test_membership(self) -> None:
        assert evaluate_condition("x in (1,2,3)", {"x": 2}) is True
        assert evaluate_condition("x in (1,2,3)", {"x": 4}) is False

    def test_missing_fact(self) -> None:
        assert evaluate_condition("x>5", {}) is False

    def test_string_equality(self) -> None:
        assert evaluate_condition("sign=Taurus", {"sign": "Taurus"}) is True
        assert evaluate_condition("sign=Taurus", {"sign": "Gemini"}) is False

    def test_numeric_comparison(self) -> None:
        assert evaluate_condition("jupiter_bala>6.0", {"jupiter_bala": 7.5}) is True
        assert evaluate_condition("jupiter_bala<6.0", {"jupiter_bala": 3.0}) is True


class TestEvaluateRule:
    """Tests for the evaluate_rule function."""

    def test_single_condition_match(self) -> None:
        rule = make_business_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP.value

    def test_single_condition_no_match(self) -> None:
        rule = make_business_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_business_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_business_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_business_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[BusinessRule, ...]) -> None:
        facts = {
            "mercury_strong": True,
            "10th_lord_connection": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 1

    def test_no_rules_match(self, sample_rules: tuple[BusinessRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[BusinessRule, ...]) -> None:
        facts = {"mercury_strong": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure a 'partnership' rule doesn't trigger 'failure'."""
        rules = (
            make_business_rule(
                rule_id="BIZ-BIZ",
                outcome=BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP,
                condition_facts=("mercury_strong=true",),
            ),
            make_business_rule(
                rule_id="BIZ-FAIL",
                outcome=BusinessOutcomeTaxonomy.BUSINESS_FAILURE,
                condition_facts=("saturn_afflicting_7th=true",),
            ),
        )
        records = evaluate_facts(rules, {"mercury_strong": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP.value

    def test_numeric_comparison(self) -> None:
        rules = (
            make_business_rule(
                rule_id="BIZ-BALA",
                outcome=BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP,
                condition_facts=("mercury_bala>6.0",),
            ),
        )
        records = evaluate_facts(rules, {"mercury_bala": 7.5})
        assert len(records) == 1


class TestBusinessConfig:
    """Tests for the BusinessConfig model."""

    def test_defaults(self) -> None:
        config = BusinessConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = BusinessConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

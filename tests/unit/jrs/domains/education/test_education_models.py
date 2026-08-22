"""Unit tests for education domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.education.conftest import make_education_rule

from jrs.domains.education.models import (
    EducationConfig,
    EducationOutcomeTaxonomy,
    EducationRule,
    EducationRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestEducationOutcomeTaxonomy:
    """Tests for the EducationOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in EducationOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(EducationOutcomeTaxonomy) == 6

    def test_outcome_from_value(self) -> None:
        high = EducationOutcomeTaxonomy("HIGHER_EDUCATION")
        assert high is EducationOutcomeTaxonomy.HIGHER_EDUCATION
        tech = EducationOutcomeTaxonomy("TECHNICAL_SKILLS")
        assert tech is EducationOutcomeTaxonomy.TECHNICAL_SKILLS

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            EducationOutcomeTaxonomy("INVALID")


class TestEducationRule:
    """Tests for the EducationRule model."""

    def test_creation(self) -> None:
        rule = make_education_rule(rule_id="R-TEST")
        assert rule.rule_id == "R-TEST"
        assert rule.outcome is EducationOutcomeTaxonomy.HIGHER_EDUCATION

    def test_frozen(self) -> None:
        rule = make_education_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_education_rule(
            rule_id="R-100",
            outcome=EducationOutcomeTaxonomy.EDUCATION_DISRUPTION,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "R-100"
        assert d["outcome"] == "EDUCATION_DISRUPTION"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_education_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestEducationRuleCatalog:
    """Tests for the EducationRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = EducationRuleCatalog(rules=(make_education_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: EducationRuleCatalog) -> None:
        high = sample_catalog.get_rules_by_outcome(EducationOutcomeTaxonomy.HIGHER_EDUCATION)
        assert len(high) == 1

    def test_get_rule_by_id(self, sample_catalog: EducationRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-TEST-002")
        assert rule is not None
        assert rule.rule_id == "R-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: EducationRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("R-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: EducationRuleCatalog) -> None:
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
        rule = make_education_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == EducationOutcomeTaxonomy.HIGHER_EDUCATION.value

    def test_single_condition_no_match(self) -> None:
        rule = make_education_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_education_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_education_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_education_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[EducationRule, ...]) -> None:
        facts = {
            "4th_lord_in_kendra": True,
            "saturn_in_4th": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 2

    def test_no_rules_match(self, sample_rules: tuple[EducationRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[EducationRule, ...]) -> None:
        facts = {"4th_lord_in_kendra": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure 'higher education' rule doesn't trigger 'education disruption'."""
        rules = (
            make_education_rule(
                rule_id="R-HIGH",
                outcome=EducationOutcomeTaxonomy.HIGHER_EDUCATION,
                condition_facts=("4th_lord_in_kendra=true",),
            ),
            make_education_rule(
                rule_id="R-DISC",
                outcome=EducationOutcomeTaxonomy.EDUCATION_DISRUPTION,
                condition_facts=("saturn_in_4th=true",),
            ),
        )
        records = evaluate_facts(rules, {"4th_lord_in_kendra": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == EducationOutcomeTaxonomy.HIGHER_EDUCATION.value

    def test_numeric_comparison(self) -> None:
        rules = (
            make_education_rule(
                rule_id="R-BALA",
                outcome=EducationOutcomeTaxonomy.TECHNICAL_SKILLS,
                condition_facts=("jupiter_bala>6.0",),
            ),
        )
        records = evaluate_facts(rules, {"jupiter_bala": 7.5})
        assert len(records) == 1


class TestEducationConfig:
    """Tests for the EducationConfig model."""

    def test_defaults(self) -> None:
        config = EducationConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = EducationConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

"""Unit tests for health domain models and fact evaluation logic.

Includes safety validation tests to ensure no medical terminology
is generated or permitted in the system.
"""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.health.conftest import make_health_rule

from jrs.domains.health.models import (
    HealthConfig,
    HealthOutcomeTaxonomy,
    HealthRule,
    HealthRuleCatalog,
    _validate_no_medical_terms,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestMedicalTermValidation:
    """CRITICAL SAFETY TESTS: Ensure no medical terminology is permitted."""

    def test_validate_clean_text(self) -> None:
        """Clean vitality text should pass."""
        _validate_no_medical_terms("High constitutional vitality indicators")

    def test_validate_rejects_disease(self) -> None:
        """Must reject 'disease'."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Has disease indicators")

    def test_validate_rejects_death(self) -> None:
        """Must reject 'death'."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Death prediction")

    def test_validate_rejects_surgery(self) -> None:
        """Must reject 'surgery'."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Surgery indicated")

    def test_validate_rejects_diagnosis(self) -> None:
        """Must reject 'diagnosis'."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Medical diagnosis")

    def test_validate_rejects_illness(self) -> None:
        """Must reject 'illness'."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Chronic illness")

    def test_validate_rejects_cancer(self) -> None:
        """Must reject 'cancer'."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Cancer risk")

    def test_validate_rejects_case_insensitive(self) -> None:
        """Validation must be case-insensitive."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Has DISEASE indicators")

    def test_validate_rejects_partial_match(self) -> None:
        """Validation must catch terms within larger words."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            _validate_no_medical_terms("Diseased constitution")

    def test_health_rule_rejects_medical_description(self) -> None:
        """HealthRule creation must reject medical terms in description."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            HealthRule(
                rule_id="BAD-001",
                description="Disease prediction",
                condition_facts=("test=true",),
                outcome=HealthOutcomeTaxonomy.HIGH_VITALITY,
                direction=EvidenceDirection.SUPPORT,
            )

    def test_health_rule_rejects_medical_condition(self) -> None:
        """HealthRule creation must reject medical terms in conditions."""
        with pytest.raises(ValueError, match="Forbidden medical term"):
            HealthRule(
                rule_id="BAD-002",
                description="Vitality check",
                condition_facts=("has_disease=true",),
                outcome=HealthOutcomeTaxonomy.HIGH_VITALITY,
                direction=EvidenceDirection.SUPPORT,
            )


class TestHealthOutcomeTaxonomy:
    """Tests for the HealthOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in HealthOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(HealthOutcomeTaxonomy) == 6

    def test_outcome_from_value(self) -> None:
        hv = HealthOutcomeTaxonomy("HIGH_VITALITY")
        assert hv is HealthOutcomeTaxonomy.HIGH_VITALITY
        cs = HealthOutcomeTaxonomy("CHRONIC_STRESS")
        assert cs is HealthOutcomeTaxonomy.CHRONIC_STRESS

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            HealthOutcomeTaxonomy("INVALID")

    def test_all_six_outcomes_are_vitality_terms(self) -> None:
        """All outcomes must be vitality/constitution terms, never medical."""
        assert HealthOutcomeTaxonomy.HIGH_VITALITY.value == "HIGH_VITALITY"
        assert HealthOutcomeTaxonomy.LOW_VITALITY.value == "LOW_VITALITY"
        assert HealthOutcomeTaxonomy.CHRONIC_STRESS.value == "CHRONIC_STRESS"
        assert HealthOutcomeTaxonomy.STRONG_RECOVERY_CAPACITY.value == (
            "STRONG_RECOVERY_CAPACITY"
        )
        assert HealthOutcomeTaxonomy.ENERGY_FLUCTUATIONS.value == "ENERGY_FLUCTUATIONS"
        assert HealthOutcomeTaxonomy.TRADITIONAL_CONSTITUTION_INDICATORS.value == (
            "TRADITIONAL_CONSTITUTION_INDICATORS"
        )


class TestHealthRule:
    """Tests for the HealthRule model."""

    def test_creation(self) -> None:
        rule = make_health_rule(rule_id="HLTH-TEST")
        assert rule.rule_id == "HLTH-TEST"
        assert rule.outcome is HealthOutcomeTaxonomy.HIGH_VITALITY

    def test_frozen(self) -> None:
        rule = make_health_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_health_rule(
            rule_id="HLTH-100",
            outcome=HealthOutcomeTaxonomy.LOW_VITALITY,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "HLTH-100"
        assert d["outcome"] == "LOW_VITALITY"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_health_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_rule_output_never_contains_medical_terms(self) -> None:
        """Verify rule descriptions and outcomes contain no medical terms."""
        rule = make_health_rule()
        d = rule.to_dict()
        # Outcome taxonomy must be a vitality term
        assert "DISEASE" not in d["outcome"].upper()
        assert "DEATH" not in d["outcome"].upper()
        assert "SURGERY" not in d["outcome"].upper()


class TestHealthRuleCatalog:
    """Tests for the HealthRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = HealthRuleCatalog(rules=(make_health_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: HealthRuleCatalog) -> None:
        hv = sample_catalog.get_rules_by_outcome(HealthOutcomeTaxonomy.HIGH_VITALITY)
        assert len(hv) == 1

    def test_get_rule_by_id(self, sample_catalog: HealthRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("HLTH-TEST-002")
        assert rule is not None
        assert rule.rule_id == "HLTH-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: HealthRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("HLTH-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: HealthRuleCatalog) -> None:
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
        rule = make_health_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == HealthOutcomeTaxonomy.HIGH_VITALITY.value

    def test_single_condition_no_match(self) -> None:
        rule = make_health_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_health_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_health_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_health_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None

    def test_output_never_contains_medical_terms(self) -> None:
        """Verify evaluate_rule output contains no medical terminology."""
        rule = make_health_rule()
        record = evaluate_rule(rule, {"test_fact": True})
        assert record is not None
        # The outcome taxonomy must be a vitality term
        assert "DISEASE" not in record.outcome_taxonomy
        assert "DEATH" not in record.outcome_taxonomy
        assert "SURGERY" not in record.outcome_taxonomy


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[HealthRule, ...]) -> None:
        facts = {
            "1st_lord_strong": True,
            "1st_lord_in_kendra": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 1

    def test_no_rules_match(self, sample_rules: tuple[HealthRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[HealthRule, ...]) -> None:
        facts = {"1st_lord_strong": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure a 'high_vitality' rule doesn't trigger 'low_vitality'."""
        rules = (
            make_health_rule(
                rule_id="HLTH-HV",
                outcome=HealthOutcomeTaxonomy.HIGH_VITALITY,
                condition_facts=("1st_lord_strong=true",),
            ),
            make_health_rule(
                rule_id="HLTH-LV",
                outcome=HealthOutcomeTaxonomy.LOW_VITALITY,
                condition_facts=("1st_lord_debilitated=true",),
            ),
        )
        records = evaluate_facts(rules, {"1st_lord_strong": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == HealthOutcomeTaxonomy.HIGH_VITALITY.value

    def test_output_never_contains_medical_terms(self) -> None:
        """Verify evaluate_facts output contains no medical terminology."""
        rules = (
            make_health_rule(
                rule_id="HLTH-V1",
                outcome=HealthOutcomeTaxonomy.HIGH_VITALITY,
            ),
            make_health_rule(
                rule_id="HLTH-V2",
                outcome=HealthOutcomeTaxonomy.CHRONIC_STRESS,
            ),
        )
        records = evaluate_facts(rules, {"test_fact": True})
        for record in records:
            assert "DISEASE" not in record.outcome_taxonomy
            assert "DEATH" not in record.outcome_taxonomy
            assert "SURGERY" not in record.outcome_taxonomy
            assert "DIAGNOSIS" not in record.outcome_taxonomy


class TestHealthConfig:
    """Tests for the HealthConfig model."""

    def test_defaults(self) -> None:
        config = HealthConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = HealthConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

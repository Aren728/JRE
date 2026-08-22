"""Unit tests for HealthDomainService.

Includes safety validation tests to ensure the service never produces
medical diagnosis terminology.
"""

from __future__ import annotations

import pytest

from jrs.domains.health.errors import InvalidFactError
from jrs.domains.health.models import (
    HealthConfig,
    HealthOutcomeTaxonomy,
    HealthRuleCatalog,
)
from jrs.domains.health.service import HealthDomainService
from jrs.evidence.models import EvidenceDirection


class TestMedicalTermSafety:
    """CRITICAL SAFETY TESTS: Ensure the service never produces medical terms."""

    def test_validate_output_safety_clean(self) -> None:
        """Service should validate clean vitality text as safe."""
        svc = HealthDomainService()
        assert svc.validate_output_safety("High vitality indicators") is True

    def test_validate_output_safety_rejects_disease(self) -> None:
        """Service must reject text containing 'disease'."""
        svc = HealthDomainService()
        assert svc.validate_output_safety("Has disease indicators") is False

    def test_validate_output_safety_rejects_death(self) -> None:
        """Service must reject text containing 'death'."""
        svc = HealthDomainService()
        assert svc.validate_output_safety("Death prediction") is False

    def test_validate_output_safety_rejects_surgery(self) -> None:
        """Service must reject text containing 'surgery'."""
        svc = HealthDomainService()
        assert svc.validate_output_safety("Surgery indicated") is False


class TestHealthDomainServiceInit:
    """Tests for HealthDomainService initialization."""

    def test_default_config(self) -> None:
        svc = HealthDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = HealthConfig(source_id="Phaladeepika")
        svc = HealthDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestHealthDomainServiceLoadRules:
    """Tests for the load_health_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = HealthDomainService()
        catalog = svc.load_health_rules()
        assert isinstance(catalog, HealthRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = HealthDomainService()
        catalog = svc.load_health_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, HealthOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = HealthDomainService()
        catalog = svc.load_health_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = HealthDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = HealthDomainService()
        c1 = svc.load_health_rules()
        c2 = svc.load_health_rules()
        assert c1.rules is c2.rules

    def test_all_rules_use_vitality_terminology(self) -> None:
        """Verify all loaded rules use vitality terms, not medical terms."""
        svc = HealthDomainService()
        catalog = svc.load_health_rules()
        medical_terms = {"disease", "death", "surgery", "diagnosis", "illness"}
        for rule in catalog.rules:
            desc_lower = rule.description.lower()
            for term in medical_terms:
                assert term not in desc_lower, (
                    f"Rule {rule.rule_id} contains forbidden term '{term}'"
                )


class TestHealthDomainServiceEvaluateFacts:
    """Tests for the evaluate_health_facts method."""

    def test_evaluate_high_vitality(self) -> None:
        svc = HealthDomainService()
        facts = {"1st_lord_strong": True, "1st_lord_in_kendra": True}
        records = svc.evaluate_health_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert HealthOutcomeTaxonomy.HIGH_VITALITY.value in outcomes

    def test_evaluate_chronic_stress(self) -> None:
        svc = HealthDomainService()
        facts = {"saturn_in_6th": True, "rahu_in_6th": True}
        records = svc.evaluate_health_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert HealthOutcomeTaxonomy.CHRONIC_STRESS.value in outcomes

    def test_evaluate_low_vitality(self) -> None:
        svc = HealthDomainService()
        facts = {"1st_lord_debilitated": True, "malefic_lagna": True}
        records = svc.evaluate_health_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert HealthOutcomeTaxonomy.LOW_VITALITY.value in outcomes

    def test_evaluate_recovery_capacity(self) -> None:
        svc = HealthDomainService()
        facts = {"jupiter_aspecting_1st": True, "1st_lord_strong": True}
        records = svc.evaluate_health_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert HealthOutcomeTaxonomy.STRONG_RECOVERY_CAPACITY.value in outcomes

    def test_evaluate_energy_fluctuations(self) -> None:
        svc = HealthDomainService()
        facts = {"moon_with_rahu": True, "moon_waning": True}
        records = svc.evaluate_health_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert HealthOutcomeTaxonomy.ENERGY_FLUCTUATIONS.value in outcomes

    def test_evaluate_traditional_constitution(self) -> None:
        svc = HealthDomainService()
        facts = {"1st_lord_own_sign": True, "ashtakavarga_high": True}
        records = svc.evaluate_health_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert HealthOutcomeTaxonomy.TRADITIONAL_CONSTITUTION_INDICATORS.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = HealthDomainService()
        records = svc.evaluate_health_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = HealthDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_health_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = HealthDomainService()
        facts = {"1st_lord_strong": True}
        r1 = svc.evaluate_health_facts(facts)
        r2 = svc.evaluate_health_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = HealthDomainService()
        facts = {"1st_lord_strong": True, "1st_lord_in_kendra": True}
        records = svc.evaluate_health_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)

    def test_output_never_contains_medical_terms(self) -> None:
        """CRITICAL: Verify all output records use vitality terminology only."""
        svc = HealthDomainService()
        facts = {
            "1st_lord_strong": True,
            "1st_lord_in_kendra": True,
            "saturn_in_6th": True,
            "rahu_in_6th": True,
            "1st_lord_debilitated": True,
            "malefic_lagna": True,
        }
        records = svc.evaluate_health_facts(facts)
        medical_terms = {"disease", "death", "surgery", "diagnosis", "illness"}
        for record in records:
            outcome_lower = record.outcome_taxonomy.lower()
            for term in medical_terms:
                assert term not in outcome_lower, (
                    f"Record {record.evidence_id} contains forbidden term '{term}'"
                )


class TestHealthDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = HealthDomainService()
        hv_rules = svc.get_rules_for_outcome(HealthOutcomeTaxonomy.HIGH_VITALITY)
        assert len(hv_rules) > 0
        for rule in hv_rules:
            assert rule.outcome is HealthOutcomeTaxonomy.HIGH_VITALITY

    def test_get_outcome_taxonomies(self) -> None:
        svc = HealthDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert HealthOutcomeTaxonomy.HIGH_VITALITY in outcomes
        assert HealthOutcomeTaxonomy.CHRONIC_STRESS in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = HealthDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

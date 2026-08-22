"""Unit tests for EducationDomainService."""

from __future__ import annotations

from pathlib import Path

import pytest

from jrs.domains.education.errors import InvalidFactError
from jrs.domains.education.models import (
    EducationConfig,
    EducationOutcomeTaxonomy,
    EducationRuleCatalog,
)
from jrs.domains.education.service import EducationDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "education.toml"
)


class TestEducationDomainServiceInit:
    """Tests for EducationDomainService initialization."""

    def test_default_config(self) -> None:
        svc = EducationDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = EducationConfig(source_id="Phaladeepika")
        svc = EducationDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestEducationDomainServiceLoadRules:
    """Tests for the load_education_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = EducationDomainService()
        catalog = svc.load_education_rules()
        assert isinstance(catalog, EducationRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = EducationDomainService()
        catalog = svc.load_education_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, EducationOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = EducationDomainService()
        catalog = svc.load_education_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = EducationDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = EducationDomainService()
        c1 = svc.load_education_rules()
        c2 = svc.load_education_rules()
        assert c1.rules is c2.rules


class TestEducationDomainServiceEvaluateFacts:
    """Tests for the evaluate_education_facts method."""

    def test_evaluate_higher_education(self) -> None:
        svc = EducationDomainService()
        facts = {"4th_lord_in_kendra": True}
        records = svc.evaluate_education_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert EducationOutcomeTaxonomy.HIGHER_EDUCATION.value in outcomes

    def test_evaluate_education_disruption(self) -> None:
        svc = EducationDomainService()
        facts = {"saturn_in_4th": True}
        records = svc.evaluate_education_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert EducationOutcomeTaxonomy.EDUCATION_DISRUPTION.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = EducationDomainService()
        records = svc.evaluate_education_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = EducationDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_education_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = EducationDomainService()
        facts = {"4th_lord_in_kendra": True}
        r1 = svc.evaluate_education_facts(facts)
        r2 = svc.evaluate_education_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = EducationDomainService()
        facts = {"4th_lord_in_kendra": True}
        records = svc.evaluate_education_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestEducationDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = EducationDomainService()
        high_rules = svc.get_rules_for_outcome(EducationOutcomeTaxonomy.HIGHER_EDUCATION)
        assert len(high_rules) > 0
        for rule in high_rules:
            assert rule.outcome is EducationOutcomeTaxonomy.HIGHER_EDUCATION

    def test_get_outcome_taxonomies(self) -> None:
        svc = EducationDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert EducationOutcomeTaxonomy.HIGHER_EDUCATION in outcomes
        assert EducationOutcomeTaxonomy.EDUCATION_DISRUPTION in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = EducationDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

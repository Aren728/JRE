"""Unit tests for BusinessDomainService."""

from __future__ import annotations

from pathlib import Path

import pytest

from jrs.domains.business.errors import InvalidFactError
from jrs.domains.business.models import (
    BusinessConfig,
    BusinessOutcomeTaxonomy,
    BusinessRuleCatalog,
)
from jrs.domains.business.service import BusinessDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "business.toml"
)


class TestBusinessDomainServiceInit:
    """Tests for BusinessDomainService initialization."""

    def test_default_config(self) -> None:
        svc = BusinessDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = BusinessConfig(source_id="Phaladeepika")
        svc = BusinessDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestBusinessDomainServiceLoadRules:
    """Tests for the load_business_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = BusinessDomainService()
        catalog = svc.load_business_rules()
        assert isinstance(catalog, BusinessRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = BusinessDomainService()
        catalog = svc.load_business_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, BusinessOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = BusinessDomainService()
        catalog = svc.load_business_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = BusinessDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = BusinessDomainService()
        c1 = svc.load_business_rules()
        c2 = svc.load_business_rules()
        assert c1.rules is c2.rules


class TestBusinessDomainServiceEvaluateFacts:
    """Tests for the evaluate_business_facts method."""

    def test_evaluate_entrepreneurship(self) -> None:
        svc = BusinessDomainService()
        facts = {"mercury_strong": True, "mercury_10th_connection": True}
        records = svc.evaluate_business_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP.value in outcomes

    def test_evaluate_partnership(self) -> None:
        svc = BusinessDomainService()
        facts = {"7th_lord_in_10th": True, "mercury_strong": True}
        records = svc.evaluate_business_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP.value in outcomes

    def test_evaluate_failure(self) -> None:
        svc = BusinessDomainService()
        facts = {"saturn_afflicts_10th_lord": True, "benefic_protection_10th": False}
        records = svc.evaluate_business_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert BusinessOutcomeTaxonomy.BUSINESS_FAILURE.value in outcomes

    def test_evaluate_self_employment(self) -> None:
        svc = BusinessDomainService()
        facts = {"mars_strong": True, "mars_in_3rd": True}
        records = svc.evaluate_business_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert BusinessOutcomeTaxonomy.SELF_EMPLOYMENT.value in outcomes

    def test_evaluate_family_business(self) -> None:
        svc = BusinessDomainService()
        facts = {"4th_lord_strong": True, "4th_10th_connection": True}
        records = svc.evaluate_business_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert BusinessOutcomeTaxonomy.FAMILY_BUSINESS.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = BusinessDomainService()
        records = svc.evaluate_business_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = BusinessDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_business_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = BusinessDomainService()
        facts = {"mercury_strong": True}
        r1 = svc.evaluate_business_facts(facts)
        r2 = svc.evaluate_business_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = BusinessDomainService()
        facts = {"mercury_strong": True, "mercury_10th_connection": True}
        records = svc.evaluate_business_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestBusinessDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = BusinessDomainService()
        part_rules = svc.get_rules_for_outcome(BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP)
        assert len(part_rules) > 0
        for rule in part_rules:
            assert rule.outcome is BusinessOutcomeTaxonomy.BUSINESS_PARTNERSHIP

    def test_get_outcome_taxonomies(self) -> None:
        svc = BusinessDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert BusinessOutcomeTaxonomy.SUCCESSFUL_ENTREPRENEURSHIP in outcomes
        assert BusinessOutcomeTaxonomy.BUSINESS_FAILURE in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = BusinessDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

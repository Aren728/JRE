"""Unit tests for PropertyDomainService."""

from __future__ import annotations

from pathlib import Path

import pytest

from jrs.domains.property.errors import InvalidFactError
from jrs.domains.property.models import (
    PropertyConfig,
    PropertyOutcomeTaxonomy,
    PropertyRuleCatalog,
)
from jrs.domains.property.service import PropertyDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "property.toml"
)


class TestPropertyDomainServiceInit:
    """Tests for PropertyDomainService initialization."""

    def test_default_config(self) -> None:
        svc = PropertyDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = PropertyConfig(source_id="Phaladeepika")
        svc = PropertyDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestPropertyDomainServiceLoadRules:
    """Tests for the load_property_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = PropertyDomainService()
        catalog = svc.load_property_rules()
        assert isinstance(catalog, PropertyRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = PropertyDomainService()
        catalog = svc.load_property_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, PropertyOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = PropertyDomainService()
        catalog = svc.load_property_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = PropertyDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = PropertyDomainService()
        c1 = svc.load_property_rules()
        c2 = svc.load_property_rules()
        assert c1.rules is c2.rules


class TestPropertyDomainServiceEvaluateFacts:
    """Tests for the evaluate_property_facts method."""

    def test_evaluate_property_acquisition(self) -> None:
        svc = PropertyDomainService()
        facts = {"4th_lord_strong": True}
        records = svc.evaluate_property_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert PropertyOutcomeTaxonomy.PROPERTY_ACQUISITION.value in outcomes

    def test_evaluate_property_disputes(self) -> None:
        svc = PropertyDomainService()
        facts = {"mars_afflicting_4th": True}
        records = svc.evaluate_property_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert PropertyOutcomeTaxonomy.DISPUTES_OVER_PROPERTY.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = PropertyDomainService()
        records = svc.evaluate_property_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = PropertyDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_property_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = PropertyDomainService()
        facts = {"4th_lord_strong": True}
        r1 = svc.evaluate_property_facts(facts)
        r2 = svc.evaluate_property_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = PropertyDomainService()
        facts = {"4th_lord_strong": True}
        records = svc.evaluate_property_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestPropertyDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = PropertyDomainService()
        acq_rules = svc.get_rules_for_outcome(PropertyOutcomeTaxonomy.PROPERTY_ACQUISITION)
        assert len(acq_rules) > 0
        for rule in acq_rules:
            assert rule.outcome is PropertyOutcomeTaxonomy.PROPERTY_ACQUISITION

    def test_get_outcome_taxonomies(self) -> None:
        svc = PropertyDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert PropertyOutcomeTaxonomy.PROPERTY_ACQUISITION in outcomes
        assert PropertyOutcomeTaxonomy.DISPUTES_OVER_PROPERTY in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = PropertyDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

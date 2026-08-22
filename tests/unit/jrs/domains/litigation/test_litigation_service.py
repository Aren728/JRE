"""Unit tests for LitigationDomainService."""

from __future__ import annotations

import pytest

from jrs.domains.litigation.errors import InvalidFactError
from jrs.domains.litigation.models import (
    LitigationConfig,
    LitigationOutcomeTaxonomy,
    LitigationRuleCatalog,
)
from jrs.domains.litigation.service import LitigationDomainService
from jrs.evidence.models import EvidenceDirection


class TestLitigationDomainServiceInit:
    """Tests for LitigationDomainService initialization."""

    def test_default_config(self) -> None:
        svc = LitigationDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = LitigationConfig(source_id="Phaladeepika")
        svc = LitigationDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestLitigationDomainServiceLoadRules:
    """Tests for the load_litigation_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = LitigationDomainService()
        catalog = svc.load_litigation_rules()
        assert isinstance(catalog, LitigationRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = LitigationDomainService()
        catalog = svc.load_litigation_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, LitigationOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = LitigationDomainService()
        catalog = svc.load_litigation_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = LitigationDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = LitigationDomainService()
        c1 = svc.load_litigation_rules()
        c2 = svc.load_litigation_rules()
        assert c1.rules is c2.rules


class TestLitigationDomainServiceEvaluateFacts:
    """Tests for the evaluate_litigation_facts method."""

    def test_evaluate_legal_victory(self) -> None:
        svc = LitigationDomainService()
        facts = {"6th_lord_strong": True, "benefic_aspects_6th": True}
        records = svc.evaluate_litigation_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert LitigationOutcomeTaxonomy.LEGAL_VICTORY.value in outcomes

    def test_evaluate_prolonged_litigation(self) -> None:
        svc = LitigationDomainService()
        facts = {"saturn_aspecting_7th": True, "rahu_in_12th": True}
        records = svc.evaluate_litigation_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert LitigationOutcomeTaxonomy.PROLONGED_LITIGATION.value in outcomes

    def test_evaluate_settlement(self) -> None:
        svc = LitigationDomainService()
        facts = {"venus_strong": True, "7th_lord_connection": True}
        records = svc.evaluate_litigation_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert LitigationOutcomeTaxonomy.SETTLEMENT_OUT_OF_COURT.value in outcomes

    def test_evaluate_false_accusation(self) -> None:
        svc = LitigationDomainService()
        facts = {"rahu_afflicting_6th_lord": True, "jupiter_weak": True}
        records = svc.evaluate_litigation_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert LitigationOutcomeTaxonomy.FALSE_ACCUSATION.value in outcomes

    def test_evaluate_criminal_litigation(self) -> None:
        svc = LitigationDomainService()
        facts = {"mars_saturn_conjunction_6th": True, "12th_lord_afflicted": True}
        records = svc.evaluate_litigation_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert LitigationOutcomeTaxonomy.CRIMINAL_LITIGATION.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = LitigationDomainService()
        records = svc.evaluate_litigation_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = LitigationDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_litigation_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = LitigationDomainService()
        facts = {"6th_lord_strong": True}
        r1 = svc.evaluate_litigation_facts(facts)
        r2 = svc.evaluate_litigation_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = LitigationDomainService()
        facts = {"6th_lord_strong": True, "benefic_aspects_6th": True}
        records = svc.evaluate_litigation_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestLitigationDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = LitigationDomainService()
        vic_rules = svc.get_rules_for_outcome(LitigationOutcomeTaxonomy.LEGAL_VICTORY)
        assert len(vic_rules) > 0
        for rule in vic_rules:
            assert rule.outcome is LitigationOutcomeTaxonomy.LEGAL_VICTORY

    def test_get_outcome_taxonomies(self) -> None:
        svc = LitigationDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert LitigationOutcomeTaxonomy.LEGAL_VICTORY in outcomes
        assert LitigationOutcomeTaxonomy.CRIMINAL_LITIGATION in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = LitigationDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

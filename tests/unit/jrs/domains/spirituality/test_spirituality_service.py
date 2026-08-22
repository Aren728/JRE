"""Unit tests for SpiritualityDomainService."""

from __future__ import annotations

import pytest

from jrs.domains.spirituality.errors import InvalidFactError
from jrs.domains.spirituality.models import (
    SpiritualityConfig,
    SpiritualityOutcomeTaxonomy,
    SpiritualityRuleCatalog,
)
from jrs.domains.spirituality.service import SpiritualityDomainService
from jrs.evidence.models import EvidenceDirection


class TestSpiritualityDomainServiceInit:
    """Tests for SpiritualityDomainService initialization."""

    def test_default_config(self) -> None:
        svc = SpiritualityDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = SpiritualityConfig(source_id="Phaladeepika")
        svc = SpiritualityDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestSpiritualityDomainServiceLoadRules:
    """Tests for the load_spirituality_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = SpiritualityDomainService()
        catalog = svc.load_spirituality_rules()
        assert isinstance(catalog, SpiritualityRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = SpiritualityDomainService()
        catalog = svc.load_spirituality_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, SpiritualityOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = SpiritualityDomainService()
        catalog = svc.load_spirituality_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = SpiritualityDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = SpiritualityDomainService()
        c1 = svc.load_spirituality_rules()
        c2 = svc.load_spirituality_rules()
        assert c1.rules is c2.rules


class TestSpiritualityDomainServiceEvaluateFacts:
    """Tests for the evaluate_spirituality_facts method."""

    def test_evaluate_spiritual_awakening(self) -> None:
        svc = SpiritualityDomainService()
        facts = {"ketu_strong": True, "jupiter_strong": True}
        records = svc.evaluate_spirituality_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING.value in outcomes

    def test_evaluate_renunciation(self) -> None:
        svc = SpiritualityDomainService()
        facts = {"ketu_in_1st": True, "saturn_strong": True}
        records = svc.evaluate_spirituality_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert SpiritualityOutcomeTaxonomy.RENUNCIATION.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = SpiritualityDomainService()
        records = svc.evaluate_spirituality_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = SpiritualityDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_spirituality_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = SpiritualityDomainService()
        facts = {"ketu_strong": True, "jupiter_strong": True}
        r1 = svc.evaluate_spirituality_facts(facts)
        r2 = svc.evaluate_spirituality_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = SpiritualityDomainService()
        facts = {"ketu_strong": True, "jupiter_strong": True}
        records = svc.evaluate_spirituality_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestSpiritualityDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = SpiritualityDomainService()
        awk_rules = svc.get_rules_for_outcome(
            SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING,
        )
        assert len(awk_rules) > 0
        for rule in awk_rules:
            assert rule.outcome is SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING

    def test_get_outcome_taxonomies(self) -> None:
        svc = SpiritualityDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert SpiritualityOutcomeTaxonomy.SPIRITUAL_AWAKENING in outcomes
        assert SpiritualityOutcomeTaxonomy.RENUNCIATION in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = SpiritualityDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

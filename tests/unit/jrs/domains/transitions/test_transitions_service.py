"""Unit tests for TransitionsDomainService."""

from __future__ import annotations

import pytest

from jrs.domains.transitions.errors import InvalidFactError
from jrs.domains.transitions.models import (
    TransitionConfig,
    TransitionOutcomeTaxonomy,
    TransitionRuleCatalog,
)
from jrs.domains.transitions.service import TransitionsDomainService
from jrs.evidence.models import EvidenceDirection


class TestTransitionsDomainServiceInit:
    """Tests for TransitionsDomainService initialization."""

    def test_default_config(self) -> None:
        svc = TransitionsDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = TransitionConfig(source_id="Phaladeepika")
        svc = TransitionsDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestTransitionsDomainServiceLoadRules:
    """Tests for the load_transitions_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = TransitionsDomainService()
        catalog = svc.load_transitions_rules()
        assert isinstance(catalog, TransitionRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = TransitionsDomainService()
        catalog = svc.load_transitions_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, TransitionOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = TransitionsDomainService()
        catalog = svc.load_transitions_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = TransitionsDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = TransitionsDomainService()
        c1 = svc.load_transitions_rules()
        c2 = svc.load_transitions_rules()
        assert c1.rules is c2.rules


class TestTransitionsDomainServiceEvaluateFacts:
    """Tests for the evaluate_transitions_facts method."""

    def test_evaluate_life_phase_shift(self) -> None:
        svc = TransitionsDomainService()
        facts = {"saturn_return": True}
        records = svc.evaluate_transitions_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert TransitionOutcomeTaxonomy.LIFE_PHASE_SHIFT.value in outcomes

    def test_evaluate_sudden_upheaval(self) -> None:
        svc = TransitionsDomainService()
        facts = {"rahu_ketu_axis": True, "rahu_ketu_transit_activation": True}
        records = svc.evaluate_transitions_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TransitionOutcomeTaxonomy.SUDDEN_UPHEAVAL.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = TransitionsDomainService()
        records = svc.evaluate_transitions_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = TransitionsDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_transitions_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = TransitionsDomainService()
        facts = {"saturn_return": True}
        r1 = svc.evaluate_transitions_facts(facts)
        r2 = svc.evaluate_transitions_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = TransitionsDomainService()
        facts = {"saturn_return": True}
        records = svc.evaluate_transitions_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestTransitionsDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = TransitionsDomainService()
        phase_rules = svc.get_rules_for_outcome(
            TransitionOutcomeTaxonomy.LIFE_PHASE_SHIFT,
        )
        assert len(phase_rules) > 0
        for rule in phase_rules:
            assert rule.outcome is TransitionOutcomeTaxonomy.LIFE_PHASE_SHIFT

    def test_get_outcome_taxonomies(self) -> None:
        svc = TransitionsDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert TransitionOutcomeTaxonomy.LIFE_PHASE_SHIFT in outcomes
        assert TransitionOutcomeTaxonomy.SUDDEN_UPHEAVAL in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = TransitionsDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

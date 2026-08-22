"""Unit tests for ProgenyDomainService."""

from __future__ import annotations

from pathlib import Path

import pytest

from jrs.domains.progeny.errors import InvalidFactError
from jrs.domains.progeny.models import (
    ProgenyConfig,
    ProgenyOutcomeTaxonomy,
    ProgenyRuleCatalog,
)
from jrs.domains.progeny.service import ProgenyDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "progeny.toml"
)


class TestProgenyDomainServiceInit:
    """Tests for ProgenyDomainService initialization."""

    def test_default_config(self) -> None:
        svc = ProgenyDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = ProgenyConfig(source_id="Phaladeepika")
        svc = ProgenyDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestProgenyDomainServiceLoadRules:
    """Tests for the load_progeny_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = ProgenyDomainService()
        catalog = svc.load_progeny_rules()
        assert isinstance(catalog, ProgenyRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = ProgenyDomainService()
        catalog = svc.load_progeny_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, ProgenyOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = ProgenyDomainService()
        catalog = svc.load_progeny_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = ProgenyDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = ProgenyDomainService()
        c1 = svc.load_progeny_rules()
        c2 = svc.load_progeny_rules()
        assert c1.rules is c2.rules


class TestProgenyDomainServiceEvaluateFacts:
    """Tests for the evaluate_progeny_facts method."""

    def test_evaluate_easy_conception(self) -> None:
        svc = ProgenyDomainService()
        facts = {"jupiter_strong": True, "5th_lord_in_kendra": True}
        records = svc.evaluate_progeny_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert ProgenyOutcomeTaxonomy.EASY_CONCEPTION.value in outcomes

    def test_evaluate_delayed_progeny(self) -> None:
        svc = ProgenyDomainService()
        facts = {"saturn_in_5th": True}
        records = svc.evaluate_progeny_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert ProgenyOutcomeTaxonomy.DELAYED_PROGENY.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = ProgenyDomainService()
        records = svc.evaluate_progeny_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = ProgenyDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_progeny_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = ProgenyDomainService()
        facts = {"jupiter_strong": True, "5th_lord_in_kendra": True}
        r1 = svc.evaluate_progeny_facts(facts)
        r2 = svc.evaluate_progeny_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = ProgenyDomainService()
        facts = {"jupiter_strong": True, "5th_lord_in_kendra": True}
        records = svc.evaluate_progeny_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestProgenyDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = ProgenyDomainService()
        delay_rules = svc.get_rules_for_outcome(ProgenyOutcomeTaxonomy.DELAYED_PROGENY)
        assert len(delay_rules) > 0
        for rule in delay_rules:
            assert rule.outcome is ProgenyOutcomeTaxonomy.DELAYED_PROGENY

    def test_get_outcome_taxonomies(self) -> None:
        svc = ProgenyDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert ProgenyOutcomeTaxonomy.EASY_CONCEPTION in outcomes
        assert ProgenyOutcomeTaxonomy.DELAYED_PROGENY in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = ProgenyDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

"""Unit tests for WealthDomainService."""

from __future__ import annotations

from pathlib import Path

import pytest

from jrs.domains.wealth.errors import InvalidFactError
from jrs.domains.wealth.models import (
    WealthConfig,
    WealthOutcomeTaxonomy,
    WealthRuleCatalog,
)
from jrs.domains.wealth.service import WealthDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = (
    Path(__file__).resolve()
    .parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "wealth.toml"
)


class TestWealthDomainServiceInit:
    """Tests for WealthDomainService initialization."""

    def test_default_config(self) -> None:
        svc = WealthDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = WealthConfig(source_id="Phaladeepika")
        svc = WealthDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestWealthDomainServiceLoadRules:
    """Tests for the load_wealth_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = WealthDomainService()
        catalog = svc.load_wealth_rules()
        assert isinstance(catalog, WealthRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = WealthDomainService()
        catalog = svc.load_wealth_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, WealthOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = WealthDomainService()
        catalog = svc.load_wealth_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = WealthDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = WealthDomainService()
        c1 = svc.load_wealth_rules()
        c2 = svc.load_wealth_rules()
        assert c1.rules is c2.rules


class TestWealthDomainServiceEvaluateFacts:
    """Tests for the evaluate_wealth_facts method."""

    def test_evaluate_accumulation(self) -> None:
        svc = WealthDomainService()
        facts = {"2nd_lord_in_11th": True}
        records = svc.evaluate_wealth_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert WealthOutcomeTaxonomy.WEALTH_ACCUMULATION.value in outcomes

    def test_evaluate_business_wealth(self) -> None:
        svc = WealthDomainService()
        facts = {"mercury_strong": True, "mercury_7th_or_10th_connection": True}
        records = svc.evaluate_wealth_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert WealthOutcomeTaxonomy.BUSINESS_WEALTH.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = WealthDomainService()
        records = svc.evaluate_wealth_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = WealthDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_wealth_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = WealthDomainService()
        facts = {"mercury_strong": True}
        r1 = svc.evaluate_wealth_facts(facts)
        r2 = svc.evaluate_wealth_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = WealthDomainService()
        facts = {"2nd_lord_in_11th": True}
        records = svc.evaluate_wealth_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestWealthDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = WealthDomainService()
        acc_rules = svc.get_rules_for_outcome(WealthOutcomeTaxonomy.WEALTH_ACCUMULATION)
        assert len(acc_rules) > 0
        for rule in acc_rules:
            assert rule.outcome is WealthOutcomeTaxonomy.WEALTH_ACCUMULATION

    def test_get_outcome_taxonomies(self) -> None:
        svc = WealthDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert WealthOutcomeTaxonomy.WEALTH_ACCUMULATION in outcomes
        assert WealthOutcomeTaxonomy.DEBT_BURDEN in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = WealthDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

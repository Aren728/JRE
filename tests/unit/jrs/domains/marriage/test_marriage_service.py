"""Unit tests for MarriageDomainService."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from jrs.domains.marriage.errors import InvalidFactError
from jrs.domains.marriage.models import (
    MarriageConfig,
    MarriageOutcomeTaxonomy,
    MarriageRule,
    MarriageRuleCatalog,
)
from jrs.domains.marriage.service import MarriageDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "config" / "domains" / "marriage.toml"


class TestMarriageDomainServiceInit:
    """Tests for MarriageDomainService initialization."""

    def test_default_config(self) -> None:
        svc = MarriageDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = MarriageConfig(source_id="Phaladeepika")
        svc = MarriageDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestMarriageDomainServiceLoadRules:
    """Tests for the load_marriage_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = MarriageDomainService()
        catalog = svc.load_marriage_rules()
        assert isinstance(catalog, MarriageRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = MarriageDomainService()
        catalog = svc.load_marriage_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, MarriageOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = MarriageDomainService()
        catalog = svc.load_marriage_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = MarriageDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = MarriageDomainService()
        c1 = svc.load_marriage_rules()
        c2 = svc.load_marriage_rules()
        # Rules are cached; catalogs have equal content
        assert c1.rules is c2.rules


class TestMarriageDomainServiceEvaluateFacts:
    """Tests for the evaluate_marriage_facts method."""

    def test_evaluate_formation(self) -> None:
        svc = MarriageDomainService()
        facts = {"7th_lord_in_kendra_or_trikona": True}
        records = svc.evaluate_marriage_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert MarriageOutcomeTaxonomy.MARRIAGE_FORMATION.value in outcomes

    def test_evaluate_delay(self) -> None:
        svc = MarriageDomainService()
        facts = {"saturn_aspects_7th_lord": True}
        records = svc.evaluate_marriage_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert MarriageOutcomeTaxonomy.DELAYED_MARRIAGE.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = MarriageDomainService()
        records = svc.evaluate_marriage_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = MarriageDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_marriage_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_multiple_outcomes(self) -> None:
        svc = MarriageDomainService()
        facts = {
            "7th_lord_in_kendra_or_trikona": True,
            "saturn_aspects_7th_lord": True,
        }
        records = svc.evaluate_marriage_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert MarriageOutcomeTaxonomy.MARRIAGE_FORMATION.value in outcomes
        assert MarriageOutcomeTaxonomy.DELAYED_MARRIAGE.value in outcomes

    def test_evaluate_deterministic(self) -> None:
        svc = MarriageDomainService()
        facts = {"venus_bala": 7.0}
        r1 = svc.evaluate_marriage_facts(facts)
        r2 = svc.evaluate_marriage_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = MarriageDomainService()
        facts = {"venus_bala": 7.0}
        records = svc.evaluate_marriage_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestMarriageDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = MarriageDomainService()
        formation_rules = svc.get_rules_for_outcome(
            MarriageOutcomeTaxonomy.MARRIAGE_FORMATION,
        )
        assert len(formation_rules) > 0
        for rule in formation_rules:
            assert rule.outcome is MarriageOutcomeTaxonomy.MARRIAGE_FORMATION

    def test_get_outcome_taxonomies(self) -> None:
        svc = MarriageDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert MarriageOutcomeTaxonomy.MARRIAGE_FORMATION in outcomes
        assert MarriageOutcomeTaxonomy.DELAYED_MARRIAGE in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = MarriageDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

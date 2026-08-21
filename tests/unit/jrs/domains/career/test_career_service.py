"""Unit tests for CareerDomainService."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from jrs.domains.career.errors import InvalidFactError
from jrs.domains.career.models import (
    CareerConfig,
    CareerOutcomeTaxonomy,
    CareerRule,
    CareerRuleCatalog,
)
from jrs.domains.career.service import CareerDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent.parent.parent.parent / "config" / "domains" / "career.toml"


class TestCareerDomainServiceInit:
    """Tests for CareerDomainService initialization."""

    def test_default_config(self) -> None:
        svc = CareerDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = CareerConfig(source_id="Phaladeepika")
        svc = CareerDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestCareerDomainServiceLoadRules:
    """Tests for the load_career_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = CareerDomainService()
        catalog = svc.load_career_rules()
        assert isinstance(catalog, CareerRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = CareerDomainService()
        catalog = svc.load_career_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, CareerOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = CareerDomainService()
        catalog = svc.load_career_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = CareerDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = CareerDomainService()
        c1 = svc.load_career_rules()
        c2 = svc.load_career_rules()
        assert c1.rules is c2.rules


class TestCareerDomainServiceEvaluateFacts:
    """Tests for the evaluate_career_facts method."""

    def test_evaluate_ascent(self) -> None:
        svc = CareerDomainService()
        facts = {"10th_lord_in_kendra_or_trikona": True}
        records = svc.evaluate_career_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert CareerOutcomeTaxonomy.CAREER_ASCENT.value in outcomes

    def test_evaluate_government(self) -> None:
        svc = CareerDomainService()
        facts = {"sun_10th_connection": True, "saturn_10th_connection": True}
        records = svc.evaluate_career_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert CareerOutcomeTaxonomy.GOVERNMENT_SERVICE.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = CareerDomainService()
        records = svc.evaluate_career_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = CareerDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_career_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = CareerDomainService()
        facts = {"mercury_strong": True}
        r1 = svc.evaluate_career_facts(facts)
        r2 = svc.evaluate_career_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = CareerDomainService()
        facts = {"10th_lord_in_kendra_or_trikona": True}
        records = svc.evaluate_career_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestCareerDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = CareerDomainService()
        ascent_rules = svc.get_rules_for_outcome(CareerOutcomeTaxonomy.CAREER_ASCENT)
        assert len(ascent_rules) > 0
        for rule in ascent_rules:
            assert rule.outcome is CareerOutcomeTaxonomy.CAREER_ASCENT

    def test_get_outcome_taxonomies(self) -> None:
        svc = CareerDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert CareerOutcomeTaxonomy.CAREER_ASCENT in outcomes
        assert CareerOutcomeTaxonomy.GOVERNMENT_SERVICE in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = CareerDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

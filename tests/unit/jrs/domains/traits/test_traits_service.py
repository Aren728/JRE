"""Unit tests for TraitsDomainService."""

from __future__ import annotations

from pathlib import Path

import pytest

from jrs.domains.traits.errors import InvalidFactError
from jrs.domains.traits.models import (
    TraitOutcomeTaxonomy,
    TraitRuleCatalog,
    TraitsConfig,
)
from jrs.domains.traits.service import TraitsDomainService
from jrs.evidence.models import EvidenceDirection

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent.parent.parent
    / "config" / "domains" / "traits.toml"
)


class TestTraitsDomainServiceInit:
    """Tests for TraitsDomainService initialization."""

    def test_default_config(self) -> None:
        svc = TraitsDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = TraitsConfig(source_id="Phaladeepika")
        svc = TraitsDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestTraitsDomainServiceLoadRules:
    """Tests for the load_traits_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = TraitsDomainService()
        catalog = svc.load_traits_rules()
        assert isinstance(catalog, TraitRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = TraitsDomainService()
        catalog = svc.load_traits_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, TraitOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = TraitsDomainService()
        catalog = svc.load_traits_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = TraitsDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = TraitsDomainService()
        c1 = svc.load_traits_rules()
        c2 = svc.load_traits_rules()
        # Rules are cached; catalogs have equal content
        assert c1.rules is c2.rules


class TestTraitsDomainServiceEvaluateFacts:
    """Tests for the evaluate_traits_facts method."""

    def test_evaluate_intellectual_depth_mercury_hora(self) -> None:
        """Mercury hora → INTELLECTUAL_DEPTH."""
        svc = TraitsDomainService()
        facts = {"hora": "MERCURY"}
        records = svc.evaluate_traits_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH.value in outcomes

    def test_evaluate_leadership_sun_hora(self) -> None:
        """Sun hora → LEADERSHIP_TENDENCY."""
        svc = TraitsDomainService()
        facts = {"hora": "SUN"}
        records = svc.evaluate_traits_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.LEADERSHIP_TENDENCY.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = TraitsDomainService()
        records = svc.evaluate_traits_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = TraitsDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_traits_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_multiple_outcomes(self) -> None:
        """Multiple trait outcomes from a single fact set."""
        svc = TraitsDomainService()
        facts = {
            "hora": "MERCURY",           # INTELLECTUAL_DEPTH
            "weekday": "SATURDAY",        # PRACTICAL_GROUNDEDNESS
        }
        records = svc.evaluate_traits_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH.value in outcomes
        assert TraitOutcomeTaxonomy.PRACTICAL_GROUNDEDNESS.value in outcomes

    def test_evaluate_deterministic(self) -> None:
        svc = TraitsDomainService()
        facts = {"yoga": "BRAHMA"}
        r1 = svc.evaluate_traits_facts(facts)
        r2 = svc.evaluate_traits_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = TraitsDomainService()
        facts = {"hora": "JUPITER"}
        records = svc.evaluate_traits_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)

    def test_spiritual_inclination_jupiter_night(self) -> None:
        """Night + Jupiter → SPIRITUAL_INCLINATION (compound rule)."""
        svc = TraitsDomainService()
        facts = {"day_night_period": "NIGHT", "hora": "JUPITER"}
        records = svc.evaluate_traits_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.SPIRITUAL_INCLINATION.value in outcomes

    def test_emotional_volatility_shula_yoga(self) -> None:
        """SHULA yoga → EMOTIONAL_VOLATILITY."""
        svc = TraitsDomainService()
        facts = {"yoga": "SHULA"}
        records = svc.evaluate_traits_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.EMOTIONAL_VOLATILITY.value in outcomes

    def test_practical_groundedness_vishkambha_yoga(self) -> None:
        """VISHKAMBHA yoga → PRACTICAL_GROUNDEDNESS."""
        svc = TraitsDomainService()
        facts = {"yoga": "VISHKAMBHA"}
        records = svc.evaluate_traits_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.PRACTICAL_GROUNDEDNESS.value in outcomes

    def test_adaptability_venus_hora(self) -> None:
        """Venus hora → ADAPTABILITY."""
        svc = TraitsDomainService()
        facts = {"hora": "VENUS"}
        records = svc.evaluate_traits_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.ADAPTABILITY.value in outcomes

    def test_nakshatra_membership_condition(self) -> None:
        """Ashwini nakshatra → SPIRITUAL_INCLINATION."""
        svc = TraitsDomainService()
        facts = {"nakshatra": "ASHWINI"}
        records = svc.evaluate_traits_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert TraitOutcomeTaxonomy.SPIRITUAL_INCLINATION.value in outcomes


class TestTraitsDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = TraitsDomainService()
        intel_rules = svc.get_rules_for_outcome(
            TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH,
        )
        assert len(intel_rules) > 0
        for rule in intel_rules:
            assert rule.outcome is TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH

    def test_get_outcome_taxonomies(self) -> None:
        svc = TraitsDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) == 6
        assert TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH in outcomes
        assert TraitOutcomeTaxonomy.EMOTIONAL_VOLATILITY in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = TraitsDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)


class TestTraitsDomainServiceConfigPath:
    """Tests for loading rules from a specific config path."""

    def test_loads_from_explicit_path(self) -> None:
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        assert len(catalog.rules) > 0

    def test_rule_ids_unique(self) -> None:
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        ids = [r.rule_id for r in catalog.rules]
        assert len(ids) == len(set(ids))

    def test_all_six_outcomes_represented(self) -> None:
        svc = TraitsDomainService(config_path=_CONFIG_PATH)
        catalog = svc.load_traits_rules()
        outcomes = {r.outcome for r in catalog.rules}
        expected = {
            TraitOutcomeTaxonomy.INTELLECTUAL_DEPTH,
            TraitOutcomeTaxonomy.EMOTIONAL_VOLATILITY,
            TraitOutcomeTaxonomy.PRACTICAL_GROUNDEDNESS,
            TraitOutcomeTaxonomy.SPIRITUAL_INCLINATION,
            TraitOutcomeTaxonomy.LEADERSHIP_TENDENCY,
            TraitOutcomeTaxonomy.ADAPTABILITY,
        }
        assert outcomes == expected

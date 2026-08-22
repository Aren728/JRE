"""Unit tests for AssetsDomainService."""

from __future__ import annotations

import pytest

from jrs.domains.assets.errors import InvalidFactError
from jrs.domains.assets.models import (
    AssetsConfig,
    AssetsOutcomeTaxonomy,
    AssetsRuleCatalog,
)
from jrs.domains.assets.service import AssetsDomainService
from jrs.evidence.models import EvidenceDirection


class TestAssetsDomainServiceInit:
    """Tests for AssetsDomainService initialization."""

    def test_default_config(self) -> None:
        svc = AssetsDomainService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = AssetsConfig(source_id="Phaladeepika")
        svc = AssetsDomainService(config=config)
        assert svc.config.source_id == "Phaladeepika"


class TestAssetsDomainServiceLoadRules:
    """Tests for the load_assets_rules method."""

    def test_loads_rules_from_config(self) -> None:
        svc = AssetsDomainService()
        catalog = svc.load_assets_rules()
        assert isinstance(catalog, AssetsRuleCatalog)
        assert len(catalog.rules) > 0

    def test_rules_have_valid_outcomes(self) -> None:
        svc = AssetsDomainService()
        catalog = svc.load_assets_rules()
        for rule in catalog.rules:
            assert isinstance(rule.outcome, AssetsOutcomeTaxonomy)

    def test_rules_have_rule_ids(self) -> None:
        svc = AssetsDomainService()
        catalog = svc.load_assets_rules()
        for rule in catalog.rules:
            assert rule.rule_id, f"Rule missing rule_id: {rule}"

    def test_rule_count(self) -> None:
        svc = AssetsDomainService()
        assert svc.rule_count > 0

    def test_caching(self) -> None:
        svc = AssetsDomainService()
        c1 = svc.load_assets_rules()
        c2 = svc.load_assets_rules()
        assert c1.rules is c2.rules


class TestAssetsDomainServiceEvaluateFacts:
    """Tests for the evaluate_assets_facts method."""

    def test_evaluate_vehicle_acquisition(self) -> None:
        svc = AssetsDomainService()
        facts = {"4th_lord_strong": True, "benefic_aspects_4th": True}
        records = svc.evaluate_assets_facts(facts)
        assert len(records) > 0
        outcomes = {r.outcome_taxonomy for r in records}
        assert AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION.value in outcomes

    def test_evaluate_luxury_assets(self) -> None:
        svc = AssetsDomainService()
        facts = {"venus_strong": True, "venus_in_4th": True}
        records = svc.evaluate_assets_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert AssetsOutcomeTaxonomy.LUXURY_ASSETS.value in outcomes

    def test_evaluate_asset_loss(self) -> None:
        svc = AssetsDomainService()
        facts = {"4th_lord_debilitated": True, "malefic_4th": True}
        records = svc.evaluate_assets_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert AssetsOutcomeTaxonomy.ASSET_LOSS.value in outcomes

    def test_evaluate_vehicle_accidents(self) -> None:
        svc = AssetsDomainService()
        facts = {"mars_afflicting_4th": True, "saturn_in_4th": True}
        records = svc.evaluate_assets_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert AssetsOutcomeTaxonomy.VEHICLE_ACCIDENTS.value in outcomes

    def test_evaluate_multiple_vehicles(self) -> None:
        svc = AssetsDomainService()
        facts = {"4th_lord_strong": True, "multiple_benefics_4th": True}
        records = svc.evaluate_assets_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert AssetsOutcomeTaxonomy.MULTIPLE_VEHICLES.value in outcomes

    def test_evaluate_real_estate(self) -> None:
        svc = AssetsDomainService()
        facts = {"4th_lord_in_kendra": True, "venus_strong": True}
        records = svc.evaluate_assets_facts(facts)
        outcomes = {r.outcome_taxonomy for r in records}
        assert AssetsOutcomeTaxonomy.REAL_ESTATE_ASSETS.value in outcomes

    def test_evaluate_empty_facts(self) -> None:
        svc = AssetsDomainService()
        records = svc.evaluate_assets_facts({})
        assert records == ()

    def test_evaluate_invalid_facts_raises(self) -> None:
        svc = AssetsDomainService()
        with pytest.raises(InvalidFactError, match="must be a dictionary"):
            svc.evaluate_assets_facts("not a dict")  # type: ignore[arg-type]

    def test_evaluate_deterministic(self) -> None:
        svc = AssetsDomainService()
        facts = {"4th_lord_strong": True}
        r1 = svc.evaluate_assets_facts(facts)
        r2 = svc.evaluate_assets_facts(facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_records_have_correct_fields(self) -> None:
        svc = AssetsDomainService()
        facts = {"4th_lord_strong": True, "benefic_aspects_4th": True}
        records = svc.evaluate_assets_facts(facts)
        for record in records:
            assert record.evidence_id
            assert record.rule_id
            assert record.source_id
            assert isinstance(record.direction, EvidenceDirection)


class TestAssetsDomainServiceQueries:
    """Tests for query methods."""

    def test_get_rules_for_outcome(self) -> None:
        svc = AssetsDomainService()
        veh_rules = svc.get_rules_for_outcome(AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION)
        assert len(veh_rules) > 0
        for rule in veh_rules:
            assert rule.outcome is AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION

    def test_get_outcome_taxonomies(self) -> None:
        svc = AssetsDomainService()
        outcomes = svc.get_outcome_taxonomies()
        assert len(outcomes) > 0
        assert AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION in outcomes
        assert AssetsOutcomeTaxonomy.ASSET_LOSS in outcomes

    def test_get_outcome_taxonomies_sorted(self) -> None:
        svc = AssetsDomainService()
        outcomes = svc.get_outcome_taxonomies()
        values = [o.value for o in outcomes]
        assert values == sorted(values)

"""Unit tests for assets domain models and fact evaluation logic."""

from __future__ import annotations

import json

import pytest
from tests.unit.jrs.domains.assets.conftest import make_assets_rule

from jrs.domains.assets.models import (
    AssetsConfig,
    AssetsOutcomeTaxonomy,
    AssetsRule,
    AssetsRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord


class TestAssetsOutcomeTaxonomy:
    """Tests for the AssetsOutcomeTaxonomy enum."""

    def test_all_outcomes_have_string_values(self) -> None:
        for o in AssetsOutcomeTaxonomy:
            assert isinstance(o.value, str)
            assert o.value == o.name

    def test_outcome_count(self) -> None:
        assert len(AssetsOutcomeTaxonomy) == 6

    def test_outcome_from_value(self) -> None:
        veh = AssetsOutcomeTaxonomy("VEHICLE_ACQUISITION")
        assert veh is AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION
        rea = AssetsOutcomeTaxonomy("REAL_ESTATE_ASSETS")
        assert rea is AssetsOutcomeTaxonomy.REAL_ESTATE_ASSETS

    def test_invalid_outcome(self) -> None:
        with pytest.raises(ValueError):
            AssetsOutcomeTaxonomy("INVALID")

    def test_all_six_outcomes_exist(self) -> None:
        assert AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION.value == "VEHICLE_ACQUISITION"
        assert AssetsOutcomeTaxonomy.LUXURY_ASSETS.value == "LUXURY_ASSETS"
        assert AssetsOutcomeTaxonomy.ASSET_LOSS.value == "ASSET_LOSS"
        assert AssetsOutcomeTaxonomy.VEHICLE_ACCIDENTS.value == "VEHICLE_ACCIDENTS"
        assert AssetsOutcomeTaxonomy.MULTIPLE_VEHICLES.value == "MULTIPLE_VEHICLES"
        assert AssetsOutcomeTaxonomy.REAL_ESTATE_ASSETS.value == "REAL_ESTATE_ASSETS"


class TestAssetsRule:
    """Tests for the AssetsRule model."""

    def test_creation(self) -> None:
        rule = make_assets_rule(rule_id="ASST-TEST")
        assert rule.rule_id == "ASST-TEST"
        assert rule.outcome is AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION

    def test_frozen(self) -> None:
        rule = make_assets_rule()
        with pytest.raises(AttributeError):
            rule.rule_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        rule = make_assets_rule(
            rule_id="ASST-100",
            outcome=AssetsOutcomeTaxonomy.ASSET_LOSS,
            direction=EvidenceDirection.CONTRADICT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "ASST-100"
        assert d["outcome"] == "ASSET_LOSS"
        assert d["direction"] == "CONTRADICT"

    def test_to_dict_deterministic(self) -> None:
        rule = make_assets_rule()
        d1 = rule.to_dict()
        d2 = rule.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestAssetsRuleCatalog:
    """Tests for the AssetsRuleCatalog model."""

    def test_creation(self) -> None:
        catalog = AssetsRuleCatalog(rules=(make_assets_rule(),))
        assert len(catalog.rules) == 1

    def test_get_rules_by_outcome(self, sample_catalog: AssetsRuleCatalog) -> None:
        veh = sample_catalog.get_rules_by_outcome(AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION)
        assert len(veh) == 1

    def test_get_rule_by_id(self, sample_catalog: AssetsRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("ASST-TEST-002")
        assert rule is not None
        assert rule.rule_id == "ASST-TEST-002"

    def test_get_rule_by_id_not_found(self, sample_catalog: AssetsRuleCatalog) -> None:
        rule = sample_catalog.get_rule_by_id("ASST-NONE")
        assert rule is None

    def test_to_dict(self, sample_catalog: AssetsRuleCatalog) -> None:
        d = sample_catalog.to_dict()
        assert d["rule_count"] == 7
        assert len(d["rules"]) == 7


class TestEvaluateCondition:
    """Tests for the evaluate_condition function."""

    def test_truthy_check(self) -> None:
        assert evaluate_condition("flag_a", {"flag_a": True}) is True
        assert evaluate_condition("flag_a", {"flag_a": False}) is False
        assert evaluate_condition("flag_a", {}) is False

    def test_equality(self) -> None:
        assert evaluate_condition("x=5", {"x": 5}) is True
        assert evaluate_condition("x=5", {"x": 4}) is False
        assert evaluate_condition("x=hello", {"x": "hello"}) is True

    def test_inequality(self) -> None:
        assert evaluate_condition("x!=5", {"x": 4}) is True
        assert evaluate_condition("x!=5", {"x": 5}) is False

    def test_greater_than(self) -> None:
        assert evaluate_condition("x>5", {"x": 6}) is True
        assert evaluate_condition("x>5", {"x": 5}) is False

    def test_less_than(self) -> None:
        assert evaluate_condition("x<5", {"x": 4}) is True
        assert evaluate_condition("x<5", {"x": 5}) is False

    def test_membership(self) -> None:
        assert evaluate_condition("x in (1,2,3)", {"x": 2}) is True
        assert evaluate_condition("x in (1,2,3)", {"x": 4}) is False

    def test_missing_fact(self) -> None:
        assert evaluate_condition("x>5", {}) is False


class TestEvaluateRule:
    """Tests for the evaluate_rule function."""

    def test_single_condition_match(self) -> None:
        rule = make_assets_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is not None
        assert isinstance(record, EvidenceRecord)
        assert record.outcome_taxonomy == AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION.value

    def test_single_condition_no_match(self) -> None:
        rule = make_assets_rule(condition_facts=("flag_a=true",))
        record = evaluate_rule(rule, {"flag_a": False})
        assert record is None

    def test_multiple_conditions_all_match(self) -> None:
        rule = make_assets_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": True})
        assert record is not None

    def test_multiple_conditions_partial_match(self) -> None:
        rule = make_assets_rule(condition_facts=("a=true", "b=true"))
        record = evaluate_rule(rule, {"a": True, "b": False})
        assert record is None

    def test_empty_conditions_returns_none(self) -> None:
        rule = make_assets_rule(condition_facts=())
        record = evaluate_rule(rule, {"flag_a": True})
        assert record is None


class TestEvaluateFacts:
    """Tests for the evaluate_facts function."""

    def test_multiple_rules(self, sample_rules: tuple[AssetsRule, ...]) -> None:
        facts = {
            "4th_lord_strong": True,
            "benefic_aspects_4th": True,
        }
        records = evaluate_facts(sample_rules, facts)
        assert len(records) >= 1

    def test_no_rules_match(self, sample_rules: tuple[AssetsRule, ...]) -> None:
        records = evaluate_facts(sample_rules, {})
        assert records == ()

    def test_deterministic_output(self, sample_rules: tuple[AssetsRule, ...]) -> None:
        facts = {"4th_lord_strong": True}
        r1 = evaluate_facts(sample_rules, facts)
        r2 = evaluate_facts(sample_rules, facts)
        ids1 = [r.evidence_id for r in r1]
        ids2 = [r.evidence_id for r in r2]
        assert ids1 == ids2

    def test_no_false_cross_contamination(self) -> None:
        """Ensure a 'vehicle_acquisition' rule doesn't trigger 'asset_loss'."""
        rules = (
            make_assets_rule(
                rule_id="ASST-VEH",
                outcome=AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION,
                condition_facts=("4th_lord_strong=true",),
            ),
            make_assets_rule(
                rule_id="ASST-LOS",
                outcome=AssetsOutcomeTaxonomy.ASSET_LOSS,
                condition_facts=("4th_lord_debilitated=true",),
            ),
        )
        records = evaluate_facts(rules, {"4th_lord_strong": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == AssetsOutcomeTaxonomy.VEHICLE_ACQUISITION.value

    def test_vehicle_accidents_vs_asset_loss_distinction(self) -> None:
        """Ensure vehicle_accidents ≠ asset_loss."""
        rules = (
            make_assets_rule(
                rule_id="ASST-ACC",
                outcome=AssetsOutcomeTaxonomy.VEHICLE_ACCIDENTS,
                condition_facts=("mars_afflicting_4th=true",),
            ),
            make_assets_rule(
                rule_id="ASST-LOS",
                outcome=AssetsOutcomeTaxonomy.ASSET_LOSS,
                condition_facts=("4th_lord_debilitated=true",),
            ),
        )
        records = evaluate_facts(rules, {"mars_afflicting_4th": True})
        assert len(records) == 1
        assert records[0].outcome_taxonomy == AssetsOutcomeTaxonomy.VEHICLE_ACCIDENTS.value


class TestAssetsConfig:
    """Tests for the AssetsConfig model."""

    def test_defaults(self) -> None:
        config = AssetsConfig()
        assert config.version == "1.0"
        assert config.source_id == "BPHS"

    def test_frozen(self) -> None:
        config = AssetsConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

"""Unit tests for JRS-067 Western Astrology interpretation models.

Tests WesternOutcomeTaxonomy, WesternRule, fact extraction from
WesternChart, and condition evaluation logic.
"""

from __future__ import annotations

import datetime as dt

import pytest

from jrs.evidence.models import EvidenceDirection, EvidenceStrength
from jrs.western.models import (
    WesternOutcomeTaxonomy,
    WesternRule,
    WesternRuleCatalog,
    _aspect_key,
    _determine_house,
    evaluate_condition,
    evaluate_rule,
    extract_facts_from_chart,
)
from western.models import (
    HouseCusp,
    WesternAspectType,
    WesternChart,
    WesternDignity,
    WesternHouseSystem,
    WesternPlanet,
)
from western.service import WesternCalculationService

# ── Enum Tests ───────────────────────────────────────────────────────────────


class TestWesternOutcomeTaxonomy:
    """WesternOutcomeTaxonomy enum tests."""

    def test_all_outcomes_defined(self) -> None:
        expected = {
            "CAREER_PROMINENCE",
            "RELATIONSHIP_HARMONY",
            "EMOTIONAL_TENSION",
            "FINANCIAL_GAIN",
            "INTELLECTUAL_CAPACITY",
            "LEADERSHIP_AUTHORITY",
            "SOCIAL_INFLUENCE",
            "PHILOSOPHICAL_DEPTH",
            "CREATIVE_TALENT",
            "DOMESTIC_PROMINENCE",
        }
        actual = {o.value for o in WesternOutcomeTaxonomy}
        assert actual == expected

    def test_outcome_count(self) -> None:
        assert len(WesternOutcomeTaxonomy) == 10


# ── Rule Model Tests ─────────────────────────────────────────────────────────


class TestWesternRule:
    """WesternRule dataclass tests."""

    def test_basic_rule(self) -> None:
        rule = WesternRule(
            rule_id="W-TEST-001",
            description="Test rule",
            condition_facts=("sun_house=10",),
            outcome=WesternOutcomeTaxonomy.CAREER_PROMINENCE,
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
            source_id="PTOLEMY",
            location="Tetrabiblos II.4",
        )
        assert rule.rule_id == "W-TEST-001"
        assert rule.outcome is WesternOutcomeTaxonomy.CAREER_PROMINENCE

    def test_to_dict(self) -> None:
        rule = WesternRule(
            rule_id="W-TEST-002",
            description="Test",
            condition_facts=("moon_house=7",),
            outcome=WesternOutcomeTaxonomy.RELATIONSHIP_HARMONY,
            direction=EvidenceDirection.SUPPORT,
        )
        d = rule.to_dict()
        assert d["rule_id"] == "W-TEST-002"
        assert d["outcome"] == "RELATIONSHIP_HARMONY"
        assert d["direction"] == "SUPPORT"


class TestWesternRuleCatalog:
    """WesternRuleCatalog tests."""

    def test_empty_catalog(self) -> None:
        catalog = WesternRuleCatalog()
        assert len(catalog.rules) == 0

    def test_get_rules_by_outcome(self) -> None:
        rules = (
            WesternRule(
                rule_id="A",
                description="",
                condition_facts=("x=1",),
                outcome=WesternOutcomeTaxonomy.CAREER_PROMINENCE,
                direction=EvidenceDirection.SUPPORT,
            ),
            WesternRule(
                rule_id="B",
                description="",
                condition_facts=("x=2",),
                outcome=WesternOutcomeTaxonomy.FINANCIAL_GAIN,
                direction=EvidenceDirection.SUPPORT,
            ),
            WesternRule(
                rule_id="C",
                description="",
                condition_facts=("x=3",),
                outcome=WesternOutcomeTaxonomy.CAREER_PROMINENCE,
                direction=EvidenceDirection.CONTRADICT,
            ),
        )
        catalog = WesternRuleCatalog(rules=rules)
        career = catalog.get_rules_by_outcome(
            WesternOutcomeTaxonomy.CAREER_PROMINENCE
        )
        assert len(career) == 2


# ── Condition Evaluation Tests ───────────────────────────────────────────────


class TestEvaluateCondition:
    """Tests for evaluate_condition function."""

    def test_equality_match(self) -> None:
        assert evaluate_condition("sun_house=10", {"sun_house": "10"}) is True

    def test_equality_no_match(self) -> None:
        assert evaluate_condition("sun_house=10", {"sun_house": "5"}) is False

    def test_equality_missing_key(self) -> None:
        assert evaluate_condition("sun_house=10", {}) is False

    def test_truthy_match(self) -> None:
        assert evaluate_condition(
            "aspect_sun_trine_jupiter=true",
            {"aspect_sun_trine_jupiter": "true"},
        ) is True

    def test_truthy_no_match(self) -> None:
        assert evaluate_condition(
            "aspect_sun_trine_jupiter=true",
            {"aspect_sun_trine_jupiter": "false"},
        ) is False

    def test_case_insensitive(self) -> None:
        assert evaluate_condition(
            "sun_dignity=DOMICILE", {"sun_dignity": "domicile"}
        ) is True


class TestEvaluateRule:
    """Tests for evaluate_rule function."""

    def test_rule_matches(self) -> None:
        rule = WesternRule(
            rule_id="T1",
            description="",
            condition_facts=("sun_house=10",),
            outcome=WesternOutcomeTaxonomy.CAREER_PROMINENCE,
            direction=EvidenceDirection.SUPPORT,
        )
        record = evaluate_rule(rule, {"sun_house": "10"})
        assert record is not None
        assert record.rule_id == "T1"
        assert record.outcome_taxonomy == "CAREER_PROMINENCE"

    def test_rule_no_match(self) -> None:
        rule = WesternRule(
            rule_id="T2",
            description="",
            condition_facts=("sun_house=10",),
            outcome=WesternOutcomeTaxonomy.CAREER_PROMINENCE,
            direction=EvidenceDirection.SUPPORT,
        )
        record = evaluate_rule(rule, {"sun_house": "5"})
        assert record is None

    def test_rule_multiple_conditions(self) -> None:
        rule = WesternRule(
            rule_id="T3",
            description="",
            condition_facts=("sun_house=10", "mars_house=10"),
            outcome=WesternOutcomeTaxonomy.CAREER_PROMINENCE,
            direction=EvidenceDirection.SUPPORT,
        )
        # Both conditions met
        record = evaluate_rule(rule, {"sun_house": "10", "mars_house": "10"})
        assert record is not None
        # Only one condition met
        record = evaluate_rule(rule, {"sun_house": "10", "mars_house": "5"})
        assert record is None

    def test_rule_empty_conditions(self) -> None:
        rule = WesternRule(
            rule_id="T4",
            description="",
            condition_facts=(),
            outcome=WesternOutcomeTaxonomy.CAREER_PROMINENCE,
            direction=EvidenceDirection.SUPPORT,
        )
        record = evaluate_rule(rule, {})
        assert record is None


# ── Fact Extraction Tests ────────────────────────────────────────────────────


class TestExtractFacts:
    """Tests for extract_facts_from_chart."""

    @pytest.fixture
    def chart(self) -> WesternChart:
        svc = WesternCalculationService()
        return svc.calculate(
            birth_date=dt.date(1879, 3, 14),
            birth_time=dt.time(10, 50, 8),
            latitude=48.4,
            longitude=9.99,
        )

    def test_house_facts_extracted(self, chart: WesternChart) -> None:
        facts = extract_facts_from_chart(chart)
        # Should have sun_house, moon_house, etc.
        assert "sun_house" in facts
        assert "moon_house" in facts
        house_val = int(facts["sun_house"])
        assert 1 <= house_val <= 12

    def test_dignity_facts_extracted(self, chart: WesternChart) -> None:
        facts = extract_facts_from_chart(chart)
        assert "sun_dignity" in facts
        assert facts["sun_dignity"] in {
            d.value for d in WesternDignity
        }

    def test_aspect_facts_extracted(self, chart: WesternChart) -> None:
        facts = extract_facts_from_chart(chart)
        aspect_keys = [k for k in facts if k.startswith("aspect_")]
        assert len(aspect_keys) > 0

    def test_aspect_key_deterministic(self) -> None:
        key1 = _aspect_key(
            WesternPlanet.SUN,
            WesternAspectType.CONJUNCTION,
            WesternPlanet.MERCURY,
        )
        key2 = _aspect_key(
            WesternPlanet.MERCURY,
            WesternAspectType.CONJUNCTION,
            WesternPlanet.SUN,
        )
        # Should be the same regardless of order
        assert key1 == key2

    def test_aspect_key_format(self) -> None:
        key = _aspect_key(
            WesternPlanet.SUN,
            WesternAspectType.TRINE,
            WesternPlanet.JUPITER,
        )
        assert key == "aspect_jupiter_trine_sun"  # alphabetical order


# ── House Determination Tests ────────────────────────────────────────────────


class TestDetermineHouse:
    """Tests for _determine_house helper."""

    def test_planet_in_first_house(self) -> None:
        chart = _make_simple_chart(
            cusps=[10.0, 40.0, 70.0, 100.0, 130.0, 160.0, 190.0,
                   220.0, 250.0, 280.0, 310.0, 340.0],
        )
        assert _determine_house(25.0, chart) == 1

    def test_planet_in_second_house(self) -> None:
        chart = _make_simple_chart(
            cusps=[10.0, 40.0, 70.0, 100.0, 130.0, 160.0, 190.0,
                   220.0, 250.0, 280.0, 310.0, 340.0],
        )
        assert _determine_house(55.0, chart) == 2

    def test_planet_wrapping_around(self) -> None:
        # House 12 wraps: 340° to 10°
        chart = _make_simple_chart(
            cusps=[10.0, 40.0, 70.0, 100.0, 130.0, 160.0, 190.0,
                   220.0, 250.0, 280.0, 310.0, 340.0],
        )
        assert _determine_house(355.0, chart) == 12

    def test_no_cusps(self) -> None:
        chart = _make_simple_chart(cusps=[])
        assert _determine_house(90.0, chart) is None


def _make_simple_chart(cusps: list[float]) -> WesternChart:
    """Create a minimal WesternChart for testing house determination."""
    house_cusps = tuple(
        HouseCusp(house_number=i + 1, longitude=cusps[i])
        for i in range(len(cusps))
    )
    return WesternChart(
        birth_date="2000-01-01",
        birth_time="12:00:00",
        latitude=40.0,
        longitude=-74.0,
        house_system=WesternHouseSystem.PLACIDUS,
        julian_day_ut=2451545.0,
        planet_positions=(),
        house_cusps=house_cusps,
        aspects=(),
        dignities={},
        ascendant=cusps[0] if cusps else 0.0,
        midheaven=0.0,
    )

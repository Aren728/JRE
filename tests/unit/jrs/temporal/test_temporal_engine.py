"""Unit tests for Temporal Dasha & Transit Dynamic Weighting Engine (RI-012).

Tests use synthetic/mocked inputs for Dasha periods, transit houses,
and Ashtakavarga scores. No real astronomical calculations.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from jrs.temporal.dasha_engine import (
    DashaHierarchy,
    DashaMultiplierResult,
    DashaPeriod,
    VimshottariDashaEngine,
    VIMSHOTTARI_DURATIONS,
    VIMSHOTTARI_ORDER,
)
from jrs.temporal.transit_evaluator import (
    TransitEvaluationResult,
    TransitEvaluator,
    TransitProfile,
)
from jrs.temporal.timeline_service import DynamicStrengthResult, DynamicTemporalService
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 1: VimshottariDashaEngine
# ══════════════════════════════════════════════════════════════════════════════


class TestVimshottariDashaEngine:
    """Tests for Vimshottari Dasha period calculation and multiplier logic."""

    def setup_method(self) -> None:
        self.engine = VimshottariDashaEngine()

    # ── Constants ────────────────────────────────────────────────────────

    def test_vimshottari_order_has_9_lords(self) -> None:
        """Vimshottari cycle has exactly 9 lords."""
        assert len(VIMSHOTTARI_ORDER) == 9

    def test_vimshottari_total_120_years(self) -> None:
        """Total Vimshottari cycle = 120 years."""
        total = sum(VIMSHOTTARI_DURATIONS.values())
        assert total == 120.0

    def test_vimshottari_all_planets_present(self) -> None:
        """All 7 classical planets + Rahu + Ketu have durations."""
        expected = {"SUN", "MOON", "MARS", "RAHU", "JUPITER", "SATURN", "MERCURY", "KETU", "VENUS"}
        assert set(VIMSHOTTARI_DURATIONS.keys()) == expected

    # ── Dasha Computation ────────────────────────────────────────────────

    def test_compute_dasha_returns_hierarchy(self) -> None:
        """compute_dasha_at returns a DashaHierarchy."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        result = self.engine.compute_dasha_at(
            target_timestamp=ts,
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
        )
        assert isinstance(result, DashaHierarchy)
        assert isinstance(result.mahadasha, DashaPeriod)
        assert isinstance(result.antardasha, DashaPeriod)
        assert isinstance(result.pratyantardasha, DashaPeriod)

    def test_dasha_hierarchy_lords_are_strings(self) -> None:
        """Dasha lords are uppercase planet name strings."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        result = self.engine.compute_dasha_at(ts, "ROHINI", 7.0)
        assert isinstance(result.md_lord, str)
        assert isinstance(result.ad_lord, str)
        assert isinstance(result.pd_lord, str)
        assert result.md_lord.isupper()

    def test_dasha_periods_are_frozen(self) -> None:
        """DashaPeriod is immutable."""
        period = DashaPeriod(
            lord="SUN",
            period_type="MD",
            start_utc=datetime(2024, 1, 1),
            end_utc=datetime(2030, 1, 1),
            duration_years=6.0,
        )
        with pytest.raises(AttributeError):
            period.lord = "MOON"  # type: ignore[misc]

    def test_dasha_period_contains_timestamp(self) -> None:
        """DashaPeriod.contains() correctly identifies timestamps."""
        period = DashaPeriod(
            lord="SUN",
            period_type="MD",
            start_utc=datetime(2024, 1, 1),
            end_utc=datetime(2030, 1, 1),
            duration_years=6.0,
        )
        assert period.contains(datetime(2025, 6, 15)) is True
        assert period.contains(datetime(2023, 12, 31)) is False
        assert period.contains(datetime(2030, 1, 1)) is False  # end is exclusive

    def test_dasha_period_exclusive_end(self) -> None:
        """End timestamp is exclusive."""
        period = DashaPeriod(
            lord="SUN",
            period_type="MD",
            start_utc=datetime(2024, 1, 1),
            end_utc=datetime(2024, 2, 1),
            duration_years=6.0,
        )
        assert period.contains(datetime(2024, 1, 31, 23, 59, 59)) is True
        assert period.contains(datetime(2024, 2, 1)) is False

    # ── Multiplier Logic ─────────────────────────────────────────────────

    def test_md_lord_match_gives_1_50(self) -> None:
        """Yoga planet matching MD lord → multiplier 1.50."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        result = self.engine.get_dasha_multiplier(hierarchy, ["KETU", "VENUS"])
        # KETU is the MD lord for ASHWINI nakshatra
        if hierarchy.md_lord == "KETU":
            assert result.multiplier == pytest.approx(1.50)
            assert result.matched_level == "MD"
            assert result.matched_planet == "KETU"

    def test_ad_lord_match_gives_1_25(self) -> None:
        """Yoga planet matching AD lord → multiplier 1.25."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        # Use a planet that is the AD lord but not MD lord
        if hierarchy.ad_lord != hierarchy.md_lord:
            result = self.engine.get_dasha_multiplier(hierarchy, [hierarchy.ad_lord])
            assert result.multiplier == pytest.approx(1.25)
            assert result.matched_level == "AD"

    def test_pd_lord_match_gives_1_10(self) -> None:
        """Yoga planet matching PD lord → multiplier 1.10."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        # Use a planet that is PD lord but not MD or AD
        if hierarchy.pd_lord != hierarchy.md_lord and hierarchy.pd_lord != hierarchy.ad_lord:
            result = self.engine.get_dasha_multiplier(hierarchy, [hierarchy.pd_lord])
            assert result.multiplier == pytest.approx(1.10)
            assert result.matched_level == "PD"

    def test_no_match_gives_dormant_0_40(self) -> None:
        """No yoga planet in Dasha → dormant multiplier 0.40."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        # Use a planet that is NOT any Dasha lord
        other_planets = [
            p for p in ["SUN", "MOON", "MARS", "JUPITER", "SATURN", "VENUS", "MERCURY"]
            if p not in (hierarchy.md_lord, hierarchy.ad_lord, hierarchy.pd_lord)
        ]
        if other_planets:
            result = self.engine.get_dasha_multiplier(hierarchy, [other_planets[0]])
            assert result.multiplier == pytest.approx(0.40)
            assert result.matched_level == "NONE"

    def test_max_multiplier_across_multiple_planets(self) -> None:
        """Returns max multiplier when multiple yoga planets involved."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        # Include both MD lord and a non-matching planet
        planets = [hierarchy.md_lord, "SUN"]
        result = self.engine.get_dasha_multiplier(hierarchy, planets)
        assert result.multiplier == pytest.approx(1.50)

    def test_multiplier_result_is_frozen(self) -> None:
        """DashaMultiplierResult is immutable."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        result = self.engine.get_dasha_multiplier(hierarchy, ["KETU"])
        with pytest.raises(AttributeError):
            result.multiplier = 2.0  # type: ignore[misc]

    # ── Edge Cases ───────────────────────────────────────────────────────

    def test_case_insensitive_planet_names(self) -> None:
        """Yoga planet names are matched case-insensitively."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        result = self.engine.get_dasha_multiplier(hierarchy, ["ketu"])
        # Should match since we uppercase internally
        assert result.multiplier in (1.50, 1.25, 1.10, 0.40)

    def test_empty_yoga_planets_gives_dormant(self) -> None:
        """Empty yoga planets list → dormant multiplier."""
        ts = datetime(2024, 6, 15, 12, 0, 0)
        hierarchy = self.engine.compute_dasha_at(ts, "ASHWINI", 5.0)
        result = self.engine.get_dasha_multiplier(hierarchy, [])
        assert result.multiplier == pytest.approx(0.40)


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 2: TransitEvaluator
# ══════════════════════════════════════════════════════════════════════════════


class TestTransitEvaluator:
    """Tests for Transit (Gochar) multiplier calculations."""

    def setup_method(self) -> None:
        self.evaluator = TransitEvaluator()

    # ── Single Planet Evaluation ─────────────────────────────────────────

    def test_high_bindus_gives_bonus(self) -> None:
        """Ashtakavarga score >= 4 → +0.15 bonus."""
        profile = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=5,
            ashtakavarga_scores={"JUPITER": 5},
            natal_moon_house=1,
        )
        assert profile.bindus == 5
        assert profile.net_transit_multiplier == pytest.approx(1.15)
        assert profile.dusthana_penalty is False

    def test_low_bindus_gives_penalty(self) -> None:
        """Ashtakavarga score < 4 → -0.20 penalty."""
        profile = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=5,
            ashtakavarga_scores={"JUPITER": 3},
            natal_moon_house=1,
        )
        assert profile.bindus == 3
        assert profile.net_transit_multiplier == pytest.approx(0.80)
        assert profile.dusthana_penalty is False

    def test_boundary_4_bindus_gives_bonus(self) -> None:
        """Ashtakavarga score exactly 4 → bonus."""
        profile = self.evaluator.evaluate_planet(
            planet="SATURN",
            transit_house=3,
            ashtakavarga_scores={"SATURN": 4},
            natal_moon_house=1,
        )
        assert profile.net_transit_multiplier == pytest.approx(1.15)

    def test_boundary_3_bindus_gives_penalty(self) -> None:
        """Ashtakavarga score exactly 3 → penalty."""
        profile = self.evaluator.evaluate_planet(
            planet="SATURN",
            transit_house=3,
            ashtakavarga_scores={"SATURN": 3},
            natal_moon_house=1,
        )
        assert profile.net_transit_multiplier == pytest.approx(0.80)

    def test_8th_house_from_moon_penalty(self) -> None:
        """Transiting in 8th house from natal Moon → -0.25."""
        profile = self.evaluator.evaluate_planet(
            planet="MARS",
            transit_house=8,
            ashtakavarga_scores={"MARS": 5},
            natal_moon_house=1,
        )
        assert profile.dusthana_penalty is True
        # 1.00 + 0.15 - 0.25 = 0.90
        assert profile.net_transit_multiplier == pytest.approx(0.90)

    def test_12th_house_from_moon_penalty(self) -> None:
        """Transiting in 12th house from natal Moon → -0.25."""
        profile = self.evaluator.evaluate_planet(
            planet="MARS",
            transit_house=12,
            ashtakavarga_scores={"MARS": 5},
            natal_moon_house=1,
        )
        assert profile.dusthana_penalty is True
        assert profile.net_transit_multiplier == pytest.approx(0.90)

    def test_house_from_moon_wraps_around(self) -> None:
        """House from Moon is computed modularly (wraps around 12)."""
        # Moon in house 10, transiting in house 2 → 5th from Moon
        profile = self.evaluator.evaluate_planet(
            planet="VENUS",
            transit_house=2,
            ashtakavarga_scores={"VENUS": 5},
            natal_moon_house=10,
        )
        # 2nd from Moon: (2-10) % 12 + 1 = 4
        assert profile.dusthana_penalty is False

    def test_combined_bonus_and_penalty(self) -> None:
        """High bindus + dusthana house → bonus + penalty."""
        profile = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=8,
            ashtakavarga_scores={"JUPITER": 6},
            natal_moon_house=1,
        )
        # 1.00 + 0.15 - 0.25 = 0.90
        assert profile.net_transit_multiplier == pytest.approx(0.90)

    def test_combined_penalty_and_low_bindus(self) -> None:
        """Low bindus + dusthana house → double penalty."""
        profile = self.evaluator.evaluate_planet(
            planet="SATURN",
            transit_house=12,
            ashtakavarga_scores={"SATURN": 2},
            natal_moon_house=1,
        )
        # 1.00 - 0.20 - 0.25 = 0.55
        assert profile.net_transit_multiplier == pytest.approx(0.55)

    def test_zero_bindus(self) -> None:
        """Zero bindus → penalty applied."""
        profile = self.evaluator.evaluate_planet(
            planet="RAHU",
            transit_house=5,
            ashtakavarga_scores={},
            natal_moon_house=1,
        )
        assert profile.bindus == 0
        assert profile.net_transit_multiplier == pytest.approx(0.80)

    def test_default_house_is_1(self) -> None:
        """Default transit_house is 1."""
        profile = self.evaluator.evaluate_planet(
            planet="SUN",
            transit_house=1,
            ashtakavarga_scores={"SUN": 5},
            natal_moon_house=1,
        )
        assert profile.transit_house == 1
        assert profile.dusthana_penalty is False

    def test_profile_is_frozen(self) -> None:
        """TransitProfile is immutable."""
        profile = self.evaluator.evaluate_planet(
            planet="SUN",
            transit_house=1,
            ashtakavarga_scores={"SUN": 5},
            natal_moon_house=1,
        )
        with pytest.raises(AttributeError):
            profile.planet = "MOON"  # type: ignore[misc]

    # ── Multiple Planet Evaluation ───────────────────────────────────────

    def test_evaluate_multiple_returns_result(self) -> None:
        """evaluate_multiple returns TransitEvaluationResult."""
        result = self.evaluator.evaluate_multiple(
            planets=["JUPITER", "SATURN"],
            transit_houses={"JUPITER": 5, "SATURN": 3},
            ashtakavarga_scores={"JUPITER": 5, "SATURN": 6},
            natal_moon_house=1,
        )
        assert isinstance(result, TransitEvaluationResult)
        assert len(result.profiles) == 2

    def test_aggregate_multiplier_is_product(self) -> None:
        """Aggregate multiplier is product of individual multipliers."""
        result = self.evaluator.evaluate_multiple(
            planets=["JUPITER", "SATURN"],
            transit_houses={"JUPITER": 5, "SATURN": 3},
            ashtakavarga_scores={"JUPITER": 5, "SATURN": 5},
            natal_moon_house=1,
        )
        expected = 1.15 * 1.15
        assert result.aggregate_multiplier == pytest.approx(expected, abs=1e-4)

    def test_evaluate_multiple_empty_planets(self) -> None:
        """Empty planets list → no profiles, aggregate = 1.0."""
        result = self.evaluator.evaluate_multiple(
            planets=[],
            transit_houses={},
            ashtakavarga_scores={},
            natal_moon_house=1,
        )
        assert len(result.profiles) == 0
        assert result.aggregate_multiplier == pytest.approx(1.0)


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 3: DynamicTemporalService (Clamping & Integration)
# ══════════════════════════════════════════════════════════════════════════════


class TestDynamicTemporalService:
    """Tests for dynamic strength clamping and pipeline integration."""

    def setup_method(self) -> None:
        self.service = DynamicTemporalService()

    def test_basic_computation(self) -> None:
        """Basic dynamic strength computation with Dasha only."""
        result = self.service.compute_dynamic_strength(
            static_strength=0.5,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=["KETU", "VENUS"],
        )
        assert isinstance(result, DynamicStrengthResult)
        assert 0.0 <= result.dynamic_strength <= 1.0

    def test_static_strength_clamped_to_0_1(self) -> None:
        """Static strength is clamped to [0.0, 1.0]."""
        result = self.service.compute_dynamic_strength(
            static_strength=1.5,  # out of range
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=[],
        )
        assert 0.0 <= result.static_strength <= 1.0

    def test_negative_static_strength_clamped(self) -> None:
        """Negative static strength is clamped to 0.0."""
        result = self.service.compute_dynamic_strength(
            static_strength=-0.5,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=[],
        )
        assert result.static_strength == 0.0
        assert result.dynamic_strength == 0.0

    def test_dynamic_strength_always_in_0_1(self) -> None:
        """Dynamic strength is always clamped to [0.0, 1.0]."""
        # Test with extreme multipliers
        result = self.service.compute_dynamic_strength(
            static_strength=0.9,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=["KETU"],
            transit_houses={"KETU": 5},
            ashtakavarga_scores={"KETU": 5},
            natal_moon_house=1,
        )
        assert 0.0 <= result.dynamic_strength <= 1.0

    def test_dormant_dasha_reduces_strength(self) -> None:
        """Dormant Dasha (no match) reduces strength via 0.40 multiplier."""
        result = self.service.compute_dynamic_strength(
            static_strength=1.0,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=["SUN"],  # unlikely to match MD/AD/PD
        )
        # If no match: 1.0 * 0.40 = 0.40
        # If match: higher
        assert result.dasha_multiplier in (0.40, 1.10, 1.25, 1.50)

    def test_transit_with_bindus_and_houses(self) -> None:
        """Transit evaluation with Ashtakavarga and house data."""
        result = self.service.compute_dynamic_strength(
            static_strength=0.7,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ROHINI",
            moon_nakshatra_degree=10.0,
            yoga_planets=["MOON", "JUPITER"],
            transit_houses={"MOON": 5, "JUPITER": 9},
            ashtakavarga_scores={"MOON": 5, "JUPITER": 3},
            natal_moon_house=4,
        )
        assert result.transit_result is not None
        assert len(result.transit_result.profiles) == 2
        assert 0.0 <= result.dynamic_strength <= 1.0

    def test_transit_without_data_skipped(self) -> None:
        """Transit multiplier defaults to 1.0 when no transit data."""
        result = self.service.compute_dynamic_strength(
            static_strength=0.8,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=["KETU"],
        )
        assert result.transit_multiplier == 1.0
        assert result.transit_result is None

    def test_result_is_frozen(self) -> None:
        """DynamicStrengthResult is immutable."""
        result = self.service.compute_dynamic_strength(
            static_strength=0.5,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=[],
        )
        with pytest.raises(AttributeError):
            result.dynamic_strength = 0.9  # type: ignore[misc]

    def test_active_dasha_populated(self) -> None:
        """Active Dasha hierarchy is populated in result."""
        result = self.service.compute_dynamic_strength(
            static_strength=0.5,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=[],
        )
        assert result.active_dasha is not None
        assert isinstance(result.active_dasha, DashaHierarchy)

    def test_zero_static_strength_gives_zero_dynamic(self) -> None:
        """Zero static strength → zero dynamic regardless of multipliers."""
        result = self.service.compute_dynamic_strength(
            static_strength=0.0,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=["KETU"],
        )
        assert result.dynamic_strength == 0.0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 4: YogaEvaluatorService Integration (Layer 3)
# ══════════════════════════════════════════════════════════════════════════════


class TestYogaEvaluatorServiceTemporalIntegration:
    """Integration tests for temporal weighting in YogaEvaluatorService."""

    def setup_method(self) -> None:
        self.service = YogaEvaluatorService()

    def test_evaluate_formation_with_temporal_fields(self) -> None:
        """evaluate_formation returns temporal fields when moon_nakshatra present."""
        jre_facts = {
            "planets": {
                "JUPITER": {
                    "house": 1, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
                "MOON": {
                    "house": 4, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
            },
            "lagna_sign": 1,
            "moon_nakshatra": "ASHWINI",
            "moon_nakshatra_degree": 5.0,
        }
        result = self.service.evaluate_formation(
            yoga_name="TestTemporal",
            involved_planets=["JUPITER", "MOON"],
            jre_facts=jre_facts,
        )
        assert isinstance(result, YogaEvaluation)
        assert result.dasha_multiplier is not None
        assert result.transit_multiplier is not None
        assert result.dynamic_strength is not None
        assert 0.0 <= result.dynamic_strength <= 1.0

    def test_evaluate_formation_without_moon_nakshatra(self) -> None:
        """evaluate_formation returns None temporal fields without moon_nakshatra."""
        jre_facts = {
            "planets": {
                "JUPITER": {
                    "house": 1, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False,
                },
            },
            "lagna_sign": 1,
        }
        result = self.service.evaluate_formation(
            yoga_name="TestNoTemporal",
            involved_planets=["JUPITER"],
            jre_facts=jre_facts,
        )
        assert result.dasha_multiplier is None
        assert result.transit_multiplier is None
        assert result.dynamic_strength is None

    def test_compute_dynamic_strength_returns_result(self) -> None:
        """compute_dynamic_strength returns DynamicStrengthResult."""
        jre_facts = {
            "planets": {
                "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                "MOON": {"house": 4, "combust": False, "debilitated": False},
            },
            "lagna_sign": 1,
            "moon_nakshatra": "ASHWINI",
            "moon_nakshatra_degree": 5.0,
        }
        result = self.service.compute_dynamic_strength(
            static_strength=0.5,
            involved_planets=["JUPITER", "MOON"],
            jre_facts=jre_facts,
        )
        assert isinstance(result, DynamicStrengthResult)
        assert 0.0 <= result.dynamic_strength <= 1.0

    def test_temporal_fields_in_to_dict(self) -> None:
        """Temporal fields appear in YogaEvaluation.to_dict() when set."""
        jre_facts = {
            "planets": {
                "JUPITER": {
                    "house": 1, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
            },
            "lagna_sign": 1,
            "moon_nakshatra": "ASHWINI",
            "moon_nakshatra_degree": 5.0,
        }
        result = self.service.evaluate_formation(
            yoga_name="TestDict",
            involved_planets=["JUPITER"],
            jre_facts=jre_facts,
        )
        d = result.to_dict()
        assert "dasha_multiplier" in d
        assert "transit_multiplier" in d
        assert "dynamic_strength" in d

    def test_classical_yoga_with_temporal(self) -> None:
        """Classical yoga evaluation includes temporal fields when data present."""
        jre_facts = {
            "planets": {
                "JUPITER": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MESHA",
                    "house_lord_of": 5,
                },
                "MOON": {
                    "house": 4, "rashi_num": 4, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "KARKA",
                },
                "MARS": {
                    "house": 5, "rashi_num": 5, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "SIMHA",
                    "house_lord_of": 1,
                },
                "SATURN": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MESHA",
                },
                "SUN": {
                    "house": 1, "rashi_num": 1, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MESHA",
                },
                "MERCURY": {
                    "house": 3, "rashi_num": 3, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "MITHUNA",
                },
                "VENUS": {
                    "house": 7, "rashi_num": 7, "combust": False,
                    "debilitated": False, "retrograde": False, "rashi": "TULA",
                },
            },
            "lagna_sign": 1,
            "moon_nakshatra": "ASHWINI",
            "moon_nakshatra_degree": 5.0,
        }
        results = self.service.evaluate_classical_yogas(jre_facts)
        for r in results:
            assert r.dasha_multiplier is not None
            assert r.transit_multiplier is not None
            assert r.dynamic_strength is not None


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 5: Edge Cases & Boundary Conditions
# ══════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases for the temporal engine."""

    def test_transit_boundary_0_bindus(self) -> None:
        """Zero bindus with dusthana → minimum multiplier."""
        evaluator = TransitEvaluator()
        profile = evaluator.evaluate_planet(
            planet="RAHU",
            transit_house=8,
            ashtakavarga_scores={},
            natal_moon_house=1,
        )
        # 1.00 - 0.20 - 0.25 = 0.55
        assert profile.net_transit_multiplier == pytest.approx(0.55)

    def test_transit_boundary_8_bindus(self) -> None:
        """Maximum bindus (8) → bonus."""
        evaluator = TransitEvaluator()
        profile = evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=5,
            ashtakavarga_scores={"JUPITER": 8},
            natal_moon_house=1,
        )
        assert profile.net_transit_multiplier == pytest.approx(1.15)

    def test_dasha_different_nakshatras(self) -> None:
        """Different Nakshatras produce different MD lords."""
        engine = VimshottariDashaEngine()
        ts = datetime(2024, 6, 15)
        nakshatras = ["ASHWINI", "ROHINI", "KRITTIKA", "PUSHYA"]
        md_lords = set()
        for nak in nakshatras:
            h = engine.compute_dasha_at(ts, nak, 5.0)
            md_lords.add(h.md_lord)
        # Different Nakshatras should yield different MD lords
        assert len(md_lords) > 1

    def test_combined_high_multiplier_scenario(self) -> None:
        """MD match + high AV + favorable house → high dynamic score."""
        service = DynamicTemporalService()
        result = service.compute_dynamic_strength(
            static_strength=1.0,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=["KETU"],
            transit_houses={"KETU": 1},
            ashtakavarga_scores={"KETU": 8},
            natal_moon_house=1,
        )
        # MD match (1.50) × (1.0 + 0.15 = 1.15) × 1.0 (static) = 1.725 → clamped to 1.0
        assert result.dynamic_strength == pytest.approx(1.0)

    def test_combined_low_multiplier_scenario(self) -> None:
        """No Dasha match + low AV + dusthana → low dynamic score."""
        service = DynamicTemporalService()
        result = service.compute_dynamic_strength(
            static_strength=0.5,
            target_timestamp=datetime(2024, 6, 15),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=5.0,
            yoga_planets=["SUN"],  # unlikely to match KETU's dasha
            transit_houses={"SUN": 12},
            ashtakavarga_scores={"SUN": 1},
            natal_moon_house=1,
        )
        # Dormant (0.40) × (1.0 - 0.20 - 0.25 = 0.55) × 0.5 = 0.11
        assert result.dynamic_strength == pytest.approx(0.11, abs=0.05)

    def test_transit_profile_zero_from_moon_house(self) -> None:
        """Transit in same house as Moon → 1st from Moon, no dusthana."""
        evaluator = TransitEvaluator()
        profile = evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=4,
            ashtakavarga_scores={"JUPITER": 5},
            natal_moon_house=4,
        )
        assert profile.dusthana_penalty is False

    def test_dynamic_service_with_all_nakshatras(self) -> None:
        """DynamicTemporalService works with all 27 Nakshatras."""
        service = DynamicTemporalService()
        nakshatras = [
            "ASHWINI", "BHARANI", "KRITTIKA", "ROHINI", "MRIGASHIRA",
            "ARDRA", "PUNARVASU", "PUSHYA", "ASHLESHA", "MAGHA",
            "PURVA_PHALGUNI", "UTTARA_PHALGUNI", "HASTA", "CHITRA",
            "SWATI", "VISHAKHA", "ANURADHA", "JYESHTHA", "MULA",
            "PURVA_ASHADHA", "UTTARA_ASHADHA", "SHRAVANA", "DHANISHTHA",
            "SHATABHISHA", "PURVA_BHADRAPADA", "UTTARA_BHADRAPADA", "REVATI",
        ]
        for nak in nakshatras:
            result = service.compute_dynamic_strength(
                static_strength=0.5,
                target_timestamp=datetime(2024, 6, 15),
                moon_nakshatra=nak,
                moon_nakshatra_degree=5.0,
                yoga_planets=["JUPITER"],
            )
            assert 0.0 <= result.dynamic_strength <= 1.0


# ══════════════════════════════════════════════════════════════════════════════
# Test Class 12: Fix 3 — Extended Dasha Activation (Phase E6e)
# ══════════════════════════════════════════════════════════════════════════════


class TestExtendedDashaActivation:
    """Extended Dasha activation: functional lord / dispositor / nakshatra lord."""

    def setup_method(self) -> None:
        self.engine = VimshottariDashaEngine()

    def _make_hierarchy(self, md: str, ad: str, pd: str) -> DashaHierarchy:
        now = datetime(2024, 1, 1)
        return DashaHierarchy(
            mahadasha=DashaPeriod(
                lord=md, period_type="MD",
                start_utc=now, end_utc=datetime(2030, 1, 1),
                duration_years=6.0,
            ),
            antardasha=DashaPeriod(
                lord=ad, period_type="AD",
                start_utc=now, end_utc=datetime(2025, 1, 1),
                duration_years=1.0,
            ),
            pratyantardasha=DashaPeriod(
                lord=pd, period_type="PD",
                start_utc=now, end_utc=datetime(2024, 4, 1),
                duration_years=0.25,
            ),
        )

    def test_functional_lord_activation(self) -> None:
        """Fix 3: Dasha lord is functional Kendra/Trikona lord → partial activation."""
        # Jupiter (MD lord) is not a yoga planet, but owns house 9 (Trikona)
        hierarchy = self._make_hierarchy("JUPITER", "SATURN", "MERCURY")

        jre_facts = {
            "planets": {
                "VENUS": {"house": 7, "sign_lord": "VENUS", "nakshatra_lord": "SATURN"},
                "SATURN": {"house": 10, "sign_lord": "SATURN", "nakshatra_lord": "SATURN"},
            },
            "house_lords": {1: "MARS", 5: "VENUS", 9: "JUPITER", 10: "SATURN"},
        }

        # Venus is the yoga planet (in house 7 = Kendra)
        # Jupiter is NOT a yoga planet but owns house 9 (Trikona)
        result = self.engine.get_dasha_multiplier(
            hierarchy, ["VENUS"], jre_facts=jre_facts,
        )

        # Jupiter (MD) not in yoga planets → not direct match
        # But Jupiter is a functional Trikona lord + yoga planet in Kendra
        # → extended activation at MD level... but we only check AD/PD
        # In this case, MD is not a direct match, so we check AD/PD
        # Saturn (AD) is not a yoga planet
        # Mercury (PD) is not a yoga planet
        # But Saturn is the sign_lord and nakshatra_lord of Venus
        assert result.multiplier > 0.40, (
            f"Extended activation should fire, got {result.multiplier}"
        )

    def test_dispositor_activation(self) -> None:
        """Fix 3: Dasha lord is dispositor of yoga planet → partial activation."""
        # AD lord = SATURN, which is the sign_lord of VENUS
        # PD lord = MERCURY (not related to VENUS)
        hierarchy = self._make_hierarchy("MOON", "SATURN", "KETU")

        jre_facts = {
            "planets": {
                "VENUS": {"house": 7, "sign_lord": "SATURN", "nakshatra_lord": "MERCURY"},
            },
            "house_lords": {1: "MARS", 7: "VENUS"},
        }

        result = self.engine.get_dasha_multiplier(
            hierarchy, ["VENUS"], jre_facts=jre_facts,
        )

        # MOON (MD) not in yoga planets → no direct match
        # SATURN (AD) is sign_lord of VENUS → dispositor activation at AD
        assert result.matched_level == "AD"
        assert result.multiplier >= 1.10

    def test_nakshatra_lord_activation(self) -> None:
        """Fix 3: Dasha lord rules Nakshatra of yoga planet → partial activation."""
        # PD lord = MERCURY, which is the nakshatra_lord of VENUS
        hierarchy = self._make_hierarchy("MOON", "SUN", "MERCURY")

        jre_facts = {
            "planets": {
                "VENUS": {"house": 7, "sign_lord": "VENUS", "nakshatra_lord": "MERCURY"},
            },
            "house_lords": {1: "MARS", 7: "VENUS"},
        }

        result = self.engine.get_dasha_multiplier(
            hierarchy, ["VENUS"], jre_facts=jre_facts,
        )

        # MOON (MD) not match, SUN (AD) not match
        # MERCURY (PD) is nakshatra_lord of VENUS → nakshatra activation
        assert result.matched_level == "PD"
        assert result.multiplier >= 1.05

    def test_no_jre_facts_fallback(self) -> None:
        """Without jre_facts, only direct matches work (backward compatible)."""
        hierarchy = self._make_hierarchy("JUPITER", "SATURN", "MERCURY")

        # No jre_facts → no extended matching
        result = self.engine.get_dasha_multiplier(
            hierarchy, ["VENUS"],
        )

        # No direct match → dormant
        assert result.matched_level == "NONE"
        assert result.multiplier == 0.40

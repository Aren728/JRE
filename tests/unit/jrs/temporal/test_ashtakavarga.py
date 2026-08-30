"""JRE Temporal — Unit tests for AshtakavargaService and TransitEvaluator.

Tests classical BAV bindus calculation, transit multiplier application,
and fallback behavior when bindu data is missing.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from jrs.temporal.ashtakavarga_service import (  # noqa: E402
    AshtakavargaService,
    _BAV_TABLE,
)
from jrs.temporal.transit_evaluator import TransitEvaluator  # noqa: E402


# ── BAV Table Tests ─────────────────────────────────────────────────────────


class TestBAVTable:
    """Verify classical BAV bindus tables match BPHS Ch 3."""

    def test_sun_bav_houses(self) -> None:
        """Sun gives bindus in houses 1,2,4,7,8,9,10,11 from Moon."""
        expected = {1, 2, 4, 7, 8, 9, 10, 11}
        assert _BAV_TABLE["SUN"] == frozenset(expected)

    def test_moon_bav_houses(self) -> None:
        """Moon gives bindus in houses 1,3,6,7,8,10,11 from Moon."""
        expected = {1, 3, 6, 7, 8, 10, 11}
        assert _BAV_TABLE["MOON"] == frozenset(expected)

    def test_mars_bav_houses(self) -> None:
        """Mars gives bindus in houses 1,2,4,7,8,9,10,11 from Moon."""
        expected = {1, 2, 4, 7, 8, 9, 10, 11}
        assert _BAV_TABLE["MARS"] == frozenset(expected)

    def test_mercury_bav_houses(self) -> None:
        """Mercury gives bindus in houses 1,2,4,6,8,9,10,11 from Moon."""
        expected = {1, 2, 4, 6, 8, 9, 10, 11}
        assert _BAV_TABLE["MERCURY"] == frozenset(expected)

    def test_jupiter_bav_houses(self) -> None:
        """Jupiter gives bindus in houses 1,2,4,5,6,7,9,10,11 from Moon."""
        expected = {1, 2, 4, 5, 6, 7, 9, 10, 11}
        assert _BAV_TABLE["JUPITER"] == frozenset(expected)

    def test_venus_bav_houses(self) -> None:
        """Venus gives bindus in houses 1,2,3,4,5,7,8,9,10,11 from Moon."""
        expected = {1, 2, 3, 4, 5, 7, 8, 9, 10, 11}
        assert _BAV_TABLE["VENUS"] == frozenset(expected)

    def test_saturn_bav_houses(self) -> None:
        """Saturn gives bindus in houses 1,2,4,5,6,7,8,9,10,11 from Moon."""
        expected = {1, 2, 4, 5, 6, 7, 8, 9, 10, 11}
        assert _BAV_TABLE["SATURN"] == frozenset(expected)

    def test_all_classical_planets_present(self) -> None:
        """BAV table contains all 7 classical planets."""
        expected_planets = {"SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"}
        assert set(_BAV_TABLE.keys()) == expected_planets

    def test_jupiter_in_1st_from_moon_gives_bindu(self) -> None:
        """Jupiter transiting 1st house from Moon → 1 bindu."""
        assert 1 in _BAV_TABLE["JUPITER"]

    def test_sun_in_6th_from_moon_no_bindu(self) -> None:
        """Sun transiting 6th house from Moon → 0 bindus."""
        assert 6 not in _BAV_TABLE["SUN"]

    def test_venus_in_6th_from_moon_no_bindu(self) -> None:
        """Venus transiting 6th house from Moon → 0 bindus."""
        assert 6 not in _BAV_TABLE["VENUS"]


# ── AshtakavargaService Tests ───────────────────────────────────────────────


class TestAshtakavargaService:
    """Tests for AshtakavargaService.compute_profile()."""

    def setup_method(self) -> None:
        self.svc = AshtakavargaService()

    def test_compute_profile_returns_correct_type(self) -> None:
        """compute_profile returns an AshtakavargaProfile."""
        from jrs.temporal.ashtakavarga_service import AshtakavargaProfile

        jre_facts = {
            "planets": {
                "MOON": {"house": 4, "longitude": 105.0},
                "SUN": {"house": 6, "longitude": 165.0},
            },
            "lagna_sign": 5,
            "natal_moon_house": 4,
        }
        ts = datetime(2024, 1, 15, tzinfo=timezone.utc)
        profile = self.svc.compute_profile(jre_facts, ts)
        assert isinstance(profile, AshtakavargaProfile)

    def test_transit_houses_populated(self) -> None:
        """Transit houses dict is populated for all planets."""
        jre_facts = {
            "planets": {
                "MOON": {"house": 1, "longitude": 15.0},
                "SUN": {"house": 1, "longitude": 15.0},
            },
            "lagna_sign": 1,
            "natal_moon_house": 1,
        }
        ts = datetime(2024, 1, 15, tzinfo=timezone.utc)
        profile = self.svc.compute_profile(jre_facts, ts)
        assert len(profile.transit_houses) > 0
        for planet, house in profile.transit_houses.items():
            assert 1 <= house <= 12

    def test_ashtakavarga_scores_non_negative(self) -> None:
        """All AV scores are non-negative."""
        jre_facts = {
            "planets": {
                "MOON": {"house": 1, "longitude": 15.0},
            },
            "lagna_sign": 1,
            "natal_moon_house": 1,
        }
        ts = datetime(2024, 1, 15, tzinfo=timezone.utc)
        profile = self.svc.compute_profile(jre_facts, ts)
        for planet, score in profile.ashtakavarga_scores.items():
            assert score >= 0, f"{planet} has negative score: {score}"

    def test_sav_scores_reasonable_range(self) -> None:
        """SAV scores are in reasonable range (0–56 for 7 planets)."""
        jre_facts = {
            "planets": {
                "MOON": {"house": 1, "longitude": 15.0},
            },
            "lagna_sign": 1,
            "natal_moon_house": 1,
        }
        ts = datetime(2024, 1, 15, tzinfo=timezone.utc)
        profile = self.svc.compute_profile(jre_facts, ts)
        for planet, score in profile.ashtakavarga_scores.items():
            assert 0 <= score <= 56, f"{planet} score out of range: {score}"


# ── TransitEvaluator with Real Data Tests ────────────────────────────────────


class TestTransitEvaluatorWithRealData:
    """Tests for TransitEvaluator using real Ashtakavarga bindu data."""

    def setup_method(self) -> None:
        self.evaluator = TransitEvaluator()

    def test_high_bindus_gives_bonus(self) -> None:
        """Planet with >= 4 bindus gets +0.15 bonus."""
        profile = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=1,
            ashtakavarga_scores={"JUPITER": 5},
            natal_moon_house=1,
        )
        # Base 1.00 + 0.15 (high bindus) = 1.15
        assert profile.bindus == 5
        assert profile.net_transit_multiplier == 1.15

    def test_low_bindus_gives_penalty(self) -> None:
        """Planet with < 4 bindus gets -0.20 penalty."""
        profile = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=1,
            ashtakavarga_scores={"JUPITER": 2},
            natal_moon_house=1,
        )
        # Base 1.00 - 0.20 (low bindus) = 0.80
        assert profile.bindus == 2
        assert profile.net_transit_multiplier == 0.80

    def test_dusthana_from_moon_penalty(self) -> None:
        """Transit in 8th or 12th from Moon gets -0.25 penalty."""
        profile = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=8,  # 8th from Moon (Moon in house 1)
            ashtakavarga_scores={"JUPITER": 5},
            natal_moon_house=1,
        )
        # Base 1.00 + 0.15 (high) - 0.25 (dusthana) = 0.90
        assert profile.dusthana_penalty is True
        assert profile.net_transit_multiplier == 0.90

    def test_12th_from_moon_penalty(self) -> None:
        """Transit in 12th from Moon gets dusthana penalty."""
        profile = self.evaluator.evaluate_planet(
            planet="SATURN",
            transit_house=12,  # 12th from Moon (Moon in house 1)
            ashtakavarga_scores={"SATURN": 6},
            natal_moon_house=1,
        )
        assert profile.dusthana_penalty is True
        # 1.00 + 0.15 - 0.25 = 0.90
        assert profile.net_transit_multiplier == 0.90

    def test_no_dusthana_penalty_in_kendra(self) -> None:
        """Transit in 1st/4th/7th/10th from Moon has no dusthana penalty."""
        for house in [1, 4, 7, 10]:
            profile = self.evaluator.evaluate_planet(
                planet="JUPITER",
                transit_house=house,
                ashtakavarga_scores={"JUPITER": 5},
                natal_moon_house=1,
            )
            assert profile.dusthana_penalty is False

    def test_boundary_bindu_threshold(self) -> None:
        """Exactly 4 bindus is the threshold for bonus."""
        profile_4 = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=1,
            ashtakavarga_scores={"JUPITER": 4},
            natal_moon_house=1,
        )
        profile_3 = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=1,
            ashtakavarga_scores={"JUPITER": 3},
            natal_moon_house=1,
        )
        assert profile_4.net_transit_multiplier == 1.15  # >= 4 → bonus
        assert profile_3.net_transit_multiplier == 0.80  # < 4 → penalty

    def test_missing_bindu_data_defaults_to_zero(self) -> None:
        """When planet not in AV scores, defaults to 0 bindus."""
        profile = self.evaluator.evaluate_planet(
            planet="JUPITER",
            transit_house=1,
            ashtakavarga_scores={},  # Empty
            natal_moon_house=1,
        )
        assert profile.bindus == 0
        assert profile.net_transit_multiplier == 0.80  # Low penalty


# ── Fallback Behavior Tests ──────────────────────────────────────────────────


class TestFallbackBehavior:
    """Tests for graceful fallback when Ashtakavarga data is unavailable."""

    def test_transit_multiplier_one_when_no_data(self) -> None:
        """When no AV data, transit multiplier defaults to 1.0."""
        from jrs.temporal.timeline_service import DynamicTemporalService

        svc = DynamicTemporalService()
        result = svc.compute_dynamic_strength(
            static_strength=0.8,
            target_timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=10.0,
            yoga_planets=["JUPITER"],
            transit_houses=None,  # No transit data
            ashtakavarga_scores=None,  # No AV data
            natal_moon_house=1,
        )
        # Transit multiplier should be 1.0 (inactive)
        assert result.transit_multiplier == 1.0

    def test_transit_multiplier_active_with_data(self) -> None:
        """When AV data provided, transit multiplier is computed."""
        from jrs.temporal.timeline_service import DynamicTemporalService

        svc = DynamicTemporalService()
        result = svc.compute_dynamic_strength(
            static_strength=0.8,
            target_timestamp=datetime(2024, 1, 15, tzinfo=timezone.utc),
            moon_nakshatra="ASHWINI",
            moon_nakshatra_degree=10.0,
            yoga_planets=["JUPITER"],
            transit_houses={"JUPITER": 1},
            ashtakavarga_scores={"JUPITER": 5},  # High bindus
            natal_moon_house=1,
        )
        # Transit multiplier should be > 1.0 (bonus applied)
        assert result.transit_multiplier > 1.0

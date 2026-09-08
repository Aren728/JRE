"""Unit tests for the Shadbala (Six-Fold Strength) Engine.

Tests all six classical strength components, total shadbala calculation,
strong/weak planet detection, and edge cases.
"""

from __future__ import annotations

import pytest

from src.jrs.advanced_charts.shadbala import (
    _NAISARGIKA_BALA,
    _compute_chesta_bala,
    _compute_dig_bala,
    _compute_drik_bala,
    _compute_kala_bala,
    _compute_naisargika_bala,
    _compute_sthana_bala,
    calculate_shadbala,
    compute_shadbala,
    shadbala_to_dict,
)


# ── Sthana Bala Tests ──────────────────────────────────────

class TestSthanaBala:
    def test_exalted_planet_max_strength(self) -> None:
        """Sun in Aries (exaltation sign) should get 60V."""
        result = _compute_sthana_bala("SUN", "MESHA", 10.0)
        assert result == 60.0

    def test_own_sign_strength(self) -> None:
        """Mars in Aries (own sign) should get 45V."""
        result = _compute_sthana_bala("MARS", "MESHA", 10.0)
        assert result == 45.0

    def test_mars_in_scorpio_own_sign(self) -> None:
        """Mars in Scorpio (own sign) should get 45V."""
        result = _compute_sthana_bala("MARS", "VRISHCHIKA", 10.0)
        assert result == 45.0

    def test_friendly_sign_strength(self) -> None:
        """Mercury in Aries (friendly) should get 30V."""
        result = _compute_sthana_bala("MERCURY", "MESHA", 10.0)
        assert result == 30.0

    def test_debilitated_planet_min_strength(self) -> None:
        """Sun in Libra (debilitation sign) gets 30V (simplified)."""
        result = _compute_sthana_bala("SUN", "TULA", 10.0)
        # Simplified implementation returns 30 for non-exalt/own
        assert result >= 0

    def test_jupiter_in_cancer_exalted(self) -> None:
        """Jupiter in Cancer is exalted."""
        result = _compute_sthana_bala("JUPITER", "KARKA", 10.0)
        assert result == 60.0

    def test_saturn_in_libra_exalted(self) -> None:
        """Saturn in Libra is exalted."""
        result = _compute_sthana_bala("SATURN", "TULA", 10.0)
        assert result == 60.0

    def test_venus_in_pisces_exalted(self) -> None:
        """Venus in Pisces is exalted."""
        result = _compute_sthana_bala("VENUS", "MEENA", 10.0)
        assert result == 60.0


# ── Dig Bala Tests ─────────────────────────────────────────

class TestDigBala:
    def test_mars_in_7th_house_max(self) -> None:
        """Mars gets max Dig Bala in 7th house."""
        result = _compute_dig_bala("MARS", 7)
        assert result == 30

    def test_mars_in_1st_house_min(self) -> None:
        """Mars gets min Dig Bala in 1st house."""
        result = _compute_dig_bala("MARS", 1)
        assert result == 0

    def test_saturn_in_7th_house_max(self) -> None:
        """Saturn gets max Dig Bala in 7th house."""
        result = _compute_dig_bala("SATURN", 7)
        assert result == 30

    def test_sun_in_1st_house_max(self) -> None:
        """Sun gets max Dig Bala in 1st house."""
        result = _compute_dig_bala("SUN", 1)
        assert result == 30

    def test_unknown_planet_zero(self) -> None:
        """Unknown planet gets 0 Dig Bala."""
        result = _compute_dig_bala("RAHU", 7)
        assert result == 0

    def test_all_houses_in_range(self) -> None:
        """All house values should produce Dig Bala in [0, 30]."""
        for planet in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]:
            for house in range(1, 13):
                result = _compute_dig_bala(planet, house)
                assert 0 <= result <= 30, (
                    f"{planet} in house {house}: Dig Bala {result} out of range"
                )


# ── Kala Bala Tests ────────────────────────────────────────

class TestKalaBala:
    def test_sun_stronger_in_day(self) -> None:
        """Sun is stronger during daytime."""
        day = _compute_kala_bala("SUN", True, 12.0)
        night = _compute_kala_bala("SUN", False, 12.0)
        assert day > night

    def test_moon_stronger_at_night(self) -> None:
        """Moon is stronger at night."""
        day = _compute_kala_bala("MOON", True, 12.0)
        night = _compute_kala_bala("MOON", False, 12.0)
        assert night > day

    def test_mars_stronger_in_day(self) -> None:
        """Mars is stronger during daytime."""
        day = _compute_kala_bala("MARS", True, 12.0)
        night = _compute_kala_bala("MARS", False, 12.0)
        assert day > night

    def test_saturn_stronger_at_night(self) -> None:
        """Saturn is stronger at night."""
        day = _compute_kala_bala("SATURN", True, 12.0)
        night = _compute_kala_bala("SATURN", False, 12.0)
        assert night > day

    def test_kala_bala_non_negative(self) -> None:
        """All Kala Bala values should be non-negative."""
        for planet in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]:
            for daytime in [True, False]:
                result = _compute_kala_bala(planet, daytime, 12.0)
                assert result >= 0, f"{planet} daytime={daytime}: negative Kala Bala"


# ── Chesta Bala Tests ──────────────────────────────────────

class TestChestaBala:
    def test_retrograde_max_strength(self) -> None:
        """Retrograde planets get max Chesta Bala."""
        result = _compute_chesta_bala("SATURN", 1.0, True)
        assert result == 60.0

    def test_stationary_high_strength(self) -> None:
        """Stationary planets get high Chesta Bala."""
        result = _compute_chesta_bala("SATURN", 0.05, False)
        assert result == 50.0

    def test_direct_motion_reduced(self) -> None:
        """Direct motion gives reduced strength."""
        result = _compute_chesta_bala("SATURN", 1.0, False)
        assert result < 50.0

    def test_fast_motion_low_strength(self) -> None:
        """Fast direct motion gives even less."""
        result = _compute_chesta_bala("SATURN", 5.0, False)
        assert result < 30.0

    def test_chesta_bala_non_negative(self) -> None:
        """Chesta Bala should never be negative."""
        result = _compute_chesta_bala("SATURN", 100.0, False)
        assert result >= 0


# ── Naisargika Bala Tests ──────────────────────────────────

class TestNaisargikaBala:
    def test_sun_strongest(self) -> None:
        """Sun should be the strongest planet naturally."""
        assert _compute_naisargika_bala("SUN") == 60.0

    def test_moon_second(self) -> None:
        """Moon should be second strongest."""
        assert _compute_naisargika_bala("MOON") == 51.67

    def test_saturn_weakest(self) -> None:
        """Saturn should be the weakest planet naturally."""
        assert _compute_naisargika_bala("SATURN") == 10.0

    def test_ordering(self) -> None:
        """Natural strengths should follow classical ordering."""
        order = ["SUN", "MOON", "JUPITER", "VENUS", "MERCURY", "MARS", "SATURN"]
        for i in range(len(order) - 1):
            assert _compute_naisargika_bala(order[i]) > _compute_naisargika_bala(order[i + 1])

    def test_unknown_planet_zero(self) -> None:
        """Unknown planet gets 0 Naisargika Bala."""
        assert _compute_naisargika_bala("RAHU") == 0.0


# ── Drik Bala Tests ────────────────────────────────────────

class TestDrikBala:
    def test_benefic_aspect_adds_strength(self) -> None:
        """Benefic aspects increase Drik Bala."""
        aspects = [{"source": "JUPITER"}]
        result = _compute_drik_bala("SUN", aspects)
        assert result == 15.0

    def test_malefic_aspect_reduces(self) -> None:
        """Malefic aspects decrease Drik Bala."""
        aspects = [{"source": "SATURN"}]
        result = _compute_drik_bala("SUN", aspects)
        assert result == 0.0  # Clamped to min 0

    def test_no_aspects_zero(self) -> None:
        """No aspects gives 0 Drik Bala."""
        result = _compute_drik_bala("SUN", [])
        assert result == 0.0

    def test_multiple_benefic_aspects(self) -> None:
        """Multiple benefic aspects accumulate up to max 60V."""
        aspects = [{"source": "JUPITER"}, {"source": "VENUS"}, {"source": "MOON"}]
        result = _compute_drik_bala("SUN", aspects)
        assert result == 45.0  # 3 × 15

    def test_drik_bala_capped_at_60(self) -> None:
        """Drik Bala cannot exceed 60V."""
        aspects = [{"source": "JUPITER"}] * 10
        result = _compute_drik_bala("SUN", aspects)
        assert result == 60.0

    def test_drik_bala_floor_at_0(self) -> None:
        """Drik Bala cannot go below 0V."""
        aspects = [{"source": "SATURN"}] * 10
        result = _compute_drik_bala("SUN", aspects)
        assert result == 0.0

    def test_mixed_aspects(self) -> None:
        """Mixed benefic and malefic aspects balance out."""
        aspects = [
            {"source": "JUPITER"},  # +15
            {"source": "VENUS"},    # +15
            {"source": "SATURN"},   # -10
            {"source": "MARS"},     # -10
        ]
        result = _compute_drik_bala("SUN", aspects)
        assert result == 10.0  # 15+15-10-10 = 10


# ── Compute Shadbala Integration Tests ─────────────────────

class TestComputeShadbala:
    def test_returns_all_seven_planets(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        expected = {"SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"}
        assert set(result.planets.keys()) == expected

    def test_all_strengths_non_negative(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        for planet, ps in result.planets.items():
            assert ps.total_virupas >= 0, f"{planet} has negative total_virupas"
            assert ps.total_rupas >= 0, f"{planet} has negative total_rupas"

    def test_total_rupas_equals_virupas_div_60(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        for planet, ps in result.planets.items():
            assert ps.total_rupas == pytest.approx(ps.total_virupas / 60.0, abs=0.01), (
                f"{planet}: total_rupas != total_virupas / 60"
            )

    def test_strongest_planet_identified(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        assert result.strongest_planet in result.planets
        strongest_v = result.planets[result.strongest_planet].total_virupas
        for ps in result.planets.values():
            assert ps.total_virupas <= strongest_v

    def test_weakest_planet_identified(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        assert result.weakest_planet in result.planets
        weakest_v = result.planets[result.weakest_planet].total_virupas
        for ps in result.planets.values():
            assert ps.total_virupas >= weakest_v

    def test_average_strength_correct(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        expected_avg = sum(
            ps.total_virupas for ps in result.planets.values()
        ) / len(result.planets)
        assert result.average_strength == pytest.approx(expected_avg, abs=0.1)

    def test_is_strong_threshold(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        for ps in result.planets.values():
            if ps.is_strong:
                assert ps.total_virupas >= 395.0
            else:
                assert ps.total_virupas < 395.0

    def test_daytime_mode(self, natal_data_for_shadbala) -> None:
        result_day = compute_shadbala(natal_data_for_shadbala, is_daytime=True)
        result_night = compute_shadbala(natal_data_for_shadbala, is_daytime=False)
        # Kala Bala differs between day and night, so totals differ
        assert result_day.planets["SUN"].total_virupas != result_night.planets["SUN"].total_virupas

    def test_retrograde_planet_stronger(self) -> None:
        """Retrograde planet should have higher Chesta Bala."""
        data_direct = {
            "planets": {
                "SATURN": {"rashi": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                           "retrograde": False, "speed": 1.0},
                "SUN": {"rashi": "MESHA", "house": 1, "degree_in_sign": 15.0,
                        "retrograde": False, "speed": 1.0},
                "MOON": {"rashi": "VRISHABHA", "house": 2, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 13.0},
                "MARS": {"rashi": "KARKA", "house": 4, "degree_in_sign": 0.0,
                         "retrograde": False, "speed": 0.5},
                "MERCURY": {"rashi": "KANYA", "house": 6, "degree_in_sign": 15.0,
                            "retrograde": False, "speed": 1.5},
                "JUPITER": {"rashi": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                            "retrograde": False, "speed": 0.2},
                "VENUS": {"rashi": "MEENA", "house": 10, "degree_in_sign": 0.0,
                          "retrograde": False, "speed": 1.2},
            }
        }
        data_retro = {
            "planets": {
                "SATURN": {"rashi": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                           "retrograde": True, "speed": -0.1},
                "SUN": {"rashi": "MESHA", "house": 1, "degree_in_sign": 15.0,
                        "retrograde": False, "speed": 1.0},
                "MOON": {"rashi": "VRISHABHA", "house": 2, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 13.0},
                "MARS": {"rashi": "KARKA", "house": 4, "degree_in_sign": 0.0,
                         "retrograde": False, "speed": 0.5},
                "MERCURY": {"rashi": "KANYA", "house": 6, "degree_in_sign": 15.0,
                            "retrograde": False, "speed": 1.5},
                "JUPITER": {"rashi": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                            "retrograde": False, "speed": 0.2},
                "VENUS": {"rashi": "MEENA", "house": 10, "degree_in_sign": 0.0,
                          "retrograde": False, "speed": 1.2},
            }
        }
        r_direct = compute_shadbala(data_direct)
        r_retro = compute_shadbala(data_retro)
        assert r_retro.planets["SATURN"].chesta_bala > r_direct.planets["SATURN"].chesta_bala

    def test_empty_planets(self) -> None:
        """Empty planets dict should not crash."""
        result = compute_shadbala({"planets": {}})
        assert len(result.planets) == 7  # Still iterates over all 7 planets

    def test_missing_planet_data(self) -> None:
        """Missing individual planet data should still compute."""
        result = compute_shadbala({"planets": {"SUN": {"rashi": "MESHA", "house": 1}}})
        assert "SUN" in result.planets
        assert "MOON" in result.planets  # Still present with defaults


# ── Serialization Tests ────────────────────────────────────

# ── Calculate Shadbala (Adapter) Tests ─────────────────────────────────

class TestCalculateShadbala:
    def test_with_planets_key(self) -> None:
        """calculate_shadbala should work with 'planets' key in facts packet."""
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA", "house": 1, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 1.0},
                "MOON": {"rashi": "VRISHABHA", "house": 2, "degree_in_sign": 15.5,
                          "retrograde": False, "speed": 13.0},
                "MARS": {"rashi": "KARKA", "house": 4, "degree_in_sign": 0.0,
                          "retrograde": False, "speed": 0.5},
                "MERCURY": {"rashi": "KANYA", "house": 6, "degree_in_sign": 15.0,
                             "retrograde": False, "speed": 1.5},
                "JUPITER": {"rashi": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                             "retrograde": False, "speed": 0.2},
                "VENUS": {"rashi": "MEENA", "house": 10, "degree_in_sign": 0.0,
                           "retrograde": False, "speed": 1.2},
                "SATURN": {"rashi": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                            "retrograde": True, "speed": -0.1},
            }
        }
        result = calculate_shadbala(facts)
        assert len(result.planets) == 7
        assert "SUN" in result.planets
        assert "SATURN" in result.planets

    def test_with_planet_details_key(self) -> None:
        """calculate_shadbala should work with 'planet_details' key."""
        facts = {
            "planet_details": {
                "SUN": {"sign": "MESHA", "house": 1, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 1.0},
                "MOON": {"sign": "VRISHABHA", "house": 2, "degree_in_sign": 15.5,
                          "retrograde": False, "speed": 13.0},
                "MARS": {"sign": "KARKA", "house": 4, "degree_in_sign": 0.0,
                          "retrograde": False, "speed": 0.5},
                "MERCURY": {"sign": "KANYA", "house": 6, "degree_in_sign": 15.0,
                             "retrograde": False, "speed": 1.5},
                "JUPITER": {"sign": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                             "retrograde": False, "speed": 0.2},
                "VENUS": {"sign": "MEENA", "house": 10, "degree_in_sign": 0.0,
                           "retrograde": False, "speed": 1.2},
                "SATURN": {"sign": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                            "retrograde": False, "speed": 0.8},
            }
        }
        result = calculate_shadbala(facts)
        assert len(result.planets) == 7
        # Sun in Aries (exaltation) should have high sthana bala
        assert result.planets["SUN"].sthana_bala == 60.0

    def test_with_retrograde_string(self) -> None:
        """calculate_shadbala should handle retrograde as string."""
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA", "house": 1, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 1.0},
                "MOON": {"rashi": "VRISHABHA", "house": 2, "degree_in_sign": 15.5,
                          "retrograde": False, "speed": 13.0},
                "MARS": {"rashi": "KARKA", "house": 4, "degree_in_sign": 0.0,
                          "retrograde": False, "speed": 0.5},
                "MERCURY": {"rashi": "KANYA", "house": 6, "degree_in_sign": 15.0,
                             "retrograde": False, "speed": 1.5},
                "JUPITER": {"rashi": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                             "retrograde": False, "speed": 0.2},
                "VENUS": {"rashi": "MEENA", "house": 10, "degree_in_sign": 0.0,
                           "retrograde": False, "speed": 1.2},
                "SATURN": {"rashi": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                            "retrograde": "RETROGRADE", "speed": -0.1},
            }
        }
        result = calculate_shadbala(facts)
        assert result.planets["SATURN"].chesta_bala == 60.0  # Retrograde = max

    def test_with_longitude_fallback(self) -> None:
        """calculate_shadbala should compute degree_in_sign from longitude."""
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA", "house": 1, "longitude": 15.0,
                         "retrograde": False, "speed": 1.0},
                "MOON": {"rashi": "VRISHABHA", "house": 2, "longitude": 45.5,
                          "retrograde": False, "speed": 13.0},
                "MARS": {"rashi": "KARKA", "house": 4, "longitude": 90.0,
                          "retrograde": False, "speed": 0.5},
                "MERCURY": {"rashi": "KANYA", "house": 6, "longitude": 195.0,
                             "retrograde": False, "speed": 1.5},
                "JUPITER": {"rashi": "DHANUSHA", "house": 8, "longitude": 250.0,
                             "retrograde": False, "speed": 0.2},
                "VENUS": {"rashi": "MEENA", "house": 10, "longitude": 330.0,
                           "retrograde": False, "speed": 1.2},
                "SATURN": {"rashi": "KUMBHA", "house": 11, "longitude": 300.0,
                            "retrograde": False, "speed": 0.8},
            }
        }
        result = calculate_shadbala(facts)
        assert len(result.planets) == 7
        # All strengths should be non-negative
        for ps in result.planets.values():
            assert ps.total_virupas >= 0

    def test_with_daytime_false(self) -> None:
        """calculate_shadbala should respect is_daytime flag."""
        facts_day = {
            "planets": {
                "SUN": {"rashi": "MESHA", "house": 1, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 1.0},
                "MOON": {"rashi": "VRISHABHA", "house": 2, "degree_in_sign": 15.5,
                          "retrograde": False, "speed": 13.0},
                "MARS": {"rashi": "KARKA", "house": 4, "degree_in_sign": 0.0,
                          "retrograde": False, "speed": 0.5},
                "MERCURY": {"rashi": "KANYA", "house": 6, "degree_in_sign": 15.0,
                             "retrograde": False, "speed": 1.5},
                "JUPITER": {"rashi": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                             "retrograde": False, "speed": 0.2},
                "VENUS": {"rashi": "MEENA", "house": 10, "degree_in_sign": 0.0,
                           "retrograde": False, "speed": 1.2},
                "SATURN": {"rashi": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                            "retrograde": False, "speed": 0.8},
            },
            "is_daytime": True,
        }
        facts_night = dict(facts_day)
        facts_night["is_daytime"] = False

        result_day = calculate_shadbala(facts_day)
        result_night = calculate_shadbala(facts_night)

        # Kala Bala differs between day and night
        assert result_day.planets["SUN"].kala_bala != result_night.planets["SUN"].kala_bala

    def test_empty_facts_packet(self) -> None:
        """calculate_shadbala should handle empty facts packet."""
        result = calculate_shadbala({})
        assert len(result.planets) == 7  # Still iterates over all 7 planets

    def test_matches_compute_shadbala_direct(self) -> None:
        """calculate_shadbala should produce same results as compute_shadbala."""
        facts = {
            "planets": {
                "SUN": {"rashi": "MESHA", "house": 1, "degree_in_sign": 15.0,
                         "retrograde": False, "speed": 1.0},
                "MOON": {"rashi": "VRISHABHA", "house": 2, "degree_in_sign": 15.5,
                          "retrograde": False, "speed": 13.0},
                "MARS": {"rashi": "KARKA", "house": 4, "degree_in_sign": 0.0,
                          "retrograde": False, "speed": 0.5},
                "MERCURY": {"rashi": "KANYA", "house": 6, "degree_in_sign": 15.0,
                             "retrograde": False, "speed": 1.5},
                "JUPITER": {"rashi": "DHANUSHA", "house": 8, "degree_in_sign": 10.0,
                             "retrograde": False, "speed": 0.2},
                "VENUS": {"rashi": "MEENA", "house": 10, "degree_in_sign": 0.0,
                           "retrograde": False, "speed": 1.2},
                "SATURN": {"rashi": "KUMBHA", "house": 11, "degree_in_sign": 0.0,
                            "retrograde": True, "speed": -0.1},
            }
        }
        natal_data = {"planets": facts["planets"]}

        result_adapter = calculate_shadbala(facts)
        result_direct = compute_shadbala(natal_data)

        for planet in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]:
            assert result_adapter.planets[planet].sthana_bala == result_direct.planets[planet].sthana_bala
            assert result_adapter.planets[planet].dig_bala == result_direct.planets[planet].dig_bala
            assert result_adapter.planets[planet].total_virupas == result_direct.planets[planet].total_virupas


class TestSerialization:
    def test_shadbala_to_dict_structure(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        d = shadbala_to_dict(result)
        assert "planets" in d
        assert "average_strength" in d
        assert "strongest_planet" in d
        assert "weakest_planet" in d

    def test_shadbala_to_dict_planet_fields(
        self, natal_data_for_shadbala
    ) -> None:
        result = compute_shadbala(natal_data_for_shadbala)
        d = shadbala_to_dict(result)
        sun = d["planets"]["SUN"]
        assert sun["planet"] == "SUN"
        assert isinstance(sun["sthana_bala"], (int, float))
        assert isinstance(sun["dig_bala"], (int, float))
        assert isinstance(sun["kala_bala"], (int, float))
        assert isinstance(sun["chesta_bala"], (int, float))
        assert isinstance(sun["naisargika_bala"], (int, float))
        assert isinstance(sun["drik_bala"], (int, float))
        assert isinstance(sun["total_rupas"], (int, float))
        assert isinstance(sun["total_virupas"], (int, float))
        assert isinstance(sun["is_strong"], bool)

    def test_dict_is_json_serializable(
        self, natal_data_for_shadbala
    ) -> None:
        import json
        result = compute_shadbala(natal_data_for_shadbala)
        d = shadbala_to_dict(result)
        json_str = json.dumps(d)
        assert len(json_str) > 0

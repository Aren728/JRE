"""Unit tests for the Ashtakavarga Engine.

Tests Bhinna Ashtakavarga (BAV), Sarva Ashtakavarga (SAV),
bindu assignment rules, and edge cases.
"""

from __future__ import annotations

import pytest

from src.jrs.advanced_charts.ashtakavarga import (
    _BINDU_RULES,
    AshtakavargaResult,
    BAVResult,
    ashtakavarga_to_dict,
    calculate_ashtakavarga,
    compute_ashtakavarga,
)


# ── Bindu Rules Tests ──────────────────────────────────────

class TestBinduRules:
    def test_all_seven_planets_defined(self) -> None:
        """All 7 classical planets should have bindu rules."""
        expected = {"SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"}
        assert set(_BINDU_RULES.keys()) == expected

    def test_rules_are_lists_of_ints(self) -> None:
        """Each rule should be a list of integers."""
        for planet, houses in _BINDU_RULES.items():
            assert isinstance(houses, list)
            for h in houses:
                assert isinstance(h, int)

    def test_rules_only_valid_houses(self) -> None:
        """All house numbers should be between 1 and 12."""
        for planet, houses in _BINDU_RULES.items():
            for h in houses:
                assert 1 <= h <= 12, f"{planet} has invalid house {h}"

    def test_all_houses_valid_range(self) -> None:
        """All house numbers should be between 1 and 12."""
        for planet, houses in _BINDU_RULES.items():
            for h in houses:
                assert 1 <= h <= 12, (
                    f"{planet} assigns bindu to house {h} outside 1-12"
                )

    def test_sun_has_eight_houses(self) -> None:
        """Sun assigns bindus to 8 houses."""
        assert len(_BINDU_RULES["SUN"]) == 8

    def test_venus_has_nine_houses(self) -> None:
        """Venus assigns bindus to 9 houses (most generous)."""
        assert len(_BINDU_RULES["VENUS"]) == 9


# ── BAV Calculation Tests ──────────────────────────────────

class TestBAVCalculation:
    def test_bav_returns_correct_planet(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        for pname in result.bav:
            assert result.bav[pname].planet == pname

    def test_bav_has_12_houses(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        for bav in result.bav.values():
            assert len(bav.bindus) == 12

    def test_bav_bindus_non_negative(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        for pname, bav in result.bav.items():
            for house, bindu in bav.bindus.items():
                assert bindu >= 0, f"{pname}: house {house} has negative bindu {bindu}"

    def test_bav_total_bindus_correct(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        for pname, bav in result.bav.items():
            assert bav.total_bindus == sum(bav.bindus.values())

    def test_nodes_excluded(self, natal_data_for_ashtakavarga) -> None:
        """RAHU and KETU should not appear in BAV results."""
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        assert "RAHU" not in result.bav
        assert "KETU" not in result.bav

    def test_seven_planets_in_bav(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        expected = {"SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"}
        assert set(result.bav.keys()) == expected


# ── SAV Calculation Tests ──────────────────────────────────

class TestSAVCalculation:
    def test_sav_has_12_houses(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        assert len(result.sav) == 12

    def test_sav_non_negative(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        for house, bindu in result.sav.items():
            assert bindu >= 0, f"House {house} has negative SAV {bindu}"

    def test_sav_is_sum_of_bavs(self, natal_data_for_ashtakavarga) -> None:
        """SAV for each house should be the sum of all BAVs for that house."""
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        for house in range(1, 13):
            expected_sav = sum(
                result.bav[p].bindus.get(house, 0) for p in result.bav
            )
            assert result.sav[house] == expected_sav, (
                f"House {house}: SAV {result.sav[house]} != sum of BAVs {expected_sav}"
            )

    def test_max_sav_possible(self) -> None:
        """Maximum SAV per house is 7 (one bindu from each of 7 planets)."""
        for planet, houses in _BINDU_RULES.items():
            # Each planet can contribute at most 1 bindu per house
            for h in houses:
                assert h >= 1 and h <= 12

    def test_strongest_house_identified(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        assert result.strongest_house in range(1, 13)
        max_sav = max(result.sav.values())
        assert result.sav[result.strongest_house] == max_sav

    def test_weakest_house_identified(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        assert result.weakest_house in range(1, 13)
        min_sav = min(result.sav.values())
        assert result.sav[result.weakest_house] == min_sav

    def test_average_sav_correct(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        expected_avg = sum(result.sav.values()) / len(result.sav)
        assert result.average_sav == pytest.approx(expected_avg, abs=0.01)


# ── Edge Cases ─────────────────────────────────────────────

class TestEdgeCases:
    def test_all_planets_in_same_house(self) -> None:
        """All planets in house 1 should still produce valid BAV/SAV."""
        data = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 1},
                "MARS": {"house": 1},
                "MERCURY": {"house": 1},
                "JUPITER": {"house": 1},
                "VENUS": {"house": 1},
                "SATURN": {"house": 1},
            }
        }
        result = compute_ashtakavarga(data)
        assert len(result.bav) == 7
        assert len(result.sav) == 12

    def test_planets_spread_evenly(self) -> None:
        """Each planet in a different house 1-7."""
        data = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 2},
                "MARS": {"house": 3},
                "MERCURY": {"house": 4},
                "JUPITER": {"house": 5},
                "VENUS": {"house": 6},
                "SATURN": {"house": 7},
            }
        }
        result = compute_ashtakavarga(data)
        assert len(result.bav) == 7

    def test_empty_planets(self) -> None:
        """Empty planets dict should not crash."""
        result = compute_ashtakavarga({"planets": {}})
        assert len(result.bav) == 0
        assert len(result.sav) == 12  # All zeros

    def test_only_nodes_in_chart(self) -> None:
        """If only nodes are present, BAV should be empty."""
        data = {
            "planets": {
                "RAHU": {"house": 5},
                "KETU": {"house": 11},
            }
        }
        result = compute_ashtakavarga(data)
        assert len(result.bav) == 0

    def test_invalid_house_ignored(self) -> None:
        """Planets with invalid house numbers should be excluded."""
        data = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 0},  # Invalid
                "MARS": {"house": 13},  # Invalid
            }
        }
        result = compute_ashtakavarga(data)
        assert "SUN" in result.bav
        assert "MOON" not in result.bav
        assert "MARS" not in result.bav


# ── Serialization Tests ────────────────────────────────────

class TestSerialization:
    def test_ashtakavarga_to_dict_structure(
        self, natal_data_for_ashtakavarga
    ) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        d = ashtakavarga_to_dict(result)
        assert "bav" in d
        assert "sav" in d
        assert "strongest_house" in d
        assert "weakest_house" in d
        assert "average_sav" in d

    def test_bav_dict_fields(self, natal_data_for_ashtakavarga) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        d = ashtakavarga_to_dict(result)
        sun_bav = d["bav"]["SUN"]
        assert sun_bav["planet"] == "SUN"
        assert isinstance(sun_bav["bindus"], dict)
        assert isinstance(sun_bav["total_bindus"], int)
        # Bindus keys should be strings (JSON serialization)
        for key in sun_bav["bindus"]:
            assert isinstance(key, str)

    def test_sav_dict_keys_are_strings(
        self, natal_data_for_ashtakavarga
    ) -> None:
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        d = ashtakavarga_to_dict(result)
        for key in d["sav"]:
            assert isinstance(key, str)

    def test_dict_is_json_serializable(
        self, natal_data_for_ashtakavarga
    ) -> None:
        import json
        result = compute_ashtakavarga(natal_data_for_ashtakavarga)
        d = ashtakavarga_to_dict(result)
        json_str = json.dumps(d)
        assert len(json_str) > 0


# ── Dataclass Tests ────────────────────────────────────────

# ── Calculate Ashtakavarga (Adapter) Tests ───────────────────────────────

class TestCalculateAshtakavarga:
    def test_with_planets_key(self) -> None:
        """calculate_ashtakavarga should work with 'planets' key in facts packet."""
        facts = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 2},
                "MARS": {"house": 4},
                "MERCURY": {"house": 6},
                "JUPITER": {"house": 8},
                "VENUS": {"house": 10},
                "SATURN": {"house": 11},
            }
        }
        result = calculate_ashtakavarga(facts)
        assert len(result.bav) == 7
        assert len(result.sav) == 12
        assert "SUN" in result.bav
        assert "SATURN" in result.bav

    def test_with_planet_details_key(self) -> None:
        """calculate_ashtakavarga should work with 'planet_details' key."""
        facts = {
            "planet_details": {
                "SUN": {"house": 1},
                "MOON": {"house": 2},
                "MARS": {"house": 4},
                "MERCURY": {"house": 6},
                "JUPITER": {"house": 8},
                "VENUS": {"house": 10},
                "SATURN": {"house": 11},
            }
        }
        result = calculate_ashtakavarga(facts)
        assert len(result.bav) == 7

    def test_nodes_excluded(self) -> None:
        """calculate_ashtakavarga should exclude RAHU and KETU."""
        facts = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 2},
                "MARS": {"house": 4},
                "MERCURY": {"house": 6},
                "JUPITER": {"house": 8},
                "VENUS": {"house": 10},
                "SATURN": {"house": 11},
                "RAHU": {"house": 5},
                "KETU": {"house": 11},
            }
        }
        result = calculate_ashtakavarga(facts)
        assert "RAHU" not in result.bav
        assert "KETU" not in result.bav

    def test_invalid_house_excluded(self) -> None:
        """Planets with invalid house numbers should be excluded."""
        facts = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 0},  # Invalid
                "MARS": {"house": 13},  # Invalid
            }
        }
        result = calculate_ashtakavarga(facts)
        assert "SUN" in result.bav
        assert "MOON" not in result.bav
        assert "MARS" not in result.bav

    def test_matches_compute_ashtakavarga_direct(self) -> None:
        """calculate_ashtakavarga should produce same results as compute_ashtakavarga."""
        facts = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 2},
                "MARS": {"house": 4},
                "MERCURY": {"house": 6},
                "JUPITER": {"house": 8},
                "VENUS": {"house": 10},
                "SATURN": {"house": 11},
            }
        }
        natal_data = {"planets": facts["planets"]}

        result_adapter = calculate_ashtakavarga(facts)
        result_direct = compute_ashtakavarga(natal_data)

        for planet in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]:
            assert result_adapter.bav[planet].bindus == result_direct.bav[planet].bindus
            assert result_adapter.bav[planet].total_bindus == result_direct.bav[planet].total_bindus

        assert result_adapter.sav == result_direct.sav

    def test_empty_facts_packet(self) -> None:
        """calculate_ashtakavarga should handle empty facts packet."""
        result = calculate_ashtakavarga({})
        assert len(result.bav) == 0
        assert len(result.sav) == 12  # All zeros

    def test_sav_is_sum_of_bavs(self) -> None:
        """SAV should be the sum of all BAVs for each house."""
        facts = {
            "planets": {
                "SUN": {"house": 1},
                "MOON": {"house": 5},
                "MARS": {"house": 9},
                "MERCURY": {"house": 3},
                "JUPITER": {"house": 7},
                "VENUS": {"house": 11},
                "SATURN": {"house": 2},
            }
        }
        result = calculate_ashtakavarga(facts)
        for house in range(1, 13):
            expected_sav = sum(
                result.bav[p].bindus.get(house, 0) for p in result.bav
            )
            assert result.sav[house] == expected_sav


class TestDataclasses:
    def test_bav_result_creation(self) -> None:
        bav = BAVResult(
            planet="SUN",
            bindus={h: 1 for h in range(1, 13)},
            total_bindus=12,
        )
        assert bav.planet == "SUN"
        assert bav.total_bindus == 12

    def test_ashtakavarga_result_creation(self) -> None:
        bav = BAVResult(planet="SUN", bindus={h: 1 for h in range(1, 13)}, total_bindus=12)
        sav = {h: 7 for h in range(1, 13)}
        result = AshtakavargaResult(
            bav={"SUN": bav},
            sav=sav,
            strongest_house=1,
            weakest_house=1,
            average_sav=7.0,
        )
        assert result.strongest_house == 1
        assert result.weakest_house == 1
        assert result.average_sav == 7.0

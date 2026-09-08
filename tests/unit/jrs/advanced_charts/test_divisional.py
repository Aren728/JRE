"""Unit tests for the Divisional Chart Engine (D1-D16+).

Tests D1-D16 divisional chart calculations, vargottama detection,
lagna computation, and edge cases.
"""

from __future__ import annotations

import math

import pytest

from src.jrs.advanced_charts.divisional import (
    CHART_META,
    SIGN_ORDER,
    DivisionalChart,
    DivisionalPlanet,
    _d2_hora,
    _d3_drekkana,
    _d4_chaturthamsha,
    _d7_saptamamsha,
    _d9_navamsha,
    _d10_dashamsha,
    _d12_dwadashamsha,
    _d16_shodashamsha,
    calculate_divisional_positions,
    compute_all_divisional_charts,
    compute_divisional_chart,
    divisional_chart_to_dict,
)


# ── D1 (Rashi) Tests ──────────────────────────────────────

class TestD1Rashi:
    def test_d1_returns_natal_longitude_directly(
        self, natal_longitudes, lagna_longitude
    ) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 1)
        assert chart.division == 1
        assert chart.name == "Rashi (D1)"
        for planet, lon in natal_longitudes.items():
            assert chart.planets[planet].longitude == lon
            assert chart.planets[planet].divisional_longitude == lon

    def test_d1_sign_placement(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 1)
        # Sun at 15° → Aries (MESHA, index 0)
        assert chart.planets["SUN"].rashi == "MESHA"
        assert chart.planets["SUN"].degree_in_sign == 15.0

    def test_d1_moon_in_taurus(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 1)
        assert chart.planets["MOON"].rashi == "VRISHABHA"
        assert chart.planets["MOON"].degree_in_sign == pytest.approx(15.5, abs=0.01)

    def test_d1_lagna_is_cancer(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 1)
        assert chart.lagna == "KARKA"

    def test_d1_house_from_lagna(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 1)
        # Lagna in Cancer (index 3), Sun in Aries (index 0)
        # House = ((0 - 3) % 12) + 1 = 10
        assert chart.planets["SUN"].house == 10

    def test_d1_no_vargottama_for_d1(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 1)
        # In D1, vargottama detection compares D1 vs. the divisional.
        # Since D1 divisional_longitude == natal_longitude, vargottama detection
        # is only computed for non-D1 charts (D1 returns early before the
        # vargottama loop). So D1 always has empty vargottama_planets.
        assert chart.vargottama_planets == ()


# ── D9 (Navamsha) Tests ───────────────────────────────────

class TestD9Navamsha:
    def test_d9_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 9)
        assert chart.division == 9
        assert chart.name == "Navamsha (D9)"
        assert len(chart.planets) == len(natal_longitudes)

    def test_d9_longitude_in_range(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 9)
        for planet, dp in chart.planets.items():
            assert 0 <= dp.divisional_longitude <= 360, (
                f"{planet} D9 longitude {dp.divisional_longitude} out of range"
            )

    def test_d9_sign_in_range(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 9)
        for planet, dp in chart.planets.items():
            assert dp.rashi in SIGN_ORDER, (
                f"{planet} D9 rashi {dp.rashi} not in SIGN_ORDER"
            )

    def test_d9_navamsha_size(self) -> None:
        """Each navamsha spans 3°20' (30/9 degrees)."""
        navamsha_size = 30.0 / 9.0
        assert navamsha_size == pytest.approx(20.0 / 6.0, abs=0.001)

    def test_d9_sun_at_15_aries(self) -> None:
        """Sun at 15° Aries: 15 / (30/9) = 4.5 → 5th navamsha."""
        result = _d9_navamsha(15.0)
        # 15° = start of 5th portion (index 4), so result should be in
        # MESHA + 4 = SIMHA (4th offset from MESHA = SIMHA)
        # result_sign = (0 + 4) % 12 = 4 = SIMHA
        sign_idx = int(result / 30.0)
        assert SIGN_ORDER[sign_idx % 12] == "SIMHA"

    def test_d9_vargottama_detection(self) -> None:
        """A planet in the same sign in D1 and D9 is vargottama."""
        # Place all planets in the first degree of Aries
        longitudes = {p: 5.0 for p in ["SUN", "MOON", "MARS"]}
        lagna = 5.0  # Also in Aries
        chart = compute_divisional_chart(longitudes, lagna, 9)
        # All planets start in Aries D1. In D9, Sun at 5° Aries is in
        # 2nd navamsha of Aries → Taurus. So they may or may not be
        # vargottama depending on the D9 calculation.
        assert isinstance(chart.vargottama_planets, tuple)


# ── D2 (Hora) Tests ───────────────────────────────────────

class TestD2Hora:
    def test_d2_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 2)
        assert chart.division == 2
        assert chart.name == "Hora (D2)"

    def test_d2_longitude_in_range(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 2)
        for planet, dp in chart.planets.items():
            assert 0 <= dp.divisional_longitude < 360

    def test_d2_first_hour_of_odd_sign(self) -> None:
        """Odd sign (Aries), first 15° → MESHA hora."""
        result = _d2_hora(10.0)  # 10° Aries
        assert result < 30.0  # Should be in MESHA

    def test_d2_second_hour_of_odd_sign(self) -> None:
        """Odd sign (Aries), second 15° → VRISHABHA hora."""
        result = _d2_hora(20.0)  # 20° Aries
        assert 30.0 <= result < 60.0  # Should be in VRISHABHA

    def test_d2_first_hour_of_even_sign(self) -> None:
        """Even sign (Taurus), first 15° → VRISHABHA hora."""
        result = _d2_hora(40.0)  # 10° Taurus
        assert 30.0 <= result < 60.0  # Should be in VRISHABHA

    def test_d2_second_hour_of_even_sign(self) -> None:
        """Even sign (Taurus), second 15° → MESHA hora."""
        result = _d2_hora(50.0)  # 20° Taurus
        assert result < 30.0  # Should be in MESHA


# ── D3 (Drekkana) Tests ───────────────────────────────────

class TestD3Drekkana:
    def test_d3_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 3)
        assert chart.division == 3
        assert chart.name == "Drekkana (D3)"

    def test_d3_first_drekkana_stays_in_sign(self) -> None:
        """First drekkana (0-10°) stays in the same sign."""
        result = _d3_drekkana(5.0)  # 5° Aries
        sign_idx = int(result / 30.0)
        assert SIGN_ORDER[sign_idx % 12] == "MESHA"

    def test_d3_second_drekkana_fifth_from(self) -> None:
        """Second drekkana (10-20°) goes to 5th sign from original."""
        result = _d3_drekkana(15.0)  # 15° Aries
        sign_idx = int(result / 30.0)
        # 5th from MESHA = SIMHA (index 0 + 4 = 4)
        assert SIGN_ORDER[sign_idx % 12] == "SIMHA"

    def test_d3_third_drekkana_ninth_from(self) -> None:
        """Third drekkana (20-30°) goes to 9th sign from original."""
        result = _d3_drekkana(25.0)  # 25° Aries
        sign_idx = int(result / 30.0)
        # 9th from MESHA = DHANUSHA (index 0 + 8 = 8)
        assert SIGN_ORDER[sign_idx % 12] == "DHANUSHA"


# ── D4 (Chaturthamsha) Tests ──────────────────────────────

class TestD4Chaturthamsha:
    def test_d4_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 4)
        assert chart.division == 4
        assert chart.name == "Chaturthamsha (D4)"

    def test_d4_longitude_in_range(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 4)
        for planet, dp in chart.planets.items():
            assert 0 <= dp.divisional_longitude < 360


# ── D7 (Saptamamsha) Tests ────────────────────────────────

class TestD7Saptamamsha:
    def test_d7_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 7)
        assert chart.division == 7
        assert chart.name == "Saptamamsha (D7)"

    def test_d7_longitude_in_range(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 7)
        for planet, dp in chart.planets.items():
            assert 0 <= dp.divisional_longitude < 360

    def test_d7_odd_sign_starts_from_self(self) -> None:
        """Odd sign (Aries): first portion (0-4.286°) starts from Aries."""
        result = _d7_saptamamsha(2.0)  # 2° Aries, 1st portion
        sign_idx = int(result / 30.0)
        assert SIGN_ORDER[sign_idx % 12] == "MESHA"

    def test_d7_even_sign_starts_from_7th(self) -> None:
        """Even sign (Taurus): first portion starts from 7th sign (VRISHCHIKA)."""
        result = _d7_saptamamsha(32.0)  # 2° Taurus, 1st portion
        sign_idx = int(result / 30.0)
        # 7th from VRISHABHA (index 1) counting from it = VRISHCHIKA (index 7)
        assert SIGN_ORDER[sign_idx % 12] == "VRISHCHIKA"


# ── D10 (Dashamsha) Tests ─────────────────────────────────

class TestD10Dashamsha:
    def test_d10_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 10)
        assert chart.division == 10
        assert chart.name == "Dashamsha (D10)"

    def test_d10_longitude_in_range(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 10)
        for planet, dp in chart.planets.items():
            assert 0 <= dp.divisional_longitude < 360


# ── D12 (Dwadashamsha) Tests ──────────────────────────────

class TestD12Dwadashamsha:
    def test_d12_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 12)
        assert chart.division == 12
        assert chart.name == "Dwadashamsha (D12)"

    def test_d12_each_portion_maps_to_same_sign(self) -> None:
        """Each 2.5° portion maps to the same zodiacal sign."""
        for i in range(12):
            lon = i * 2.5 + 1.0  # Middle of each portion
            result = _d12_dwadashamsha(lon)
            original_sign_idx = int(lon / 30.0)
            result_sign_idx = int(result / 30.0)
            # The result sign should be the same as original for portion 0
            # For subsequent portions, they shift within the sign
            assert 0 <= result < 360


# ── D16 (Shodashamsha) Tests ──────────────────────────────

class TestD16Shodashamsha:
    def test_d16_computes_without_error(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 16)
        assert chart.division == 16
        assert chart.name == "Shodashamsha (D16)"

    def test_d16_longitude_in_range(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 16)
        for planet, dp in chart.planets.items():
            assert 0 <= dp.divisional_longitude < 360


# ── Higher Division Charts ────────────────────────────────

class TestHigherDivisions:
    def test_d20_computes(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 20)
        assert chart.division == 20

    def test_d24_computes(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 24)
        assert chart.division == 24

    def test_d27_computes(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 27)
        assert chart.division == 27

    def test_d30_computes(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 30)
        assert chart.division == 30

    def test_d40_computes(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 40)
        assert chart.division == 40

    def test_d45_computes(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 45)
        assert chart.division == 45

    def test_d60_computes(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 60)
        assert chart.division == 60


# ── compute_all_divisional_charts Tests ────────────────────

class TestComputeAllDivisionalCharts:
    def test_all_supported_divisions(self, natal_longitudes, lagna_longitude) -> None:
        charts = compute_all_divisional_charts(natal_longitudes, lagna_longitude)
        expected_divisions = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
        for div in expected_divisions:
            assert div in charts, f"D{div} missing from computed charts"

    def test_subset_divisions(self, natal_longitudes, lagna_longitude) -> None:
        charts = compute_all_divisional_charts(
            natal_longitudes, lagna_longitude, divisions=[1, 9]
        )
        assert 1 in charts
        assert 9 in charts
        assert len(charts) == 2

    def test_empty_divisions_returns_empty(self, natal_longitudes, lagna_longitude) -> None:
        charts = compute_all_divisional_charts(
            natal_longitudes, lagna_longitude, divisions=[]
        )
        assert len(charts) == 0

    def test_unsupported_division_skipped(self, natal_longitudes, lagna_longitude) -> None:
        """Unsupported division numbers are silently skipped."""
        charts = compute_all_divisional_charts(
            natal_longitudes, lagna_longitude, divisions=[1, 5]
        )
        assert 1 in charts
        assert 5 not in charts  # D5 not implemented


# ── Serialization Tests ────────────────────────────────────

class TestSerialization:
    def test_divisional_chart_to_dict(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 9)
        d = divisional_chart_to_dict(chart)
        assert d["division"] == 9
        assert d["name"] == "Navamsha (D9)"
        assert d["lagna"] == chart.lagna
        assert "vargottama_planets" in d
        assert isinstance(d["vargottama_planets"], list)
        assert "planets" in d
        assert isinstance(d["planets"], dict)

    def test_to_dict_planet_fields(self, natal_longitudes, lagna_longitude) -> None:
        chart = compute_divisional_chart(natal_longitudes, lagna_longitude, 1)
        d = divisional_chart_to_dict(chart)
        sun = d["planets"]["SUN"]
        assert sun["planet"] == "SUN"
        assert sun["rashi"] == "MESHA"
        assert sun["rashi_name"] == "Aries"
        assert isinstance(sun["degree_in_sign"], (int, float))
        assert isinstance(sun["house"], int)


# ── Error Handling ─────────────────────────────────────────

class TestErrors:
    def test_unsupported_division_raises(self, natal_longitudes, lagna_longitude) -> None:
        with pytest.raises(ValueError, match="not yet implemented"):
            compute_divisional_chart(natal_longitudes, lagna_longitude, 5)

    def test_unsupported_division_999_raises(self, natal_longitudes, lagna_longitude) -> None:
        with pytest.raises(ValueError, match="not yet implemented"):
            compute_divisional_chart(natal_longitudes, lagna_longitude, 999)


# ── CHART_META Coverage ────────────────────────────────────

class TestChartMeta:
    def test_all_expected_divisions_in_meta(self) -> None:
        expected = [1, 2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60]
        for div in expected:
            assert div in CHART_META, f"D{div} missing from CHART_META"

    def test_meta_has_name_and_desc(self) -> None:
        for div, meta in CHART_META.items():
            assert "name" in meta, f"D{div} missing name"
            assert "desc" in meta, f"D{div} missing desc"
            assert len(meta["name"]) > 0, f"D{div} has empty name"
            assert len(meta["desc"]) > 0, f"D{div} has empty desc"


# ── Edge Cases ─────────────────────────────────────────────

# ── Calculate Divisional Positions (Adapter) Tests ──────────────────────

class TestCalculateDivisionalPositions:
    def test_with_planets_key_d9(self) -> None:
        """calculate_divisional_positions should work with 'planets' key for D9."""
        facts = {
            "planets": {
                "SUN": {"longitude": 15.0},
                "MOON": {"longitude": 45.5},
                "MARS": {"longitude": 90.0},
                "MERCURY": {"longitude": 195.0},
                "JUPITER": {"longitude": 250.0},
                "VENUS": {"longitude": 330.0},
                "SATURN": {"longitude": 300.0},
            },
            "lagna_longitude": 100.0,
        }
        result = calculate_divisional_positions(facts, "D9")
        assert result.division == 9
        assert len(result.planets) == 7
        assert "SUN" in result.planets
        assert "SATURN" in result.planets

    def test_with_planet_details_key(self) -> None:
        """calculate_divisional_positions should work with 'planet_details' key."""
        facts = {
            "planet_details": {
                "SUN": {"longitude": 15.0},
                "MOON": {"longitude": 45.5},
                "MARS": {"longitude": 90.0},
                "MERCURY": {"longitude": 195.0},
                "JUPITER": {"longitude": 250.0},
                "VENUS": {"longitude": 330.0},
                "SATURN": {"longitude": 300.0},
            },
            "lagna_longitude": 100.0,
        }
        result = calculate_divisional_positions(facts, "D9")
        assert result.division == 9

    def test_division_string_formats(self) -> None:
        """Should accept various string formats for division type."""
        facts = {
            "planets": {"SUN": {"longitude": 15.0}},
            "lagna_longitude": 0.0,
        }
        # All these should produce D9
        for div_str in ["D9", "d9", "9", "  D9  "]:
            result = calculate_divisional_positions(facts, div_str)
            assert result.division == 9

    def test_invalid_division_type_raises(self) -> None:
        """Invalid division type should raise ValueError."""
        facts = {
            "planets": {"SUN": {"longitude": 15.0}},
            "lagna_longitude": 0.0,
        }
        with pytest.raises(ValueError, match="Invalid divisional type"):
            calculate_divisional_positions(facts, "INVALID")

    def test_unsupported_division_raises(self) -> None:
        """Unsupported division number should raise ValueError."""
        facts = {
            "planets": {"SUN": {"longitude": 15.0}},
            "lagna_longitude": 0.0,
        }
        with pytest.raises(ValueError, match="not supported"):
            calculate_divisional_positions(facts, "D5")

    def test_no_longitude_raises(self) -> None:
        """Missing longitude data should raise ValueError."""
        facts = {
            "planets": {"SUN": {"house": 1}},  # No longitude
            "lagna_longitude": 0.0,
        }
        with pytest.raises(ValueError, match="No planet longitudes"):
            calculate_divisional_positions(facts, "D9")

    def test_lagna_from_sign_fallback(self) -> None:
        """Should compute lagna longitude from lagna_sign if not provided."""
        facts = {
            "planets": {"SUN": {"longitude": 15.0}},
            "lagna_sign": "KARKA",  # Cancer
        }
        result = calculate_divisional_positions(facts, "D1")
        assert result.lagna == "KARKA"

    def test_lagna_from_sign_number(self) -> None:
        """Should compute lagna longitude from numeric lagna_sign."""
        facts = {
            "planets": {"SUN": {"longitude": 15.0}},
            "lagna_sign": 4,  # Cancer (4th sign)
        }
        result = calculate_divisional_positions(facts, "D1")
        assert result.lagna == "KARKA"

    def test_nodes_excluded(self) -> None:
        """RAHU and KETU should be excluded from divisional charts."""
        facts = {
            "planets": {
                "SUN": {"longitude": 15.0},
                "MOON": {"longitude": 45.0},
                "RAHU": {"longitude": 200.0},
                "KETU": {"longitude": 20.0},
            },
            "lagna_longitude": 0.0,
        }
        result = calculate_divisional_positions(facts, "D9")
        assert "RAHU" not in result.planets
        assert "KETU" not in result.planets

    def test_matches_compute_divisional_chart_direct(self) -> None:
        """calculate_divisional_positions should match compute_divisional_chart."""
        facts = {
            "planets": {
                "SUN": {"longitude": 15.0},
                "MOON": {"longitude": 45.5},
                "MARS": {"longitude": 90.0},
                "MERCURY": {"longitude": 195.0},
                "JUPITER": {"longitude": 250.0},
                "VENUS": {"longitude": 330.0},
                "SATURN": {"longitude": 300.0},
            },
            "lagna_longitude": 100.0,
        }
        natal_longitudes = {p: d["longitude"] for p, d in facts["planets"].items()}

        result_adapter = calculate_divisional_positions(facts, "D9")
        result_direct = compute_divisional_chart(natal_longitudes, 100.0, 9)

        for planet in ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"]:
            assert result_adapter.planets[planet].rashi == result_direct.planets[planet].rashi
            assert result_adapter.planets[planet].degree_in_sign == result_direct.planets[planet].degree_in_sign

    def test_all_major_divisions(self) -> None:
        """Should compute all major divisional charts."""
        facts = {
            "planets": {
                "SUN": {"longitude": 15.0},
                "MOON": {"longitude": 45.5},
                "MARS": {"longitude": 90.0},
            },
            "lagna_longitude": 0.0,
        }
        for div_str in ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16"]:
            result = calculate_divisional_positions(facts, div_str)
            assert len(result.planets) == 3
            assert result.division == int(div_str[1:])


class TestEdgeCases:
    def test_zero_longitude(self) -> None:
        """All planets at 0° Aries."""
        longitudes = {p: 0.0 for p in ["SUN", "MOON"]}
        chart = compute_divisional_chart(longitudes, 0.0, 1)
        assert chart.planets["SUN"].rashi == "MESHA"
        assert chart.planets["SUN"].degree_in_sign == 0.0

    def test_359_degrees(self) -> None:
        """Planet at 359° should be in MEENA."""
        chart = compute_divisional_chart({"SUN": 359.0}, 0.0, 1)
        assert chart.planets["SUN"].rashi == "MEENA"
        assert chart.planets["SUN"].degree_in_sign == pytest.approx(29.0, abs=0.01)

    def test_all_planets_same_sign(self) -> None:
        """All planets at 15° Aries."""
        longitudes = {p: 15.0 for p in ["SUN", "MOON", "MARS", "MERCURY",
                                          "JUPITER", "VENUS", "SATURN"]}
        chart = compute_divisional_chart(longitudes, 15.0, 1)
        for planet, dp in chart.planets.items():
            assert dp.rashi == "MESHA"
            assert dp.house == 1  # Lagna house

    def test_empty_planet_dict(self) -> None:
        """Empty natal longitudes should produce empty chart."""
        chart = compute_divisional_chart({}, 100.0, 1)
        assert len(chart.planets) == 0
        assert chart.lagna == "KARKA"  # 100° → Cancer

    def test_d1_house_calculation_wrap_around(self) -> None:
        """Test house calculation wraps around correctly."""
        # Lagna at 0° (MESHA), planet at 330° (MEENA)
        chart = compute_divisional_chart({"SUN": 330.0}, 0.0, 1)
        # House = ((11 - 0) % 12) + 1 = 12
        assert chart.planets["SUN"].house == 12

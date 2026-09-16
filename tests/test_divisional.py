# tests/test_divisional.py
"""Unit tests for divisional chart calculations (D3, D7, D12).

Verifies sign placement accuracy, including across sign boundaries.
"""

from src.jrs.services.divisional import (
    calculate_d12_dwadasamsha,
    calculate_d3_drekkana,
    calculate_d7_saptamsha,
    enrich_with_divisional_charts,
)


def test_calculate_d3_drekkana():
    # Sun at 15° Virgo (Sign Index 5, 2nd Drekkana -> 5th from Virgo = Capricorn)
    d3 = calculate_d3_drekkana(165.0)
    assert d3["sign"] == "Capricorn"
    assert d3["sign_index"] == 10
    assert d3["drekkana_num"] == 2


def test_calculate_d3_first_drekkana_same_sign():
    # Sun at 5° Virgo (1st Drekkana -> stays in Virgo)
    d3 = calculate_d3_drekkana(155.0)
    assert d3["sign"] == "Virgo"
    assert d3["drekkana_num"] == 1


def test_calculate_d3_third_drekkana_trine():
    # Sun at 29° Virgo (3rd Drekkana -> 9th from Virgo = Taurus)
    d3 = calculate_d3_drekkana(179.0)
    assert d3["sign"] == "Taurus"
    assert d3["drekkana_num"] == 3


def test_calculate_d7_saptamsha():
    # Moon at 5° Taurus (Sign Index 1 [Even], 2nd division -> 7th from Taurus = Scorpio + 1 = Sagittarius)
    d7 = calculate_d7_saptamsha(35.0)
    assert d7["sign"] == "Sagittarius"
    assert d7["saptamsha_num"] == 2


def test_calculate_d7_odd_sign_starts_from_itself():
    # Moon at 5° Aries (Sign Index 0 [Odd] -> counts from Aries itself)
    d7 = calculate_d7_saptamsha(5.0)
    assert d7["sign"] == "Taurus"
    assert d7["saptamsha_num"] == 2


def test_calculate_d7_last_division_wraps():
    # Moon at 25° Taurus (last Saptamsha -> wraps back to Aries)
    d7 = calculate_d7_saptamsha(55.0)
    assert d7["sign"] == "Aries"
    assert d7["saptamsha_num"] == 6


def test_calculate_d12_dwadasamsha():
    # Mars at 3° Aries (Sign Index 0, 2nd division -> 2nd from Aries = Taurus)
    d12 = calculate_d12_dwadasamsha(3.0)
    assert d12["sign"] == "Taurus"
    assert d12["dwadasamsha_num"] == 2


def test_calculate_d12_last_division_wraps():
    # Mars at 29° Aries (12th division -> wraps to Pisces)
    d12 = calculate_d12_dwadasamsha(29.0)
    assert d12["sign"] == "Pisces"
    assert d12["dwadasamsha_num"] == 12


def test_enrich_with_divisional_charts_includes_all_divisions():
    """Enrichment adds D3, D7, D9, D10, and D12 for every planet."""
    planetary_data = {
        "julian_day": 2461000.0,
        "planets": {
            "Sun": {"longitude": 165.0},
            "Moon": {"longitude": 35.0},
        },
    }
    result = enrich_with_divisional_charts(planetary_data)

    for planet, data in result["planets"].items():
        assert set(data["divisional"].keys()) == {"d3", "d7", "d9", "d10", "d12"}
        assert data["divisional"]["d3"]["division"] == "D3"
        assert data["divisional"]["d7"]["division"] == "D7"
        assert data["divisional"]["d12"]["division"] == "D12"
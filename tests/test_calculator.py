"""
Unit tests for src/jrs/engine/calculator.py
"""

import pytest
from src.jrs.engine.calculator import (
    ZODIAC_SIGNS,
    calculate_chart_positions,
    calculate_d3_sign,
    calculate_d10_sign,
    calculate_nakshatra,
    calculate_varga_d60,
    calculate_varga_d9,
    get_ayanamsha_offset,
    get_julian_day,
    get_utc_offset_hours,
)


def test_get_utc_offset_hours_ist():
    """Verify Asia/Kolkata returns +5.5 hours."""
    offset = get_utc_offset_hours("1995-10-24", "14:30:00", "Asia/Kolkata")
    assert offset == 5.5


def test_get_utc_offset_hours_fallback():
    """Verify invalid timezone falls back safely to 5.5 without crashing."""
    offset = get_utc_offset_hours("1995-10-24", "14:30:00", "Invalid/Timezone")
    assert offset == 5.5


def test_get_julian_day_calculation():
    """Verify Julian Day calculation produces valid float timestamp."""
    jd = get_julian_day("1995-10-24", "14:30:00", "Asia/Kolkata")
    assert isinstance(jd, float)
    assert jd > 2400000.0  # Reasonable Julian Day threshold for 20th century


def test_calculate_nakshatra():
    """Verify Nakshatra and Pada mapping from absolute degree."""
    # 0 degrees -> Ashwini, Pada 1
    nak, pada = calculate_nakshatra(0.0)
    assert nak == "Ashwini"
    assert pada == 1

    # 13.333 degrees -> Bharani, Pada 1
    nak, pada = calculate_nakshatra(13.34)
    assert nak == "Bharani"
    assert pada == 1


def test_calculate_varga_d9():
    """Verify Navamsha (D9) sign derivation."""
    # Mesha (Aries) 0° -> Mesha in D9
    sign, deg = calculate_varga_d9(1.0)
    assert sign == "Mesha"

    # Mesha 15° -> Simha (Leo) in D9
    sign, deg = calculate_varga_d9(15.0)
    assert sign == "Simha"


def test_calculate_varga_d60():
    """Verify Shashtiamsha (D60) sign derivation."""
    sign, deg = calculate_varga_d60(0.25)
    assert sign in ZODIAC_SIGNS


def test_calculate_chart_positions_structure():
    """Verify full chart calculation returns expected data shape."""
    res = calculate_chart_positions(
        date="1995-10-24",
        time="14:30:00",
        latitude=13.0827,
        longitude=80.2707,
        timezone="Asia/Kolkata",
    )

    assert "lagna" in res
    assert "planets" in res

    # Verify Lagna properties
    lagna = res["lagna"]
    assert lagna["sign"] in ZODIAC_SIGNS
    assert 1 <= lagna["pada"] <= 4

    # Verify all 9 planetary nodes exist
    expected_planets = {
        "Sun",
        "Moon",
        "Mars",
        "Mercury",
        "Jupiter",
        "Venus",
        "Saturn",
        "Rahu",
        "Ketu",
    }
    assert expected_planets.issubset(set(res["planets"].keys()))

    # Verify Ketu is 180 degrees opposite Rahu
    rahu_long = res["planets"]["Rahu"]["longitude"]
    ketu_long = res["planets"]["Ketu"]["longitude"]
    assert abs(((rahu_long + 180) % 360) - ketu_long) < 1e-4

    # Verify D3/D10 are present for each planet
    for p_data in res["planets"].values():
        assert "d3" in p_data
        assert "d10" in p_data

    # Verify chart response includes ayanamsha offset field
    assert "ayanamsha" in res

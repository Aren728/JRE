# src/jrs/services/divisional.py

"""Divisional chart calculations (D3 Drekkana, D7 Saptamsha, D9 Navamsha,
D10 Dashamsha, D12 Dwadasamsha).

Provides functions to calculate divisional chart sign placements
for planetary longitudes.
"""

from __future__ import annotations

from typing import Any

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


def calculate_d9_navamsha(longitude: float) -> dict[str, Any]:
    """Calculates D9 (Navamsha) sign placement (3°20' per division).

    Args:
        longitude: Planetary longitude in degrees (0-360).

    Returns:
        Dictionary with division, sign, sign_index, and navamsha_num.
    """
    sign_index = int(longitude // 30)
    pos_in_sign = longitude % 30
    nav_index = int(pos_in_sign // (30 / 9))  # 3.3333 degrees per Navamsha

    # Fire signs (0, 4, 8) start from Aries (0)
    # Earth signs (1, 5, 9) start from Capricorn (9)
    # Air signs (2, 6, 10) start from Libra (6)
    # Water signs (3, 7, 11) start from Cancer (3)
    start_offsets = [0, 9, 6, 3]
    element_type = sign_index % 4
    start_sign = start_offsets[element_type]

    d9_sign_index = (start_sign + nav_index) % 12
    return {
        "division": "D9",
        "sign": ZODIAC_SIGNS[d9_sign_index],
        "sign_index": d9_sign_index + 1,
        "navamsha_num": nav_index + 1,
    }


def calculate_d10_dashamsha(longitude: float) -> dict[str, Any]:
    """Calculates D10 (Dashamsha) sign placement (3°00' per division).

    Args:
        longitude: Planetary longitude in degrees (0-360).

    Returns:
        Dictionary with division, sign, sign_index, and dashamsha_num.
    """
    sign_index = int(longitude // 30)
    pos_in_sign = longitude % 30
    dash_index = int(pos_in_sign // 3)  # 3.0 degrees per Dashamsha

    # Odd signs start from the sign itself
    # Even signs start from 9th sign from itself
    if sign_index % 2 == 0:  # Odd sign (1-indexed: Aries=1, Gemini=3...)
        d10_sign_index = (sign_index + dash_index) % 12
    else:  # Even sign (Taurus=2, Cancer=4...)
        d10_sign_index = (sign_index + 8 + dash_index) % 12

    return {
        "division": "D10",
        "sign": ZODIAC_SIGNS[d10_sign_index],
        "sign_index": d10_sign_index + 1,
        "dashamsha_num": dash_index + 1,
    }


def calculate_d3_drekkana(longitude: float) -> dict[str, Any]:
    """Calculates D3 (Drekkana) sign placement (10° per division).

    Rule:
    - 1st Drekkana (0°-10°): Same sign (1st, 5th, 9th trine)
    - 2nd Drekkana (10°-20°): 5th sign from current sign
    - 3rd Drekkana (20°-30°): 9th sign from current sign

    Args:
        longitude: Planetary longitude in degrees (0-360).

    Returns:
        Dictionary with division, sign, sign_index, and drekkana_num.
    """
    sign_index = int(longitude // 30)
    pos_in_sign = longitude % 30
    drekkana_num = int(pos_in_sign // 10)  # 0, 1, or 2

    trine_offsets = [0, 4, 8]  # 1st (0), 5th (+4), 9th (+8)
    d3_sign_index = (sign_index + trine_offsets[drekkana_num]) % 12

    return {
        "division": "D3",
        "sign": ZODIAC_SIGNS[d3_sign_index],
        "sign_index": d3_sign_index + 1,
        "drekkana_num": drekkana_num + 1,
    }


def calculate_d7_saptamsha(longitude: float) -> dict[str, Any]:
    """Calculates D7 (Saptamsha) sign placement (4°17'08.57" per division / ~4.2857°).

    Rule:
    - Odd signs: Start counting from the sign itself.
    - Even signs: Start counting from the 7th sign from itself.

    Args:
        longitude: Planetary longitude in degrees (0-360).

    Returns:
        Dictionary with division, sign, sign_index, and saptamsha_num.
    """
    sign_index = int(longitude // 30)
    pos_in_sign = longitude % 30
    saptamsha_num = int(pos_in_sign // (30 / 7))  # 0 to 6

    if sign_index % 2 == 0:  # Odd sign (0-indexed: 0=Aries, 2=Gemini...)
        d7_sign_index = (sign_index + saptamsha_num) % 12
    else:  # Even sign (1=Taurus, 3=Cancer...)
        d7_sign_index = (sign_index + 6 + saptamsha_num) % 12

    return {
        "division": "D7",
        "sign": ZODIAC_SIGNS[d7_sign_index],
        "sign_index": d7_sign_index + 1,
        "saptamsha_num": saptamsha_num + 1,
    }


def calculate_d12_dwadasamsha(longitude: float) -> dict[str, Any]:
    """Calculates D12 (Dwadasamsha) sign placement (2°30' per division).

    Rule:
    - Always starts counting from the sign itself for all 12 divisions.

    Args:
        longitude: Planetary longitude in degrees (0-360).

    Returns:
        Dictionary with division, sign, sign_index, and dwadasamsha_num.
    """
    sign_index = int(longitude // 30)
    pos_in_sign = longitude % 30
    dwadasamsha_num = int(pos_in_sign // 2.5)  # 0 to 11

    d12_sign_index = (sign_index + dwadasamsha_num) % 12

    return {
        "division": "D12",
        "sign": ZODIAC_SIGNS[d12_sign_index],
        "sign_index": d12_sign_index + 1,
        "dwadasamsha_num": dwadasamsha_num + 1,
    }


def enrich_with_divisional_charts(planetary_data: dict[str, Any]) -> dict[str, Any]:
    """Appends D3, D7, D9, D10, and D12 calculations to planetary positions.

    Args:
        planetary_data: Dictionary containing 'planets' key with
            planetary position data including 'longitude'.

    Returns:
        The same dictionary with 'divisional' data added to each planet.
    """
    enriched_planets = {}
    for planet, data in planetary_data["planets"].items():
        long = data["longitude"]
        data_copy = dict(data)
        data_copy["divisional"] = {
            "d3": calculate_d3_drekkana(long),
            "d7": calculate_d7_saptamsha(long),
            "d9": calculate_d9_navamsha(long),
            "d10": calculate_d10_dashamsha(long),
            "d12": calculate_d12_dwadasamsha(long),
        }
        enriched_planets[planet] = data_copy

    planetary_data["planets"] = enriched_planets
    return planetary_data

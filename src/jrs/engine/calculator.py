"""
Calculates precise sidereal planetary positions, Lagna, and Varga placements (D1, D9, D60)
using PySwisseph (Lahiri Ayanamsha) and IANA timezone resolution via zoneinfo.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any

import swisseph as swe

# Configure Sidereal Mode (Lahiri / Chitra Paksha Ayanamsha)
swe.set_sid_mode(swe.SIDM_LAHIRI)

PLANET_MAP = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}

ZODIAC_SIGNS = [
    "Mesha",
    "Vrishabha",
    "Mithuna",
    "Karka",
    "Simha",
    "Kanya",
    "Tula",
    "Vrishchika",
    "Dhanu",
    "Makara",
    "Kumbha",
    "Meena",
]

NAKSHATRAS = [
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]


def get_utc_offset_hours(date_str: str, time_str: str, timezone_iana: str) -> float:
    """Parses IANA timezone string and calculates UTC offset in hours, adjusting for DST."""
    if time_str.count(":") == 1:
        time_str = f"{time_str}:00"
    try:
        dt_naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        local_dt = dt_naive.replace(tzinfo=ZoneInfo(timezone_iana))
        return local_dt.utcoffset().total_seconds() / 3600.0
    except Exception:
        # Fallback to IST (+5.5) if parsing fails
        return 5.5


def get_julian_day(date_str: str, time_str: str, timezone_iana: str) -> float:
    """Converts local birth datetime and IANA timezone into Universal Time Julian Day."""
    if time_str.count(":") == 1:
        time_str = f"{time_str}:00"
    tz_offset_hours = get_utc_offset_hours(date_str, time_str, timezone_iana)
    dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    utc_hours = dt.hour + (dt.minute / 60.0) + (dt.second / 3600.0) - tz_offset_hours
    return swe.julday(dt.year, dt.month, dt.day, utc_hours)


def calculate_varga_position(abs_deg: float) -> tuple[str, float]:
    """Returns sign name and degree within sign (0-30°)."""
    sign_idx = int(abs_deg // 30) % 12
    deg_in_sign = abs_deg % 30
    return ZODIAC_SIGNS[sign_idx], round(deg_in_sign, 2)


def calculate_nakshatra(abs_deg: float) -> tuple[str, int]:
    """Calculates Nakshatra name and Pada (1-4)."""
    nak_idx = int(abs_deg // (13 + 1 / 3)) % 27
    rem_deg = abs_deg % (13 + 1 / 3)
    pada = int(rem_deg // (3 + 1 / 3)) + 1
    return NAKSHATRAS[nak_idx], min(pada, 4)


def calculate_varga_d9(abs_deg: float) -> tuple[str, float]:
    """Calculates D9 (Navamsha) sign placement."""
    sign_idx = int(abs_deg // 30) % 12
    deg_in_sign = abs_deg % 30
    nav_idx = int(deg_in_sign // (3 + 1 / 3))

    element_type = sign_idx % 4
    start_sign = [0, 9, 6, 3][element_type]
    target_sign_idx = (start_sign + nav_idx) % 12
    return ZODIAC_SIGNS[target_sign_idx], round((deg_in_sign % (3 + 1 / 3)) * 9, 2)


def calculate_varga_d60(abs_deg: float) -> tuple[str, float]:
    """Calculates D60 (Shashtiamsha) sign placement."""
    sign_idx = int(abs_deg // 30) % 12
    deg_in_sign = abs_deg % 30
    d60_part = int(deg_in_sign // 0.5)
    target_sign_idx = (sign_idx + d60_part) % 12
    return ZODIAC_SIGNS[target_sign_idx], round((deg_in_sign % 0.5) * 60, 2)


AYANAMSHA_OFFSETS: dict[str, float] = {
    "lahiri": 0.0,
    "raman": 1.4167,
    "kp": 0.1000,
}


def get_ayanamsha_offset(mode: str | None) -> float:
    """Return a simple ayanamsha offset in degrees for display/selection.

    This is a placeholder offset model. The live ephemeris path uses
    swisseph's SIDM_LAHIRI by default; ayanamsha selection should eventually
    drive the swisseph sidereal mode / offset configuration.
    """
    if not mode:
        return 0.0
    return AYANAMSHA_OFFSETS.get(mode.lower(), 0.0)


def calculate_d3_sign(longitude: float) -> str:
    """Calculate Drekkana (D3) sign from absolute longitude."""
    norm_lon = longitude % 360.0
    sign_idx = int(norm_lon // 30)
    pos_in_sign = norm_lon % 30
    drekkana_part = int(pos_in_sign // 10)

    if drekkana_part == 0:
        d3_sign_idx = sign_idx
    elif drekkana_part == 1:
        d3_sign_idx = (sign_idx + 4) % 12
    else:
        d3_sign_idx = (sign_idx + 8) % 12

    return ZODIAC_SIGNS[d3_sign_idx]


def calculate_d10_sign(longitude: float) -> str:
    """Calculate Dashamsha (D10) sign from absolute longitude."""
    norm_lon = longitude % 360.0
    sign_idx = int(norm_lon // 30)
    pos_in_sign = norm_lon % 30
    part_idx = int(pos_in_sign // 3)

    # Odd signs start from the same sign, even signs from the 9th sign
    is_odd_sign = (sign_idx % 2) == 0
    if is_odd_sign:
        start_sign = sign_idx
    else:
        start_sign = (sign_idx + 8) % 12

    d10_sign_idx = (start_sign + part_idx) % 12
    return ZODIAC_SIGNS[d10_sign_idx]


def calculate_chart_positions(
    date: str,
    time: str,
    latitude: float,
    longitude: float,
    timezone: str,
    ayanamsha: str | None = None,
) -> dict[str, Any]:
    """Calculates precise sidereal planetary positions via PySwisseph."""
    jd = get_julian_day(date, time, timezone)

    # Calculate Ascendant (Lagna)
    houses, ascmc = swe.houses_ex(jd, latitude, longitude, b"P", swe.FLG_SIDEREAL)
    asc_deg = ascmc[0] % 360
    asc_sign, asc_deg_in_sign = calculate_varga_position(asc_deg)
    asc_nak, asc_pada = calculate_nakshatra(asc_deg)
    asc_sign_idx = ZODIAC_SIGNS.index(asc_sign)

    planets_data: dict[str, Any] = {}
    for p_name, p_code in PLANET_MAP.items():
        calc_out = swe.calc_ut(jd, p_code, swe.FLG_SIDEREAL | swe.FLG_SPEED)
        res = calc_out[0] if isinstance(calc_out, (tuple, list)) else calc_out
        abs_deg = res[0] % 360

        p_sign, p_deg_in_sign = calculate_varga_position(abs_deg)
        p_sign_idx = ZODIAC_SIGNS.index(p_sign)
        house = ((p_sign_idx - asc_sign_idx) % 12) + 1

        nak_name, pada = calculate_nakshatra(abs_deg)
        d3_sign = calculate_d3_sign(abs_deg)
        d9_sign, _ = calculate_varga_d9(abs_deg)
        d10_sign = calculate_d10_sign(abs_deg)
        d60_sign, _ = calculate_varga_d60(abs_deg)

        planets_data[p_name] = {
            "longitude": abs_deg,
            "d1": {
                "sign": p_sign,
                "house": house,
                "degree": p_deg_in_sign,
                "nakshatra": nak_name,
                "pada": pada,
            },
            "d3": {
                "sign": d3_sign,
                "house": ((ZODIAC_SIGNS.index(d3_sign) - asc_sign_idx) % 12) + 1,
                "degree": p_deg_in_sign,
                "nakshatra": nak_name,
                "pada": pada,
            },
            "d9": {
                "sign": d9_sign,
                "house": ((ZODIAC_SIGNS.index(d9_sign) - asc_sign_idx) % 12) + 1,
                "degree": p_deg_in_sign,
                "nakshatra": nak_name,
                "pada": pada,
            },
            "d10": {
                "sign": d10_sign,
                "house": ((ZODIAC_SIGNS.index(d10_sign) - asc_sign_idx) % 12) + 1,
                "degree": p_deg_in_sign,
                "nakshatra": nak_name,
                "pada": pada,
            },
            "d60": {
                "sign": d60_sign,
                "house": ((ZODIAC_SIGNS.index(d60_sign) - asc_sign_idx) % 12) + 1,
                "degree": p_deg_in_sign,
                "nakshatra": nak_name,
                "pada": pada,
            },
            "shadbala_score": 1.20,
            "functional_role": "Calculated Position",
        }

    # Derive Ketu (180° opposite Rahu)
    rahu_deg = planets_data["Rahu"]["longitude"]
    ketu_deg = (rahu_deg + 180) % 360
    k_sign, k_deg_in_sign = calculate_varga_position(ketu_deg)
    k_sign_idx = ZODIAC_SIGNS.index(k_sign)
    k_nak, k_pada = calculate_nakshatra(ketu_deg)
    kd3_sign = calculate_d3_sign(ketu_deg)
    kd9_sign, _ = calculate_varga_d9(ketu_deg)
    kd10_sign = calculate_d10_sign(ketu_deg)
    kd60_sign, _ = calculate_varga_d60(ketu_deg)

    planets_data["Ketu"] = {
        "longitude": ketu_deg,
        "d1": {
            "sign": k_sign,
            "house": ((k_sign_idx - asc_sign_idx) % 12) + 1,
            "degree": k_deg_in_sign,
            "nakshatra": k_nak,
            "pada": k_pada,
        },
        "d3": {
            "sign": kd3_sign,
            "house": ((ZODIAC_SIGNS.index(kd3_sign) - asc_sign_idx) % 12) + 1,
            "degree": k_deg_in_sign,
            "nakshatra": k_nak,
            "pada": k_pada,
        },
        "d9": {
            "sign": kd9_sign,
            "house": ((ZODIAC_SIGNS.index(kd9_sign) - asc_sign_idx) % 12) + 1,
            "degree": k_deg_in_sign,
            "nakshatra": k_nak,
            "pada": k_pada,
        },
        "d10": {
            "sign": kd10_sign,
            "house": ((ZODIAC_SIGNS.index(kd10_sign) - asc_sign_idx) % 12) + 1,
            "degree": k_deg_in_sign,
            "nakshatra": k_nak,
            "pada": k_pada,
        },
        "d60": {
            "sign": kd60_sign,
            "house": ((ZODIAC_SIGNS.index(kd60_sign) - asc_sign_idx) % 12) + 1,
            "degree": k_deg_in_sign,
            "nakshatra": k_nak,
            "pada": k_pada,
        },
        "shadbala_score": 1.10,
        "functional_role": "Karmic Axis Node",
    }

    return {
        "lagna": {
            "sign": asc_sign,
            "house": 1,
            "degree": asc_deg_in_sign,
            "nakshatra": asc_nak,
            "pada": asc_pada,
        },
        "planets": planets_data,
        "ayanamsha": get_ayanamsha_offset(ayanamsha),
    }

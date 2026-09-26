"""JRE Horoscope — Gochar (Transit) Engine.

Calculates real-time Moon and Sun positions using Swiss Ephemeris,
determines current Nakshatra and Rashi placements, and generates
deterministic daily/weekly horoscope narratives.

This is a SEPARATE module from the natal v1.0.0 reasoning engine.
It operates on current (transit) positions only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── Constants ─────────────────────────────────────────────

_RASHI_ORDER = [
    "MESHA",
    "VRISHABHA",
    "MITHUNA",
    "KARKA",
    "SIMHA",
    "KANYA",
    "TULA",
    "VRISHCHIKA",
    "DHANUSHA",
    "MAKARA",
    "KUMBHA",
    "MEENA",
]

_RASHI_NAMES: dict[str, str] = {
    "MESHA": "Aries",
    "VRISHABHA": "Taurus",
    "MITHUNA": "Gemini",
    "KARKA": "Cancer",
    "SIMHA": "Leo",
    "KANYA": "Virgo",
    "TULA": "Libra",
    "VRISHCHIKA": "Scorpio",
    "DHANUSHA": "Sagittarius",
    "MAKARA": "Capricorn",
    "KUMBHA": "Aquarius",
    "MEENA": "Pisces",
}

_RASHI_LORDS: dict[str, str] = {
    "MESHA": "Mars",
    "VRISHABHA": "Venus",
    "MITHUNA": "Mercury",
    "KARKA": "Moon",
    "SIMHA": "Sun",
    "KANYA": "Mercury",
    "TULA": "Venus",
    "VRISHCHIKA": "Mars",
    "DHANUSHA": "Jupiter",
    "MAKARA": "Saturn",
    "KUMBHA": "Saturn",
    "MEENA": "Jupiter",
}

_NAKSHATRA_ORDER = [
    "ASHWINI",
    "BHARANI",
    "KRITTIKA",
    "ROHINI",
    "MRIGASHIRA",
    "ARDRA",
    "PUNARVASU",
    "PUSHA",
    "ASHLESHA",
    "MAGHA",
    "PURVA_PHALGUNI",
    "UTTARA_PHALGUNI",
    "HASTA",
    "CHITRA",
    "SWATI",
    "VISHAKHA",
    "ANURADHA",
    "JYESHTHA",
    "MULA",
    "PURVA_ASHADHA",
    "UTTARA_ASHADHA",
    "SHRAVANA",
    "DHANISHTA",
    "SHATABHISHA",
    "PURVA_BHADRAPADA",
    "UTTARA_BHADRAPADA",
    "REVATI",
]

_NAKSHATRA_NAMES: dict[str, str] = {
    "ASHWINI": "Ashwini",
    "BHARANI": "Bharani",
    "KRITTIKA": "Krittika",
    "ROHINI": "Rohini",
    "MRIGASHIRA": "Mrigashira",
    "ARDRA": "Ardra",
    "PUNARVASU": "Punarvasu",
    "PUSHA": "Pushya",
    "ASHLESHA": "Ashlesha",
    "MAGHA": "Magha",
    "PURVA_PHALGUNI": "Purva Phalguni",
    "UTTARA_PHALGUNI": "Uttara Phalguni",
    "HASTA": "Hasta",
    "CHITRA": "Chitra",
    "SWATI": "Swati",
    "VISHAKHA": "Vishakha",
    "ANURADHA": "Anuradha",
    "JYESHTHA": "Jyeshtha",
    "MULA": "Mula",
    "PURVA_ASHADHA": "Purva Ashadha",
    "UTTARA_ASHADHA": "Uttara Ashadha",
    "SHRAVANA": "Shravana",
    "DHANISHTA": "Dhanishta",
    "SHATABHISHA": "Shatabhisha",
    "PURVA_BHADRAPADA": "Purva Bhadrapada",
    "UTTARA_BHADRAPADA": "Uttara Bhadrapada",
    "REVATI": "Revati",
}

_NAKSHATRA_PADAS = 4  # Each nakshatra has 4 padas

_PLANET_BODY_MAP: dict[str, int] = {
    "SUN": 0,
    "MOON": 1,
    "MARS": 4,
    "MERCURY": 2,
    "JUPITER": 5,
    "VENUS": 3,
    "SATURN": 6,
    "RAHU": 10,
    "KETU": 11,
}

# ── Horoscope Locales ─────────────────────────────────────
_LOCALES_DIR = Path(__file__).parent / "locales"


def _load_horoscope_registry(lang: str = "en") -> dict[str, Any]:
    """Load horoscope narrative registry with English fallback."""
    path = _LOCALES_DIR / f"gochar_{lang}.json"
    if not path.exists():
        path = _LOCALES_DIR / "gochar_en.json"
    try:
        with path.open(encoding="utf-8") as f:
            loaded: dict[str, Any] = json.load(f)
            return loaded
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


# ── Data Structures ───────────────────────────────────────


@dataclass
class PlanetPosition:
    """Current position of a planet."""

    planet: str
    longitude: float  # Ecliptic longitude in degrees (0-360)
    rashi: str  # Rashi name (e.g., "SIMHA")
    rashi_index: int  # 0-11
    degree_in_sign: float  # 0-30
    nakshatra: str | None = None  # Only for Moon
    nakshatra_index: int | None = None
    nakshatra_pada: int | None = None  # 1-4


@dataclass
class PanchangData:
    """Panchang (five-limb) data for the current day."""

    tithi: str
    nakshatra: str
    yoga: str
    karana: str
    vara: str  # Day of week


@dataclass
class GocharResult:
    """Complete Gochar (transit) result for the current moment."""

    timestamp: str
    moon: PlanetPosition
    sun: PlanetPosition
    panchang: PanchangData
    all_planets: dict[str, PlanetPosition]
    moon_from_rashis: dict[str, int]  # Moon's house from each Rashi
    daily_rashi: dict[str, str]  # Rashi -> narrative token
    daily_nakshatra: dict[str, str]  # Nakshatra -> narrative token


# ── Position Calculation ──────────────────────────────────


def _longitude_to_rashi(longitude: float) -> tuple[str, int, float]:
    """Convert ecliptic longitude to Rashi, index, and degree-in-sign."""
    normalized = longitude % 360.0
    rashi_index = int(normalized / 30.0)
    degree_in_sign = normalized - (rashi_index * 30.0)
    rashi = _RASHI_ORDER[rashi_index]
    return rashi, rashi_index, degree_in_sign


def _longitude_to_nakshatra(longitude: float) -> tuple[str, int, int]:
    """Convert ecliptic longitude to Nakshatra, index, and pada."""
    normalized = longitude % 360.0
    nak_span = 360.0 / 27.0  # ~13.333 degrees per nakshatra
    nak_index = int(normalized / nak_span)
    nakshatra = _NAKSHATRA_ORDER[nak_index]

    # Calculate pada (1-4)
    pada_span = nak_span / _NAKSHATRA_PADAS
    within_nak = normalized - (nak_index * nak_span)
    pada = int(within_nak / pada_span) + 1
    pada = min(pada, _NAKSHATRA_PADAS)

    return nakshatra, nak_index, pada


def _compute_moon_from_rashis(moon_rashi_index: int) -> dict[str, int]:
    """Compute Moon's house position from each of the 12 Rashis."""
    result = {}
    for i, rashi in enumerate(_RASHI_ORDER):
        house = ((moon_rashi_index - i) % 12) + 1
        result[rashi] = house
    return result


# ── Swiss Ephemeris Calculation ───────────────────────────


def calculate_current_positions(
    latitude: float = 0.0,
    longitude: float = 0.0,
) -> dict[str, PlanetPosition]:
    """Calculate current planetary positions using Swiss Ephemeris.

    Args:
        latitude: Observer latitude (default 0 for geocentric).
        longitude: Observer longitude (default 0 for geocentric).

    Returns:
        Dictionary of planet name -> PlanetPosition.
    """
    import swisseph as swe

    # Set ephe path
    swe.set_ephe_path(None)  # Use built-in data
    # CRITICAL: Set Sidereal Mode to Lahiri (Chitrapaksha) for Vedic astrology
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0.0, 0.0)

    # Current UTC time as Julian Day — includes fractional hours (h + min/60 + sec/3600)
    now = datetime.now(timezone.utc)
    jd = swe.julday(
        now.year, now.month, now.day, now.hour + now.minute / 60.0 + now.second / 3600.0
    )
    print(
        f"DEBUG calculate_current_positions: Calculating transits for DATE: {now.date()} TIME: {now.time()} UTC — JD: {jd}"
    )

    positions = {}

    for planet_name, planet_id in _PLANET_BODY_MAP.items():
        try:
            flag = swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_SIDEREAL
            xx = swe.calc_ut(jd, planet_id, flag)
            longitude_deg = xx[0][0] % 360.0
        except Exception:
            # Fallback: skip planets that fail to calculate
            continue

        rashi, rashi_index, degree_in_sign = _longitude_to_rashi(longitude_deg)

        pos = PlanetPosition(
            planet=planet_name,
            longitude=longitude_deg,
            rashi=rashi,
            rashi_index=rashi_index,
            degree_in_sign=degree_in_sign,
        )

        # Calculate Nakshatra only for Moon
        if planet_name == "MOON":
            nak, nak_idx, pada = _longitude_to_nakshatra(longitude_deg)
            pos.nakshatra = nak
            pos.nakshatra_index = nak_idx
            pos.nakshatra_pada = pada

        positions[planet_name] = pos

    return positions


def _estimate_panchang(
    moon_pos: PlanetPosition, sun_pos: PlanetPosition, now: datetime
) -> PanchangData:
    """Estimate Panchang data from Moon/Sun positions.

    This is a simplified estimation. Full Panchang calculation requires
    precise tithi/yoga/karana computation from Moon-Sun angular distance.
    """
    # Tithi: Moon-Sun angular distance / 12 (each tithi = 12°)
    moon_sun_diff = (moon_pos.longitude - sun_pos.longitude) % 360.0
    tithi_num = int(moon_sun_diff / 12.0) + 1
    tithi_num = min(tithi_num, 30)

    tithi_names = [
        "Pratipada",
        "Dwitiya",
        "Tritiya",
        "Chaturthi",
        "Panchami",
        "Shashthi",
        "Saptami",
        "Ashtami",
        "Navami",
        "Dashami",
        "Ekadashi",
        "Dwadashi",
        "Trayodashi",
        "Chaturdashi",
        "Purnima",
        "Pratipada",
        "Dwitiya",
        "Tritiya",
        "Chaturthi",
        "Panchami",
        "Shashthi",
        "Saptami",
        "Ashtami",
        "Navami",
        "Dashami",
        "Ekadashi",
        "Dwadashi",
        "Trayodashi",
        "Chaturdashi",
        "Amavasya",
    ]

    # Yoga: Sun-Moon angular distance / 13°20' (each yoga = 13.333°)
    yoga_num = int(moon_sun_diff / 13.333) % 27
    yoga_names = [
        "Vishkumbha",
        "Priti",
        "Ayushman",
        "Saubhagya",
        "Shobhana",
        "Atiganda",
        "Sukarma",
        "Dhriti",
        "Shula",
        "Ganda",
        "Vriddhi",
        "Dhruva",
        "Vyaghata",
        "Harshana",
        "Vajra",
        "Siddhi",
        "Vyatipata",
        "Variyan",
        "Parigha",
        "Shiva",
        "Siddha",
        "Sadhya",
        "Shubha",
        "Shukla",
        "Brahma",
        "Indra",
        "Vaidhriti",
    ]

    # Karana: half of tithi
    karana_num = ((tithi_num - 1) * 2) % 60
    karana_names = [
        "Kimstughna",
        "Shakuni",
        "Chatushpada",
        "Nagava",
        "Kimstughna",
        "Bava",
        "Balava",
        "Kaulava",
        "Taitila",
        "Gara",
        "Vanija",
        "Vishti",
    ]

    # Var day of week
    day_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    vara = day_names[now.weekday()]

    return PanchangData(
        tithi=f"{tithi_names[(tithi_num - 1) % 30]} ({tithi_num})",
        nakshatra=_NAKSHATRA_NAMES.get(moon_pos.nakshatra or "ASHWINI", "Ashwini"),
        yoga=yoga_names[yoga_num],
        karana=karana_names[karana_num % len(karana_names)],
        vara=vara,
    )


def generate_gochar_result(
    latitude: float = 28.6139,
    longitude: float = 77.2090,
    language: str = "en",
) -> GocharResult:
    """Generate the complete Gochar result for the current moment.

    Args:
        latitude: Observer latitude for position calculation.
        longitude: Observer longitude for position calculation.
        language: Language code for narrative output.

    Returns:
        GocharResult with all transit data and narratives.
    """
    now = datetime.now(timezone.utc)

    # Calculate real-time positions
    all_planets = calculate_current_positions(latitude, longitude)

    moon = all_planets.get("MOON")
    sun = all_planets.get("SUN")

    if not moon or not sun:
        # Fallback with minimal data
        moon = moon or PlanetPosition("MOON", 0, "MESHA", 0, 0)
        sun = sun or PlanetPosition("SUN", 0, "MESHA", 0, 0)

    # Panchang
    panchang = _estimate_panchang(moon, sun, now)

    # Moon's house from each Rashi
    moon_from_rashis = _compute_moon_from_rashis(moon.rashi_index)

    # Load narrative registry
    registry = _load_horoscope_registry(language)

    # Generate daily Rashi narratives
    daily_rashi = {}
    for rashi in _RASHI_ORDER:
        house = moon_from_rashis[rashi]
        token = f"MOON_{house}TH_FROM_{rashi}"
        narrative = registry.get("DAILY_RASHI", {}).get(token, "")
        if not narrative:
            # Fallback to generic
            narrative = registry.get("DAILY_RASHI", {}).get(f"MOON_{house}TH_GENERIC", "")
        daily_rashi[rashi] = narrative

    # Generate daily Nakshatra narratives
    daily_nakshatra = {}
    if moon.nakshatra:
        # Narrative for Moon's current nakshatra
        token = f"MOON_IN_{moon.nakshatra}"
        narrative = registry.get("DAILY_NAKSHATRA", {}).get(token, "")
        daily_nakshatra[moon.nakshatra] = narrative

        # Narratives for all 27 nakshatras (general daily)
        for nak in _NAKSHATRA_ORDER:
            if nak not in daily_nakshatra:
                daily_nakshatra[nak] = registry.get("DAILY_NAKSHATRA", {}).get(f"GENERAL_{nak}", "")

    return GocharResult(
        timestamp=now.isoformat(),
        moon=moon,
        sun=sun,
        panchang=panchang,
        all_planets=all_planets,
        moon_from_rashis=moon_from_rashis,
        daily_rashi=daily_rashi,
        daily_nakshatra=daily_nakshatra,
    )


def gochar_to_dict(result: GocharResult) -> dict[str, Any]:
    """Convert GocharResult to a JSON-serializable dictionary."""

    def _pos_dict(p: PlanetPosition) -> dict[str, Any]:
        d: dict[str, Any] = {
            "planet": p.planet,
            "longitude": round(p.longitude, 4),
            "rashi": p.rashi,
            "rashi_name": _RASHI_NAMES.get(p.rashi, p.rashi),
            "rashi_index": p.rashi_index,
            "degree_in_sign": round(p.degree_in_sign, 2),
        }
        if p.nakshatra:
            d["nakshatra"] = p.nakshatra
            d["nakshatra_name"] = _NAKSHATRA_NAMES.get(p.nakshatra, p.nakshatra)
            d["nakshatra_index"] = p.nakshatra_index
            d["nakshatra_pada"] = p.nakshatra_pada
        return d

    return {
        "timestamp": result.timestamp,
        "moon": _pos_dict(result.moon),
        "sun": _pos_dict(result.sun),
        "panchang": {
            "tithi": result.panchang.tithi,
            "nakshatra": result.panchang.nakshatra,
            "yoga": result.panchang.yoga,
            "karana": result.panchang.karana,
            "vara": result.panchang.vara,
        },
        "all_planets": {k: _pos_dict(v) for k, v in result.all_planets.items()},
        "moon_from_rashis": result.moon_from_rashis,
        "daily_rashi": result.daily_rashi,
        "daily_nakshatra": result.daily_nakshatra,
    }

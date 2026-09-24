"""
Daily Panchang Engine - Computes Tithi, Nakshatra, Yoga, Karana, and Muhurta timings.
Uses accurate weekday-based calculations for inauspicious/auspicious times.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import swisseph as swe


@dataclass
class PanchangData:
    date: str
    tithi: Dict[str, Any]
    nakshatra: Dict[str, Any]
    yoga: Dict[str, Any]
    karana: str
    sunrise: str
    sunset: str
    moonrise: str
    moonset: str
    rahu_kaalam: str
    yamagandam: str
    gulika_kaalam: str
    abhijit_muhurta: str
    varjya: str
    weekday: str


TITHI_NAMES = [
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
]

NAKSHATRA_NAMES = [
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

YOGA_NAMES = [
    "Vishkambha",
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

KARANA_NAMES = [
    "Bava",
    "Balava",
    "Kaulava",
    "Taitila",
    "Garaja",
    "Vanija",
    "Vishti (Bhadra)",
    "Shakuni",
    "Chatushpada",
    "Naga",
    "Kimstughna",
]

WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Rahu Kaalam - 8th part of the day (1.5 hours each) by weekday (0=Sunday)
# Traditional order: Sun=8, Mon=2, Tue=7, Wed=5, Thu=6, Fri=4, Sat=3 (using 1-indexed parts)
RAHU_KAALAM_PARTS = {
    0: 8,  # Sunday: 8th part (4:30 PM - 6:00 PM)
    1: 2,  # Monday: 2nd part (7:30 AM - 9:00 AM)
    2: 7,  # Tuesday: 7th part (3:00 PM - 4:30 PM)
    3: 5,  # Wednesday: 5th part (12:00 PM - 1:30 PM)
    4: 6,  # Thursday: 6th part (10:30 AM - 12:00 PM)
    5: 4,  # Friday: 4th part (9:00 AM - 10:30 AM)
    6: 3,  # Saturday: 3rd part (6:00 AM - 7:30 AM)
}

# Yamagandam by weekday
YAMAGANDAM_PARTS = {
    0: 6,  # Sunday: 6th part
    1: 5,  # Monday: 5th part
    2: 4,  # Tuesday: 4th part
    3: 3,  # Wednesday: 3rd part
    4: 2,  # Thursday: 2nd part
    5: 1,  # Friday: 1st part
    6: 7,  # Saturday: 7th part
}

# Gulika Kaalam by weekday
GULIKA_PARTS = {
    0: 7,  # Sunday: 7th part
    1: 6,  # Monday: 6th part
    2: 5,  # Tuesday: 5th part
    3: 4,  # Wednesday: 4th part
    4: 3,  # Thursday: 3rd part
    5: 2,  # Friday: 2nd part
    6: 1,  # Saturday: 1st part
}


def _format_time(dt: datetime) -> str:
    """Format datetime to HH:MM AM/PM."""
    return dt.strftime("%I:%M %p").lstrip("0")


def _jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day to datetime."""
    dt = swe.revjul(jd)
    year, month, day, hour = dt
    hours = int(hour)
    minutes = int((hour - hours) * 60)
    seconds = int(((hour - hours) * 60 - minutes) * 60)
    return datetime(year, month, day, hours, minutes, seconds)


def compute_tithi(jd: float) -> Dict[str, Any]:
    """Compute current Tithi."""
    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]

    diff = (moon_pos - sun_pos) % 360
    tithi_index = int(diff / 12)
    tithi_name = TITHI_NAMES[tithi_index % 15]
    paksha = "Shukla" if tithi_index < 15 else "Krishna"

    return {
        "name": tithi_name,
        "paksha": paksha,
        "full_name": f"{paksha} {tithi_name}",
        "number": (tithi_index % 15) + 1,
    }


def compute_nakshatra(jd: float) -> Dict[str, Any]:
    """Compute current Nakshatra."""
    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    nak_index = int(moon_pos / (360 / 27))
    nak_name = NAKSHATRA_NAMES[nak_index]

    lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    lord = lords[nak_index % 9]

    # Calculate pada (quarter)
    pada_start = nak_index * (360 / 27)
    pada_offset = moon_pos - pada_start
    pada = int(pada_offset / ((360 / 27) / 4)) + 1

    return {"name": nak_name, "lord": lord, "index": nak_index + 1, "pada": pada}


def compute_yoga(jd: float) -> Dict[str, Any]:
    """Compute current Yoga."""
    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]

    combined = (moon_pos + sun_pos) % 360
    yoga_index = int(combined / (360 / 27))
    yoga_name = YOGA_NAMES[yoga_index]

    return {"name": yoga_name, "index": yoga_index + 1}


def compute_karana(jd: float) -> str:
    """Compute current Karana."""
    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]

    diff = (moon_pos - sun_pos) % 360
    karana_index = int(diff / 6) % 11

    return KARANA_NAMES[karana_index]


def compute_sun_times(jd_noon: float, lat: float, lon: float) -> Dict[str, Any]:
    """Compute sunrise and sunset using Swiss Ephemeris."""
    try:
        # Use Swiss Ephemeris for accurate sunrise/sunset
        result = swe.rise_trans(jd_noon - 1, swe.SUN, lon, lat, 0, 0, rsmi=swe.CALC_RISE)
        sunrise_jd = result[0]

        result = swe.rise_trans(jd_noon - 1, swe.SUN, lon, lat, 0, 0, rsmi=swe.CALC_SET)
        sunset_jd = result[0]

        sunrise = _jd_to_datetime(sunrise_jd)
        sunset = _jd_to_datetime(sunset_jd)

        return {
            "sunrise": _format_time(sunrise),
            "sunset": _format_time(sunset),
            "sunrise_jd": sunrise_jd,
            "sunset_jd": sunset_jd,
        }
    except Exception:
        # Fallback to approximate times
        sunrise = _jd_to_datetime(jd_noon - 0.25)
        sunset = _jd_to_datetime(jd_noon + 0.25)
        return {
            "sunrise": _format_time(sunrise),
            "sunset": _format_time(sunset),
            "sunrise_jd": jd_noon - 0.25,
            "sunset_jd": jd_noon + 0.25,
        }


def compute_moon_times(jd_noon: float, lat: float, lon: float) -> Dict[str, Any]:
    """Compute moonrise and moonset."""
    try:
        result = swe.rise_trans(jd_noon - 1, swe.MOON, lon, lat, 0, 0, rsmi=swe.CALC_RISE)
        moonrise_jd = result[0]

        result = swe.rise_trans(jd_noon - 1, swe.MOON, lon, lat, 0, 0, rsmi=swe.CALC_SET)
        moonset_jd = result[0]

        moonrise = _jd_to_datetime(moonrise_jd)
        moonset = _jd_to_datetime(moonset_jd)

        return {"moonrise": _format_time(moonrise), "moonset": _format_time(moonset)}
    except Exception:
        moonrise = _jd_to_datetime(jd_noon - 0.15)
        moonset = _jd_to_datetime(jd_noon + 0.35)
        return {"moonrise": _format_time(moonrise), "moonset": _format_time(moonset)}


def compute_muhurtas(
    sunrise_jd: float, sunset_jd: float, weekday: int
) -> Dict[str, Any]:
    """
    Compute Rahu Kaalam, Yamagandam, Gulika, and Abhijit Muhurta.
    Day is divided into 8 equal parts (each ~1.5 hours).
    """
    day_duration = sunset_jd - sunrise_jd
    part_duration = day_duration / 8

    # Rahu Kaalam
    rahu_part = RAHU_KAALAM_PARTS[weekday]
    rahu_start = sunrise_jd + (rahu_part - 1) * part_duration
    rahu_end = rahu_start + part_duration

    # Yamagandam
    yama_part = YAMAGANDAM_PARTS[weekday]
    yama_start = sunrise_jd + (yama_part - 1) * part_duration
    yama_end = yama_start + part_duration

    # Gulika Kaalam
    gulika_part = GULIKA_PARTS[weekday]
    gulika_start = sunrise_jd + (gulika_part - 1) * part_duration
    gulika_end = gulika_start + part_duration

    # Abhijit Muhurta (45 minutes before and after noon)
    noon_jd = sunrise_jd + (day_duration / 2)
    abhijit_duration = 0.0208333  # ~30 minutes in days
    abhijit_start = noon_jd - abhijit_duration
    abhijit_end = noon_jd + abhijit_duration

    # Varjya (1 hour 30 min after sunrise, inauspicious)
    varjya_start = sunrise_jd + (day_duration * 0.0625)
    varjya_end = varjya_start + (day_duration * 0.0625)

    return {
        "rahu_kaalam": f"{_format_time(_jd_to_datetime(rahu_start))} - {_format_time(_jd_to_datetime(rahu_end))}",
        "yamagandam": f"{_format_time(_jd_to_datetime(yama_start))} - {_format_time(_jd_to_datetime(yama_end))}",
        "gulika_kaalam": f"{_format_time(_jd_to_datetime(gulika_start))} - {_format_time(_jd_to_datetime(gulika_end))}",
        "abhijit_muhurta": f"{_format_time(_jd_to_datetime(abhijit_start))} - {_format_time(_jd_to_datetime(abhijit_end))}",
        "varjya": f"{_format_time(_jd_to_datetime(varjya_start))} - {_format_time(_jd_to_datetime(varjya_end))}",
    }


def compute_daily_panchang(date_str: str, lat: float, lon: float, tz: float = 5.5) -> PanchangData:
    """Compute complete daily panchang."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    jd_noon = swe.julday(dt.year, dt.month, dt.day, 12.0 - tz)

    # Set sidereal mode
    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Compute all elements
    tithi = compute_tithi(jd_noon)
    nakshatra = compute_nakshatra(jd_noon)
    yoga = compute_yoga(jd_noon)
    karana = compute_karana(jd_noon)

    sun_times = compute_sun_times(jd_noon, lat, lon)
    moon_times = compute_moon_times(jd_noon, lat, lon)

    weekday = dt.weekday()  # 0=Monday, 6=Sunday
    # Convert to 0=Sunday for muhurta calculations
    weekday_sunday_first = (weekday + 1) % 7

    muhurtas = compute_muhurtas(
        sun_times["sunrise_jd"], sun_times["sunset_jd"], weekday_sunday_first
    )

    return PanchangData(
        date=date_str,
        tithi=tithi,
        nakshatra=nakshatra,
        yoga=yoga,
        karana=karana,
        sunrise=sun_times["sunrise"],
        sunset=sun_times["sunset"],
        moonrise=moon_times["moonrise"],
        moonset=moon_times["moonset"],
        rahu_kaalam=muhurtas["rahu_kaalam"],
        yamagandam=muhurtas["yamagandam"],
        gulika_kaalam=muhurtas["gulika_kaalam"],
        abhijit_muhurta=muhurtas["abhijit_muhurta"],
        varjya=muhurtas["varjya"],
        weekday=WEEKDAY_NAMES[weekday_sunday_first],
    )

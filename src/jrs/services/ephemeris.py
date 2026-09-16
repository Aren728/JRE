# src/jrs/services/ephemeris.py
"""Swiss Ephemeris calculation utilities for planetary positions.

Provides functions to calculate Julian Day and planetary positions
(Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu/Ketu)
using pyswisseph.
"""

from __future__ import annotations

import datetime
import zoneinfo

import swisseph as swe

from .divisional import enrich_with_divisional_charts

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}


def calculate_planetary_positions(
    query_date: datetime.date,
    query_time_str: str,
    latitude: float,
    longitude: float,
    tz_str: str,
) -> dict:
    """Calculate planetary positions for a given date, time, and location.

    Args:
        query_date: The date to calculate positions for.
        query_time_str: Time string in HH:MM or HH:MM:SS format.
        latitude: Latitude of the location.
        longitude: Longitude of the location.
        tz_str: Timezone string (e.g., "Asia/Kolkata").

    Returns:
        Dictionary containing Julian Day and planetary positions.
    """
    time_parts = list(map(int, query_time_str.split(":")))
    naive_dt = datetime.datetime.combine(
        query_date,
        datetime.time(
            time_parts[0],
            time_parts[1],
            time_parts[2] if len(time_parts) > 2 else 0,
        ),
    )

    tz = zoneinfo.ZoneInfo(tz_str)
    local_dt = naive_dt.replace(tzinfo=tz)
    utc_dt = local_dt.astimezone(datetime.timezone.utc)

    # Convert UTC to Julian Day
    decimal_hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    julian_day = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, decimal_hour)

    positions = {}
    for name, body_code in PLANETS.items():
        res, _retflags, _warning = swe.calc_ut(julian_day, body_code)
        positions[name] = {
            "longitude": round(res[0], 4),
            "latitude": round(res[1], 4),
            "distance_au": round(res[2], 6),
            "speed_long": round(res[3], 4),
        }

    # Ketu is opposite Rahu (+180 deg)
    ketu_long = (positions["Rahu"]["longitude"] + 180.0) % 360.0
    positions["Ketu"] = {
        "longitude": round(ketu_long, 4),
        "latitude": 0.0,
        "distance_au": positions["Rahu"]["distance_au"],
        "speed_long": positions["Rahu"]["speed_long"],
    }

    result = {"julian_day": julian_day, "planets": positions}
    return enrich_with_divisional_charts(result)

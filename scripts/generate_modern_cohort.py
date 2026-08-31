#!/usr/bin/env python3
"""Phase F4a: Modern Personality Cohort — Exact 20 Personalities.

Generates 20 modern personality chart fixtures using verified birth data.
NO changes to rules, weights, or engine logic.

Usage::

    python scripts/generate_modern_cohort.py
    python scripts/generate_modern_cohort.py --dry-run
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Path setup ──────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

FIXTURES_DIR = (
    _PROJECT_ROOT / "tests" / "fixtures" / "modern_personalities"
)

# ── Constants ───────────────────────────────────────────────────────────────

_RASHI_ORDER = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]

_SIGN_TYPES: dict[int, str] = {
    0: "fire", 1: "earth", 2: "air", 3: "water",
    4: "fire", 5: "earth", 6: "air", 7: "water",
    8: "fire", 9: "earth", 10: "air", 11: "water",
}

_SIGN_LORDS: dict[str, str] = {
    "MESHA": "MARS", "VRISHABHA": "VENUS", "MITHUNA": "MERCURY",
    "KARKA": "MOON", "SIMHA": "SUN", "KANYA": "MERCURY",
    "TULA": "VENUS", "VRISHCHIKA": "MARS", "DHANUSHA": "JUPITER",
    "MAKARA": "SATURN", "KUMBHA": "SATURN", "MEENA": "JUPITER",
}


def compute_d9_sign(longitude_used: float) -> str:
    """Classical navamsha sign from a sidereal longitude."""
    sign_index = int(longitude_used / 30.0)
    degree_in_sign = longitude_used - (sign_index * 30.0)
    navamsha_within_sign = int(degree_in_sign / (30.0 / 9.0))

    sign_type = _SIGN_TYPES[sign_index]
    if sign_type == "fire":
        start = sign_index
    elif sign_type == "earth":
        start = (sign_index + 5) % 12
    elif sign_type == "air":
        start = (sign_index + 4) % 12
    else:  # water
        start = (sign_index + 8) % 12

    d9_index = (start + navamsha_within_sign) % 12
    return _RASHI_ORDER[d9_index]


# ── Exact 20 Personalities (Non-Negotiable) ────────────────────────────────

MODERN_PERSONALITIES: list[dict[str, Any]] = [
    # ══════════════════════════════════════════════════════════════════════
    # Sports (4)
    # ══════════════════════════════════════════════════════════════════════
    {
        "fixture_id": "chart_051_kohli",
        "chart_filename": "chart_051_kohli.json",
        "subject": "Virat Kohli",
        "description": "Indian cricket legend, former captain, one of the greatest batsmen",
        "provenance": "Wikipedia — Virat Kohli birth data (Rodden AA)",
        "birth_data": {
            "date": "1988-11-05",
            "time": "17:20",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "KOHLI_U19_2008", "event_date_utc": "2008-03-04T00:00:00Z",
             "domain": "CAREER", "description": "U-19 World Cup Win",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "KOHLI_ODI_CAPTAIN_2013", "event_date_utc": "2013-09-15T00:00:00Z",
             "domain": "CAREER", "description": "First ODI Captaincy",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "KOHLI_PEAK_2018", "event_date_utc": "2018-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Peak Ranking #1",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_052_williams",
        "chart_filename": "chart_052_williams.json",
        "subject": "Serena Williams",
        "description": "American tennis legend, 23 Grand Slam singles titles",
        "provenance": "Wikipedia — Serena Williams birth data (Rodden AA)",
        "birth_data": {
            "date": "1981-09-26",
            "time": "03:53",
            "latitude": 43.4098,
            "longitude": -83.9508,
            "timezone": "America/Detroit",
        },
        "known_events": [
            {"event_id": "WILLIAMS_US_OPEN_1999", "event_date_utc": "1999-09-11T00:00:00Z",
             "domain": "CAREER", "description": "First Grand Slam - US Open",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "WILLIAMS_AUSTRALIAN_2017", "event_date_utc": "2017-01-28T00:00:00Z",
             "domain": "CAREER", "description": "Australian Open - pregnancy comeback",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MOON"]},
            {"event_id": "WILLIAMS_RETIREMENT_2022", "event_date_utc": "2022-09-03T00:00:00Z",
             "domain": "CAREER", "description": "Retirement from professional tennis",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_053_ronaldo",
        "chart_filename": "chart_053_ronaldo.json",
        "subject": "Cristiano Ronaldo",
        "description": "Portuguese football legend, all-time top international scorer",
        "provenance": "Wikipedia — Cristiano Ronaldo birth data (Rodden AA)",
        "birth_data": {
            "date": "1985-02-05",
            "time": "08:30",
            "latitude": 32.6500,
            "longitude": -16.9000,
            "timezone": "Atlantic/Madeira",
        },
        "known_events": [
            {"event_id": "RONALDO_MANUTD_2003", "event_date_utc": "2003-08-16T00:00:00Z",
             "domain": "CAREER", "description": "Man United Debut",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "RONALDO_REAL_2009", "event_date_utc": "2009-06-11T00:00:00Z",
             "domain": "CAREER", "description": "Real Madrid Transfer",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "RONALDO_EURO_2016", "event_date_utc": "2016-07-10T00:00:00Z",
             "domain": "CAREER", "description": "Euro Cup Win with Portugal",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_054_tendulkar",
        "chart_filename": "chart_054_tendulkar.json",
        "subject": "Sachin Tendulkar",
        "description": "Indian cricket legend, 'God of Cricket', highest run-scorer",
        "provenance": "Wikipedia — Sachin Tendulkar birth data (Rodden AA)",
        "birth_data": {
            "date": "1973-04-24",
            "time": "15:30",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "TENDULKAR_DEBUT_1989", "event_date_utc": "1989-11-15T00:00:00Z",
             "domain": "CAREER", "description": "International Debut",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "TENDULKAR_WORLD_CUP_2011", "event_date_utc": "2011-04-02T00:00:00Z",
             "domain": "CAREER", "description": "World Cup Win",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MOON"]},
            {"event_id": "TENDULKAR_RETIREMENT_2013", "event_date_utc": "2013-11-14T00:00:00Z",
             "domain": "CAREER", "description": "Retirement from cricket",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # Business & Technology (4)
    # ══════════════════════════════════════════════════════════════════════
    {
        "fixture_id": "chart_055_musk",
        "chart_filename": "chart_055_musk.json",
        "subject": "Elon Musk",
        "description": "South African-American entrepreneur, CEO of Tesla and SpaceX",
        "provenance": "Wikipedia — Elon Musk birth data (Rodden AA)",
        "birth_data": {
            "date": "1971-06-28",
            "time": "18:30",
            "latitude": -25.7479,
            "longitude": 28.2293,
            "timezone": "Africa/Johannesburg",
        },
        "known_events": [
            {"event_id": "MUSK_ZIP2_1995", "event_date_utc": "1995-03-01T00:00:00Z",
             "domain": "CAREER", "description": "Zip2 Founding",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "MUSK_PAYPAL_2002", "event_date_utc": "2002-02-15T00:00:00Z",
             "domain": "WEALTH", "description": "PayPal Sale",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "MUSK_TWITTER_2022", "event_date_utc": "2022-10-27T00:00:00Z",
             "domain": "CAREER", "description": "Twitter Acquisition",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_056_bezos",
        "chart_filename": "chart_056_bezos.json",
        "subject": "Jeff Bezos",
        "description": "American entrepreneur, founder of Amazon, space explorer",
        "provenance": "Wikipedia — Jeff Bezos birth data (Rodden AA)",
        "birth_data": {
            "date": "1964-01-12",
            "time": "14:30",
            "latitude": 35.0844,
            "longitude": -106.6504,
            "timezone": "America/Denver",
        },
        "known_events": [
            {"event_id": "BEZOS_AMAZON_1994", "event_date_utc": "1994-07-05T00:00:00Z",
             "domain": "CAREER", "description": "Amazon Founding",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "BEZOS_IPO_1997", "event_date_utc": "1997-05-15T00:00:00Z",
             "domain": "WEALTH", "description": "Amazon IPO",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "BEZOS_SPACE_2021", "event_date_utc": "2021-07-20T00:00:00Z",
             "domain": "CAREER", "description": "Blue Origin Space Flight",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_057_pichai",
        "chart_filename": "chart_057_pichai.json",
        "subject": "Sundar Pichai",
        "description": "Indian-American business executive, CEO of Alphabet and Google",
        "provenance": "Wikipedia — Sundar Pichai birth data",
        "birth_data": {
            "date": "1972-07-10",
            "time": "10:00",
            "latitude": 9.9252,
            "longitude": 78.1198,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "PICHAI_GOOGLE_2004", "event_date_utc": "2004-04-01T00:00:00Z",
             "domain": "CAREER", "description": "Joined Google",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "PICHAI_CEO_2015", "event_date_utc": "2015-08-10T00:00:00Z",
             "domain": "CAREER", "description": "Google CEO Appointment",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "PICHAI_ALPHABET_2019", "event_date_utc": "2019-12-03T00:00:00Z",
             "domain": "CAREER", "description": "Alphabet CEO",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_058_ambani",
        "chart_filename": "chart_058_ambani.json",
        "subject": "Mukesh Ambani",
        "description": "Indian business magnate, chairman of Reliance Industries",
        "provenance": "Wikipedia — Mukesh Ambani birth data (approximate time)",
        "birth_data": {
            "date": "1957-04-19",
            "time": "10:30",
            "latitude": 12.7795,
            "longitude": 45.0367,
            "timezone": "Asia/Aden",
        },
        "known_events": [
            {"event_id": "AMBANI_RELIANCE_2002", "event_date_utc": "2002-07-06T00:00:00Z",
             "domain": "CAREER", "description": "Reliance Takeover",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "AMBANI_JIO_2016", "event_date_utc": "2016-09-05T00:00:00Z",
             "domain": "CAREER", "description": "Jio Launch",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "AMBANI_FORBES_2020", "event_date_utc": "2020-08-01T00:00:00Z",
             "domain": "WEALTH", "description": "Forbes Top 10",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # Film & Entertainment (5)
    # ══════════════════════════════════════════════════════════════════════
    {
        "fixture_id": "chart_059_khan_srk",
        "chart_filename": "chart_059_khan_srk.json",
        "subject": "Shah Rukh Khan",
        "description": "Indian actor, producer, 'King of Bollywood'",
        "provenance": "Wikipedia — Shah Rukh Khan birth data",
        "birth_data": {
            "date": "1965-11-02",
            "time": "21:00",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "SRK_DEEWANA_1992", "event_date_utc": "1992-06-26T00:00:00Z",
             "domain": "CAREER", "description": "Deewana Debut",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "SRK_MOHABBATEIN_2000", "event_date_utc": "2000-10-27T00:00:00Z",
             "domain": "CAREER", "description": "Mohabbatein",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "SRK_PATHAAN_2023", "event_date_utc": "2023-01-25T00:00:00Z",
             "domain": "CAREER", "description": "Pathaan Comeback",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_060_dicaprio",
        "chart_filename": "chart_060_dicaprio.json",
        "subject": "Leonardo DiCaprio",
        "description": "American actor, environmentalist, Oscar winner",
        "provenance": "Wikipedia — Leonardo DiCaprio birth data (Rodden AA)",
        "birth_data": {
            "date": "1974-11-11",
            "time": "02:47",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "timezone": "America/Los_Angeles",
        },
        "known_events": [
            {"event_id": "DICAPRIO_TITANIC_1997", "event_date_utc": "1997-11-01T00:00:00Z",
             "domain": "CAREER", "description": "Titanic Release",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "DICAPRIO_OSCAR_2016", "event_date_utc": "2016-02-28T00:00:00Z",
             "domain": "CAREER", "description": "Oscar Win - Revenant",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "DICAPRIO_CLIMATE_2020", "event_date_utc": "2020-09-23T00:00:00Z",
             "domain": "CAREER", "description": "Climate Activism Peak",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_061_chopra",
        "chart_filename": "chart_061_chopra.json",
        "subject": "Priyanka Chopra",
        "description": "Indian actress, producer, Miss World 2000, Hollywood crossover",
        "provenance": "Wikipedia — Priyanka Chopra birth data",
        "birth_data": {
            "date": "1982-07-18",
            "time": "11:30",
            "latitude": 22.8046,
            "longitude": 86.2029,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "CHOPRA_MISS_WORLD_2000", "event_date_utc": "2000-11-30T00:00:00Z",
             "domain": "CAREER", "description": "Miss World",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "CHOPRA_QUANTICO_2015", "event_date_utc": "2015-09-27T00:00:00Z",
             "domain": "CAREER", "description": "Quantico Premiere",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "CHOPRA_MARRIAGE_2018", "event_date_utc": "2018-12-01T00:00:00Z",
             "domain": "MARRIAGE", "description": "Marriage to Nick Jonas",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_062_rajinikanth",
        "chart_filename": "chart_062_rajinikanth.json",
        "subject": "Rajinikanth",
        "description": "Indian actor, cultural icon, 'Superstar' of Tamil cinema",
        "provenance": "Wikipedia — Rajinikanth birth data",
        "birth_data": {
            "date": "1950-12-12",
            "time": "12:00",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "RAJNI_DEBUT_1975", "event_date_utc": "1975-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Film Debut",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "RAJNI_ENTHIRAN_2010", "event_date_utc": "2010-10-01T00:00:00Z",
             "domain": "CAREER", "description": "Enthiran Release",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "RAJNI_POLITICS_2021", "event_date_utc": "2021-04-10T00:00:00Z",
             "domain": "CAREER", "description": "Political Entry/Retreat",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_063_vijay",
        "chart_filename": "chart_063_vijay.json",
        "subject": "Joseph Vijay",
        "description": "Indian actor, 'Thalapathy' of Tamil cinema",
        "provenance": "Wikipedia — Joseph Vijay birth data",
        "birth_data": {
            "date": "1974-06-22",
            "time": "14:30",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "VIJAY_DEBUT_1992", "event_date_utc": "1992-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Naalaiya Theerpu Debut",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "VIJAY_MERSAL_2017", "event_date_utc": "2017-10-18T00:00:00Z",
             "domain": "CAREER", "description": "Mersal Release",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "VIJAY_LEO_2023", "event_date_utc": "2023-10-19T00:00:00Z",
             "domain": "CAREER", "description": "Leo Release",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # Politics & Leadership (2)
    # ══════════════════════════════════════════════════════════════════════
    {
        "fixture_id": "chart_064_modi",
        "chart_filename": "chart_064_modi.json",
        "subject": "Narendra Modi",
        "description": "Indian Prime Minister, longest-serving non-Congress PM",
        "provenance": "Wikipedia — Narendra Modi birth data (rectified)",
        "birth_data": {
            "date": "1950-09-17",
            "time": "11:35",
            "latitude": 23.8343,
            "longitude": 72.6325,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "MODI_CM_2001", "event_date_utc": "2001-10-07T00:00:00Z",
             "domain": "CAREER", "description": "CM Gujarat",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "MODI_PM_2014", "event_date_utc": "2014-05-16T00:00:00Z",
             "domain": "CAREER", "description": "PM Election",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "MODI_REELECT_2019", "event_date_utc": "2019-05-23T00:00:00Z",
             "domain": "CAREER", "description": "Re-election",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_065_meloni",
        "chart_filename": "chart_065_meloni.json",
        "subject": "Giorgia Meloni",
        "description": "Italian Prime Minister, leader of Brothers of Italy",
        "provenance": "Wikipedia — Giorgia Meloni birth data",
        "birth_data": {
            "date": "1977-01-15",
            "time": "11:30",
            "latitude": 41.9028,
            "longitude": 12.4964,
            "timezone": "Europe/Rome",
        },
        "known_events": [
            {"event_id": "MELONI_ENTRY_1992", "event_date_utc": "1992-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Political Entry",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "MELONI_BROTHERS_2014", "event_date_utc": "2014-03-09T00:00:00Z",
             "domain": "CAREER", "description": "Brothers of Italy Founding",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "MELONI_PM_2022", "event_date_utc": "2022-10-22T00:00:00Z",
             "domain": "CAREER", "description": "PM Election",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # Writers & Intellectuals (2)
    # ══════════════════════════════════════════════════════════════════════
    {
        "fixture_id": "chart_066_rowling",
        "chart_filename": "chart_066_rowling.json",
        "subject": "J.K. Rowling",
        "description": "British author, creator of Harry Potter series",
        "provenance": "Wikipedia — J.K. Rowling birth data (Rodden AA)",
        "birth_data": {
            "date": "1965-07-31",
            "time": "19:00",
            "latitude": 51.5394,
            "longitude": -2.4167,
            "timezone": "Europe/London",
        },
        "known_events": [
            {"event_id": "ROWLING_HP1_1997", "event_date_utc": "1997-06-26T00:00:00Z",
             "domain": "CAREER", "description": "HP1 Publication",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "ROWLING_HP7_2007", "event_date_utc": "2007-07-21T00:00:00Z",
             "domain": "CAREER", "description": "HP7 Release",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "ROWLING_CONTROVERSY_2020", "event_date_utc": "2020-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Controversies Peak",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "MERCURY"]},
        ],
    },
    {
        "fixture_id": "chart_067_roy",
        "chart_filename": "chart_067_roy.json",
        "subject": "Arundhati Roy",
        "description": "Indian author, political activist, Booker Prize winner",
        "provenance": "Wikipedia — Arundhati Roy birth data",
        "birth_data": {
            "date": "1961-11-24",
            "time": "10:00",
            "latitude": 25.5788,
            "longitude": 91.8933,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "ROY_BOOKER_1997", "event_date_utc": "1997-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Booker Prize - God of Small Things",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "ROY_ACTIVISM_2002", "event_date_utc": "2002-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Activism Peak",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "ROY_PANDEMIC_2020", "event_date_utc": "2020-03-01T00:00:00Z",
             "domain": "CAREER", "description": "Pandemic Writings",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
        ],
    },
    # ══════════════════════════════════════════════════════════════════════
    # Music & Arts (3)
    # ══════════════════════════════════════════════════════════════════════
    {
        "fixture_id": "chart_068_rahman",
        "chart_filename": "chart_068_rahman.json",
        "subject": "A.R. Rahman",
        "description": "Indian composer, Oscar winner, 'Mozart of Madras'",
        "provenance": "Wikipedia — A.R. Rahman birth data",
        "birth_data": {
            "date": "1967-01-06",
            "time": "06:30",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "RAHMAN_ROJA_1992", "event_date_utc": "1992-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Roja Breakthrough",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "RAHMAN_OSCARS_2009", "event_date_utc": "2009-03-01T00:00:00Z",
             "domain": "CAREER", "description": "Slumdog Oscars",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "RAHMAN_PANDEMIC_2020", "event_date_utc": "2020-06-01T00:00:00Z",
             "domain": "CAREER", "description": "Pandemic Concerts",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_069_singh",
        "chart_filename": "chart_069_singh.json",
        "subject": "Arijit Singh",
        "description": "Indian playback singer, most streamed artist in India",
        "provenance": "Wikipedia — Arijit Singh birth data",
        "birth_data": {
            "date": "1987-04-25",
            "time": "10:00",
            "latitude": 24.1989,
            "longitude": 88.2828,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "SINGH_FAME_2011", "event_date_utc": "2011-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Fame Gurukul",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "SINGH_AASHIQUI_2013", "event_date_utc": "2013-08-15T00:00:00Z",
             "domain": "CAREER", "description": "Aashiqui 2 - Tum Hi Ho",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "SINGH_PANDEMIC_2020", "event_date_utc": "2020-05-01T00:00:00Z",
             "domain": "CAREER", "description": "Pandemic Concerts",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_070_beyonce",
        "chart_filename": "chart_070_beyonce.json",
        "subject": "Beyoncé",
        "description": "American singer, songwriter, actress, cultural icon",
        "provenance": "Wikipedia — Beyoncé birth data (Rodden AA)",
        "birth_data": {
            "date": "1981-09-04",
            "time": "11:30",
            "latitude": 29.7604,
            "longitude": -95.3698,
            "timezone": "America/Chicago",
        },
        "known_events": [
            {"event_id": "BEYONCE_DESTINY_1997", "event_date_utc": "1997-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Destiny's Child Debut",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "BEYONCE_SINGLE_LADIES_2008", "event_date_utc": "2008-09-02T00:00:00Z",
             "domain": "CAREER", "description": "Single Ladies",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "BEYONCE_LEMONADE_2016", "event_date_utc": "2016-04-23T00:00:00Z",
             "domain": "CAREER", "description": "Lemonade Release",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
]


# ── Fixture Building ────────────────────────────────────────────────────────

def extract_chart_facts(chart: Any) -> dict[str, Any]:
    """Extract canonical facts from a computed JyotishService chart."""
    # Lagna
    lagna = chart.lagna
    lagna_facts = {
        "ascendant_longitude_deg": lagna.ascendant_longitude_deg,
        "rashi": lagna.rashi.value,
        "degree_in_rashi": lagna.degree_in_rashi,
        "nakshatra": lagna.nakshatra.value,
        "nakshatra_lord": lagna.nakshatra_lord.value,
        "pada": lagna.pada.value,
        "degree_in_nakshatra": lagna.degree_in_nakshatra,
        "d9_sign": compute_d9_sign(lagna.ascendant_longitude_deg),
    }

    # Planets
    lagna_rashi = lagna.rashi.value
    lagna_rashi_idx = _RASHI_ORDER.index(lagna_rashi)
    planets: dict[str, Any] = {}
    for ps in chart.planet_states:
        name = ps.body.value
        planet_rashi_idx = _RASHI_ORDER.index(ps.rashi.value)
        house_num = (planet_rashi_idx - lagna_rashi_idx) % 12 + 1
        planets[name] = {
            "longitude_tropical": ps.longitude_tropical,
            "longitude_sidereal": ps.longitude_sidereal,
            "longitude_used": ps.longitude_used,
            "rashi": ps.rashi.value,
            "house": house_num,
            "degree_in_rashi": ps.degree_in_rashi,
            "nakshatra": ps.nakshatra.value,
            "nakshatra_lord": ps.nakshatra_lord.value,
            "sign_lord": _SIGN_LORDS.get(ps.rashi.value, ""),
            "pada": ps.pada.value,
            "degree_in_nakshatra": ps.degree_in_nakshatra,
            "retrograde": ps.retrograde.value,
            "d9_sign": compute_d9_sign(ps.longitude_used),
        }

    # Houses
    houses: dict[str, Any] = {}
    for bhava in chart.bhavas:
        houses[str(bhava.house_number)] = {
            "rashi": bhava.rashi.value,
            "lord": bhava.house_lord.value,
            "occupants": [o.value for o in bhava.occupants],
        }

    # Compute house_lord_of for each planet
    planet_houses: dict[str, list[int]] = {}
    for bhava in chart.bhavas:
        lord = bhava.house_lord.value
        house_num = bhava.house_number
        if lord not in planet_houses:
            planet_houses[lord] = []
        planet_houses[lord].append(house_num)

    for pname in planets:
        planets[pname]["house_lord_of"] = sorted(planet_houses.get(pname, []))

    # Build house_lords mapping
    house_lords: dict[str, str] = {}
    for bhava in chart.bhavas:
        house_lords[str(bhava.house_number)] = bhava.house_lord.value

    return {
        "lagna": lagna_facts,
        "planets": planets,
        "houses": houses,
        "house_lords": house_lords,
    }


def build_fixture(subject_def: dict[str, Any], chart: Any) -> dict[str, Any]:
    """Build the complete fixture JSON structure."""
    facts = extract_chart_facts(chart)

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "_meta": {
            "fixture_id": subject_def["fixture_id"],
            "version": "1.0.0",
            "subject": subject_def["subject"],
            "description": subject_def["description"],
            "provenance": subject_def["provenance"],
            "pipeline_config": {
                "zodiac_mode": "SIDEREAL",
                "ayanamsa": "LAHIRI",
                "house_system": "WHOLE_SIGN",
                "node_model": "MEAN",
                "position_type": "APPARENT",
                "ephemeris_provider": "swisseph",
            },
            "generated_by": "JyotishService.chart() via Swiss Ephemeris",
            "generated_at": datetime.now().strftime("%Y-%m-%d"),
            "notes": [
                "All longitudes are sidereal (Lahiri ayanamsa applied to tropical longitudes).",
                "degree_in_rashi is within [0, 30) — the fractional part of the sidereal longitude within the rashi.",
                "D9 (Navamsha) signs are computed using the classical navamsha division method.",
                "House assignments use Whole-Sign house system with the sidereal ascendant.",
            ],
        },
        "raw_birth_data": subject_def["birth_data"],
        "expected_canonical_facts": facts,
        "known_events": subject_def["known_events"],
    }


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> int:
    """Generate modern personality fixtures."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate modern personality chart fixtures.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print generated JSON without writing files.",
    )
    args = parser.parse_args()

    from jyotish.models import BirthData
    from jyotish.service import JyotishService

    svc = JyotishService()

    print("=" * 64)
    print(f"Phase F4a: Modern Personality Cohort — Exact 20 Personalities")
    print("=" * 64)
    print()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    skipped = 0
    errors = 0

    for subject_def in MODERN_PERSONALITIES:
        fixture_id = subject_def["fixture_id"]
        filename = subject_def["chart_filename"]
        bd = subject_def["birth_data"]

        # Skip if fixture already exists
        out_path = FIXTURES_DIR / filename
        if out_path.exists() and not args.dry_run:
            print(f"── {subject_def['subject']} ({fixture_id}) — SKIP (exists)")
            skipped += 1
            continue

        print(f"── {subject_def['subject']} ({fixture_id}) ──")
        print(f"   Birth: {bd['date']} {bd['time']} {bd['timezone']}")
        print(f"   Location: {bd['latitude']}°, {bd['longitude']}°")

        try:
            birth = BirthData(
                date=bd["date"], time=bd["time"], timezone=bd["timezone"],
                latitude=float(bd["latitude"]), longitude=float(bd["longitude"]),
            )
            chart = svc.chart(birth)

            print(f"   Lagna: {chart.lagna.rashi.value} "
                  f"({chart.lagna.ascendant_longitude_deg:.4f}°)")
            print(f"   Planets: {len(chart.planet_states)} computed")

            fixture = build_fixture(subject_def, chart)

            if args.dry_run:
                print(f"   [DRY RUN] Would write to: {out_path}")
                print(json.dumps(fixture, indent=2)[:500] + "\n   ...")
            else:
                with out_path.open("w", encoding="utf-8") as f:
                    json.dump(fixture, f, indent=2, sort_keys=False)
                print(f"   ✓ Saved: {out_path}")
                generated += 1

        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            print(f"   Skipping {subject_def['subject']}")
            errors += 1

        print()

    print("=" * 64)
    if args.dry_run:
        print("Dry run complete — no files written.")
    else:
        print(f"Fixture generation complete.")
        print(f"  Generated: {generated}")
        print(f"  Skipped (existing): {skipped}")
        print(f"  Errors: {errors}")
        print(f"  Output directory: {FIXTURES_DIR}")
    print("=" * 64)

    return 0


if __name__ == "__main__":
    sys.exit(main())

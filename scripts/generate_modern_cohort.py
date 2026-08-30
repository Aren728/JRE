#!/usr/bin/env python3
"""Phase F4: Modern Personality Cohort — Fixture Generator.

Generates 20 modern personality chart fixtures for validation.
Uses the existing JRE fact-generation pipeline (JyotishService + Swiss Ephemeris).

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


# ── Modern Personalities (20 subjects) ─────────────────────────────────────

MODERN_PERSONALITIES: list[dict[str, Any]] = [
    {
        "fixture_id": "chart_051_kohli",
        "chart_filename": "chart_051_kohli.json",
        "subject": "Virat Kohli",
        "description": "Indian cricket legend, former captain, one of the greatest batsmen",
        "provenance": "Wikipedia — Virat Kohli birth data",
        "birth_data": {
            "date": "1988-11-05",
            "time": "17:20",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "KOHLI_U19_2008", "event_date_utc": "2008-03-02T00:00:00Z",
             "domain": "CAREER", "description": "U-19 World Cup captaincy win",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "KOHLI_ODI_CAPTAIN_2013", "event_date_utc": "2013-09-15T00:00:00Z",
             "domain": "CAREER", "description": "First ODI captaincy appointment",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "KOHLI_PEAK_2018", "event_date_utc": "2018-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Peak ICC ranking #1 across all formats",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_052_ambani",
        "chart_filename": "chart_052_ambani.json",
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
             "domain": "CAREER", "description": "Took over Reliance Industries after father's death",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "AMBANI_JIO_2016", "event_date_utc": "2016-09-05T00:00:00Z",
             "domain": "CAREER", "description": "Launched Reliance Jio, disrupted telecom industry",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "AMBANI_FORBES_2020", "event_date_utc": "2020-08-01T00:00:00Z",
             "domain": "WEALTH", "description": "Forbes Top 10 richest globally",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_053_tendulkar",
        "chart_filename": "chart_053_tendulkar.json",
        "subject": "Sachin Tendulkar",
        "description": "Indian cricket legend, 'God of Cricket', highest run-scorer in internationals",
        "provenance": "Wikipedia — Sachin Tendulkar birth data",
        "birth_data": {
            "date": "1973-04-24",
            "time": "07:20",
            "latitude": 19.0760,
            "longitude": 72.8777,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "TENDULKAR_DEBUT_1989", "event_date_utc": "1989-11-15T00:00:00Z",
             "domain": "CAREER", "description": "International cricket debut at age 16",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "TENDULKAR_WORLD_CUP_2011", "event_date_utc": "2011-04-02T00:00:00Z",
             "domain": "CAREER", "description": "Won Cricket World Cup, fulfilled lifelong dream",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MOON"]},
            {"event_id": "TENDULKAR_RETIREMENT_2013", "event_date_utc": "2013-11-16T00:00:00Z",
             "domain": "CAREER", "description": "Retired from international cricket with record books",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_054_oprah",
        "chart_filename": "chart_054_oprah.json",
        "subject": "Oprah Winfrey",
        "description": "American media mogul, talk show host, philanthropist, billionaire",
        "provenance": "Wikipedia — Oprah Winfrey birth data",
        "birth_data": {
            "date": "1954-01-29",
            "time": "04:30",
            "latitude": 35.1495,
            "longitude": -90.0490,
            "timezone": "America/Chicago",
        },
        "known_events": [
            {"event_id": "OPRAH_SHOW_1986", "event_date_utc": "1986-09-08T00:00:00Z",
             "domain": "CAREER", "description": "The Oprah Winfrey Show goes national",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "OPRAH_BILLIONAIRE_2003", "event_date_utc": "2003-02-01T00:00:00Z",
             "domain": "WEALTH", "description": "Became first Black female billionaire",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "OPRAH_NETWORK_2011", "event_date_utc": "2011-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Launched OWN: Oprah Winfrey Network",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_055_bezos",
        "chart_filename": "chart_055_bezos.json",
        "subject": "Jeff Bezos",
        "description": "American entrepreneur, founder of Amazon, space explorer",
        "provenance": "Wikipedia — Jeff Bezos birth data",
        "birth_data": {
            "date": "1964-01-12",
            "time": "03:00",
            "latitude": 39.0438,
            "longitude": -77.4874,
            "timezone": "America/New_York",
        },
        "known_events": [
            {"event_id": "BEZOS_AMAZON_1994", "event_date_utc": "1994-07-05T00:00:00Z",
             "domain": "CAREER", "description": "Founded Amazon in Bellevue, Washington",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "BEZOS_BILLIONAIRE_2017", "event_date_utc": "2017-10-27T00:00:00Z",
             "domain": "WEALTH", "description": "Became world's richest person",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "BEZOS_SPACE_2021", "event_date_utc": "2021-07-20T00:00:00Z",
             "domain": "CAREER", "description": "Blue Origin space flight",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_056_beyonce",
        "chart_filename": "chart_056_beyonce.json",
        "subject": "Beyoncé Knowles",
        "description": "American singer, songwriter, actress, cultural icon",
        "provenance": "Wikipedia — Beyoncé birth data",
        "birth_data": {
            "date": "1981-09-04",
            "time": "10:00",
            "latitude": 29.7604,
            "longitude": -95.3698,
            "timezone": "America/Chicago",
        },
        "known_events": [
            {"event_id": "BEYONCE_DESTINY_1999", "event_date_utc": "1999-11-15T00:00:00Z",
             "domain": "CAREER", "description": "Destiny's Child wins first Grammy",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "BEYONCE_SOLO_2003", "event_date_utc": "2003-06-20T00:00:00Z",
             "domain": "CAREER", "description": "Solo debut 'Dangerously in Love' wins 5 Grammys",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "BEYONCE_SUPERBOWL_2013", "event_date_utc": "2013-02-03T00:00:00Z",
             "domain": "CAREER", "description": "Super Bowl XLVII halftime show performance",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "SUN"]},
        ],
    },
    {
        "fixture_id": "chart_057_messi",
        "chart_filename": "chart_057_messi.json",
        "subject": "Lionel Messi",
        "description": "Argentine football legend, World Cup winner, 8 Ballon d'Or",
        "provenance": "Wikipedia — Lionel Messi birth data",
        "birth_data": {
            "date": "1987-06-24",
            "time": "06:00",
            "latitude": -32.8895,
            "longitude": -68.8255,
            "timezone": "America/Argentina/Mendoza",
        },
        "known_events": [
            {"event_id": "MESSI_DEBUT_2004", "event_date_utc": "2004-10-16T00:00:00Z",
             "domain": "CAREER", "description": "FC Barcelona first-team debut at age 17",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "MESSI_BALLONDOR_2009", "event_date_utc": "2009-12-01T00:00:00Z",
             "domain": "CAREER", "description": "First Ballon d'Or award",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "MESSI_WORLDCUP_2022", "event_date_utc": "2022-12-18T00:00:00Z",
             "domain": "CAREER", "description": "FIFA World Cup victory with Argentina",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_058_malala",
        "chart_filename": "chart_058_malala.json",
        "subject": "Malala Yousafzai",
        "description": "Pakistani activist for female education, youngest Nobel laureate",
        "provenance": "Wikipedia — Malala Yousafzai birth data",
        "birth_data": {
            "date": "1997-07-12",
            "time": "12:00",
            "latitude": 34.1683,
            "longitude": 71.7489,
            "timezone": "Asia/Karachi",
        },
        "known_events": [
            {"event_id": "MALALA_BLOG_2009", "event_date_utc": "2009-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Started BBC Urdu blog about life under Taliban",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "MALALA_SHOOTING_2012", "event_date_utc": "2012-10-09T00:00:00Z",
             "domain": "HEALTH", "description": "Shot by Taliban, survived and became global symbol",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "MARS"]},
            {"event_id": "MALALA_NOBEL_2014", "event_date_utc": "2014-10-10T00:00:00Z",
             "domain": "CAREER", "description": "Awarded Nobel Peace Prize at age 17",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_059_zuckerberg",
        "chart_filename": "chart_059_zuckerberg.json",
        "subject": "Mark Zuckerberg",
        "description": "American entrepreneur, co-founder of Meta (Facebook)",
        "provenance": "Wikipedia — Mark Zuckerberg birth data",
        "birth_data": {
            "date": "1984-05-14",
            "time": "08:00",
            "latitude": 40.7608,
            "longitude": -73.9776,
            "timezone": "America/New_York",
        },
        "known_events": [
            {"event_id": "ZUCK_FACEBOOK_2004", "event_date_utc": "2004-02-04T00:00:00Z",
             "domain": "CAREER", "description": "Launched Facebook from Harvard dorm",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "ZUCK_IPO_2012", "event_date_utc": "2012-05-18T00:00:00Z",
             "domain": "WEALTH", "description": "Facebook IPO, became billionaire",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "ZUCK_META_2021", "event_date_utc": "2021-10-28T00:00:00Z",
             "domain": "CAREER", "description": "Rebranded Facebook to Meta, pivot to metaverse",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_060_swift",
        "chart_filename": "chart_060_swift.json",
        "subject": "Taylor Swift",
        "description": "American singer-songwriter, highest-grossing touring artist",
        "provenance": "Wikipedia — Taylor Swift birth data",
        "birth_data": {
            "date": "1989-12-13",
            "time": "08:30",
            "latitude": 35.1495,
            "longitude": -90.0490,
            "timezone": "America/Chicago",
        },
        "known_events": [
            {"event_id": "SWIFT_DEBUT_2006", "event_date_utc": "2006-10-24T00:00:00Z",
             "domain": "CAREER", "description": "Self-titled debut album released",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "SWIFT_1989_2014", "event_date_utc": "2014-10-27T00:00:00Z",
             "domain": "CAREER", "description": "'1989' album breaks sales records",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "SWIFT_ERAS_2023", "event_date_utc": "2023-03-17T00:00:00Z",
             "domain": "CAREER", "description": "Eras Tour becomes highest-grossing concert tour ever",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_061_gates",
        "chart_filename": "chart_061_gates.json",
        "subject": "Bill Gates",
        "description": "American entrepreneur, co-founder of Microsoft, philanthropist",
        "provenance": "Wikipedia — Bill Gates birth data",
        "birth_data": {
            "date": "1955-10-28",
            "time": "22:00",
            "latitude": 47.6062,
            "longitude": -122.3321,
            "timezone": "America/Los_Angeles",
        },
        "known_events": [
            {"event_id": "GATES_MICROSOFT_1975", "event_date_utc": "1975-04-04T00:00:00Z",
             "domain": "CAREER", "description": "Co-founded Microsoft with Paul Allen",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "GATES_RICHEST_1995", "event_date_utc": "1995-07-17T00:00:00Z",
             "domain": "WEALTH", "description": "Became world's richest person (Forbes)",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "GATES_PHILANTHROPY_2000", "event_date_utc": "2000-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Founded Bill & Melinda Gates Foundation",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_062_mandela_modern",
        "chart_filename": "chart_062_mandela_modern.json",
        "subject": "Nelson Mandela (Validation)",
        "description": "South African anti-apartheid leader, first Black president (validation fixture)",
        "provenance": "Wikipedia — Nelson Mandela birth data",
        "birth_data": {
            "date": "1918-07-18",
            "time": "14:30",
            "latitude": -32.8895,
            "longitude": 25.5186,
            "timezone": "Africa/Johannesburg",
        },
        "known_events": [
            {"event_id": "MANDELA_FREEDOM_1990", "event_date_utc": "1990-02-11T00:00:00Z",
             "domain": "CAREER", "description": "Released from prison after 27 years",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "MANDELA_PRESIDENT_1994", "event_date_utc": "1994-05-10T00:00:00Z",
             "domain": "CAREER", "description": "Inaugurated as first Black president of South Africa",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "MANDELA_NOBEL_1993", "event_date_utc": "1993-10-15T00:00:00Z",
             "domain": "CAREER", "description": "Nobel Peace Prize with de Klerk",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_063_king",
        "chart_filename": "chart_063_king.json",
        "subject": "Martin Luther King Jr.",
        "description": "American civil rights leader, Nobel Peace Prize laureate",
        "provenance": "Wikipedia — Martin Luther King Jr. birth data",
        "birth_data": {
            "date": "1929-01-15",
            "time": "12:00",
            "latitude": 33.7490,
            "longitude": -84.3880,
            "timezone": "America/New_York",
        },
        "known_events": [
            {"event_id": "KING_MARCH_1963", "event_date_utc": "1963-08-28T00:00:00Z",
             "domain": "CAREER", "description": "March on Washington, 'I Have a Dream' speech",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "KING_NOBEL_1964", "event_date_utc": "1964-12-10T00:00:00Z",
             "domain": "CAREER", "description": "Awarded Nobel Peace Prize",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "KING_ASSASSINATION_1968", "event_date_utc": "1968-04-04T00:00:00Z",
             "domain": "HEALTH", "description": "Assassinated in Memphis, Tennessee",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "MARS"]},
        ],
    },
    {
        "fixture_id": "chart_064_curie_modern",
        "chart_filename": "chart_064_curie_modern.json",
        "subject": "Marie Curie (Validation)",
        "description": "Polish-French physicist, first woman to win Nobel Prize (validation fixture)",
        "provenance": "Wikipedia — Marie Curie birth data",
        "birth_data": {
            "date": "1867-11-07",
            "time": "12:00",
            "latitude": 52.2297,
            "longitude": 21.0122,
            "timezone": "Europe/Warsaw",
        },
        "known_events": [
            {"event_id": "CURIE_PHD_1898", "event_date_utc": "1898-06-25T00:00:00Z",
             "domain": "CAREER", "description": "Discovered polonium and radium",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "CURIE_NOBEL_1903", "event_date_utc": "1903-11-05T00:00:00Z",
             "domain": "CAREER", "description": "First Nobel Prize in Physics (shared with Pierre)",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "CURIE_NOBEL2_1911", "event_date_utc": "1911-12-10T00:00:00Z",
             "domain": "CAREER", "description": "Second Nobel Prize in Chemistry (solo)",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MERCURY"]},
        ],
    },
    {
        "fixture_id": "chart_065_musk",
        "chart_filename": "chart_065_musk.json",
        "subject": "Elon Musk",
        "description": "South African-American entrepreneur, CEO of Tesla and SpaceX",
        "provenance": "Wikipedia — Elon Musk birth data",
        "birth_data": {
            "date": "1971-06-28",
            "time": "02:30",
            "latitude": -25.7479,
            "longitude": 28.2293,
            "timezone": "Africa/Johannesburg",
        },
        "known_events": [
            {"event_id": "MUSK_PAYPAL_2002", "event_date_utc": "2002-02-01T00:00:00Z",
             "domain": "WEALTH", "description": "Sold PayPal to eBay for $1.5 billion",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "MUSK_SPACEX_2008", "event_date_utc": "2008-09-28T00:00:00Z",
             "domain": "CAREER", "description": "SpaceX Falcon 1 reaches orbit",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "MUSK_RICHEST_2021", "event_date_utc": "2021-01-07T00:00:00Z",
             "domain": "WEALTH", "description": "Became world's richest person",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_066_ratan_tata",
        "chart_filename": "chart_066_ratan_tata.json",
        "subject": "Ratan Tata",
        "description": "Indian industrialist, chairman emeritus of Tata Group",
        "provenance": "Wikipedia — Ratan Tata birth data",
        "birth_data": {
            "date": "1937-12-28",
            "time": "15:00",
            "latitude": 21.1702,
            "longitude": 72.8311,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "TATA_CHAIRMAN_1991", "event_date_utc": "1991-04-01T00:00:00Z",
             "domain": "CAREER", "description": "Became chairman of Tata Group",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "TATA_JAGUAR_2008", "event_date_utc": "2008-06-02T00:00:00Z",
             "domain": "CAREER", "description": "Acquired Jaguar Land Rover",
             "yoga_types": ["RAJA", "DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "TATA_NANO_2008", "event_date_utc": "2008-01-10T00:00:00Z",
             "domain": "CAREER", "description": "Launched Tata Nano, world's cheapest car",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MERCURY"]},
        ],
    },
    {
        "fixture_id": "chart_067_ruth_bader",
        "chart_filename": "chart_067_ruth_bader.json",
        "subject": "Ruth Bader Ginsburg",
        "description": "American Supreme Court Justice, gender equality champion",
        "provenance": "Wikipedia — Ruth Bader Ginsburg birth data",
        "birth_data": {
            "date": "1933-03-15",
            "time": "17:00",
            "latitude": 40.6782,
            "longitude": -73.9442,
            "timezone": "America/New_York",
        },
        "known_events": [
            {"event_id": "RBG_JUDGE_1980", "event_date_utc": "1980-06-01T00:00:00Z",
             "domain": "CAREER", "description": "Appointed to U.S. Court of Appeals",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "RBG_SCOTUS_1993", "event_date_utc": "1993-08-10T00:00:00Z",
             "domain": "CAREER", "description": "Confirmed to Supreme Court",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "RBG_NOTORIOUS_2013", "event_date_utc": "2013-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Became cultural icon 'Notorious RBG'",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
        ],
    },
    {
        "fixture_id": "chart_068_ambedkar",
        "chart_filename": "chart_068_ambedkar.json",
        "subject": "B.R. Ambedkar",
        "description": "Indian jurist, architect of the Indian Constitution, social reformer",
        "provenance": "Wikipedia — B.R. Ambedkar birth data",
        "birth_data": {
            "date": "1891-04-14",
            "time": "12:00",
            "latitude": 20.9336,
            "longitude": 77.7643,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "AMBEDKAR_PHD_1923", "event_date_utc": "1923-06-01T00:00:00Z",
             "domain": "CAREER", "description": "Earned PhD from Columbia University",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "AMBEDKAR_CONSTITUTION_1950", "event_date_utc": "1950-01-26T00:00:00Z",
             "domain": "CAREER", "description": "Indian Constitution came into effect, drafted by Ambedkar",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "AMBEDKAR_DEATH_1956", "event_date_utc": "1956-12-06T00:00:00Z",
             "domain": "HEALTH", "description": "Passed away in Delhi",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "MARS"]},
        ],
    },
    {
        "fixture_id": "chart_069_nagarjuna",
        "chart_filename": "chart_069_nagarjuna.json",
        "subject": "Akkineni Nagarjuna",
        "description": "Indian actor, producer, entrepreneur, Telugu cinema icon",
        "provenance": "Wikipedia — Nagarjuna birth data",
        "birth_data": {
            "date": "1959-08-29",
            "time": "02:30",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "NAGARJUNA_DEBUT_1986", "event_date_utc": "1986-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Breakthrough role in 'Vikram'",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "NAGARJUNA_SHIVA_1989", "event_date_utc": "1989-03-15T00:00:00Z",
             "domain": "CAREER", "description": "Blockbuster 'Shiva' established stardom",
             "yoga_types": ["RAJA"], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "NAGARJUNA_BUSINESS_2005", "event_date_utc": "2005-01-01T00:00:00Z",
             "domain": "WEALTH", "description": "Expanded into film production and business",
             "yoga_types": ["DHANA"], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_070_awadh",
        "chart_filename": "chart_070_awadh.json",
        "subject": "Narendra Modi",
        "description": "Indian Prime Minister, longest-serving non-Congress PM",
        "provenance": "Wikipedia — Narendra Modi birth data (rectified)",
        "birth_data": {
            "date": "1950-09-17",
            "time": "11:00",
            "latitude": 23.0225,
            "longitude": 72.5714,
            "timezone": "Asia/Kolkata",
        },
        "known_events": [
            {"event_id": "MODI_CM_2001", "event_date_utc": "2001-10-07T00:00:00Z",
             "domain": "CAREER", "description": "Became Chief Minister of Gujarat",
             "yoga_types": ["RAJA"], "expected_planets": ["SATURN", "JUPITER"]},
            {"event_id": "MODI_PM_2014", "event_date_utc": "2014-05-26T00:00:00Z",
             "domain": "CAREER", "description": "Inaugurated as Prime Minister of India",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "MODI_REELECT_2019", "event_date_utc": "2019-05-30T00:00:00Z",
             "domain": "CAREER", "description": "Re-elected as Prime Minister with larger majority",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
        ],
    },
]


# ── Fixture Building ────────────────────────────────────────────────────────

def extract_chart_facts(chart: Any) -> dict[str, Any]:
    """Extract canonical facts from a computed JyotishService chart."""
    lagna_rashi = chart.lagna.rashi.value
    lagna_rashi_idx = _RASHI_ORDER.index(lagna_rashi)

    lagna_facts = {
        "sign": lagna_rashi,
        "longitude": chart.lagna.ascendant_longitude_deg,
    }

    planets: dict[str, Any] = {}
    for ps in chart.planet_states:
        name = ps.body.value
        planet_rashi_idx = _RASHI_ORDER.index(ps.rashi.value)
        house_num = (planet_rashi_idx - lagna_rashi_idx) % 12 + 1
        planets[name] = {
            "longitude_used": ps.longitude_used,
            "rashi": ps.rashi.value,
            "house": house_num,
            "degree_in_rashi": ps.degree_in_rashi,
            "nakshatra": ps.nakshatra.value,
            "nakshatra_lord": ps.nakshatra_lord.value,
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

    # Build expected_canonical_facts in the same format as validation charts
    expected_facts = {
        "lagna": {
            "sign": facts["lagna"]["sign"],
            "longitude": facts["lagna"]["longitude"],
        },
        "planets": {},
        "houses": {},
        "house_lords": facts["house_lords"],
    }

    # Add planet data with sign_lord computation
    _SIGN_LORDS: dict[str, str] = {
        "MESHA": "MARS", "VRISHABHA": "VENUS", "MITHUNA": "MERCURY",
        "KARKA": "MOON", "SIMHA": "SUN", "KANYA": "MERCURY",
        "TULA": "VENUS", "VRISHCHIKA": "MARS", "DHANUSHA": "JUPITER",
        "MAKARA": "SATURN", "KUMBHA": "SATURN", "MEENA": "JUPITER",
    }

    for pname, pdata in facts["planets"].items():
        expected_facts["planets"][pname] = {
            "longitude_used": pdata["longitude_used"],
            "rashi": pdata["rashi"],
            "house": pdata["house"],
            "degree_in_rashi": pdata["degree_in_rashi"],
            "nakshatra": pdata["nakshatra"],
            "nakshatra_lord": pdata["nakshatra_lord"],
            "sign_lord": _SIGN_LORDS.get(pdata["rashi"], ""),
            "retrograde": pdata["retrograde"],
            "d9_sign": pdata["d9_sign"],
            "house_lord_of": pdata.get("house_lord_of", []),
        }

    # Add house data
    for hnum, hdata in facts["houses"].items():
        expected_facts["houses"][hnum] = {
            "rashi": hdata["rashi"],
            "lord": hdata["lord"],
            "occupants": hdata["occupants"],
        }

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
        "expected_canonical_facts": expected_facts,
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
    print(f"Phase F4: Modern Personality Cohort — Fixture Generator ({len(MODERN_PERSONALITIES)} subjects)")
    print("=" * 64)
    print()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    for subject_def in MODERN_PERSONALITIES:
        fixture_id = subject_def["fixture_id"]
        filename = subject_def["chart_filename"]
        bd = subject_def["birth_data"]

        # Skip if fixture already exists
        out_path = FIXTURES_DIR / filename
        if out_path.exists() and not args.dry_run:
            print(f"── {subject_def['subject']} ({fixture_id}) — SKIP (exists)")
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

        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            print(f"   Skipping {subject_def['subject']}")

        print()

    print("=" * 64)
    if args.dry_run:
        print("Dry run complete — no files written.")
    else:
        print(f"Fixture generation complete.")
        print(f"Output directory: {FIXTURES_DIR}")
    print("=" * 64)

    return 0


if __name__ == "__main__":
    sys.exit(main())

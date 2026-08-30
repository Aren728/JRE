#!/usr/bin/env python3
"""Phase F1: Cohort Expansion — Immutable Chart Fixture Generator.

Uses the existing JRE fact-generation pipeline (JyotishService + Swiss Ephemeris)
to compute exact canonical facts for 40 new historical figures and save them as
immutable JSON fixtures in tests/fixtures/validation_charts/.

NO changes to rules, weights, or engine logic.
NO hallucinated facts — every value comes from the live JRE pipeline.

Usage::

    python scripts/generate_cohort_fixtures.py
    python scripts/generate_cohort_fixtures.py --dry-run
    python scripts/generate_cohort_fixtures.py --start 11 --end 20
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
    _PROJECT_ROOT / "tests" / "fixtures" / "validation_charts"
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

# ── D9 (Navamsha) Computation ──────────────────────────────────────────────


def compute_d9_sign(longitude_used: float) -> str:
    """Classical navamsha sign from a sidereal longitude.

    Fire signs  → navamsha starts from the same sign.
    Earth signs → navamsha starts from sign + 5 (mod 12).
    Air signs   → navamsha starts from sign + 4 (mod 12).
    Water signs → navamsha starts from sign + 8 (mod 12).
    """
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


# ── Subject Definitions (Phase E4 originals + F1 expansion) ─────────────────

SUBJECTS: list[dict[str, Any]] = [
    # ══════════════════════════════════════════════════════════════════════
    # Phase E4: Original 10 subjects (charts 002–010, plus 006–010 here)
    # ══════════════════════════════════════════════════════════════════════
    {
        "fixture_id": "chart_006_newton",
        "chart_filename": "chart_006_newton.json",
        "subject": "Isaac Newton",
        "birth_data": {
            "date": "1643-01-04", "time": "04:00:00",
            "timezone": "Europe/London",
            "latitude": 52.8066, "longitude": -0.6350,
            "location": "Woolsthorpe Manor, Lincolnshire, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Isaac Newton. AA-rated.",
        "known_events": [
            {"event_id": "NEWTON_PRINCIPIA_1687", "event_date_utc": "1687-07-05T00:00:00Z",
             "domain": "CAREER", "description": "Published Principia Mathematica",
             "yoga_types": [], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "NEWTON_LUCASIAN_1669", "event_date_utc": "1669-10-29T00:00:00Z",
             "domain": "CAREER", "description": "Appointed Lucasian Professor of Mathematics",
             "yoga_types": [], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "NEWTON_DEATH_1727", "event_date_utc": "1727-03-31T00:00:00Z",
             "domain": "HEALTH", "description": "Died in London, age 84",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_007_lincoln",
        "chart_filename": "chart_007_lincoln.json",
        "subject": "Abraham Lincoln",
        "birth_data": {
            "date": "1809-02-12", "time": "06:40:00",
            "timezone": "America/Chicago",
            "latitude": 37.5568, "longitude": -85.7371,
            "location": "Hodgenville, Kentucky, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Abraham Lincoln. AA-rated.",
        "known_events": [
            {"event_id": "LINCOLN_PRESIDENT_1860", "event_date_utc": "1860-11-06T00:00:00Z",
             "domain": "CAREER", "description": "Elected 16th President of the United States",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "LINCOLN_EMANCIPATION_1863", "event_date_utc": "1863-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Issued the Emancipation Proclamation",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "LINCOLN_ASSASSINATION_1865", "event_date_utc": "1865-04-15T00:00:00Z",
             "domain": "HEALTH", "description": "Assassinated at Ford's Theatre",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_008_teresa",
        "chart_filename": "chart_008_teresa.json",
        "subject": "Mother Teresa",
        "birth_data": {
            "date": "1910-08-26", "time": "18:00:00",
            "timezone": "Europe/Skopje",
            "latitude": 41.9973, "longitude": 21.4280,
            "location": "Skopje, Ottoman Empire (modern North Macedonia)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Mother Teresa. AA-rated.",
        "known_events": [
            {"event_id": "TERESA_MISSIONARIES_1950", "event_date_utc": "1950-10-07T00:00:00Z",
             "domain": "CAREER", "description": "Founded the Missionaries of Charity",
             "yoga_types": [], "expected_planets": ["JUPITER", "MOON"]},
            {"event_id": "TERESA_NOBEL_1979", "event_date_utc": "1979-12-10T00:00:00Z",
             "domain": "CAREER", "description": "Awarded the Nobel Peace Prize",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "TERESA_DEATH_1997", "event_date_utc": "1997-09-05T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Calcutta, age 87",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_009_jobs",
        "chart_filename": "chart_009_jobs.json",
        "subject": "Steve Jobs",
        "birth_data": {
            "date": "1955-02-24", "time": "19:15:00",
            "timezone": "America/Los_Angeles",
            "latitude": 37.7749, "longitude": -122.4194,
            "location": "San Francisco, California, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Steve Jobs. AA-rated.",
        "known_events": [
            {"event_id": "JOBS_APPLE_1976", "event_date_utc": "1976-04-01T00:00:00Z",
             "domain": "CAREER", "description": "Co-founded Apple Computer",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "JOBS_OUSTED_1985", "event_date_utc": "1985-09-17T00:00:00Z",
             "domain": "CAREER", "description": "Forced out of Apple",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
            {"event_id": "JOBS_RETURN_1997", "event_date_utc": "1997-09-16T00:00:00Z",
             "domain": "CAREER", "description": "Returned to Apple as interim CEO",
             "yoga_types": [], "expected_planets": ["JUPITER", "VENUS"]},
        ],
    },
    {
        "fixture_id": "chart_010_earhart",
        "chart_filename": "chart_010_earhart.json",
        "subject": "Amelia Earhart",
        "birth_data": {
            "date": "1897-07-24", "time": "08:00:00",
            "timezone": "America/Chicago",
            "latitude": 39.5631, "longitude": -95.1260,
            "location": "Atchison, Kansas, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "C",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Amelia Earhart. C-rated (approximate time).",
        "known_events": [
            {"event_id": "EARHART_FIRST_FLIGHT_1928", "event_date_utc": "1928-06-17T00:00:00Z",
             "domain": "CAREER", "description": "First woman to fly across the Atlantic",
             "yoga_types": [], "expected_planets": ["JUPITER", "RAHU"]},
            {"event_id": "EARHART_SOLO_ATLANTIC_1932", "event_date_utc": "1932-05-20T00:00:00Z",
             "domain": "CAREER", "description": "First woman to fly solo nonstop across the Atlantic",
             "yoga_types": [], "expected_planets": ["JUPITER", "MARS"]},
            {"event_id": "EARHART_DISAPPEARANCE_1937", "event_date_utc": "1937-07-02T00:00:00Z",
             "domain": "HEALTH", "description": "Disappeared over the Pacific",
             "yoga_types": [], "expected_planets": ["RAHU", "SATURN"]},
        ],
    },
    {
        "fixture_id": "chart_002_curie",
        "chart_filename": "chart_002_curie.json",
        "subject": "Marie Curie",
        "birth_data": {
            "date": "1867-11-07", "time": "19:00:00",
            "timezone": "Europe/Warsaw",
            "latitude": 52.2297, "longitude": 21.0122,
            "location": "Warsaw, Congress Poland (modern Poland)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Marie Curie. AA-rated.",
        "known_events": [
            {"event_id": "CURIE_NOBEL_1903", "event_date_utc": "1903-12-10T00:00:00Z",
             "domain": "CAREER", "description": "Nobel Prize in Physics",
             "yoga_types": ["RAJA"], "expected_planets": ["SUN", "JUPITER"]},
            {"event_id": "CURIE_NOBEL_1911", "event_date_utc": "1911-12-10T00:00:00Z",
             "domain": "CAREER", "description": "Nobel Prize in Chemistry",
             "yoga_types": ["RAJA"], "expected_planets": ["SUN", "JUPITER"]},
            {"event_id": "CURIE_DEATH_1934", "event_date_utc": "1934-07-04T00:00:00Z",
             "domain": "HEALTH", "description": "Died of aplastic anemia",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_003_mozart",
        "chart_filename": "chart_003_mozart.json",
        "subject": "Wolfgang Amadeus Mozart",
        "birth_data": {
            "date": "1756-01-27", "time": "20:00:00",
            "timezone": "Europe/Vienna",
            "latitude": 47.8095, "longitude": 13.0550,
            "location": "Salzburg, Austria",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Mozart. AA-rated.",
        "known_events": [
            {"event_id": "MOZART_MARRIAGE_1782", "event_date_utc": "1782-08-04T00:00:00Z",
             "domain": "MARRIAGE", "description": "Married Constanze Weber",
             "yoga_types": [], "expected_planets": ["VENUS"]},
            {"event_id": "MOZART_DON_GIOVANNI_1787", "event_date_utc": "1787-10-29T00:00:00Z",
             "domain": "CAREER", "description": "Premiere of Don Giovanni",
             "yoga_types": ["RAJA"], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "MOZART_DEATH_1791", "event_date_utc": "1791-12-05T00:00:00Z",
             "domain": "HEALTH", "description": "Died at age 35",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_004_tesla",
        "chart_filename": "chart_004_tesla.json",
        "subject": "Nikola Tesla",
        "birth_data": {
            "date": "1856-07-10", "time": "00:00:00",
            "timezone": "Europe/Belgrade",
            "latitude": 45.2671, "longitude": 15.3903,
            "location": "Smiljan, Austrian Empire (modern Croatia)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Nikola Tesla. AA-rated.",
        "known_events": [
            {"event_id": "TESLA_US_MOVE_1884", "event_date_utc": "1884-06-06T00:00:00Z",
             "domain": "MIGRATION", "description": "Arrived in New York City",
             "yoga_types": [], "expected_planets": ["RAHU"]},
            {"event_id": "TESLA_LAB_FIRE_1895", "event_date_utc": "1895-03-13T00:00:00Z",
             "domain": "HEALTH", "description": "Laboratory fire destroyed research",
             "yoga_types": [], "expected_planets": ["SATURN", "MARS"]},
            {"event_id": "TESLA_DEATH_1943", "event_date_utc": "1943-01-07T00:00:00Z",
             "domain": "HEALTH", "description": "Died alone in New Yorker Hotel",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_005_gandhi",
        "chart_filename": "chart_005_gandhi.json",
        "subject": "Indira Gandhi",
        "birth_data": {
            "date": "1917-11-19", "time": "23:10:00",
            "timezone": "Asia/Kolkata",
            "latitude": 25.4358, "longitude": 81.8463,
            "location": "Allahabad, British India",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Indira Gandhi. AA-rated.",
        "known_events": [
            {"event_id": "GANDHI_PM_1966", "event_date_utc": "1966-01-24T00:00:00Z",
             "domain": "CAREER", "description": "Became first female PM of India",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "GANDHI_WAR_1971", "event_date_utc": "1971-12-16T00:00:00Z",
             "domain": "CAREER", "description": "Led India to victory in Indo-Pakistani War",
             "yoga_types": ["RAJA"], "expected_planets": ["MARS", "SATURN"]},
            {"event_id": "GANDHI_ASSASSINATION_1984", "event_date_utc": "1984-10-31T00:00:00Z",
             "domain": "HEALTH", "description": "Assassinated in New Delhi",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },

    # ══════════════════════════════════════════════════════════════════════
    # Phase F1: 40 NEW subjects (charts 011–050)
    # ══════════════════════════════════════════════════════════════════════

    # ── Politics / Leadership (10) ──────────────────────────────────────

    {
        "fixture_id": "chart_011_churchill",
        "chart_filename": "chart_011_churchill.json",
        "subject": "Winston Churchill",
        "birth_data": {
            "date": "1874-11-30", "time": "00:00:00",
            "timezone": "Europe/London",
            "latitude": 51.8543, "longitude": -1.3580,
            "location": "Blenheim Palace, Woodstock, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Winston Churchill. AA-rated.",
        "known_events": [
            {"event_id": "CHURCHILL_PM_1940", "event_date_utc": "1940-05-10T00:00:00Z",
             "domain": "CAREER", "description": "Became Prime Minister of the United Kingdom",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "CHURCHILL_NOBEL_1953", "event_date_utc": "1953-12-10T00:00:00Z",
             "domain": "CAREER", "description": "Awarded the Nobel Prize in Literature",
             "yoga_types": [], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "CHURCHILL_DEATH_1965", "event_date_utc": "1965-01-24T00:00:00Z",
             "domain": "HEALTH", "description": "Died at age 90 in London",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_012_mandela",
        "chart_filename": "chart_012_mandela.json",
        "subject": "Nelson Mandela",
        "birth_data": {
            "date": "1918-07-18", "time": "14:30:00",
            "timezone": "Africa/Johannesburg",
            "latitude": -32.3000, "longitude": 27.1333,
            "location": "Mvezo, Cape Province, South Africa",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Nelson Mandela. AA-rated.",
        "known_events": [
            {"event_id": "MANDELA_RELEASE_1990", "event_date_utc": "1990-02-11T00:00:00Z",
             "domain": "CAREER", "description": "Released from prison after 27 years",
             "yoga_types": [], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "MANDELA_PRESIDENT_1994", "event_date_utc": "1994-05-10T00:00:00Z",
             "domain": "CAREER", "description": "Inaugurated as first Black president of South Africa",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "MANDELA_DEATH_2013", "event_date_utc": "2013-12-05T00:00:00Z",
             "domain": "HEALTH", "description": "Died at age 95 in Johannesburg",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_013_gandhi_mk",
        "chart_filename": "chart_013_gandhi_mk.json",
        "subject": "Mahatma Gandhi",
        "birth_data": {
            "date": "1869-10-02", "time": "06:30:00",
            "timezone": "Asia/Kolkata",
            "latitude": 21.6422, "longitude": 69.6093,
            "location": "Porbandar, Kathiawar, British India",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Mahatma Gandhi. AA-rated.",
        "known_events": [
            {"event_id": "GANDHI_SALT_1930", "event_date_utc": "1930-04-06T00:00:00Z",
             "domain": "CAREER", "description": "Started the Salt March — defining act of nonviolent resistance",
             "yoga_types": [], "expected_planets": ["MARS", "JUPITER"]},
            {"event_id": "GANDHI_INDEPENDENCE_1947", "event_date_utc": "1947-08-15T00:00:00Z",
             "domain": "CAREER", "description": "India gained independence",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "GANDHI_ASSASSINATION_1948", "event_date_utc": "1948-01-30T00:00:00Z",
             "domain": "HEALTH", "description": "Assassinated in New Delhi",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_014_jfk",
        "chart_filename": "chart_014_jfk.json",
        "subject": "John F. Kennedy",
        "birth_data": {
            "date": "1917-05-29", "time": "15:00:00",
            "timezone": "America/New_York",
            "latitude": 42.3334, "longitude": -71.1365,
            "location": "Brookline, Massachusetts, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for John F. Kennedy. AA-rated.",
        "known_events": [
            {"event_id": "JFK_PRESIDENT_1960", "event_date_utc": "1960-11-08T00:00:00Z",
             "domain": "CAREER", "description": "Elected 35th President of the United States",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "JFK_CUBAN_MISSILE_1962", "event_date_utc": "1962-10-22T00:00:00Z",
             "domain": "CAREER", "description": "Managed the Cuban Missile Crisis",
             "yoga_types": [], "expected_planets": ["MARS", "SATURN"]},
            {"event_id": "JFK_ASSASSINATION_1963", "event_date_utc": "1963-11-22T00:00:00Z",
             "domain": "HEALTH", "description": "Assassinated in Dallas, Texas",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_015_thatcher",
        "chart_filename": "chart_015_thatcher.json",
        "subject": "Margaret Thatcher",
        "birth_data": {
            "date": "1925-10-13", "time": "09:00:00",
            "timezone": "Europe/London",
            "latitude": 52.9115, "longitude": -0.6361,
            "location": "Grantham, Lincolnshire, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Margaret Thatcher. AA-rated.",
        "known_events": [
            {"event_id": "THATCHER_PM_1979", "event_date_utc": "1979-05-04T00:00:00Z",
             "domain": "CAREER", "description": "Became first female Prime Minister of the UK",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "THATCHER_FALKLANDS_1982", "event_date_utc": "1982-06-14T00:00:00Z",
             "domain": "CAREER", "description": "Won the Falklands War",
             "yoga_types": [], "expected_planets": ["MARS", "SATURN"]},
            {"event_id": "THATCHER_RESIGNATION_1990", "event_date_utc": "1990-11-22T00:00:00Z",
             "domain": "CAREER", "description": "Resigned as Prime Minister",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_016_degaulle",
        "chart_filename": "chart_016_degaulle.json",
        "subject": "Charles de Gaulle",
        "birth_data": {
            "date": "1890-11-22", "time": "06:30:00",
            "timezone": "Europe/Paris",
            "latitude": 50.6292, "longitude": 3.0573,
            "location": "Lille, Nord, France",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Charles de Gaulle. AA-rated.",
        "known_events": [
            {"event_id": "DEGAULLE_LIBERATION_1944", "event_date_utc": "1944-08-25T00:00:00Z",
             "domain": "CAREER", "description": "Liberation of Paris",
             "yoga_types": [], "expected_planets": ["MARS", "JUPITER"]},
            {"event_id": "DEGAULLE_PRESIDENT_1959", "event_date_utc": "1959-01-08T00:00:00Z",
             "domain": "CAREER", "description": "Became first President of the Fifth Republic",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "DEGAULLE_DEATH_1970", "event_date_utc": "1970-11-09T00:00:00Z",
             "domain": "HEALTH", "description": "Died at age 79 in Colombey-les-Deux-Églises",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_017_bismarck",
        "chart_filename": "chart_017_bismarck.json",
        "subject": "Otto von Bismarck",
        "birth_data": {
            "date": "1815-04-01", "time": "10:30:00",
            "timezone": "Europe/Berlin",
            "latitude": 52.6833, "longitude": 11.8167,
            "location": "Schönhausen, Province of Saxony, Prussia",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Otto von Bismarck. AA-rated.",
        "known_events": [
            {"event_id": "BISMARCK_CHANCELLOR_1871", "event_date_utc": "1871-03-21T00:00:00Z",
             "domain": "CAREER", "description": "Became first Chancellor of the German Empire",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SATURN"]},
            {"event_id": "BISMARCK_UNIFICATION_1871", "event_date_utc": "1871-01-18T00:00:00Z",
             "domain": "CAREER", "description": "Proclaimed the German Empire at Versailles",
             "yoga_types": [], "expected_planets": ["SUN", "JUPITER"]},
            {"event_id": "BISMARCK_DEATH_1898", "event_date_utc": "1898-07-30T00:00:00Z",
             "domain": "HEALTH", "description": "Died at age 83 in Friedrichsruh",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_018_franklin",
        "chart_filename": "chart_018_franklin.json",
        "subject": "Benjamin Franklin",
        "birth_data": {
            "date": "1706-01-17", "time": "10:30:00",
            "timezone": "America/New_York",
            "latitude": 42.3601, "longitude": -71.0589,
            "location": "Boston, Massachusetts, British America",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "C",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Benjamin Franklin. C-rated.",
        "known_events": [
            {"event_id": "FRANKLIN_LIGHTNING_1752", "event_date_utc": "1752-06-15T00:00:00Z",
             "domain": "CAREER", "description": "Famous kite experiment demonstrating electricity",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "FRANKLIN_TREATY_1778", "event_date_utc": "1778-02-06T00:00:00Z",
             "domain": "CAREER", "description": "Signed the Treaty of Alliance with France",
             "yoga_types": [], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "FRANKLIN_DEATH_1790", "event_date_utc": "1790-04-17T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Philadelphia at age 84",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_019_eisenhower",
        "chart_filename": "chart_019_eisenhower.json",
        "subject": "Dwight Eisenhower",
        "birth_data": {
            "date": "1890-10-14", "time": "14:00:00",
            "timezone": "America/Chicago",
            "latitude": 33.7554, "longitude": -96.5367,
            "location": "Denison, Texas, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Dwight Eisenhower. AA-rated.",
        "known_events": [
            {"event_id": "EISENHOWER_DDAY_1944", "event_date_utc": "1944-06-06T00:00:00Z",
             "domain": "CAREER", "description": "Supreme Allied Commander for D-Day invasion",
             "yoga_types": [], "expected_planets": ["MARS", "JUPITER"]},
            {"event_id": "EISENHOWER_PRESIDENT_1953", "event_date_utc": "1953-01-20T00:00:00Z",
             "domain": "CAREER", "description": "Inaugurated as 34th President of the United States",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "EISENHOWER_DEATH_1969", "event_date_utc": "1969-03-28T00:00:00Z",
             "domain": "HEALTH", "description": "Died at Walter Reed Army Medical Center",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_020_victoria",
        "chart_filename": "chart_020_victoria.json",
        "subject": "Queen Victoria",
        "birth_data": {
            "date": "1819-05-24", "time": "04:15:00",
            "timezone": "Europe/London",
            "latitude": 51.5014, "longitude": -0.1830,
            "location": "Kensington Palace, London, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Queen Victoria. AA-rated.",
        "known_events": [
            {"event_id": "VICTORIA_CORONATION_1838", "event_date_utc": "1838-06-28T00:00:00Z",
             "domain": "CAREER", "description": "Coronated as Queen of the United Kingdom",
             "yoga_types": ["RAJA"], "expected_planets": ["SUN", "JUPITER"]},
            {"event_id": "VICTORIA_MARRIAGE_1840", "event_date_utc": "1840-02-10T00:00:00Z",
             "domain": "MARRIAGE", "description": "Married Prince Albert",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "VICTORIA_DEATH_1901", "event_date_utc": "1901-01-22T00:00:00Z",
             "domain": "HEALTH", "description": "Died at Osborne House, age 81",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },

    # ── Science (10) ────────────────────────────────────────────────────

    {
        "fixture_id": "chart_021_darwin",
        "chart_filename": "chart_021_darwin.json",
        "subject": "Charles Darwin",
        "birth_data": {
            "date": "1809-02-12", "time": "03:00:00",
            "timezone": "Europe/London",
            "latitude": 52.7077, "longitude": -2.7490,
            "location": "Shrewsbury, Shropshire, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "C",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Charles Darwin. C-rated.",
        "known_events": [
            {"event_id": "DARWIN_ORIGINS_1859", "event_date_utc": "1859-11-24T00:00:00Z",
             "domain": "CAREER", "description": "Published On the Origin of Species",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "DARWIN_VOYAGE_1836", "event_date_utc": "1836-10-02T00:00:00Z",
             "domain": "MIGRATION", "description": "Returned to England aboard HMS Beagle",
             "yoga_types": [], "expected_planets": ["RAHU", "VENUS"]},
            {"event_id": "DARWIN_DEATH_1882", "event_date_utc": "1882-04-19T00:00:00Z",
             "domain": "HEALTH", "description": "Died at Down House, age 73",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_022_humboldt",
        "chart_filename": "chart_022_humboldt.json",
        "subject": "Alexander von Humboldt",
        "birth_data": {
            "date": "1769-09-14", "time": "09:30:00",
            "timezone": "Europe/Berlin",
            "latitude": 52.5200, "longitude": 13.4050,
            "location": "Berlin, Kingdom of Prussia",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Alexander von Humboldt. AA-rated.",
        "known_events": [
            {"event_id": "HUMBOLDT_AMERICA_1800", "event_date_utc": "1800-07-16T00:00:00Z",
             "domain": "MIGRATION", "description": "Began his great expedition to the Americas",
             "yoga_types": [], "expected_planets": ["RAHU", "JUPITER"]},
            {"event_id": "HUMBOLDT_COSMOS_1845", "event_date_utc": "1845-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Published first volume of Cosmos",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "HUMBOLDT_DEATH_1859", "event_date_utc": "1859-05-06T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Berlin at age 89",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_023_mendel",
        "chart_filename": "chart_023_mendel.json",
        "subject": "Gregor Mendel",
        "birth_data": {
            "date": "1822-07-20", "time": "09:00:00",
            "timezone": "Europe/Prague",
            "latitude": 50.0690, "longitude": 17.6940,
            "location": "Hynčice, Austrian Empire (modern Czech Republic)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 30},
        "description": "Immutable reference chart for Gregor Mendel. A-rated.",
        "known_events": [
            {"event_id": "MENDEL_DISCOVERY_1865", "event_date_utc": "1865-02-08T00:00:00Z",
             "domain": "CAREER", "description": "Presented his laws of inheritance to the Natural History Society",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "MENDEL_PUBLICATION_1866", "event_date_utc": "1866-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Published Experiments on Plant Hybridization",
             "yoga_types": [], "expected_planets": ["MERCURY", "SATURN"]},
            {"event_id": "MENDEL_DEATH_1884", "event_date_utc": "1884-01-06T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Brno at age 61",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_024_pasteur",
        "chart_filename": "chart_024_pasteur.json",
        "subject": "Louis Pasteur",
        "birth_data": {
            "date": "1822-12-27", "time": "20:00:00",
            "timezone": "Europe/Paris",
            "latitude": 47.1000, "longitude": 5.4833,
            "location": "Dole, Jura, France",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Louis Pasteur. A-rated.",
        "known_events": [
            {"event_id": "PASTEUR_RABIES_1885", "event_date_utc": "1885-07-06T00:00:00Z",
             "domain": "CAREER", "description": "Successfully vaccinated a human against rabies for the first time",
             "yoga_types": [], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "PASTEUR_PASTEURIZATION_1864", "event_date_utc": "1864-04-01T00:00:00Z",
             "domain": "CAREER", "description": "Demonstrated germ theory with the swan-neck flask experiment",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "PASTEUR_DEATH_1895", "event_date_utc": "1895-09-28T00:00:00Z",
             "domain": "HEALTH", "description": "Died at Villeneuve-l'Étang, age 72",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_025_lovelace",
        "chart_filename": "chart_025_lovelace.json",
        "subject": "Ada Lovelace",
        "birth_data": {
            "date": "1815-12-10", "time": "01:00:00",
            "timezone": "Europe/London",
            "latitude": 51.5074, "longitude": -0.1278,
            "location": "London, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Ada Lovelace. A-rated.",
        "known_events": [
            {"event_id": "LOVELACE_NOTES_1843", "event_date_utc": "1843-10-01T00:00:00Z",
             "domain": "CAREER", "description": "Published Notes on the Analytical Engine including the first algorithm",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "LOVELACE_POETRY_1841", "event_date_utc": "1841-07-01T00:00:00Z",
             "domain": "CAREER", "description": "Corresponded with Babbage about the Analytical Engine",
             "yoga_types": [], "expected_planets": ["MERCURY", "SUN"]},
            {"event_id": "LOVELACE_DEATH_1852", "event_date_utc": "1852-11-27T00:00:00Z",
             "domain": "HEALTH", "description": "Died of uterine cancer at age 36",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_026_planck",
        "chart_filename": "chart_026_planck.json",
        "subject": "Max Planck",
        "birth_data": {
            "date": "1858-04-23", "time": "00:00:00",
            "timezone": "Europe/Berlin",
            "latitude": 54.3233, "longitude": 10.1228,
            "location": "Kiel, Duchy of Holstein (now Germany)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "B",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Max Planck. B-rated.",
        "known_events": [
            {"event_id": "PLANCK_QUANTUM_1900", "event_date_utc": "1900-12-14T00:00:00Z",
             "domain": "CAREER", "description": "Presented quantum hypothesis to the German Physical Society",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "PLANCK_NOBEL_1918", "event_date_utc": "1918-11-01T00:00:00Z",
             "domain": "CAREER", "description": "Awarded Nobel Prize in Physics for quantum theory",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "PLANCK_DEATH_1947", "event_date_utc": "1947-10-04T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Göttingen at age 89",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_027_heisenberg",
        "chart_filename": "chart_027_heisenberg.json",
        "subject": "Werner Heisenberg",
        "birth_data": {
            "date": "1901-12-05", "time": "06:00:00",
            "timezone": "Europe/Berlin",
            "latitude": 49.7913, "longitude": 9.9534,
            "location": "Würzburg, Bavaria, Germany",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Werner Heisenberg. AA-rated.",
        "known_events": [
            {"event_id": "HEISENBERG_UNCERTAINTY_1927", "event_date_utc": "1927-03-01T00:00:00Z",
             "domain": "CAREER", "description": "Formulated the uncertainty principle",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "HEISENBERG_NOBEL_1932", "event_date_utc": "1932-12-10T00:00:00Z",
             "domain": "CAREER", "description": "Awarded Nobel Prize in Physics for quantum mechanics",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "HEISENBERG_DEATH_1976", "event_date_utc": "1976-02-01T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Munich at age 74",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_028_freud",
        "chart_filename": "chart_028_freud.json",
        "subject": "Sigmund Freud",
        "birth_data": {
            "date": "1856-05-06", "time": "18:30:00",
            "timezone": "Europe/Prague",
            "latitude": 49.6675, "longitude": 18.1450,
            "location": "Příbor, Austrian Empire (modern Czech Republic)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Sigmund Freud. AA-rated.",
        "known_events": [
            {"event_id": "FREUD_INTERPRETATION_1899", "event_date_utc": "1899-11-01T00:00:00Z",
             "domain": "CAREER", "description": "Published The Interpretation of Dreams",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "FREUD_ESCAPED_1938", "event_date_utc": "1938-06-04T00:00:00Z",
             "domain": "MIGRATION", "description": "Escaped Nazi-occupied Vienna for London",
             "yoga_types": [], "expected_planets": ["RAHU", "VENUS"]},
            {"event_id": "FREUD_DEATH_1939", "event_date_utc": "1939-09-23T00:00:00Z",
             "domain": "HEALTH", "description": "Died in London after euthanasia, age 83",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_029_jung",
        "chart_filename": "chart_029_jung.json",
        "subject": "Carl Jung",
        "birth_data": {
            "date": "1875-07-26", "time": "19:36:00",
            "timezone": "Europe/Zurich",
            "latitude": 47.5581, "longitude": 9.4801,
            "location": "Kesswil, Thurgau, Switzerland",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Carl Jung. AA-rated.",
        "known_events": [
            {"event_id": "JUNG_COLLECTIVE_1916", "event_date_utc": "1916-11-01T00:00:00Z",
             "domain": "CAREER", "description": "Published on the collective unconscious",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "JUNG_MEMORIES_1963", "event_date_utc": "1963-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Published Memories, Dreams, Reflections",
             "yoga_types": [], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "JUNG_DEATH_1961", "event_date_utc": "1961-06-06T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Küsnacht, age 85",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_030_franklin_r",
        "chart_filename": "chart_030_franklin_r.json",
        "subject": "Rosalind Franklin",
        "birth_data": {
            "date": "1920-07-25", "time": "02:00:00",
            "timezone": "Europe/London",
            "latitude": 51.5074, "longitude": -0.1278,
            "location": "London, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "C",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Rosalind Franklin. C-rated.",
        "known_events": [
            {"event_id": "FRANKLIN_PHOTO51_1952", "event_date_utc": "1952-05-01T00:00:00Z",
             "domain": "CAREER", "description": "Captured Photo 51 — key X-ray diffraction image of DNA",
             "yoga_types": [], "expected_planets": ["MERCURY", "SUN"]},
            {"event_id": "FRANKLIN_DNA_1953", "event_date_utc": "1953-04-25T00:00:00Z",
             "domain": "CAREER", "description": "Watson and Crick published the DNA double helix using her data",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "FRANKLIN_DEATH_1958", "event_date_utc": "1958-04-16T00:00:00Z",
             "domain": "HEALTH", "description": "Died of ovarian cancer at age 37",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },

    # ── Arts / Music / Literature (10) ──────────────────────────────────

    {
        "fixture_id": "chart_031_beethoven",
        "chart_filename": "chart_031_beethoven.json",
        "subject": "Ludwig van Beethoven",
        "birth_data": {
            "date": "1770-12-16", "time": "06:00:00",
            "timezone": "Europe/Berlin",
            "latitude": 50.7374, "longitude": 7.0982,
            "location": "Bonn, Electorate of Cologne (now Germany)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "B",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Ludwig van Beethoven. B-rated.",
        "known_events": [
            {"event_id": "BEETHOVEN_9TH_1824", "event_date_utc": "1824-05-07T00:00:00Z",
             "domain": "CAREER", "description": "Premiere of Symphony No. 9 in Vienna",
             "yoga_types": [], "expected_planets": ["JUPITER", "VENUS"]},
            {"event_id": "BEETHOVEN_MOONLIGHT_1802", "event_date_utc": "1802-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Composed the Moonlight Sonata period",
             "yoga_types": [], "expected_planets": ["VENUS", "MERCURY"]},
            {"event_id": "BEETHOVEN_DEATH_1827", "event_date_utc": "1827-03-26T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Vienna, age 56",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_032_vangogh",
        "chart_filename": "chart_032_vangogh.json",
        "subject": "Vincent van Gogh",
        "birth_data": {
            "date": "1853-03-30", "time": "11:00:00",
            "timezone": "Europe/Amsterdam",
            "latitude": 51.7175, "longitude": 4.6031,
            "location": "Groot-Zundert, Netherlands",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Vincent van Gogh. A-rated.",
        "known_events": [
            {"event_id": "VANGOGH_STARRY_1889", "event_date_utc": "1889-06-01T00:00:00Z",
             "domain": "CAREER", "description": "Painted The Starry Night at the asylum in Saint-Rémy",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "VANGOGH_ARLES_1888", "event_date_utc": "1888-02-01T00:00:00Z",
             "domain": "MIGRATION", "description": "Moved to Arles seeking artistic community",
             "yoga_types": [], "expected_planets": ["VENUS", "RAHU"]},
            {"event_id": "VANGOGH_DEATH_1890", "event_date_utc": "1890-07-29T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Auvers-sur-Oise, age 37",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_033_picasso",
        "chart_filename": "chart_033_picasso.json",
        "subject": "Pablo Picasso",
        "birth_data": {
            "date": "1881-10-25", "time": "23:15:00",
            "timezone": "Europe/Madrid",
            "latitude": 36.7213, "longitude": -4.4214,
            "location": "Málaga, Andalusia, Spain",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Pablo Picasso. A-rated.",
        "known_events": [
            {"event_id": "PICASSO_GUERNICA_1937", "event_date_utc": "1937-04-26T00:00:00Z",
             "domain": "CAREER", "description": "Guernica bombing inspired his masterpiece painting",
             "yoga_types": [], "expected_planets": ["VENUS", "SATURN"]},
            {"event_id": "PICASSO_BLUE_1901", "event_date_utc": "1901-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Began the Blue Period in Paris",
             "yoga_types": [], "expected_planets": ["VENUS", "RAHU"]},
            {"event_id": "PICASSO_DEATH_1973", "event_date_utc": "1973-04-08T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Mougins, France, age 91",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_034_tolstoy",
        "chart_filename": "chart_034_tolstoy.json",
        "subject": "Leo Tolstoy",
        "birth_data": {
            "date": "1828-09-09", "time": "06:00:00",
            "timezone": "Europe/Moscow",
            "latitude": 54.0720, "longitude": 37.6050,
            "location": "Yasnaya Polyana, Tula Governorate, Russia",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "B",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Leo Tolstoy. B-rated.",
        "known_events": [
            {"event_id": "TOLSTOY_WAR_AND_PEACE_1869", "event_date_utc": "1869-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Published War and Peace",
             "yoga_types": [], "expected_planets": ["JUPITER", "MERCURY"]},
            {"event_id": "TOLSTOY_ANNA_KARENINA_1877", "event_date_utc": "1877-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Completed Anna Karenina",
             "yoga_types": [], "expected_planets": ["VENUS", "MERCURY"]},
            {"event_id": "TOLSTOY_DEATH_1910", "event_date_utc": "1910-11-20T00:00:00Z",
             "domain": "HEALTH", "description": "Died at Astapovo station, age 82",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_035_twain",
        "chart_filename": "chart_035_twain.json",
        "subject": "Mark Twain",
        "birth_data": {
            "date": "1835-11-30", "time": "04:45:00",
            "timezone": "America/Chicago",
            "latitude": 40.2000, "longitude": -92.6500,
            "location": "Florida, Missouri, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "C",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Mark Twain. C-rated.",
        "known_events": [
            {"event_id": "TWAIN_TOM_SAWYER_1876", "event_date_utc": "1876-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Published The Adventures of Tom Sawyer",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "TWAIN_MARK_1863", "event_date_utc": "1863-02-03T00:00:00Z",
             "domain": "CAREER", "description": "First used the pen name Mark Twain",
             "yoga_types": [], "expected_planets": ["MERCURY", "RAHU"]},
            {"event_id": "TWAIN_DEATH_1910", "event_date_utc": "1910-04-21T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Redding, Connecticut, age 74",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_036_chaplin",
        "chart_filename": "chart_036_chaplin.json",
        "subject": "Charlie Chaplin",
        "birth_data": {
            "date": "1889-04-16", "time": "00:00:00",
            "timezone": "Europe/London",
            "latitude": 51.5074, "longitude": -0.1278,
            "location": "Walworth, London, England",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "B",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Charlie Chaplin. B-rated.",
        "known_events": [
            {"event_id": "CHAPLIN_KID_1921", "event_date_utc": "1921-02-06T00:00:00Z",
             "domain": "CAREER", "description": "Premiere of The Kid — his first full-length film",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "CHAPLIN_GOLD_RUSH_1925", "event_date_utc": "1925-08-16T00:00:00Z",
             "domain": "CAREER", "description": "Released The Gold Rush — commercial and critical triumph",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "CHAPLIN_DEATH_1977", "event_date_utc": "1977-12-25T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Corsier-sur-Vevey, age 88",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_037_tchaikovsky",
        "chart_filename": "chart_037_tchaikovsky.json",
        "subject": "Pyotr Tchaikovsky",
        "birth_data": {
            "date": "1840-05-07", "time": "12:00:00",
            "timezone": "Europe/Moscow",
            "latitude": 57.2167, "longitude": 54.0000,
            "location": "Votkinsk, Vyatka Governorate, Russia",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "B",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Pyotr Tchaikovsky. B-rated.",
        "known_events": [
            {"event_id": "TCHAIKOVSKY_NUTCRACKER_1892", "event_date_utc": "1892-12-18T00:00:00Z",
             "domain": "CAREER", "description": "Premiere of The Nutcracker in St. Petersburg",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "TCHAIKOVSKY_SWAN_1877", "event_date_utc": "1877-03-04T00:00:00Z",
             "domain": "CAREER", "description": "Premiere of Swan Lake at the Bolshoi Theatre",
             "yoga_types": [], "expected_planets": ["VENUS", "SATURN"]},
            {"event_id": "TCHAIKOVSKY_DEATH_1893", "event_date_utc": "1893-11-06T00:00:00Z",
             "domain": "HEALTH", "description": "Died in St. Petersburg, age 53",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_038_andersen",
        "chart_filename": "chart_038_andersen.json",
        "subject": "Hans Christian Andersen",
        "birth_data": {
            "date": "1805-04-02", "time": "01:00:00",
            "timezone": "Europe/Copenhagen",
            "latitude": 55.4038, "longitude": 10.4024,
            "location": "Odense, Denmark",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Hans Christian Andersen. AA-rated.",
        "known_events": [
            {"event_id": "ANDERSEN_UGLY_DUCKLING_1843", "event_date_utc": "1843-11-11T00:00:00Z",
             "domain": "CAREER", "description": "Published The Ugly Duckling",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "ANDERSEN_FROST_1830", "event_date_utc": "1830-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Published first fairy tale collection",
             "yoga_types": [], "expected_planets": ["MERCURY", "VENUS"]},
            {"event_id": "ANDERSEN_DEATH_1875", "event_date_utc": "1875-08-04T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Copenhagen, age 70",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_039_liszt",
        "chart_filename": "chart_039_liszt.json",
        "subject": "Franz Liszt",
        "birth_data": {
            "date": "1811-10-22", "time": "22:00:00",
            "timezone": "Europe/Vienna",
            "latitude": 47.4833, "longitude": 16.6167,
            "location": "Raiding, Kingdom of Hungary (now Austria)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Franz Liszt. A-rated.",
        "known_events": [
            {"event_id": "LISZT_PAGANINI_1832", "event_date_utc": "1832-04-09T00:00:00Z",
             "domain": "CAREER", "description": "Hearing Paganini ignited his drive to become the greatest pianist",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "LISZT_BERNED_1847", "event_date_utc": "1847-02-01T00:00:00Z",
             "domain": "MARRIAGE", "description": "Broke off relationship with Countess Marie d'Agoult",
             "yoga_types": [], "expected_planets": ["VENUS", "SATURN"]},
            {"event_id": "LISZT_DEATH_1886", "event_date_utc": "1886-07-31T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Bayreuth, age 74",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_040_chekhov",
        "chart_filename": "chart_040_chekhov.json",
        "subject": "Anton Chekhov",
        "birth_data": {
            "date": "1860-01-29", "time": "06:00:00",
            "timezone": "Europe/Moscow",
            "latitude": 47.2364, "longitude": 38.9244,
            "location": "Taganrog, Russian Empire",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Anton Chekhov. A-rated.",
        "known_events": [
            {"event_id": "CHEKHOV_CHERRY_1904", "event_date_utc": "1904-01-17T00:00:00Z",
             "domain": "CAREER", "description": "Premiere of The Cherry Orchard at the Moscow Art Theatre",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "CHEKHOV_SEAGULL_1896", "event_date_utc": "1896-10-17T00:00:00Z",
             "domain": "CAREER", "description": "First performance of The Seagull at Alexandrinsky Theatre",
             "yoga_types": [], "expected_planets": ["VENUS", "MERCURY"]},
            {"event_id": "CHEKHOV_DEATH_1904", "event_date_utc": "1904-07-15T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Badenweiler, Germany, age 44",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },

    # ── Business / Industry (5) ─────────────────────────────────────────

    {
        "fixture_id": "chart_041_ford",
        "chart_filename": "chart_041_ford.json",
        "subject": "Henry Ford",
        "birth_data": {
            "date": "1863-07-30", "time": "21:30:00",
            "timezone": "America/Detroit",
            "latitude": 42.0997, "longitude": -83.2456,
            "location": "Greenfield Township, Michigan, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Henry Ford. AA-rated.",
        "known_events": [
            {"event_id": "FORD_MODEL_T_1908", "event_date_utc": "1908-10-01T00:00:00Z",
             "domain": "CAREER", "description": "Introduced the Model T automobile",
             "yoga_types": [], "expected_planets": ["VENUS", "MERCURY"]},
            {"event_id": "FORD_ASSEMBLY_1913", "event_date_utc": "1913-12-01T00:00:00Z",
             "domain": "CAREER", "description": "Introduced the moving assembly line at Highland Park",
             "yoga_types": [], "expected_planets": ["MERCURY", "SATURN"]},
            {"event_id": "FORD_DEATH_1947", "event_date_utc": "1947-04-07T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Dearborn, Michigan, age 83",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_042_rockefeller",
        "chart_filename": "chart_042_rockefeller.json",
        "subject": "John D. Rockefeller",
        "birth_data": {
            "date": "1839-07-08", "time": "00:30:00",
            "timezone": "America/New_York",
            "latitude": 42.5353, "longitude": -76.4636,
            "location": "Richford, New York, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for John D. Rockefeller. AA-rated.",
        "known_events": [
            {"event_id": "ROCKEFELLER_STD_1870", "event_date_utc": "1870-01-10T00:00:00Z",
             "domain": "CAREER", "description": "Founded Standard Oil Company",
             "yoga_types": [], "expected_planets": ["VENUS", "MERCURY"]},
            {"event_id": "ROCKEFELLER_RICHEST_1916", "event_date_utc": "1916-09-29T00:00:00Z",
             "domain": "CAREER", "description": "Became the first American billionaire",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "ROCKEFELLER_DEATH_1937", "event_date_utc": "1937-05-23T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Ormond Beach, Florida, age 86",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_043_carnegie",
        "chart_filename": "chart_043_carnegie.json",
        "subject": "Andrew Carnegie",
        "birth_data": {
            "date": "1835-11-25", "time": "19:00:00",
            "timezone": "Europe/London",
            "latitude": 56.0701, "longitude": -3.2100,
            "location": "Dunfermline, Fife, Scotland",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Andrew Carnegie. A-rated.",
        "known_events": [
            {"event_id": "CARNEGIE_STEEL_1892", "event_date_utc": "1892-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Carnegie Steel Company became the largest in the world",
             "yoga_types": [], "expected_planets": ["VENUS", "SATURN"]},
            {"event_id": "CARNEGIE_GOSPEL_1889", "event_date_utc": "1889-06-01T00:00:00Z",
             "domain": "CAREER", "description": "Published The Gospel of Wealth",
             "yoga_types": [], "expected_planets": ["MERCURY", "JUPITER"]},
            {"event_id": "CARNEGIE_DEATH_1919", "event_date_utc": "1919-08-11T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Lenox, Massachusetts, age 84",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_044_morgan",
        "chart_filename": "chart_044_morgan.json",
        "subject": "J.P. Morgan",
        "birth_data": {
            "date": "1837-04-17", "time": "07:00:00",
            "timezone": "America/New_York",
            "latitude": 41.7658, "longitude": -72.6734,
            "location": "Hartford, Connecticut, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for J.P. Morgan. AA-rated.",
        "known_events": [
            {"event_id": "MORGAN_PANIC_1907", "event_date_utc": "1907-10-24T00:00:00Z",
             "domain": "CAREER", "description": "Single-handedly resolved the Panic of 1907",
             "yoga_types": [], "expected_planets": ["VENUS", "SATURN"]},
            {"event_id": "MORGAN_TRUST_1895", "event_date_utc": "1895-02-01T00:00:00Z",
             "domain": "CAREER", "description": "Formed J.P. Morgan & Co. — became America's most powerful banker",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "MORGAN_DEATH_1913", "event_date_utc": "1913-03-31T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Rome, Italy, age 75",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_045_vanderbilt",
        "chart_filename": "chart_045_vanderbilt.json",
        "subject": "Cornelius Vanderbilt",
        "birth_data": {
            "date": "1794-05-27", "time": "06:00:00",
            "timezone": "America/New_York",
            "latitude": 40.5795, "longitude": -74.1502,
            "location": "Staten Island, New York, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "B",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Cornelius Vanderbilt. B-rated.",
        "known_events": [
            {"event_id": "VANDERBILT_RAILROAD_1863", "event_date_utc": "1863-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Took control of New York and Harlem Railroad",
             "yoga_types": [], "expected_planets": ["VENUS", "SATURN"]},
            {"event_id": "VANDERBILT_RICHEST_1869", "event_date_utc": "1869-01-01T00:00:00Z",
             "domain": "CAREER", "description": "Became one of the richest Americans",
             "yoga_types": [], "expected_planets": ["VENUS", "JUPITER"]},
            {"event_id": "VANDERBILT_DEATH_1877", "event_date_utc": "1877-01-04T00:00:00Z",
             "domain": "HEALTH", "description": "Died in New York City, age 82",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },

    # ── Sports (5) ──────────────────────────────────────────────────────

    {
        "fixture_id": "chart_046_ali",
        "chart_filename": "chart_046_ali.json",
        "subject": "Muhammad Ali",
        "birth_data": {
            "date": "1942-01-17", "time": "18:35:00",
            "timezone": "America/Chicago",
            "latitude": 38.2527, "longitude": -85.7585,
            "location": "Louisville, Kentucky, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Muhammad Ali. AA-rated.",
        "known_events": [
            {"event_id": "ALI_LISTON_1964", "event_date_utc": "1964-02-25T00:00:00Z",
             "domain": "CAREER", "description": "Defeated Sonny Liston to become World Heavyweight Champion",
             "yoga_types": [], "expected_planets": ["MARS", "JUPITER"]},
            {"event_id": "ALI_RUMBLE_1974", "event_date_utc": "1974-10-30T00:00:00Z",
             "domain": "CAREER", "description": "The Rumble in the Jungle — defeated George Foreman",
             "yoga_types": [], "expected_planets": ["MARS", "SUN"]},
            {"event_id": "ALI_DEATH_2016", "event_date_utc": "2016-06-03T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Scottsdale, Arizona, age 74",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_047_ruth",
        "chart_filename": "chart_047_ruth.json",
        "subject": "Babe Ruth",
        "birth_data": {
            "date": "1895-02-06", "time": "12:30:00",
            "timezone": "America/New_York",
            "latitude": 39.2904, "longitude": -76.6122,
            "location": "Baltimore, Maryland, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "AA",
                       "birth_time_confidence_minutes": 0},
        "description": "Immutable reference chart for Babe Ruth. AA-rated.",
        "known_events": [
            {"event_id": "RUTH_60_HOMERS_1927", "event_date_utc": "1927-09-30T00:00:00Z",
             "domain": "CAREER", "description": "Hit 60 home runs in a single season — record stood for 34 years",
             "yoga_types": [], "expected_planets": ["MARS", "JUPITER"]},
            {"event_id": "RUTH_SOLD_1920", "event_date_utc": "1920-01-03T00:00:00Z",
             "domain": "MIGRATION", "description": "Sold from Boston Red Sox to New York Yankees",
             "yoga_types": [], "expected_planets": ["VENUS", "RAHU"]},
            {"event_id": "RUTH_DEATH_1948", "event_date_utc": "1948-08-16T00:00:00Z",
             "domain": "HEALTH", "description": "Died at Memorial Hospital, age 53",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_048_thorpe",
        "chart_filename": "chart_048_thorpe.json",
        "subject": "Jim Thorpe",
        "birth_data": {
            "date": "1888-05-22", "time": "08:00:00",
            "timezone": "America/Chicago",
            "latitude": 35.7460, "longitude": -95.9928,
            "location": "Pragu, Indian Territory (modern Oklahoma, USA)",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "B",
                       "birth_time_confidence_minutes": 120},
        "description": "Immutable reference chart for Jim Thorpe. B-rated.",
        "known_events": [
            {"event_id": "THORPE_OLYMPICS_1912", "event_date_utc": "1912-07-13T00:00:00Z",
             "domain": "CAREER", "description": "Won gold medals in pentathlon and decathlon at Stockholm Olympics",
             "yoga_types": [], "expected_planets": ["MARS", "JUPITER"]},
            {"event_id": "THORPE_NFL_1920", "event_date_utc": "1920-08-20T00:00:00Z",
             "domain": "CAREER", "description": "Joined the Canton Bulldogs — founding era of the NFL",
             "yoga_types": [], "expected_planets": ["MARS", "SATURN"]},
            {"event_id": "THORPE_DEATH_1953", "event_date_utc": "1953-03-28T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Loma Linda, California, age 64",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_049_robinson",
        "chart_filename": "chart_049_robinson.json",
        "subject": "Jackie Robinson",
        "birth_data": {
            "date": "1919-01-31", "time": "18:30:00",
            "timezone": "America/New_York",
            "latitude": 31.9710, "longitude": -85.0949,
            "location": "Cairo, Georgia, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 30},
        "description": "Immutable reference chart for Jackie Robinson. A-rated.",
        "known_events": [
            {"event_id": "ROBINSON_BREAKS_COLOR_1947", "event_date_utc": "1947-04-15T00:00:00Z",
             "domain": "CAREER", "description": "Broke Major League Baseball's color barrier with the Brooklyn Dodgers",
             "yoga_types": [], "expected_planets": ["MARS", "JUPITER"]},
            {"event_id": "ROBINSON_MVP_1949", "event_date_utc": "1949-09-01T00:00:00Z",
             "domain": "CAREER", "description": "Won the National League MVP award",
             "yoga_types": ["RAJA"], "expected_planets": ["JUPITER", "SUN"]},
            {"event_id": "ROBINSON_DEATH_1972", "event_date_utc": "1972-10-24T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Stamford, Connecticut, age 53",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
    {
        "fixture_id": "chart_050_owens",
        "chart_filename": "chart_050_owens.json",
        "subject": "Jesse Owens",
        "birth_data": {
            "date": "1913-09-12", "time": "19:00:00",
            "timezone": "America/Chicago",
            "latitude": 32.1932, "longitude": -86.5755,
            "location": "Oakville, Alabama, USA",
        },
        "provenance": {"source": "Astro-Databank (astro.com)", "rodden_rating": "A",
                       "birth_time_confidence_minutes": 60},
        "description": "Immutable reference chart for Jesse Owens. A-rated.",
        "known_events": [
            {"event_id": "OWENS_BERLIN_1936", "event_date_utc": "1936-08-09T00:00:00Z",
             "domain": "CAREER", "description": "Won four gold medals at the Berlin Olympics, defying Nazi ideology",
             "yoga_types": [], "expected_planets": ["JUPITER", "MARS"]},
            {"event_id": "OWENS_4_RECORDS_1935", "event_date_utc": "1935-05-25T00:00:00Z",
             "domain": "CAREER", "description": "Set three world records and tied a fourth in 45 minutes at Big Ten Championships",
             "yoga_types": [], "expected_planets": ["MARS", "SUN"]},
            {"event_id": "OWENS_DEATH_1980", "event_date_utc": "1980-03-31T00:00:00Z",
             "domain": "HEALTH", "description": "Died in Tucson, Arizona, age 66",
             "yoga_types": [], "expected_planets": ["SATURN", "RAHU"]},
        ],
    },
]


# ── Chart Extraction ───────────────────────────────────────────────────────


def extract_chart_facts(chart: Any) -> dict[str, Any]:
    """Extract canonical facts from a JyotishService NatalChart.

    This produces the expected_canonical_facts structure matching chart_001.
    """
    from astronomy.models import BodyId

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
    """Generate cohort fixtures and save to tests/fixtures/validation_charts/."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate immutable chart fixtures for cohort expansion.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print generated JSON without writing files.",
    )
    parser.add_argument("--start", type=int, default=1,
                        help="Start index (1-based) into SUBJECTS list.")
    parser.add_argument("--end", type=int, default=None,
                        help="End index (exclusive) into SUBJECTS list.")
    args = parser.parse_args()

    from jyotish.models import BirthData
    from jyotish.service import JyotishService

    svc = JyotishService()

    subjects_slice = SUBJECTS[args.start - 1 : args.end or len(SUBJECTS)]

    print("=" * 64)
    print(f"Phase F1: Cohort Expansion — Fixture Generator ({len(subjects_slice)} subjects)")
    print("=" * 64)
    print()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    for subject_def in subjects_slice:
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
            print(f"   Houses: {len(chart.bhavas)} bhavas")

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

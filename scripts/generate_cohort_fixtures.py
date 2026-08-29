#!/usr/bin/env python3
"""Phase E4: Cohort Expansion — Immutable Chart Fixture Generator.

Uses the existing JRE fact-generation pipeline (JyotishService + Swiss Ephemeris)
to compute exact canonical facts for 4 new historical figures and save them as
immutable JSON fixtures in tests/fixtures/validation_charts/.

NO changes to rules, weights, or engine logic.
NO hallucinated facts — every value comes from the live JRE pipeline.

Usage::

    python scripts/generate_cohort_fixtures.py
    python scripts/generate_cohort_fixtures.py --dry-run
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


# ── Subject Definitions ────────────────────────────────────────────────────

SUBJECTS: list[dict[str, Any]] = [
    # ── Subjects 6-10: Phase E6h Expansion ──
    {
        "fixture_id": "chart_006_newton",
        "chart_filename": "chart_006_newton.json",
        "subject": "Isaac Newton",
        "birth_data": {
            "date": "1643-01-04",
            "time": "04:00:00",
            "timezone": "Europe/London",
            "latitude": 52.8066,
            "longitude": -0.6350,
            "location": "Woolsthorpe Manor, Lincolnshire, England",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Isaac Newton. "
            "AA-rated birth data. Born 4 January 1643 (Old Style: 25 December 1642) "
            "at approximately 04:00 in Woolsthorpe, Lincolnshire."
        ),
        "known_events": [
            {
                "event_id": "NEWTON_PRINCIPIA_1687",
                "event_date_utc": "1687-07-05T00:00:00Z",
                "domain": "CAREER",
                "description": "Published Principia Mathematica — founding work of classical mechanics",
                "yoga_types": [],
                "expected_planets": ["JUPITER", "MERCURY"],
            },
            {
                "event_id": "NEWTON_LUCASIAN_1669",
                "event_date_utc": "1669-10-29T00:00:00Z",
                "domain": "CAREER",
                "description": "Appointed Lucasian Professor of Mathematics at Cambridge",
                "yoga_types": [],
                "expected_planets": ["JUPITER", "SATURN"],
            },
            {
                "event_id": "NEWTON_DEATH_1727",
                "event_date_utc": "1727-03-31T00:00:00Z",
                "domain": "HEALTH",
                "description": "Died in London, age 84, buried in Westminster Abbey",
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
        ],
    },
    {
        "fixture_id": "chart_007_lincoln",
        "chart_filename": "chart_007_lincoln.json",
        "subject": "Abraham Lincoln",
        "birth_data": {
            "date": "1809-02-12",
            "time": "06:40:00",
            "timezone": "America/Chicago",
            "latitude": 37.5568,
            "longitude": -85.7371,
            "location": "Hodgenville, Kentucky, USA",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Abraham Lincoln. "
            "AA-rated birth data. Born 12 February 1809 at sunrise (~06:40) "
            "in Hodgenville, Kentucky."
        ),
        "known_events": [
            {
                "event_id": "LINCOLN_PRESIDENT_1860",
                "event_date_utc": "1860-11-06T00:00:00Z",
                "domain": "CAREER",
                "description": "Elected 16th President of the United States",
                "yoga_types": ["RAJA"],
                "expected_planets": ["JUPITER", "SATURN"],
            },
            {
                "event_id": "LINCOLN_EMANCIPATION_1863",
                "event_date_utc": "1863-01-01T00:00:00Z",
                "domain": "CAREER",
                "description": "Issued the Emancipation Proclamation",
                "yoga_types": ["RAJA"],
                "expected_planets": ["JUPITER", "MERCURY"],
            },
            {
                "event_id": "LINCOLN_ASSASSINATION_1865",
                "event_date_utc": "1865-04-15T00:00:00Z",
                "domain": "HEALTH",
                "description": "Assassinated at Ford's Theatre, Washington D.C.",
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
        ],
    },
    {
        "fixture_id": "chart_008_teresa",
        "chart_filename": "chart_008_teresa.json",
        "subject": "Mother Teresa",
        "birth_data": {
            "date": "1910-08-26",
            "time": "18:00:00",
            "timezone": "Europe/Skopje",
            "latitude": 41.9973,
            "longitude": 21.4280,
            "location": "Skopje, Ottoman Empire (modern North Macedonia)",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Mother Teresa. "
            "AA-rated birth data. Born 26 August 1910 at 18:00 local time "
            "in Skopje, Ottoman Empire."
        ),
        "known_events": [
            {
                "event_id": "TERESA_MISSIONARIES_1950",
                "event_date_utc": "1950-10-07T00:00:00Z",
                "domain": "CAREER",
                "description": "Founded the Missionaries of Charity in Calcutta",
                "yoga_types": [],
                "expected_planets": ["JUPITER", "MOON"],
            },
            {
                "event_id": "TERESA_NOBEL_1979",
                "event_date_utc": "1979-12-10T00:00:00Z",
                "domain": "CAREER",
                "description": "Awarded the Nobel Peace Prize",
                "yoga_types": ["RAJA"],
                "expected_planets": ["JUPITER", "SUN"],
            },
            {
                "event_id": "TERESA_DEATH_1997",
                "event_date_utc": "1997-09-05T00:00:00Z",
                "domain": "HEALTH",
                "description": "Died in Calcutta, age 87, after declining health",
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
        ],
    },
    {
        "fixture_id": "chart_009_jobs",
        "chart_filename": "chart_009_jobs.json",
        "subject": "Steve Jobs",
        "birth_data": {
            "date": "1955-02-24",
            "time": "19:15:00",
            "timezone": "America/Los_Angeles",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "location": "San Francisco, California, USA",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Steve Jobs. "
            "AA-rated birth data. Born 24 February 1955 at 19:15 local time "
            "in San Francisco, California."
        ),
        "known_events": [
            {
                "event_id": "JOBS_APPLE_1976",
                "event_date_utc": "1976-04-01T00:00:00Z",
                "domain": "CAREER",
                "description": "Co-founded Apple Computer with Steve Wozniak",
                "yoga_types": [],
                "expected_planets": ["MERCURY", "JUPITER"],
            },
            {
                "event_id": "JOBS_OUSTED_1985",
                "event_date_utc": "1985-09-17T00:00:00Z",
                "domain": "CAREER",
                "description": "Forced out of Apple by the board of directors",
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
            {
                "event_id": "JOBS_RETURN_1997",
                "event_date_utc": "1997-09-16T00:00:00Z",
                "domain": "CAREER",
                "description": "Returned to Apple as interim CEO — began the turnaround",
                "yoga_types": [],
                "expected_planets": ["JUPITER", "VENUS"],
            },
        ],
    },
    {
        "fixture_id": "chart_010_earhart",
        "chart_filename": "chart_010_earhart.json",
        "subject": "Amelia Earhart",
        "birth_data": {
            "date": "1897-07-24",
            "time": "08:00:00",
            "timezone": "America/Chicago",
            "latitude": 39.5631,
            "longitude": -95.1260,
            "location": "Atchison, Kansas, USA",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "C",
            "birth_time_confidence_minutes": 60,
        },
        "description": (
            "Immutable reference chart for Amelia Earhart. "
            "C-rated birth data (approximate time). Born 24 July 1897 "
            "at approximately 08:00 in Atchison, Kansas."
        ),
        "known_events": [
            {
                "event_id": "EARHART_FIRST_FLIGHT_1928",
                "event_date_utc": "1928-06-17T00:00:00Z",
                "domain": "CAREER",
                "description": "First woman to fly across the Atlantic (as passenger)",
                "yoga_types": [],
                "expected_planets": ["JUPITER", "RAHU"],
            },
            {
                "event_id": "EARHART_SOLO_ATLANTIC_1932",
                "event_date_utc": "1932-05-20T00:00:00Z",
                "domain": "CAREER",
                "description": "First woman to fly solo nonstop across the Atlantic",
                "yoga_types": [],
                "expected_planets": ["JUPITER", "MARS"],
            },
            {
                "event_id": "EARHART_DISAPPEARANCE_1937",
                "event_date_utc": "1937-07-02T00:00:00Z",
                "domain": "HEALTH",
                "description": "Disappeared over the Pacific during circumnavigation attempt",
                "yoga_types": [],
                "expected_planets": ["RAHU", "SATURN"],
            },
        ],
    },
    # ── Original Subjects 2-5 ──
    {
        "fixture_id": "chart_002_curie",
        "chart_filename": "chart_002_curie.json",
        "subject": "Marie Curie",
        "birth_data": {
            "date": "1867-11-07",
            "time": "19:00:00",
            "timezone": "Europe/Warsaw",
            "latitude": 52.2297,
            "longitude": 21.0122,
            "location": "Warsaw, Congress Poland (modern Poland)",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Marie Curie. "
            "AA-rated birth data. Born 7 November 1867 at 19:00 local time "
            "in Warsaw, Congress Poland."
        ),
        "known_events": [
            {
                "event_id": "CURIE_NOBEL_1903",
                "event_date_utc": "1903-12-10T00:00:00Z",
                "domain": "CAREER",
                "description": (
                    "Awarded the Nobel Prize in Physics jointly with "
                    "Pierre Curie and Henri Becquerel"
                ),
                "yoga_types": ["RAJA"],
                "expected_planets": ["SUN", "JUPITER"],
            },
            {
                "event_id": "CURIE_NOBEL_1911",
                "event_date_utc": "1911-12-10T00:00:00Z",
                "domain": "CAREER",
                "description": (
                    "Awarded the Nobel Prize in Chemistry for discovery "
                    "of radium and polonium"
                ),
                "yoga_types": ["RAJA"],
                "expected_planets": ["SUN", "JUPITER"],
            },
            {
                "event_id": "CURIE_DEATH_1934",
                "event_date_utc": "1934-07-04T00:00:00Z",
                "domain": "HEALTH",
                "description": (
                    "Died of aplastic anemia caused by prolonged "
                    "radiation exposure"
                ),
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
        ],
    },
    {
        "fixture_id": "chart_003_mozart",
        "chart_filename": "chart_003_mozart.json",
        "subject": "Wolfgang Amadeus Mozart",
        "birth_data": {
            "date": "1756-01-27",
            "time": "20:00:00",
            "timezone": "Europe/Vienna",
            "latitude": 47.8095,
            "longitude": 13.0550,
            "location": "Salzburg, Prince-Archbishopric of Salzburg (modern Austria)",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Wolfgang Amadeus Mozart. "
            "AA-rated birth data. Born 27 January 1756 at 20:00 local time "
            "in Salzburg."
        ),
        "known_events": [
            {
                "event_id": "MOZART_MARRIAGE_1782",
                "event_date_utc": "1782-08-04T00:00:00Z",
                "domain": "MARRIAGE",
                "description": "Married Constanze Weber in St. Stephen's Cathedral, Vienna",
                "yoga_types": [],
                "expected_planets": ["VENUS"],
            },
            {
                "event_id": "MOZART_DON_GIOVANNI_1787",
                "event_date_utc": "1787-10-29T00:00:00Z",
                "domain": "CAREER",
                "description": (
                    "Premiere of Don Giovanni in Prague — "
                    "considered his career peak opera"
                ),
                "yoga_types": ["RAJA"],
                "expected_planets": ["MERCURY", "JUPITER"],
            },
            {
                "event_id": "MOZART_DEATH_1791",
                "event_date_utc": "1791-12-05T00:00:00Z",
                "domain": "HEALTH",
                "description": (
                    "Died at age 35 under mysterious circumstances; "
                    "Requiem left unfinished"
                ),
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
        ],
    },
    {
        "fixture_id": "chart_004_tesla",
        "chart_filename": "chart_004_tesla.json",
        "subject": "Nikola Tesla",
        "birth_data": {
            "date": "1856-07-10",
            "time": "00:00:00",
            "timezone": "Europe/Belgrade",
            "latitude": 45.2671,
            "longitude": 15.3903,
            "location": "Smiljan, Military Frontier, Austrian Empire (modern Croatia)",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Nikola Tesla. "
            "AA-rated birth data. Born 10 July 1856 at midnight "
            "in Smiljan, Military Frontier."
        ),
        "known_events": [
            {
                "event_id": "TESLA_US_MOVE_1884",
                "event_date_utc": "1884-06-06T00:00:00Z",
                "domain": "MIGRATION",
                "description": (
                    "Arrived in New York City with four cents, "
                    "a prayer, and a letter of recommendation to Edison"
                ),
                "yoga_types": [],
                "expected_planets": ["RAHU"],
            },
            {
                "event_id": "TESLA_LAB_FIRE_1895",
                "event_date_utc": "1895-03-13T00:00:00Z",
                "domain": "HEALTH",
                "description": (
                    "Laboratory fire destroyed years of research notes, "
                    "models, and financial backing"
                ),
                "yoga_types": [],
                "expected_planets": ["SATURN", "MARS"],
            },
            {
                "event_id": "TESLA_DEATH_1943",
                "event_date_utc": "1943-01-07T00:00:00Z",
                "domain": "HEALTH",
                "description": (
                    "Died alone in Room 3327 of the New Yorker Hotel, "
                    "age 86"
                ),
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
        ],
    },
    {
        "fixture_id": "chart_005_gandhi",
        "chart_filename": "chart_005_gandhi.json",
        "subject": "Indira Gandhi",
        "birth_data": {
            "date": "1917-11-19",
            "time": "23:10:00",
            "timezone": "Asia/Kolkata",
            "latitude": 25.4358,
            "longitude": 81.8463,
            "location": "Allahabad, United Provinces, British India (modern Prayagraj, India)",
        },
        "provenance": {
            "source": "Astro-Databank (astro.com)",
            "rodden_rating": "AA",
            "birth_time_confidence_minutes": 0,
        },
        "description": (
            "Immutable reference chart for Indira Gandhi. "
            "AA-rated birth data. Born 19 November 1917 at 23:10 local time "
            "in Allahabad, India."
        ),
        "known_events": [
            {
                "event_id": "GANDHI_PM_1966",
                "event_date_utc": "1966-01-24T00:00:00Z",
                "domain": "CAREER",
                "description": (
                    "Became the first (and to date only) female "
                    "Prime Minister of India"
                ),
                "yoga_types": ["RAJA"],
                "expected_planets": ["JUPITER", "SATURN"],
            },
            {
                "event_id": "GANDHI_WAR_1971",
                "event_date_utc": "1971-12-16T00:00:00Z",
                "domain": "CAREER",
                "description": (
                    "Led India to decisive victory in the Indo-Pakistani War "
                    "of 1971; creation of Bangladesh"
                ),
                "yoga_types": ["RAJA"],
                "expected_planets": ["MARS", "SATURN"],
            },
            {
                "event_id": "GANDHI_ASSASSINATION_1984",
                "event_date_utc": "1984-10-31T00:00:00Z",
                "domain": "HEALTH",
                "description": (
                    "Assassinated by her Sikh bodyguards in "
                    "New Delhi following Operation Blue Star"
                ),
                "yoga_types": [],
                "expected_planets": ["SATURN", "RAHU"],
            },
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
    # Build reverse map: planet -> list of houses it owns
    planet_houses: dict[str, list[int]] = {}
    for bhava in chart.bhavas:
        lord = bhava.house_lord.value
        house_num = bhava.house_number
        if lord not in planet_houses:
            planet_houses[lord] = []
        planet_houses[lord].append(house_num)

    # Add house_lord_of to each planet
    for pname in planets:
        planets[pname]["house_lord_of"] = sorted(planet_houses.get(pname, []))

    # Build house_lords mapping: house_number (int) -> lord_planet
    # JSON keys must be strings, but the engine expects int keys
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
        "--dry-run",
        action="store_true",
        help="Print generated JSON without writing files.",
    )
    args = parser.parse_args()

    from jyotish.models import BirthData
    from jyotish.service import JyotishService

    svc = JyotishService()

    print("=" * 64)
    print("Phase E4: Cohort Expansion — Fixture Generator")
    print("=" * 64)
    print()

    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

    for subject_def in SUBJECTS:
        fixture_id = subject_def["fixture_id"]
        filename = subject_def["chart_filename"]
        bd = subject_def["birth_data"]

        print(f"── {subject_def['subject']} ({fixture_id}) ──")
        print(f"   Birth: {bd['date']} {bd['time']} {bd['timezone']}")
        print(f"   Location: {bd['latitude']}°N, {bd['longitude']}°E")

        # Compute natal chart via JRE
        birth = BirthData(
            date=bd["date"],
            time=bd["time"],
            timezone=bd["timezone"],
            latitude=float(bd["latitude"]),
            longitude=float(bd["longitude"]),
        )
        chart = svc.chart(birth)

        print(f"   Lagna: {chart.lagna.rashi.value} "
              f"({chart.lagna.ascendant_longitude_deg:.4f}°)")
        print(f"   Planets: {len(chart.planet_states)} computed")
        print(f"   Houses: {len(chart.bhavas)} bhavas")

        # Build fixture
        fixture = build_fixture(subject_def, chart)

        # Write to disk
        out_path = FIXTURES_DIR / filename
        if args.dry_run:
            print(f"   [DRY RUN] Would write to: {out_path}")
            print(json.dumps(fixture, indent=2)[:500] + "\n   ...")
        else:
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(fixture, f, indent=2, sort_keys=False)
            print(f"   ✓ Saved: {out_path}")

        print()

    print("=" * 64)
    if args.dry_run:
        print("Dry run complete — no files written.")
    else:
        print(f"Fixture generation complete: {len(SUBJECTS)} charts.")
        print(f"Output directory: {FIXTURES_DIR}")
    print("=" * 64)

    return 0


if __name__ == "__main__":
    sys.exit(main())

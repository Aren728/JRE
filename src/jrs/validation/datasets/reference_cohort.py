"""JRS-089: Initial Historical Reference Dataset — 12-Chart Cohort.

Provides REFERENCE_COHORT_12, a verified reference dataset of 12 historical
charts with AA-rated birth data from Astro-Databank (astro.com) and
independently verifiable ground-truth historical events.

All birth data uses ISO-8601 UTC-aware timestamps. Every chart subject
has a Rodden Rating of AA unless explicitly noted. Event records contain
only factual real-world outcomes — zero astrological descriptors.

Source: Astro-Databank (astro.com); public historical records.
"""

from __future__ import annotations

from typing import List, Tuple

from jrs.validation.models import (
    BirthProvenance,
    ChartSubject,
    DomainType,
    HistoricalEvent,
    RoddenRating,
)

# ── Reference Cohort: 12 Verified Historical Charts ─────────────────────────

REFERENCE_COHORT_12: List[Tuple[ChartSubject, HistoricalEvent]] = [
    # ── 1. Albert Einstein ────────────────────────────────────────────────
    # Nobel Prize in Physics 1921
    (
        ChartSubject(
            chart_id="EINSTEIN_1879",
            latitude=48.4011,
            longitude=9.9876,
            birth_timestamp="1879-03-14T11:30:00+01:00",
            timezone="Europe/Berlin",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="EINSTEIN_NOBEL_1921",
            chart_id="EINSTEIN_1879",
            domain=DomainType.CAREER_PEAK,
            start_date="1921-11-09T00:00:00Z",
            end_date="1921-11-09T23:59:59Z",
            event_certainty=1.0,
            description="Awarded the Nobel Prize in Physics for the photoelectric effect",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "MODERATE",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 2. Queen Elizabeth II ─────────────────────────────────────────────
    # Coronation 1953
    (
        ChartSubject(
            chart_id="ELIZABETH_II_1926",
            latitude=51.5074,
            longitude=-0.1278,
            birth_timestamp="1926-04-21T02:40:00+01:00",
            timezone="Europe/London",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="ELIZABETH_CORONATION_1953",
            chart_id="ELIZABETH_II_1926",
            domain=DomainType.CAREER_PEAK,
            start_date="1953-06-02T00:00:00Z",
            end_date="1953-06-02T23:59:59Z",
            event_certainty=1.0,
            description="Coronation as Queen of the United Kingdom at Westminster Abbey",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "STRONG",
                "modification": "MODERATE",
                "confirmation": "MODERATE",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 3. Steve Jobs ────────────────────────────────────────────────────
    # Co-founded Apple Computer 1976
    (
        ChartSubject(
            chart_id="JOBS_1955",
            latitude=37.7749,
            longitude=-122.4194,
            birth_timestamp="1955-02-24T19:15:00-08:00",
            timezone="America/Los_Angeles",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="JOBS_APPLE_1976",
            chart_id="JOBS_1955",
            domain=DomainType.WEALTH_EVENT,
            start_date="1976-04-01T00:00:00Z",
            end_date="1976-04-01T23:59:59Z",
            event_certainty=1.0,
            description="Co-founded Apple Computer with Steve Wozniak and Ronald Wayne",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "MODERATE",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 4. Marie Curie ───────────────────────────────────────────────────
    # Nobel Prize in Physics 1903
    (
        ChartSubject(
            chart_id="CURIE_1867",
            latitude=52.2297,
            longitude=21.0122,
            birth_timestamp="1867-11-07T12:00:00+01:00",
            timezone="Europe/Warsaw",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="CURIE_NOBEL_1903",
            chart_id="CURIE_1867",
            domain=DomainType.CAREER_PEAK,
            start_date="1903-12-10T00:00:00Z",
            end_date="1903-12-10T23:59:59Z",
            event_certainty=1.0,
            description="Awarded the Nobel Prize in Physics jointly with Pierre Curie and Henri Becquerel",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "MODERATE",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 5. Franklin D. Roosevelt ──────────────────────────────────────────
    # Elected President 1932
    (
        ChartSubject(
            chart_id="FDR_1882",
            latitude=41.7959,
            longitude=-73.9370,
            birth_timestamp="1882-01-30T20:45:00-05:00",
            timezone="America/New_York",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="FDR_ELECTED_1932",
            chart_id="FDR_1882",
            domain=DomainType.CAREER_PEAK,
            start_date="1932-11-08T00:00:00Z",
            end_date="1932-11-08T23:59:59Z",
            event_certainty=1.0,
            description="Elected 32nd President of the United States",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "STRONG",
                "modification": "MODERATE",
                "confirmation": "MODERATE",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 6. Princess Diana ────────────────────────────────────────────────
    # Marriage to Prince Charles 1981
    (
        ChartSubject(
            chart_id="DIANA_1961",
            latitude=52.8234,
            longitude=0.5017,
            birth_timestamp="1961-07-01T18:45:00+01:00",
            timezone="Europe/London",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="DIANA_MARRIAGE_1981",
            chart_id="DIANA_1961",
            domain=DomainType.MARRIAGE,
            start_date="1981-07-29T00:00:00Z",
            end_date="1981-07-29T23:59:59Z",
            event_certainty=1.0,
            description="Marriage to Prince Charles at St Paul's Cathedral, London",
            expected_layer_states={
                "formation": "WEAK",
                "relationship": "STRONG",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "MODERATE",
            },
        ),
    ),
    # ── 7. John F. Kennedy ───────────────────────────────────────────────
    # Elected President 1960
    (
        ChartSubject(
            chart_id="JFK_1917",
            latitude=42.3334,
            longitude=-71.1237,
            birth_timestamp="1917-05-29T15:00:00-05:00",
            timezone="America/New_York",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="JFK_ELECTED_1960",
            chart_id="JFK_1917",
            domain=DomainType.CAREER_PEAK,
            start_date="1960-11-08T00:00:00Z",
            end_date="1960-11-08T23:59:59Z",
            event_certainty=1.0,
            description="Elected 35th President of the United States",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "STRONG",
                "modification": "MODERATE",
                "confirmation": "MODERATE",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 8. Marilyn Monroe ────────────────────────────────────────────────
    # Career peak 1953 (Gentlemen Prefer Blondes, Niagara)
    (
        ChartSubject(
            chart_id="MONROE_1926",
            latitude=34.0522,
            longitude=-118.2437,
            birth_timestamp="1926-06-01T09:30:00-07:00",
            timezone="America/Los_Angeles",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="MONROE_PEAK_1953",
            chart_id="MONROE_1926",
            domain=DomainType.CAREER_PEAK,
            start_date="1953-07-15T00:00:00Z",
            end_date="1953-12-31T23:59:59Z",
            event_certainty=1.0,
            description="Career peak year starring in Gentlemen Prefer Blondes and Niagara",
            expected_layer_states={
                "formation": "MODERATE",
                "relationship": "WEAK",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 9. Winston Churchill ──────────────────────────────────────────────
    # Became Prime Minister 1940
    (
        ChartSubject(
            chart_id="CHURCHILL_1874",
            latitude=51.8415,
            longitude=-1.3615,
            birth_timestamp="1874-11-30T01:00:00+00:00",
            timezone="Europe/London",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="CHURCHILL_PM_1940",
            chart_id="CHURCHILL_1874",
            domain=DomainType.CAREER_PEAK,
            start_date="1940-05-10T00:00:00Z",
            end_date="1940-05-10T23:59:59Z",
            event_certainty=1.0,
            description="Became Prime Minister of the United Kingdom",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "STRONG",
                "modification": "MODERATE",
                "confirmation": "MODERATE",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 10. Mahatma Gandhi ───────────────────────────────────────────────
    # Independence Movement / Salt March 1930
    (
        ChartSubject(
            chart_id="GANDHI_1869",
            latitude=21.6414,
            longitude=69.6088,
            birth_timestamp="1869-10-02T07:45:00+05:30",
            timezone="Asia/Kolkata",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="GANDHI_SALT_1930",
            chart_id="GANDHI_1869",
            domain=DomainType.CAREER_PEAK,
            start_date="1930-03-12T00:00:00Z",
            end_date="1930-04-06T23:59:59Z",
            event_certainty=1.0,
            description="Led the Salt March (Dandi March) as a pivotal act of civil disobedience",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "MODERATE",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 11. Walt Disney ──────────────────────────────────────────────────
    # Founded Disney Brothers Studio 1923
    (
        ChartSubject(
            chart_id="DISNEY_1901",
            latitude=41.8827,
            longitude=-87.6233,
            birth_timestamp="1901-12-05T08:35:00-06:00",
            timezone="America/Chicago",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="DISNEY_STUDIO_1923",
            chart_id="DISNEY_1901",
            domain=DomainType.WEALTH_EVENT,
            start_date="1923-10-16T00:00:00Z",
            end_date="1923-10-16T23:59:59Z",
            event_certainty=1.0,
            description="Founded the Disney Brothers Cartoon Studio (later Walt Disney Company)",
            expected_layer_states={
                "formation": "STRONG",
                "relationship": "MODERATE",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            },
        ),
    ),
    # ── 12. Julia Roberts ────────────────────────────────────────────────
    # Oscar Win for Erin Brockovich 2001
    (
        ChartSubject(
            chart_id="ROBERTS_1967",
            latitude=33.8689,
            longitude=-84.4847,
            birth_timestamp="1967-10-28T00:16:00-04:00",
            timezone="America/New_York",
            provenance=BirthProvenance(
                source="Astro-Databank (astro.com)",
                rodden_rating=RoddenRating.AA,
                birth_time_confidence_minutes=0,
            ),
        ),
        HistoricalEvent(
            event_id="ROBERTS_OSCAR_2001",
            chart_id="ROBERTS_1967",
            domain=DomainType.CAREER_PEAK,
            start_date="2001-03-25T00:00:00Z",
            end_date="2001-03-25T23:59:59Z",
            event_certainty=1.0,
            description="Won the Academy Award for Best Actress for Erin Brockovich",
            expected_layer_states={
                "formation": "MODERATE",
                "relationship": "WEAK",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            },
        ),
    ),
]

"""Integration tests for JRE-019 Prashna.

Verifies the full PrashnaReport against a known reference query,
ensuring end-to-end correctness from inputs through to
the final Prashna Lagna and house mapping output.
"""

from __future__ import annotations

from jyotish import BodyId, RashiId

from prashna.models import (
    PrashnaCategory,
    PrashnaChart,
    PrashnaHouseMapping,
    PrashnaReport,
    QueryLocation,
)
from prashna.service import PrashnaService
from tests.unit.prashna.conftest import make_planet_state, make_query_location


# --------------------------------------------------------------------------- #
# Reference query: Krittika nakshatra Moon → Sun lord → Leo Prashna Lagna
# --------------------------------------------------------------------------- #

REFERENCE_QUERY_TIME = "2024-06-21T14:45:00Z"
REFERENCE_LOCATION = make_query_location(19.0760, 72.8777)  # Mumbai

REFERENCE_PLANETS = (
    make_planet_state(BodyId.SUN, 89.0),       # Cancer
    make_planet_state(BodyId.MOON, 33.0),      # Taurus (Krittika → lord = Sun → Leo)
    make_planet_state(BodyId.MARS, 60.0),      # Gemini
    make_planet_state(BodyId.MERCURY, 95.0),   # Cancer
    make_planet_state(BodyId.JUPITER, 150.0),  # Virgo
    make_planet_state(BodyId.VENUS, 210.0),    # Libra
    make_planet_state(BodyId.SATURN, 270.0),   # Capricorn
)


class TestReferenceQueryKrittika:
    """Full integration test against a reference Krittika-nakshatra query."""

    def test_full_report_structure(self) -> None:
        svc = PrashnaService()
        report = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "CAREER", REFERENCE_PLANETS,
        )
        assert isinstance(report, PrashnaReport)
        assert isinstance(report.chart, PrashnaChart)
        assert isinstance(report.house_mapping, PrashnaHouseMapping)

    def test_prashna_lagna_is_leo(self) -> None:
        # Moon at 33.0 → Taurus, Krittika nakshatra, lord = Sun → Leo
        svc = PrashnaService()
        report = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "CAREER", REFERENCE_PLANETS,
        )
        assert report.chart.prashna_lagna == RashiId.SIMHA

    def test_moon_rashi_recorded(self) -> None:
        svc = PrashnaService()
        report = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "CAREER", REFERENCE_PLANETS,
        )
        assert report.chart.query_moon_rashi == RashiId.VRISHABHA

    def test_query_metadata_preserved(self) -> None:
        svc = PrashnaService()
        report = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "CAREER", REFERENCE_PLANETS,
        )
        assert report.chart.query_time_utc == REFERENCE_QUERY_TIME
        assert report.chart.query_location.latitude == 19.0760
        assert report.chart.query_location.longitude == 72.8777

    def test_career_houses_correct(self) -> None:
        svc = PrashnaService()
        report = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "CAREER", REFERENCE_PLANETS,
        )
        assert report.house_mapping.query_category == PrashnaCategory.CAREER
        assert report.house_mapping.primary_house == 10
        assert report.house_mapping.secondary_house == 6

    def test_deterministic_output(self) -> None:
        svc = PrashnaService()
        r1 = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "CAREER", REFERENCE_PLANETS,
        )
        r2 = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "CAREER", REFERENCE_PLANETS,
        )
        assert r1.to_dict() == r2.to_dict()


class TestReferenceQueryAshvini:
    """Integration test for an Ashvini-nakshatra query (Moon lord = Ketu → fallback)."""

    def test_prashna_lagna_for_ashvini(self) -> None:
        # Moon at 13.0 → Ashvini nakshatra (0-13.33), lord = Ketu
        # Ketu not in the classical mapping → fallback to Leo
        planets = (
            make_planet_state(BodyId.MOON, 13.0, nakshatra_lord=BodyId.KETU),
            make_planet_state(BodyId.SUN, 10.0),
        )
        svc = PrashnaService()
        report = svc.cast_prashna(
            REFERENCE_QUERY_TIME, REFERENCE_LOCATION, "WEALTH", planets,
        )
        # Fallback gives Leo (SIMHA)
        assert report.chart.prashna_lagna == RashiId.SIMHA
        assert report.house_mapping.primary_house == 2  # Wealth
        assert report.house_mapping.secondary_house == 11


class TestReferenceQueryMultipleCategories:
    """Test that the same chart produces different house mappings per category."""

    def test_same_chart_different_categories(self) -> None:
        svc = PrashnaService()
        categories_expected = {
            "WEALTH": (2, 11),
            "CAREER": (10, 6),
            "MARRIAGE": (7, 2),
            "HEALTH": (1, 8),
            "EDUCATION": (4, 9),
            "PROPERTY": (4, 11),
            "LITIGATION": (6, 7),
            "TRAVEL": (3, 12),
            "CHILDREN": (5, 11),
            "GENERAL": (1, 7),
        }
        for cat_name, (primary, secondary) in categories_expected.items():
            report = svc.cast_prashna(
                REFERENCE_QUERY_TIME, REFERENCE_LOCATION, cat_name, REFERENCE_PLANETS,
            )
            assert report.house_mapping.primary_house == primary, f"{cat_name} primary"
            assert report.house_mapping.secondary_house == secondary, f"{cat_name} secondary"

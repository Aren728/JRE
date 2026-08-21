"""Unit tests for JRE-019 PrashnaService."""

from __future__ import annotations

import pytest

from jyotish import BodyId, RashiId

from prashna.errors import InvalidPrashnaRequestError
from prashna.models import PrashnaCategory, PrashnaReport, QueryLocation
from prashna.service import PrashnaService
from tests.unit.prashna.conftest import make_planet_state, make_query_location


QUERY_TIME = "2024-01-15T10:30:00Z"
QUERY_LOC = make_query_location(28.6139, 77.2090)


class TestPrashnaServiceBasic:
    def test_cast_prashna_wealth(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = PrashnaService()
        report = svc.cast_prashna(QUERY_TIME, QUERY_LOC, "WEALTH", planets)
        assert isinstance(report, PrashnaReport)
        assert report.chart.query_time_utc == QUERY_TIME
        assert report.chart.query_location == QUERY_LOC
        assert report.house_mapping.query_category == PrashnaCategory.WEALTH
        assert report.house_mapping.primary_house == 2
        assert report.house_mapping.secondary_house == 11

    def test_cast_prashna_career(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = PrashnaService()
        report = svc.cast_prashna(QUERY_TIME, QUERY_LOC, "CAREER", planets)
        assert report.house_mapping.query_category == PrashnaCategory.CAREER
        assert report.house_mapping.primary_house == 10
        assert report.house_mapping.secondary_house == 6

    def test_cast_prashna_marriage(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = PrashnaService()
        report = svc.cast_prashna(QUERY_TIME, QUERY_LOC, "MARRIAGE", planets)
        assert report.house_mapping.primary_house == 7
        assert report.house_mapping.secondary_house == 2

    def test_prashna_lagna_deterministic_from_moon(self) -> None:
        # Moon at 33.0 deg = Taurus, Krittika nakshatra (lord = Sun)
        # Sun's rashi = Leo (SIMHA)
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
        )
        svc = PrashnaService()
        report = svc.cast_prashna(QUERY_TIME, QUERY_LOC, "GENERAL", planets)
        assert report.chart.prashna_lagna == RashiId.SIMHA
        assert report.chart.query_moon_rashi == RashiId.VRISHABHA

    def test_deterministic(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
        )
        svc = PrashnaService()
        r1 = svc.cast_prashna(QUERY_TIME, QUERY_LOC, "WEALTH", planets)
        r2 = svc.cast_prashna(QUERY_TIME, QUERY_LOC, "WEALTH", planets)
        assert r1.to_dict() == r2.to_dict()

    def test_all_categories_produce_valid_report(self) -> None:
        planets = (
            make_planet_state(BodyId.SUN, 10.0),
            make_planet_state(BodyId.MOON, 33.0),
            make_planet_state(BodyId.MARS, 60.0),
            make_planet_state(BodyId.MERCURY, 90.0),
            make_planet_state(BodyId.JUPITER, 150.0),
            make_planet_state(BodyId.VENUS, 210.0),
            make_planet_state(BodyId.SATURN, 270.0),
        )
        svc = PrashnaService()
        for category in PrashnaCategory:
            report = svc.cast_prashna(QUERY_TIME, QUERY_LOC, category.value, planets)
            assert isinstance(report, PrashnaReport)
            assert report.house_mapping.query_category == category
            assert 1 <= report.house_mapping.primary_house <= 12
            assert 1 <= report.house_mapping.secondary_house <= 12


class TestPrashnaServiceValidation:
    def test_empty_query_time_raises(self) -> None:
        svc = PrashnaService()
        planets = (make_planet_state(BodyId.SUN, 10.0), make_planet_state(BodyId.MOON, 33.0))
        with pytest.raises(InvalidPrashnaRequestError):
            svc.cast_prashna("", QUERY_LOC, "WEALTH", planets)

    def test_invalid_category_raises(self) -> None:
        svc = PrashnaService()
        planets = (make_planet_state(BodyId.SUN, 10.0), make_planet_state(BodyId.MOON, 33.0))
        with pytest.raises(InvalidPrashnaRequestError):
            svc.cast_prashna(QUERY_TIME, QUERY_LOC, "INVALID", planets)

    def test_empty_planet_states_raises(self) -> None:
        svc = PrashnaService()
        with pytest.raises(InvalidPrashnaRequestError):
            svc.cast_prashna(QUERY_TIME, QUERY_LOC, "WEALTH", ())

    def test_missing_moon_raises(self) -> None:
        svc = PrashnaService()
        planets = (make_planet_state(BodyId.SUN, 10.0),)
        with pytest.raises(InvalidPrashnaRequestError):
            svc.cast_prashna(QUERY_TIME, QUERY_LOC, "WEALTH", planets)

    def test_invalid_location_type_raises(self) -> None:
        svc = PrashnaService()
        planets = (make_planet_state(BodyId.SUN, 10.0), make_planet_state(BodyId.MOON, 33.0))
        with pytest.raises(InvalidPrashnaRequestError):
            svc.cast_prashna(QUERY_TIME, "NOT_A_LOCATION", "WEALTH", planets)  # type: ignore[arg-type]

    def test_empty_category_string_raises(self) -> None:
        svc = PrashnaService()
        planets = (make_planet_state(BodyId.SUN, 10.0), make_planet_state(BodyId.MOON, 33.0))
        with pytest.raises(InvalidPrashnaRequestError):
            svc.cast_prashna(QUERY_TIME, QUERY_LOC, "", planets)

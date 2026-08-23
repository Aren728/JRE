"""Unit tests for JRE-066 Western Astrology calculation service.

Tests the full calculation pipeline using known historical charts.
Verifies determinism, correct tropical positions, house cusps,
aspects, and essential dignities.
"""

from __future__ import annotations

import datetime as dt

import pytest
from src.western.errors import WesternInputError
from src.western.models import (
    WesternAspectType,
    WesternChart,
    WesternDignity,
    WesternHouseSystem,
    WesternPlanet,
)
from src.western.service import WesternCalculationService

# ── Test Fixtures ────────────────────────────────────────────────────────────


@pytest.fixture
def svc() -> WesternCalculationService:
    """Default WesternCalculationService instance."""
    return WesternCalculationService()


# Einstein: March 14, 1879, 10:50:08 UTC, Ulm (48.4N, 9.99E)
_EINSTEIN_DATE = dt.date(1879, 3, 14)
_EINSTEIN_TIME = dt.time(10, 50, 8)
_EINSTEIN_LAT = 48.4
_EINSTEIN_LON = 9.99

# JFK: May 29, 1917, 3:00 PM EDT = 19:00 UTC, Brookline MA (42.33N, 71.12W)
_JFK_DATE = dt.date(1917, 5, 29)
_JFK_TIME = dt.time(19, 0, 0)
_JFK_LAT = 42.33
_JFK_LON = -71.12


# ── Input Validation Tests ───────────────────────────────────────────────────


class TestInputValidation:
    """Tests for input parameter validation."""

    def test_invalid_birth_date_type(self, svc: WesternCalculationService) -> None:
        with pytest.raises(WesternInputError, match="datetime.date"):
            svc.calculate(
                birth_date="2000-01-01",  # type: ignore[arg-type]
                birth_time=dt.time(12, 0),
                latitude=40.0,
                longitude=-74.0,
            )

    def test_invalid_birth_time_type(self, svc: WesternCalculationService) -> None:
        with pytest.raises(WesternInputError, match="datetime.time"):
            svc.calculate(
                birth_date=dt.date(2000, 1, 1),
                birth_time="12:00",  # type: ignore[arg-type]
                latitude=40.0,
                longitude=-74.0,
            )

    def test_latitude_out_of_range(self, svc: WesternCalculationService) -> None:
        with pytest.raises(WesternInputError, match="latitude"):
            svc.calculate(
                birth_date=dt.date(2000, 1, 1),
                birth_time=dt.time(12, 0),
                latitude=91.0,
                longitude=-74.0,
            )

    def test_latitude_negative_out_of_range(
        self, svc: WesternCalculationService
    ) -> None:
        with pytest.raises(WesternInputError, match="latitude"):
            svc.calculate(
                birth_date=dt.date(2000, 1, 1),
                birth_time=dt.time(12, 0),
                latitude=-91.0,
                longitude=-74.0,
            )

    def test_longitude_out_of_range(self, svc: WesternCalculationService) -> None:
        with pytest.raises(WesternInputError, match="longitude"):
            svc.calculate(
                birth_date=dt.date(2000, 1, 1),
                birth_time=dt.time(12, 0),
                latitude=40.0,
                longitude=181.0,
            )

    def test_date_before_1582(self, svc: WesternCalculationService) -> None:
        with pytest.raises(WesternInputError, match="1582"):
            svc.calculate(
                birth_date=dt.date(1500, 1, 1),
                birth_time=dt.time(12, 0),
                latitude=40.0,
                longitude=-74.0,
            )

    def test_valid_southern_hemisphere(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=dt.date(2000, 1, 1),
            birth_time=dt.time(12, 0),
            latitude=-33.87,
            longitude=151.21,
        )
        assert isinstance(chart, WesternChart)
        assert chart.latitude == -33.87
        assert chart.longitude == 151.21

    def test_valid_boundary_longitude(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=dt.date(2000, 1, 1),
            birth_time=dt.time(12, 0),
            latitude=0.0,
            longitude=180.0,
        )
        assert isinstance(chart, WesternChart)


# ── Einstein Chart Tests ─────────────────────────────────────────────────────


class TestEinsteinChart:
    """Tests using Einstein's known birth chart as reference."""

    def test_chart_structure(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        assert isinstance(chart, WesternChart)
        assert chart.birth_date == "1879-03-14"
        assert chart.birth_time == "10:50:08"
        assert chart.latitude == _EINSTEIN_LAT
        assert chart.longitude == _EINSTEIN_LON

    def test_planet_count(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        # 11 core + south node = 12 (Chiron may or may not be present)
        assert len(chart.planet_positions) >= 12

    def test_sun_in_pisces(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        sun = next(p for p in chart.planet_positions if p.planet == WesternPlanet.SUN)
        assert sun.sign == "PISCES"
        assert 23.0 < sun.degree_in_sign < 24.0

    def test_mercury_in_aries(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        mercury = next(
            p for p in chart.planet_positions if p.planet == WesternPlanet.MERCURY
        )
        assert mercury.sign == "ARIES"
        assert 3.0 < mercury.degree_in_sign < 3.5

    def test_mars_exalted_in_capricorn(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        mars = next(
            p for p in chart.planet_positions if p.planet == WesternPlanet.MARS
        )
        assert mars.sign == "CAPRICORN"
        assert chart.dignities[WesternPlanet.MARS] == WesternDignity.EXALTATION

    def test_house_cusps_count(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        assert len(chart.house_cusps) == 12

    def test_ascendant_in_cancer(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        # Ascendant ~101.67° = Cancer (90-120°)
        assert 90.0 < chart.ascendant < 120.0

    def test_aspects_exist(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        assert len(chart.aspects) > 0

    def test_all_aspects_are_major(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        for aspect in chart.aspects:
            assert isinstance(aspect.aspect_type, WesternAspectType)

    def test_mercury_conjunct_saturn(self, svc: WesternCalculationService) -> None:
        """Einstein's Mercury-Saturn conjunction is well-documented."""
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        ms_conj = [
            a
            for a in chart.aspects
            if a.aspect_type == WesternAspectType.CONJUNCTION
            and {a.planet_a, a.planet_b} == {WesternPlanet.MERCURY, WesternPlanet.SATURN}
        ]
        assert len(ms_conj) == 1
        assert ms_conj[0].orb < 2.0


# ── JFK Chart Tests ──────────────────────────────────────────────────────────


class TestJFKChart:
    """Tests using JFK's known birth chart as reference."""

    def test_chart_structure(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_JFK_DATE,
            birth_time=_JFK_TIME,
            latitude=_JFK_LAT,
            longitude=_JFK_LON,
        )
        assert isinstance(chart, WesternChart)
        assert chart.birth_date == "1917-05-29"

    def test_sun_in_gemini(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_JFK_DATE,
            birth_time=_JFK_TIME,
            latitude=_JFK_LAT,
            longitude=_JFK_LON,
        )
        sun = next(p for p in chart.planet_positions if p.planet == WesternPlanet.SUN)
        assert sun.sign == "GEMINI"

    def test_ascendant_in_libra(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_JFK_DATE,
            birth_time=_JFK_TIME,
            latitude=_JFK_LAT,
            longitude=_JFK_LON,
        )
        # JFK's Ascendant at 19:00 UTC is in Libra (~188°)
        assert 180.0 < chart.ascendant < 210.0


# ── House System Tests ───────────────────────────────────────────────────────


class TestHouseSystems:
    """Tests for different house system calculations."""

    def test_placidus_houses(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
            house_system=WesternHouseSystem.PLACIDUS,
        )
        assert chart.house_system == WesternHouseSystem.PLACIDUS
        assert len(chart.house_cusps) == 12
        # House 1 cusp should be close to Ascendant (Placidus)
        h1 = chart.house_cusps[0]
        assert h1.house_number == 1
        assert abs(h1.longitude - chart.ascendant) < 2.0

    def test_whole_sign_houses(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
            house_system=WesternHouseSystem.WHOLE_SIGN,
        )
        assert chart.house_system == WesternHouseSystem.WHOLE_SIGN
        assert len(chart.house_cusps) == 12
        # In Whole Sign, house cusps are at sign boundaries
        for hc in chart.house_cusps:
            assert hc.longitude % 30.0 < 0.1 or hc.longitude % 30.0 > 29.9

    def test_equal_houses(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
            house_system=WesternHouseSystem.EQUAL,
        )
        assert chart.house_system == WesternHouseSystem.EQUAL
        assert len(chart.house_cusps) == 12
        # In Equal houses, each cusp is 30° apart from H1
        h1_lon = chart.house_cusps[0].longitude
        for i in range(1, 12):
            diff = (chart.house_cusps[i].longitude - h1_lon) % 360.0
            expected = i * 30.0
            assert abs(diff - expected) < 1.0, (
                f"House {i+1} cusp at {chart.house_cusps[i].longitude:.2f}, "
                f"expected {h1_lon + expected:.2f} (diff={diff:.2f})"
            )

    def test_ascendant_consistent_across_systems(
        self, svc: WesternCalculationService
    ) -> None:
        """Ascendant should be the same regardless of house system."""
        charts = {}
        for hsys in WesternHouseSystem:
            charts[hsys] = svc.calculate(
                birth_date=_EINSTEIN_DATE,
                birth_time=_EINSTEIN_TIME,
                latitude=_EINSTEIN_LAT,
                longitude=_EINSTEIN_LON,
                house_system=hsys,
            )
        asc_values = [c.ascendant for c in charts.values()]
        assert max(asc_values) - min(asc_values) < 0.01


# ── Determinism Tests ────────────────────────────────────────────────────────


class TestDeterminism:
    """Tests for deterministic output."""

    def test_same_input_same_chart_id(
        self, svc: WesternCalculationService
    ) -> None:
        c1 = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        c2 = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        assert c1.deterministic_id == c2.deterministic_id

    def test_same_input_same_positions(
        self, svc: WesternCalculationService
    ) -> None:
        c1 = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        c2 = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        for p1, p2 in zip(c1.planet_positions, c2.planet_positions, strict=True):
            assert p1.planet == p2.planet
            assert abs(p1.longitude - p2.longitude) < 1e-10

    def test_different_input_different_chart_id(
        self, svc: WesternCalculationService
    ) -> None:
        c1 = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        c2 = svc.calculate(
            birth_date=_JFK_DATE,
            birth_time=_JFK_TIME,
            latitude=_JFK_LAT,
            longitude=_JFK_LON,
        )
        assert c1.deterministic_id != c2.deterministic_id

    def test_chart_id_is_16_char_hex(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        assert len(chart.deterministic_id) == 16
        int(chart.deterministic_id, 16)  # Should not raise


# ── Dignity Integration Tests ────────────────────────────────────────────────


class TestDignityIntegration:
    """Tests that dignities are correctly computed in a full chart."""

    def test_all_planets_have_dignities(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        for pp in chart.planet_positions:
            assert pp.planet in chart.dignities

    def test_dignities_are_valid_enums(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        for dignity in chart.dignities.values():
            assert isinstance(dignity, WesternDignity)

    def test_expected_dignities_for_einstein(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        # Mars at 26.91° Capricorn → EXALTATION
        assert chart.dignities[WesternPlanet.MARS] == WesternDignity.EXALTATION
        # Saturn at 4.19° Aries → FALL
        assert chart.dignities[WesternPlanet.SATURN] == WesternDignity.FALL


# ── Serialization Tests ──────────────────────────────────────────────────────


class TestSerialization:
    """Tests for deterministic serialization."""

    def test_to_dict_has_all_fields(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        d = chart.to_dict()
        assert "birth_date" in d
        assert "birth_time" in d
        assert "latitude" in d
        assert "longitude" in d
        assert "house_system" in d
        assert "julian_day_ut" in d
        assert "planet_positions" in d
        assert "house_cusps" in d
        assert "aspects" in d
        assert "dignities" in d
        assert "ascendant" in d
        assert "midheaven" in d
        assert "deterministic_id" in d

    def test_planet_positions_serialized(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        d = chart.to_dict()
        assert len(d["planet_positions"]) == len(chart.planet_positions)
        first = d["planet_positions"][0]
        assert "planet" in first
        assert "longitude" in first
        assert "sign" in first

    def test_aspects_serialized(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        d = chart.to_dict()
        assert len(d["aspects"]) == len(chart.aspects)
        if d["aspects"]:
            first = d["aspects"][0]
            assert "planet_a" in first
            assert "aspect_type" in first
            assert "orb" in first

    def test_dignities_serialized_as_strings(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        d = chart.to_dict()
        for key, val in d["dignities"].items():
            assert isinstance(key, str)
            assert isinstance(val, str)


# ── Tropical Position Accuracy Tests ─────────────────────────────────────────


class TestTropicalPositions:
    """Tests for tropical position accuracy using known values."""

    def test_sun_longitude_einstein(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        sun = next(p for p in chart.planet_positions if p.planet == WesternPlanet.SUN)
        # Sun at ~353.51° (23.51° Pisces)
        assert abs(sun.longitude - 353.51) < 0.1

    def test_moon_longitude_einstein(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        moon = next(p for p in chart.planet_positions if p.planet == WesternPlanet.MOON)
        # Moon at ~254.53° (14.53° Sagittarius)
        assert abs(moon.longitude - 254.53) < 0.2

    def test_north_node_opposite_south_node(
        self, svc: WesternCalculationService
    ) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        nn = next(
            p for p in chart.planet_positions if p.planet == WesternPlanet.NORTH_NODE
        )
        sn = next(
            p for p in chart.planet_positions if p.planet == WesternPlanet.SOUTH_NODE
        )
        # They should be exactly 180° apart
        diff = abs(nn.longitude - sn.longitude)
        assert abs(diff - 180.0) < 0.01

    def test_speeds_non_zero(self, svc: WesternCalculationService) -> None:
        chart = svc.calculate(
            birth_date=_EINSTEIN_DATE,
            birth_time=_EINSTEIN_TIME,
            latitude=_EINSTEIN_LAT,
            longitude=_EINSTEIN_LON,
        )
        for pp in chart.planet_positions:
            # All planets should have non-zero speed (even retrograde is non-zero)
            assert pp.speed_longitude != 0.0 or pp.planet == WesternPlanet.SOUTH_NODE

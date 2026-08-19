"""Shared builders for JRE-016 Ashtakavarga unit tests."""

from __future__ import annotations

import pytest

from jyotish import (
    BodyId,
    DmsValue,
    PlanetState,
    RetrogradeState,
    degree_in_nakshatra,
    degree_in_rashi,
    lord_of,
    nakshatra_of,
    pada_of,
    rashi_of,
)


def make_planet_state(
    body: BodyId,
    longitude: float,
    latitude: float = 0.0,
    speed: float = 1.0,
    retrograde: RetrogradeState = RetrogradeState.DIRECT,
) -> PlanetState:
    """Build a ``PlanetState`` at a specific longitude."""
    return PlanetState(
        body=body,
        longitude_tropical=longitude,
        longitude_sidereal=longitude,
        longitude_used=longitude,
        dms=DmsValue(degrees=int(longitude), minutes=0, seconds=0.0, sign=1),
        rashi=rashi_of(longitude),
        degree_in_rashi=degree_in_rashi(longitude),
        nakshatra=nakshatra_of(longitude),
        nakshatra_lord=lord_of(nakshatra_of(longitude)),
        pada=pada_of(longitude),
        degree_in_nakshatra=degree_in_nakshatra(longitude),
        latitude=latitude,
        speed_longitude=speed,
        retrograde=retrograde,
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=2451545.0,
        provider_id="fake.astronomy",
        ephemeris_version="18",
    )


def make_sun_state(longitude: float = 100.0) -> PlanetState:
    return make_planet_state(BodyId.SUN, longitude)


def make_moon_state(longitude: float = 33.0) -> PlanetState:
    return make_planet_state(BodyId.MOON, longitude)


def make_mars_state(longitude: float = 60.0) -> PlanetState:
    return make_planet_state(BodyId.MARS, longitude)


def make_mercury_state(longitude: float = 90.0) -> PlanetState:
    return make_planet_state(BodyId.MERCURY, longitude)


def make_jupiter_state(longitude: float = 150.0) -> PlanetState:
    return make_planet_state(BodyId.JUPITER, longitude)


def make_venus_state(longitude: float = 210.0) -> PlanetState:
    return make_planet_state(BodyId.VENUS, longitude)


def make_saturn_state(longitude: float = 270.0) -> PlanetState:
    return make_planet_state(BodyId.SATURN, longitude)


@pytest.fixture
def sun_in_aries() -> PlanetState:
    """Sun at 10° Aries (Mesha, index 0)."""
    return make_sun_state(10.0)


@pytest.fixture
def sun_in_taurus() -> PlanetState:
    """Sun at 10° Taurus (Vrishabha, index 1)."""
    return make_sun_state(40.0)


@pytest.fixture
def all_planets_in_aries() -> tuple[PlanetState, ...]:
    """All 7 classical planets in Aries."""
    return (
        make_sun_state(10.0),
        make_moon_state(15.0),
        make_mars_state(20.0),
        make_mercury_state(5.0),
        make_jupiter_state(25.0),
        make_venus_state(8.0),
        make_saturn_state(12.0),
    )

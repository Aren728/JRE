"""Shared builders for JRE-019 Prashna unit tests."""

from __future__ import annotations

import pytest

from jyotish import (
    BodyId,
    DmsValue,
    PlanetState,
    RetrogradeState,
    RashiId,
    degree_in_nakshatra,
    degree_in_rashi,
    lord_of,
    nakshatra_of,
    pada_of,
    rashi_of,
)

from prashna.models import QueryLocation


def make_planet_state(
    body: BodyId,
    longitude: float,
    latitude: float = 0.0,
    speed: float = 1.0,
    retrograde: RetrogradeState = RetrogradeState.DIRECT,
    nakshatra_lord: BodyId | None = None,
) -> PlanetState:
    """Build a ``PlanetState`` at a specific longitude."""
    nak = nakshatra_of(longitude)
    return PlanetState(
        body=body,
        longitude_tropical=longitude,
        longitude_sidereal=longitude,
        longitude_used=longitude,
        dms=DmsValue(degrees=int(longitude), minutes=0, seconds=0.0, sign=1),
        rashi=rashi_of(longitude),
        degree_in_rashi=degree_in_rashi(longitude),
        nakshatra=nak,
        nakshatra_lord=nakshatra_lord if nakshatra_lord is not None else lord_of(nak),
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


def make_query_location(
    latitude: float = 28.6139, longitude: float = 77.2090,
) -> QueryLocation:
    """Build a ``QueryLocation`` (default: New Delhi)."""
    return QueryLocation(latitude=latitude, longitude=longitude)


@pytest.fixture
def query_location() -> QueryLocation:
    """A sample query location (New Delhi)."""
    return make_query_location()


@pytest.fixture
def sun_in_aries() -> PlanetState:
    """Sun at 10 degrees Aries."""
    return make_planet_state(BodyId.SUN, 10.0)


@pytest.fixture
def moon_in_taurus() -> PlanetState:
    """Moon at 3 degrees Taurus (Krittika nakshatra, lord = Sun)."""
    return make_planet_state(BodyId.MOON, 33.0)


@pytest.fixture
def classic_planets() -> tuple[PlanetState, ...]:
    """All seven classical planets at known positions."""
    return (
        make_planet_state(BodyId.SUN, 10.0),
        make_planet_state(BodyId.MOON, 33.0),
        make_planet_state(BodyId.MARS, 60.0),
        make_planet_state(BodyId.MERCURY, 90.0),
        make_planet_state(BodyId.JUPITER, 150.0),
        make_planet_state(BodyId.VENUS, 210.0),
        make_planet_state(BodyId.SATURN, 270.0),
    )

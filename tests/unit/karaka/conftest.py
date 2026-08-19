"""Shared builders for JRE-014 Karaka unit tests."""

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


def make_classical_planets() -> tuple[PlanetState, ...]:
    """Sun through Saturn at staggered longitudes."""
    return (
        make_planet_state(BodyId.SUN, 100.0),
        make_planet_state(BodyId.MOON, 33.0),
        make_planet_state(BodyId.MARS, 200.0),
        make_planet_state(BodyId.MERCURY, 165.0),
        make_planet_state(BodyId.JUPITER, 95.0),
        make_planet_state(BodyId.VENUS, 357.0),
        make_planet_state(BodyId.SATURN, 250.0),
    )


@pytest.fixture
def classical_planets() -> tuple[PlanetState, ...]:
    return make_classical_planets()

"""Shared builders for JRE-011 Bala unit tests.

Synthetic ``PlanetState`` and ``LagnaState`` values are constructed via
the ``jyotish`` PUBLIC API only, so the pure Bala derivation is testable
without an ephemeris.
"""

from __future__ import annotations

import pytest

from jyotish import (
    BodyId,
    DmsValue,
    HouseSystem,
    LagnaState,
    NakshatraId,
    Pada,
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
    """Build a Sun PlanetState."""
    return make_planet_state(BodyId.SUN, longitude)


def make_moon_state(longitude: float = 33.0) -> PlanetState:
    """Build a Moon PlanetState."""
    return make_planet_state(BodyId.MOON, longitude)


def make_mars_state(longitude: float = 298.0) -> PlanetState:
    """Build a Mars PlanetState."""
    return make_planet_state(BodyId.MARS, longitude)


def make_mercury_state(longitude: float = 165.0) -> PlanetState:
    """Build a Mercury PlanetState."""
    return make_planet_state(BodyId.MERCURY, longitude)


def make_jupiter_state(longitude: float = 95.0) -> PlanetState:
    """Build a Jupiter PlanetState."""
    return make_planet_state(BodyId.JUPITER, longitude)


def make_venus_state(longitude: float = 357.0) -> PlanetState:
    """Build a Venus PlanetState."""
    return make_planet_state(BodyId.VENUS, longitude)


def make_saturn_state(longitude: float = 200.0) -> PlanetState:
    """Build a Saturn PlanetState."""
    return make_planet_state(BodyId.SATURN, longitude)


def make_rahu_state(longitude: float = 33.0) -> PlanetState:
    """Build a Rahu PlanetState."""
    return make_planet_state(BodyId.RAHU, longitude)


def make_ketu_state(longitude: float = 213.0) -> PlanetState:
    """Build a Ketu PlanetState."""
    return make_planet_state(BodyId.KETU, longitude)


def make_all_planet_states(
    base_longitude: float = 0.0,
) -> tuple[PlanetState, ...]:
    """Build PlanetState for all 9 planets at staggered longitudes."""
    offsets = [0, 33, 60, 100, 165, 200, 250, 298, 357]
    bodies = [
        BodyId.SUN, BodyId.MOON, BodyId.MARS, BodyId.MERCURY,
        BodyId.JUPITER, BodyId.VENUS, BodyId.SATURN, BodyId.RAHU,
        BodyId.KETU,
    ]
    return tuple(
        make_planet_state(body, (base_longitude + offset) % 360.0)
        for body, offset in zip(bodies, offsets)
    )


def make_lagna_state(
    ascendant_longitude: float = 0.0,
) -> LagnaState:
    """Build a ``LagnaState`` at a specific longitude."""
    return LagnaState(
        ascendant_longitude_deg=ascendant_longitude,
        dms=DmsValue(
            degrees=int(ascendant_longitude),
            minutes=0,
            seconds=0.0,
            sign=1,
        ),
        rashi=rashi_of(ascendant_longitude),
        degree_in_rashi=degree_in_rashi(ascendant_longitude),
        nakshatra=nakshatra_of(ascendant_longitude),
        nakshatra_lord=lord_of(nakshatra_of(ascendant_longitude)),
        pada=pada_of(ascendant_longitude),
        degree_in_nakshatra=degree_in_nakshatra(ascendant_longitude),
        bhava_relationship=None,
        house_system=HouseSystem.WHOLE_SIGN,
    )


@pytest.fixture
def all_planets() -> tuple[PlanetState, ...]:
    """All 9 planet states at staggered longitudes."""
    return make_all_planet_states()


@pytest.fixture
def lagna_aries() -> LagnaState:
    """Lagna at 0° Aries."""
    return make_lagna_state(0.0)


@pytest.fixture
def lagna_cancer() -> LagnaState:
    """Lagna at 0° Cancer."""
    return make_lagna_state(90.0)

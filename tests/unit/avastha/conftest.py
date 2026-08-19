"""Shared builders for JRE-015 Avastha unit tests."""

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


@pytest.fixture
def sun_at_aries_3deg() -> PlanetState:
    """Sun at 3° Aries — Jagrat, exalted (Deepta)."""
    return make_sun_state(3.0)


@pytest.fixture
def sun_at_aries_10deg() -> PlanetState:
    """Sun at 10° Aries — Swapna, exalted (Deepta)."""
    return make_sun_state(10.0)


@pytest.fixture
def sun_at_aries_20deg() -> PlanetState:
    """Sun at 20° Aries — Sushupti, exalted (Deepta)."""
    return make_sun_state(20.0)


@pytest.fixture
def sun_in_own_sign() -> PlanetState:
    """Sun at 10° Leo — Swapna, own sign (Swastha)."""
    return make_sun_state(100.0)  # 10° Leo


@pytest.fixture
def sun_debilitated() -> PlanetState:
    """Sun at 10° Libra — Swapna, debilitated (Kshobhita)."""
    return make_sun_state(200.0)  # 10° Libra

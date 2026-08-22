"""Shared test fixtures for Birth Signature tests."""

from __future__ import annotations

import pytest

from jyotish import (
    BodyId,
    DmsValue,
    LagnaState,
    PlanetState,
    RetrogradeState,
    degree_in_nakshatra,
    degree_in_rashi,
    lord_of,
    nakshatra_of,
    pada_of,
    rashi_of,
)
from jyotish.models import HouseSystem


def make_planet_state(
    body: BodyId,
    longitude: float,
    latitude: float = 0.0,
    speed: float = 13.0,
    retrograde: RetrogradeState = RetrogradeState.DIRECT,
    julian_day_ut: float = 2451545.0,
) -> PlanetState:
    """Build a PlanetState at a specific sidereal longitude."""
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
        julian_day_ut=julian_day_ut,
        provider_id="test",
        ephemeris_version="test",
    )


def make_lagna(
    ascendant_longitude: float = 45.0,
    house_system: HouseSystem = HouseSystem.WHOLE_SIGN,
) -> LagnaState:
    """Build a LagnaState at a specific ascendant longitude."""
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
        house_system=house_system,
    )


@pytest.fixture
def sun_at_10_moon_at_33() -> tuple[tuple[PlanetState, ...], LagnaState]:
    """Sun at 10° (ASHWINI), Moon at 33° (ROHINI).

    Moon-Sun distance = 23°, so tithi = floor(23/12) + 1 = 2 = SHUKLA_DVITIYA.
    Sun+Moon = 43°, yoga = floor(43/13.333) + 1 = 4 = SOUBHAGYA.
    """
    sun = make_planet_state(BodyId.SUN, 10.0, julian_day_ut=2451545.0)
    moon = make_planet_state(BodyId.MOON, 33.0, julian_day_ut=2451545.0)
    lagna = make_lagna(45.0)
    return (sun, moon), lagna


@pytest.fixture
def sun_at_0_moon_at_0() -> tuple[tuple[PlanetState, ...], LagnaState]:
    """Sun and Moon both at 0° (conjunction in ASHWINI).

    Moon-Sun distance = 0°, so tithi = floor(0/12) + 1 = 1 = SHUKLA_PRATIPADA.
    Sun+Moon = 0°, yoga = floor(0/13.333) + 1 = 1 = VISHKAMBHA.
    """
    sun = make_planet_state(BodyId.SUN, 0.0, julian_day_ut=2451545.0)
    moon = make_planet_state(BodyId.MOON, 0.0, julian_day_ut=2451545.0)
    lagna = make_lagna(0.0)
    return (sun, moon), lagna


@pytest.fixture
def sun_at_100_moon_at_200() -> tuple[tuple[PlanetState, ...], LagnaState]:
    """Sun at 100°, Moon at 200°.

    Moon-Sun distance = 100°, so tithi = floor(100/12) + 1 = 9 = SHUKLA_NAVAMI.
    Sun+Moon = 300°, yoga = floor(300/13.333) + 1 = 23 = SUBHA.
    """
    sun = make_planet_state(BodyId.SUN, 100.0, julian_day_ut=2451545.0)
    moon = make_planet_state(BodyId.MOON, 200.0, julian_day_ut=2451545.0)
    lagna = make_lagna(100.0)
    return (sun, moon), lagna


@pytest.fixture
def sun_at_250_moon_at_50() -> tuple[tuple[PlanetState, ...], LagnaState]:
    """Sun at 250°, Moon at 50° (wrapping case).

    Moon-Sun distance = (50 - 250) % 360 = 160°, so tithi = floor(160/12) + 1
    = 14 = SHUKLA_CHATURDASHI.
    Sun+Moon = 300°, yoga = floor(300/13.333) + 1 = 23 = SUBHA.
    """
    sun = make_planet_state(BodyId.SUN, 250.0, julian_day_ut=2451545.0)
    moon = make_planet_state(BodyId.MOON, 50.0, julian_day_ut=2451545.0)
    lagna = make_lagna(250.0)
    return (sun, moon), lagna

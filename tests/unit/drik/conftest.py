"""Shared builders for JRE-012 Drik unit tests.

Synthetic ``PlanetState`` values are constructed via the ``jyotish``
PUBLIC API only, so the pure Drik derivation is testable without an
ephemeris.
"""

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


def make_mars_state(longitude: float = 200.0) -> PlanetState:
    return make_planet_state(BodyId.MARS, longitude)


def make_jupiter_state(longitude: float = 250.0) -> PlanetState:
    return make_planet_state(BodyId.JUPITER, longitude)


def make_saturn_state(longitude: float = 300.0) -> PlanetState:
    return make_planet_state(BodyId.SATURN, longitude)


def make_opposition_pair() -> tuple[PlanetState, PlanetState]:
    """Sun at 0, Moon at 180 — exact opposition (7th house)."""
    return make_planet_state(BodyId.SUN, 0.0), make_planet_state(BodyId.MOON, 180.0)


def make_conjunction_pair() -> tuple[PlanetState, PlanetState]:
    """Sun at 0, Moon at 0 — same sign (no aspect via house counting)."""
    return make_planet_state(BodyId.SUN, 0.0), make_planet_state(BodyId.MOON, 10.0)


def make_mars_4th_aspect() -> tuple[PlanetState, PlanetState]:
    """Mars at 0 (Aries), target at 90 (Cancer) — 4th house aspect."""
    return make_planet_state(BodyId.MARS, 0.0), make_planet_state(BodyId.SUN, 90.0)


def make_mars_8th_aspect() -> tuple[PlanetState, PlanetState]:
    """Mars at 0 (Aries), target at 210 (Scorpio) — 8th house aspect."""
    return make_planet_state(BodyId.MARS, 0.0), make_planet_state(BodyId.SUN, 210.0)


def make_jupiter_5th_aspect() -> tuple[PlanetState, PlanetState]:
    """Jupiter at 0 (Sagittarius via Aries offset), target at 120 — 5th house."""
    return make_planet_state(BodyId.JUPITER, 0.0), make_planet_state(BodyId.SUN, 120.0)


def make_jupiter_9th_aspect() -> tuple[PlanetState, PlanetState]:
    """Jupiter at 0, target at 240 — 9th house aspect."""
    return make_planet_state(BodyId.JUPITER, 0.0), make_planet_state(BodyId.SUN, 240.0)


def make_saturn_3rd_aspect() -> tuple[PlanetState, PlanetState]:
    """Saturn at 0, target at 60 — 3rd house aspect."""
    return make_planet_state(BodyId.SATURN, 0.0), make_planet_state(BodyId.SUN, 60.0)


def make_saturn_10th_aspect() -> tuple[PlanetState, PlanetState]:
    """Saturn at 0, target at 270 — 10th house aspect."""
    return make_planet_state(BodyId.SATURN, 0.0), make_planet_state(BodyId.SUN, 270.0)


@pytest.fixture
def two_planets_opposition() -> tuple[PlanetState, PlanetState]:
    return make_opposition_pair()


@pytest.fixture
def two_planets_conjunction() -> tuple[PlanetState, PlanetState]:
    return make_conjunction_pair()

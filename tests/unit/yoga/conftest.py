"""Shared builders for JRE-013 Yoga unit tests.

Synthetic ``PlanetState`` values are constructed via the ``jyotish``
PUBLIC API only, so the pure Yoga derivation is testable without an
ephemeris.
"""

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


# --------------------------------------------------------------------------- #
# Gajakesari Yoga test charts
# --------------------------------------------------------------------------- #

def make_gajakesari_chart() -> tuple[PlanetState, ...]:
    """Moon at 0 (Aries), Jupiter at 90 (Cancer) — Kendra (4th from Moon).

    Gajakesari Yoga should be present.
    """
    return (
        make_planet_state(BodyId.MOON, 0.0),
        make_planet_state(BodyId.JUPITER, 90.0),
        make_planet_state(BodyId.SUN, 150.0),
    )


def make_no_gajakesari_chart() -> tuple[PlanetState, ...]:
    """Moon at 0 (Aries), Jupiter at 30 (Taurus) — 2nd from Moon, not Kendra.

    Gajakesari Yoga should NOT be present.
    """
    return (
        make_planet_state(BodyId.MOON, 0.0),
        make_planet_state(BodyId.JUPITER, 30.0),
        make_planet_state(BodyId.SUN, 150.0),
    )


# --------------------------------------------------------------------------- #
# Raja Yoga test charts
# --------------------------------------------------------------------------- #

def make_raja_yoga_chart() -> tuple[PlanetState, ...]:
    """Lagna Aries (0). 1st lord = Mars, 5th lord = Sun.
    Mars at 0 (Aries), Sun at 0 (Aries) — conjunct.

    Raja Yoga should be present (Kendra lord Mars conjunct Trikona lord Sun).
    """
    return (
        make_planet_state(BodyId.MARS, 0.0),
        make_planet_state(BodyId.SUN, 5.0),
        make_planet_state(BodyId.MOON, 90.0),
        make_planet_state(BodyId.JUPITER, 180.0),
    )


def make_no_raja_yoga_chart() -> tuple[PlanetState, ...]:
    """Lagna Aries (0). Mars at 0, Sun at 60 — no connection.

    Raja Yoga should NOT be present.
    """
    return (
        make_planet_state(BodyId.MARS, 0.0),
        make_planet_state(BodyId.SUN, 60.0),
        make_planet_state(BodyId.MOON, 90.0),
    )


# --------------------------------------------------------------------------- #
# Dhana Yoga test charts
# --------------------------------------------------------------------------- #

def make_dhana_yoga_chart() -> tuple[PlanetState, ...]:
    """Lagna Aries (0). 2nd lord = Venus, 11th lord = Saturn.
    Venus at 0 (Aries), Saturn at 0 (Aries) — conjunct.

    Dhana Yoga should be present.
    """
    return (
        make_planet_state(BodyId.VENUS, 0.0),
        make_planet_state(BodyId.SATURN, 5.0),
        make_planet_state(BodyId.MOON, 90.0),
        make_planet_state(BodyId.JUPITER, 180.0),
    )


# --------------------------------------------------------------------------- #
# Viparita Raja Yoga test charts
# --------------------------------------------------------------------------- #

def make_viparita_chart() -> tuple[PlanetState, ...]:
    """Lagna Aries (0). 6th lord = Mercury, 8th lord = Mars.
    Mercury at 0 (Aries), Mars at 0 (Aries) — conjunct.

    Viparita Raja Yoga should be present.
    """
    return (
        make_planet_state(BodyId.MERCURY, 0.0),
        make_planet_state(BodyId.MARS, 5.0),
        make_planet_state(BodyId.MOON, 90.0),
    )


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture
def gajakesari_chart() -> tuple[PlanetState, ...]:
    return make_gajakesari_chart()


@pytest.fixture
def no_gajakesari_chart() -> tuple[PlanetState, ...]:
    return make_no_gajakesari_chart()


@pytest.fixture
def raja_yoga_chart() -> tuple[PlanetState, ...]:
    return make_raja_yoga_chart()


@pytest.fixture
def aries_lagna() -> RashiId:
    return RashiId.MESHA

"""Shared builders for JRE-010 Dasha unit tests.

Synthetic ``PlanetState`` values are constructed via the ``jyotish`` PUBLIC
API only, so the pure Dasha derivation is testable without an ephemeris.
``make_moon_state`` places the Moon at an exact longitude inside a chosen
Nakshatra.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from jyotish import (
    BodyId,
    DmsValue,
    NakshatraId,
    Pada,
    PlanetState,
    RetrogradeState,
    degree_in_nakshatra as _jyotish_din,
    degree_in_rashi,
    lord_of,
    nakshatra_of,
    pada_of,
    rashi_of,
)

from dasha.models import DashaConfig, DashaSystem, VIMSHOTTARI_YEARS

#: Nakshatra boundaries (start longitude in degrees).
NAKSHATRA_START: dict[NakshatraId, float] = {}
for i, nak in enumerate([
    NakshatraId.ASHWINI, NakshatraId.BHARANI, NakshatraId.KRITTIKA,
    NakshatraId.ROHINI, NakshatraId.MRIGASHIRA, NakshatraId.ARDRA,
    NakshatraId.PUNARVASU, NakshatraId.PUSHYA, NakshatraId.ASHLESHA,
    NakshatraId.MAGHA, NakshatraId.PURVA_PHALGUNI, NakshatraId.UTTARA_PHALGUNI,
    NakshatraId.HASTA, NakshatraId.CHITRA, NakshatraId.SWATI,
    NakshatraId.VISHAKHA, NakshatraId.ANURADHA, NakshatraId.JYESHTHA,
    NakshatraId.MULA, NakshatraId.PURVA_ASHADHA, NakshatraId.UTTARA_ASHADHA,
    NakshatraId.SHRAVANA, NakshatraId.DHANISHTHA, NakshatraId.SHATABHISHA,
    NakshatraId.PURVA_BHADRAPADA, NakshatraId.UTTARA_BHADRAPADA,
    NakshatraId.REVATI,
]):
    NAKSHATRA_START[nak] = i * (360.0 / 27.0)


def make_moon_state(
    nakshatra: NakshatraId = NakshatraId.ROHINI,
    pada: Pada = Pada.PADA_1,
    degree_in_nakshatra_deg: float | None = None,
) -> PlanetState:
    """Build a Moon ``PlanetState`` at a specific Nakshatra/Pada.

    If ``degree_in_nakshatra_deg`` is not given, it is computed as the
    midpoint of the given pada.
    """
    nak_start = NAKSHATRA_START[nakshatra]
    pada_span = (360.0 / 27.0) / 4.0
    if degree_in_nakshatra_deg is None:
        degree_in_nakshatra_deg = (int(pada) - 1) * pada_span + pada_span / 2.0
    lon = (nak_start + degree_in_nakshatra_deg) % 360.0

    return PlanetState(
        body=BodyId.MOON,
        longitude_tropical=lon,
        longitude_sidereal=lon,
        longitude_used=lon,
        dms=DmsValue(degrees=int(lon), minutes=0, seconds=0.0, sign=1),
        rashi=rashi_of(lon),
        degree_in_rashi=degree_in_rashi(lon),
        nakshatra=nakshatra_of(lon),
        nakshatra_lord=lord_of(nakshatra_of(lon)),
        pada=pada_of(lon),
        degree_in_nakshatra=_jyotish_din(lon),
        latitude=0.0,
        speed_longitude=13.0,
        retrograde=RetrogradeState.DIRECT,
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=2451545.0,
        provider_id="fake.astronomy",
        ephemeris_version="18",
    )


def make_sun_state(
    longitude: float = 100.0,
) -> PlanetState:
    """Build a non-Moon PlanetState for rejection testing."""
    return PlanetState(
        body=BodyId.SUN,
        longitude_tropical=longitude,
        longitude_sidereal=longitude,
        longitude_used=longitude,
        dms=DmsValue(degrees=int(longitude), minutes=0, seconds=0.0, sign=1),
        rashi=rashi_of(longitude),
        degree_in_rashi=degree_in_rashi(longitude),
        nakshatra=nakshatra_of(longitude),
        nakshatra_lord=lord_of(nakshatra_of(longitude)),
        pada=pada_of(longitude),
        degree_in_nakshatra=_jyotish_din(longitude),
        latitude=0.0,
        speed_longitude=1.0,
        retrograde=RetrogradeState.DIRECT,
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=2451545.0,
        provider_id="fake.astronomy",
        ephemeris_version="18",
    )


@pytest.fixture
def moon_rohini_pada1() -> PlanetState:
    """Moon in Rohini Pada 1 (KETU's first nakshatra is Ashwini,
    but Rohini is MOON's nakshatra)."""
    return make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)


@pytest.fixture
def moon_ashwini_pada1() -> PlanetState:
    """Moon at the very start of Ashwini Pada 1 (KETU lord)."""
    return make_moon_state(NakshatraId.ASHWINI, Pada.PADA_1, 0.0)


@pytest.fixture
def moon_ashwini_pada4_end() -> PlanetState:
    """Moon near the end of Ashwini Pada 4 (maximum balance for KETU)."""
    nak_span = 360.0 / 27.0
    return make_moon_state(
        NakshatraId.ASHWINI, Pada.PADA_4,
        degree_in_nakshatra_deg=nak_span - 0.01,
    )


@pytest.fixture
def default_config() -> DashaConfig:
    """Default DashaConfig for testing."""
    return DashaConfig()

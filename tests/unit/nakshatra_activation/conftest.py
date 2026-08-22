"""Shared test fixtures for Nakshatra Activation tests."""

from __future__ import annotations

import pytest

from jyotish import (
    BodyId,
    JyotishService,
    NakshatraId,
    Pada,
    PlanetState,
    RashiId,
    RetrogradeState,
)
from jyotish.models import DmsValue


@pytest.fixture
def jyotish_service() -> JyotishService:
    """Create a JyotishService for computing planet positions."""
    return JyotishService()


@pytest.fixture
def simple_planet_states() -> tuple[PlanetState, ...]:
    """Create a simple set of planet states for testing.

    Moon in ASHWINI (Ketu's nakshatra), Sun in ROHINI (Moon's nakshatra).
    """
    return (
        PlanetState(
            body=BodyId.MOON,
            longitude_tropical=10.0,
            longitude_sidereal=10.0,
            longitude_used=10.0,
            dms=DmsValue(degrees=10, minutes=0, seconds=0.0, sign=0),
            rashi=RashiId.MESHA,
            degree_in_rashi=10.0,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            pada=Pada.PADA_1,
            degree_in_nakshatra=10.0,
            latitude=0.0,
            speed_longitude=13.0,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-01-01T00:00:00Z",
            julian_day_ut=2451544.5,
            provider_id="test",
            ephemeris_version="test",
        ),
        PlanetState(
            body=BodyId.SUN,
            longitude_tropical=45.0,
            longitude_sidereal=45.0,
            longitude_used=45.0,
            dms=DmsValue(degrees=15, minutes=0, seconds=0.0, sign=1),
            rashi=RashiId.VRISHABHA,
            degree_in_rashi=15.0,
            nakshatra=NakshatraId.ROHINI,
            nakshatra_lord=BodyId.MOON,
            pada=Pada.PADA_2,
            degree_in_nakshatra=5.0,
            latitude=0.0,
            speed_longitude=1.0,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-01-01T00:00:00Z",
            julian_day_ut=2451544.5,
            provider_id="test",
            ephemeris_version="test",
        ),
        PlanetState(
            body=BodyId.MARS,
            longitude_tropical=130.0,
            longitude_sidereal=130.0,
            longitude_used=130.0,
            dms=DmsValue(degrees=10, minutes=0, seconds=0.0, sign=4),
            rashi=RashiId.SIMHA,
            degree_in_rashi=10.0,
            nakshatra=NakshatraId.PURVA_PHALGUNI,
            nakshatra_lord=BodyId.VENUS,
            pada=Pada.PADA_2,
            degree_in_nakshatra=5.0,
            latitude=0.0,
            speed_longitude=0.5,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-01-01T00:00:00Z",
            julian_day_ut=2451544.5,
            provider_id="test",
            ephemeris_version="test",
        ),
    )


@pytest.fixture
def mutual_exchange_states() -> tuple[PlanetState, ...]:
    """Create planet states with a mutual nakshatra lord exchange.

    Planet A in nakshatra owned by Lord B.
    Planet B in nakshatra owned by Lord A.
    """
    return (
        PlanetState(
            body=BodyId.MERCURY,
            longitude_tropical=10.0,
            longitude_sidereal=10.0,
            longitude_used=10.0,
            dms=DmsValue(degrees=10, minutes=0, seconds=0.0, sign=0),
            rashi=RashiId.MESHA,
            degree_in_rashi=10.0,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            pada=Pada.PADA_1,
            degree_in_nakshatra=10.0,
            latitude=0.0,
            speed_longitude=1.0,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-01-01T00:00:00Z",
            julian_day_ut=2451544.5,
            provider_id="test",
            ephemeris_version="test",
        ),
        PlanetState(
            body=BodyId.VENUS,
            longitude_tropical=310.0,
            longitude_sidereal=310.0,
            longitude_used=310.0,
            dms=DmsValue(degrees=10, minutes=0, seconds=0.0, sign=10),
            rashi=RashiId.KUMBHA,
            degree_in_rashi=10.0,
            nakshatra=NakshatraId.SHATABHISHA,
            nakshatra_lord=BodyId.RAHU,
            pada=Pada.PADA_2,
            degree_in_nakshatra=5.0,
            latitude=0.0,
            speed_longitude=1.2,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-01-01T00:00:00Z",
            julian_day_ut=2451544.5,
            provider_id="test",
            ephemeris_version="test",
        ),
    )


@pytest.fixture
def shared_nakshatra_states() -> tuple[PlanetState, ...]:
    """Create planet states where two planets share a nakshatra."""
    return (
        PlanetState(
            body=BodyId.MOON,
            longitude_tropical=10.0,
            longitude_sidereal=10.0,
            longitude_used=10.0,
            dms=DmsValue(degrees=10, minutes=0, seconds=0.0, sign=0),
            rashi=RashiId.MESHA,
            degree_in_rashi=10.0,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            pada=Pada.PADA_1,
            degree_in_nakshatra=10.0,
            latitude=0.0,
            speed_longitude=13.0,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-01-01T00:00:00Z",
            julian_day_ut=2451544.5,
            provider_id="test",
            ephemeris_version="test",
        ),
        PlanetState(
            body=BodyId.MERCURY,
            longitude_tropical=11.0,
            longitude_sidereal=11.0,
            longitude_used=11.0,
            dms=DmsValue(degrees=11, minutes=0, seconds=0.0, sign=0),
            rashi=RashiId.MESHA,
            degree_in_rashi=11.0,
            nakshatra=NakshatraId.ASHWINI,
            nakshatra_lord=BodyId.KETU,
            pada=Pada.PADA_1,
            degree_in_nakshatra=11.0,
            latitude=0.0,
            speed_longitude=1.0,
            retrograde=RetrogradeState.DIRECT,
            timestamp_utc_iso="2000-01-01T00:00:00Z",
            julian_day_ut=2451544.5,
            provider_id="test",
            ephemeris_version="test",
        ),
    )

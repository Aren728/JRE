"""Shared builders for JRE-020 Muhurta unit tests."""

from __future__ import annotations

import pytest

from jyotish import (
    BodyId,
    DmsValue,
    NakshatraId,
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

from muhurta.models import (
    Karana,
    MuhurtaCategory,
    MuhurtaWindow,
    PanchangaState,
    Tithi,
    Var,
    Yoga,
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


def make_panchanga(
    tithi: Tithi = Tithi.SHUKLA_PRADEMA,
    vara: Var = Var.THURSDAY,
    nakshatra: NakshatraId = NakshatraId.ASHWINI,
    yoga: Yoga = Yoga.SUBHA,
    karana: Karana = Karana.BALAVA,
) -> PanchangaState:
    """Build a ``PanchangaState``."""
    return PanchangaState(
        tithi=tithi,
        vara=vara,
        nakshatra=nakshatra,
        yoga=yoga,
        karana=karana,
    )


def make_window(
    start_utc: str = "2024-01-15T06:00:00Z",
    end_utc: str = "2024-01-15T12:00:00Z",
) -> MuhurtaWindow:
    """Build a ``MuhurtaWindow``."""
    return MuhurtaWindow(start_utc=start_utc, end_utc=end_utc)


@pytest.fixture
def auspicious_panchanga() -> PanchangaState:
    """Panchanga with favorable elements for most categories."""
    return make_panchanga(
        tithi=Tithi.SHUKLA_PRADEMA,
        vara=Var.THURSDAY,
        nakshatra=NakshatraId.HASTA,
        yoga=Yoga.SUBHA,
        karana=Karana.BALAVA,
    )


@pytest.fixture
def inauspicious_panchanga() -> PanchangaState:
    """Panchanga with multiple inauspicious elements."""
    return make_panchanga(
        tithi=Tithi.SHUKLA_NAVAMI,
        vara=Var.SATURDAY,
        nakshatra=NakshatraId.ARDDRA,
        yoga=Yoga.SHULA,
        karana=Karana.VISHTI,
    )


@pytest.fixture
def neutral_panchanga() -> PanchangaState:
    """Panchanga with neither auspicious nor inauspicious elements."""
    return make_panchanga(
        tithi=Tithi.SHUKLA_PANCHAMI,
        vara=Var.WEDNESDAY,
        nakshatra=NakshatraId.PUNARVASU,
        yoga=Yoga.SIDDHI,
        karana=Karana.TAITILA,
    )


@pytest.fixture
def all_planets() -> tuple[PlanetState, ...]:
    """All seven classical planets at known longitudes."""
    return (
        make_planet_state(BodyId.SUN, 10.0),
        make_planet_state(BodyId.MOON, 33.0),
        make_planet_state(BodyId.MARS, 60.0),
        make_planet_state(BodyId.MERCURY, 90.0),
        make_planet_state(BodyId.JUPITER, 150.0),
        make_planet_state(BodyId.VENUS, 210.0),
        make_planet_state(BodyId.SATURN, 270.0),
    )

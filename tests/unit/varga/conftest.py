"""Shared builders for JRE-008 unit tests.

Synthetic ``PlanetState`` values are constructed via the ``jyotish`` PUBLIC
API only (mirroring the JRE-003/005/007 unit conftests), so the pure varga
derivation is testable without an ephemeris. ``make_state`` places a body
at an exact longitude inside a chosen Rashi.
"""

from __future__ import annotations

from jyotish import (
    BodyId,
    DmsValue,
    PlanetState,
    RashiId,
    RetrogradeState,
    degree_in_nakshatra,
    degree_in_rashi,
    lord_of,
    nakshatra_of,
    pada_of,
    rashi_of,
)

#: Zodiacal offset (degrees) of the start of each Rashi (Aries = 0).
RASHI_START: dict[RashiId, float] = {
    RashiId.MESHA: 0.0,
    RashiId.VRISHABHA: 30.0,
    RashiId.MITHUNA: 60.0,
    RashiId.KARKA: 90.0,
    RashiId.SIMHA: 120.0,
    RashiId.KANYA: 150.0,
    RashiId.TULA: 180.0,
    RashiId.VRISHCHIKA: 210.0,
    RashiId.DHANUSHA: 240.0,
    RashiId.MAKARA: 270.0,
    RashiId.KUMBHA: 300.0,
    RashiId.MEENA: 330.0,
}


def make_state(
    rashi: RashiId = RashiId.MESHA,
    degree: float = 5.0,
    body: BodyId = BodyId.SUN,
) -> PlanetState:
    """Build a full ``PlanetState`` at ``degree`` within ``rashi`` (public
    JRE-003 API derived fields; ``degree`` must be in [0, 30))."""
    assert 0.0 <= degree < 30.0, f"degree must be in [0, 30), got {degree!r}"
    lon = (RASHI_START[rashi] + degree) % 360.0
    nakshatra = nakshatra_of(lon)
    return PlanetState(
        body=body,
        longitude_tropical=lon,
        longitude_sidereal=lon,
        longitude_used=lon,
        dms=DmsValue(degrees=int(lon), minutes=0, seconds=0.0, sign=1),
        rashi=rashi_of(lon),
        degree_in_rashi=degree_in_rashi(lon),
        nakshatra=nakshatra,
        nakshatra_lord=lord_of(nakshatra),
        pada=pada_of(lon),
        degree_in_nakshatra=degree_in_nakshatra(lon),
        latitude=0.0,
        speed_longitude=1.0,
        retrograde=RetrogradeState.DIRECT,
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=2451545.0,
        provider_id="fake.astronomy",
        ephemeris_version="18",
    )


def make_raw_state(
    degree_in_rashi: float,
    rashi: RashiId = RashiId.MESHA,
    body: BodyId = BodyId.SUN,
) -> PlanetState:
    """Build a ``PlanetState`` whose ``degree_in_rashi`` is set verbatim
    (bypassing JRE-003 normalization) — used ONLY to prove the engine
    rejects out-of-range input (e.g. 30.0 / negatives) with the typed
    error rather than the value ever entering a computation."""
    lon = (RASHI_START[rashi] + degree_in_rashi) % 360.0
    return PlanetState(
        body=body,
        longitude_tropical=lon,
        longitude_sidereal=lon,
        longitude_used=lon,
        dms=DmsValue(degrees=int(lon), minutes=0, seconds=0.0, sign=1),
        rashi=rashi,
        degree_in_rashi=degree_in_rashi,
        nakshatra=None,
        nakshatra_lord=None,
        pada=None,
        degree_in_nakshatra=None,
        latitude=0.0,
        speed_longitude=1.0,
        retrograde=RetrogradeState.DIRECT,
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=2451545.0,
        provider_id="fake.astronomy",
        ephemeris_version="18",
    )

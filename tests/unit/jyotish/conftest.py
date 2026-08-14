"""Shared fakes and fixtures for the JRE-003 unit suite (no Swiss Ephemeris).

These provide:

- ``FakeAstronomy`` — a duck-typed replacement for ``AstronomicalService``
  with fully deterministic per-body longitudes/speeds (also used to build
  ``EphemerisResult``-shaped objects for the service tests).
- ``FakeHouseProvider`` / ``FakeEclipseProvider`` — deterministic providers
  for the house-cusp and eclipse protocols.
- ``make_planet_state`` — build a full ``PlanetState`` for pure-function tests.
"""

from __future__ import annotations

import datetime as dt

import pytest

from astronomy.models import (
    BodyId,
    BodyPosition,
    EphemerisRequest,
    EphemerisResult,
    PositionType,
    ProviderMetadata,
    ProviderRun,
    RetrogradeState,
    classify_retrograde,
)
from jyotish.houses import (
    HouseCuspResult,
    HouseProviderMetadata,
    whole_sign_cusps,
)
from jyotish.models import (
    DmsValue,
    EclipseClassification,
    EclipseContact,
    EclipseEvent,
    EclipseKind,
    HouseSystem,
    JyotishConfig,
    PlanetState,
    RashiId,
)

#: Sidereal offset used by the fake astronomy (degrees, "Lahiri-like").
FAKE_AYANAMSA = 24.0

#: Per-body tropical longitude drift (deg/day) used by the fake astronomy.
FAKE_DRIFT: dict[BodyId, float] = {
    BodyId.SUN: 0.98565,
    BodyId.MOON: 13.176,
    BodyId.MARS: 0.524,
    BodyId.MERCURY: 1.383,
    BodyId.JUPITER: 0.083,
    BodyId.VENUS: 1.602,
    BodyId.SATURN: 0.033,
    BodyId.RAHU: -0.053,
    BodyId.KETU: -0.053,
}

#: Base tropical longitude at JD 2451545.0 (arbitrary but fixed).
FAKE_BASE: dict[BodyId, float] = {
    BodyId.SUN: 280.0,
    BodyId.MOON: 35.0,
    BodyId.MARS: 120.0,
    BodyId.MERCURY: 200.0,
    BodyId.JUPITER: 150.0,
    BodyId.VENUS: 300.0,
    BodyId.SATURN: 90.0,
    BodyId.RAHU: 240.0,
    BodyId.KETU: 60.0,
}

FAKE_JD = 2451545.0


class FakeAstronomy:
    """Deterministic stand-in for ``AstronomicalService``."""

    def __init__(
        self,
        drift: dict[BodyId, float] | None = None,
        base: dict[BodyId, float] | None = None,
    ) -> None:
        self._drift = dict(FAKE_DRIFT if drift is None else drift)
        self._base = dict(FAKE_BASE if base is None else base)

    def compute(self, request: EphemerisRequest) -> EphemerisResult:
        from astronomy.models import CANONICAL_BODIES
        from astronomy.time import julian_day_ut, local_time_to_utc

        requested = request.bodies or tuple(CANONICAL_BODIES)
        bodies = tuple(b for b in CANONICAL_BODIES if b in requested)
        ayanamsa = request.config.ayanamsa
        _, _, utc_iso = local_time_to_utc(request.date, request.time, request.timezone)
        jd_ut = julian_day_ut(
            dt.datetime.fromisoformat(utc_iso.replace("Z", "+00:00"))
        )
        positions: list[BodyPosition] = []
        for body in bodies:
            tropical = (self._base[body] + self._drift[body] * (jd_ut - FAKE_JD)) % 360.0
            sidereal = None if ayanamsa is None else (tropical - FAKE_AYANAMSA) % 360.0
            speed = self._drift[body]
            positions.append(
                BodyPosition(
                    body=body,
                    longitude_tropical=tropical,
                    longitude_sidereal=sidereal,
                    latitude=0.0,
                    distance_au=1.0,
                    speed_longitude=speed,
                    speed_latitude=0.0,
                    speed_distance=0.0,
                    retrograde=classify_retrograde(speed),
                    position_type=PositionType.APPARENT,
                    ayanamsa_value=None if ayanamsa is None else FAKE_AYANAMSA,
                )
            )
        run = ProviderRun(
            positions=tuple(positions),
            ephemeris_mode=request.config.ephemeris_mode,
            ephemeris_files=("sepl_18.se1", "semo_18.se1"),
        )
        return EphemerisResult(
            request_snapshot=request,
            timestamp_utc_iso=utc_iso,
            timestamp_local_iso="",
            julian_day_ut=jd_ut,
            positions=tuple(positions),
            provider=ProviderMetadata(
                provider_id="fake.astronomy",
                library_name="fake",
                library_version="0.0.1",
                ephemeris_version="18",
            ),
            provider_run=run,
            config=request.config,
        )


class FakeHouseProvider:
    """Deterministic house-cusp provider for unit tests."""

    provider_id = "fake.houses"

    def __init__(self) -> None:
        self._metadata = HouseProviderMetadata(
            provider_id=self.provider_id,
            library_name="fake",
            library_version="0.0.1",
            ephemeris_version="fake",
        )

    @property
    def metadata(self) -> HouseProviderMetadata:
        return self._metadata

    def compute_cusps(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        house_system: HouseSystem,
        config: JyotishConfig,
    ) -> HouseCuspResult:
        asc = (longitude + jd_ut * 0.05) % 360.0
        if house_system is HouseSystem.WHOLE_SIGN:
            cusps = whole_sign_cusps(asc)
        else:
            cusps = tuple(((asc + i * 30.0) % 360.0) for i in range(12))
        return HouseCuspResult(
            cusps=cusps,
            ascendant_deg=asc,
            mc_deg=(asc + 90.0) % 360.0,
            ayanamsa_value=FAKE_AYANAMSA,
            provider=self._metadata,
        )


class FakeEclipseProvider:
    """Deterministic eclipse provider for unit tests."""

    provider_id = "fake.eclipse"

    def find_eclipses(
        self,
        jd_start: float,
        jd_end: float,
        kind: EclipseKind | None,
        config: JyotishConfig,
    ) -> tuple[EclipseEvent, ...]:
        maximum = (jd_start + jd_end) / 2.0
        contact = EclipseContact("MAX", maximum, "2000-01-01T00:00:00Z")
        event = EclipseEvent(
            kind=EclipseKind.SOLAR if kind in (None, EclipseKind.SOLAR) else kind,
            classification=EclipseClassification.TOTAL,
            maximum_jd_ut=maximum,
            maximum_utc_iso="2000-01-01T00:00:00Z",
            contacts=(contact,),
            magnitude=1.0,
            node_positions=(),
            solar_lunar_positions=(),
            geographic_visibility=None,
            pre_event_interval_days=0.5,
            post_event_interval_days=0.5,
            provider_id=self.provider_id,
            ephemeris_version="fake",
        )
        return (event,)


def make_planet_state(
    body: BodyId = BodyId.SUN,
    longitude_used: float = 120.0,
    speed: float = 1.0,
    latitude: float = 0.0,
    retrograde: RetrogradeState | None = None,
    rashi: RashiId | None = None,
) -> PlanetState:
    """Build a full ``PlanetState`` with consistent fields for pure tests."""
    from jyotish.nakshatra import degree_in_nakshatra, lord_of, nakshatra_of, pada_of
    from jyotish.position import _normalize
    from jyotish.rashi import degree_in_rashi, rashi_of

    lon = _normalize(longitude_used)
    nakshatra = nakshatra_of(lon)
    return PlanetState(
        body=body,
        longitude_tropical=lon,
        longitude_sidereal=(lon - FAKE_AYANAMSA) % 360.0,
        longitude_used=lon,
        dms=DmsValue(degrees=int(lon), minutes=0, seconds=0.0, sign=1),
        rashi=rashi if rashi is not None else rashi_of(lon),
        degree_in_rashi=degree_in_rashi(lon),
        nakshatra=nakshatra,
        nakshatra_lord=lord_of(nakshatra),
        pada=pada_of(lon),
        degree_in_nakshatra=degree_in_nakshatra(lon),
        latitude=latitude,
        speed_longitude=speed,
        retrograde=retrograde if retrograde is not None else classify_retrograde(speed),
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        julian_day_ut=FAKE_JD,
        provider_id="fake.astronomy",
        ephemeris_version="18",
    )


@pytest.fixture
def fake_astronomy() -> FakeAstronomy:
    return FakeAstronomy()


@pytest.fixture
def base_config() -> JyotishConfig:
    return JyotishConfig()


@pytest.fixture
def jd_epoch() -> float:
    return FAKE_JD


def jd_for(iso_utc: str) -> float:
    """JD of an ISO-UTC instant (Meeus; mirrors transit.iso_utc_to_jd)."""
    from jyotish.transit import iso_utc_to_jd

    return iso_utc_to_jd(iso_utc)


def iso_for(jd_ut: float) -> str:
    from jyotish.transit import jd_to_iso_utc

    return jd_to_iso_utc(jd_ut)

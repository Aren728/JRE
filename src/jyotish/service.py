"""``JyotishService`` — the deterministic public facade of JRE-003.

One deterministic engine serves both modes (JSP-001):
- GENERIC: ``planetary_state`` / ``pair_geometry`` / ``events_between`` /
  ``eclipses`` — no birth data anywhere.
- INDIVIDUAL: ``chart`` / ``transit_through_houses`` — birth data is request
  input only, echoed as ``birth_snapshot``, never engine state.

The service delegates all astronomy to JRE-002's public API and all house /
eclipse computation to the registered providers. It never interprets.
"""

from __future__ import annotations

import datetime as _dt
import math
from collections.abc import Callable

from astronomy.models import (
    BodyId,
    CalculationConfig,
    EphemerisMode,
    EphemerisRequest,
    EphemerisResult,
    ProviderMetadata,
)
from astronomy.service import AstronomicalService

from . import geometry as _geometry
from . import position as _position
from .config import load_config, validate
from .eclipse import SWISSEPH_ECLIPSE_PROVIDER_ID, EclipseProvider, EclipseRegistry
from .errors import (
    InvalidBirthDataError,
    InvalidConfigError,
    JyotishError,
    ProviderCompatibilityError,
    UnsupportedReferencePointError,
)
from .houses import (
    SWISSEPH_HOUSE_PROVIDER_ID,
    HouseCuspProvider,
    HouseCuspRegistry,
    bhava_containing_longitude,
    compute_bhavas,
    whole_sign_cusps,
)
from .lagna import derive_lagna
from .models import (
    AspectRelationship,
    Bhava,
    BirthData,
    EclipseEvent,
    EclipseKind,
    HouseCuspResult,
    HouseSystem,
    HouseTransitEntry,
    JyotishConfig,
    LagnaState,
    NatalChart,
    PairGeometry,
    PlanetState,
    RashiId,
    TransitEvent,
    TransitEventKind,
    TransitReferencePoint,
    TransitThroughHouses,
)
from .transit import ContinuousTransitEngine, iso_utc_to_jd, jd_to_iso_utc

#: Canonical body order (astronomy declaration order).
_CANONICAL_BODIES: tuple[BodyId, ...] = (
    BodyId.SUN,
    BodyId.MOON,
    BodyId.MARS,
    BodyId.MERCURY,
    BodyId.JUPITER,
    BodyId.VENUS,
    BodyId.SATURN,
    BodyId.RAHU,
    BodyId.KETU,
)

#: Minimum civil date accepted (astronomy contract, proleptic Gregorian).
_MIN_CIVIL_DATE = _dt.date(1582, 10, 15)

#: Providers registered by default; populated lazily on first use.
_default_house_registry: HouseCuspRegistry | None = None
_default_eclipse_registry: EclipseRegistry | None = None


def default_house_registry() -> HouseCuspRegistry:
    """Process-wide house registry; registers the Swiss Ephemeris provider once."""
    global _default_house_registry
    if _default_house_registry is None:
        from .swisseph.houses import SwissEphemerisHouseCuspProvider  # noqa: PLC0415

        registry = HouseCuspRegistry()
        registry.register(
            SwissEphemerisHouseCuspProvider(),
            tuple(house for house in _house_system_list()),
        )
        _default_house_registry = registry
    return _default_house_registry


def default_eclipse_registry() -> EclipseRegistry:
    """Process-wide eclipse registry; registers the Swiss Ephemeris provider once."""
    global _default_eclipse_registry
    if _default_eclipse_registry is None:
        from .swisseph.eclipse import SwissEphemerisEclipseProvider  # noqa: PLC0415

        registry = EclipseRegistry()
        registry.register(SwissEphemerisEclipseProvider())
        _default_eclipse_registry = registry
    return _default_eclipse_registry


def get_house_provider(provider_id: str | None = None) -> HouseCuspProvider:
    """Return a house provider instance (default: the Swiss Ephemeris adapter)."""
    if provider_id is None or provider_id == SWISSEPH_HOUSE_PROVIDER_ID:
        from .swisseph.houses import SwissEphemerisHouseCuspProvider  # noqa: PLC0415

        return SwissEphemerisHouseCuspProvider()
    return default_house_registry().get(provider_id)


def get_eclipse_provider(provider_id: str | None = None) -> EclipseProvider:
    """Return an eclipse provider instance (default: the Swiss Ephemeris adapter)."""
    if provider_id is None or provider_id == SWISSEPH_ECLIPSE_PROVIDER_ID:
        from .swisseph.eclipse import SwissEphemerisEclipseProvider  # noqa: PLC0415

        return SwissEphemerisEclipseProvider()
    return default_eclipse_registry().get(provider_id)


def _house_system_list() -> tuple[HouseSystem, ...]:
    from .models import HouseSystem

    return tuple(HouseSystem)


class JyotishService:
    """Deterministic Jyotish coordinate/state facade (both modes)."""

    def __init__(
        self,
        astronomy: AstronomicalService | None = None,
        house_registry: HouseCuspRegistry | None = None,
        eclipse_registry: EclipseRegistry | None = None,
        config: JyotishConfig | None = None,
    ) -> None:
        self._astronomy = astronomy if astronomy is not None else AstronomicalService()
        self._house_registry = (
            house_registry if house_registry is not None else default_house_registry()
        )
        self._eclipse_registry = (
            eclipse_registry if eclipse_registry is not None else default_eclipse_registry()
        )
        self._default_config = load_config() if config is None else validate(config)

    # ------------------------------------------------------------------ #
    # GENERIC mode
    # ------------------------------------------------------------------ #

    def planetary_state(
        self,
        date: _dt.date,
        time: _dt.time,
        timezone: str,
        latitude: float,
        longitude: float,
        bodies: tuple[BodyId, ...] | None = None,
        config: JyotishConfig | None = None,
    ) -> tuple[PlanetState, ...]:
        """Generic mode: instant -> continuous Jyotish states (no birth data)."""
        cfg = self._resolve_config(config)
        result = self._compute(date, time, timezone, latitude, longitude, bodies, cfg)
        return self._states_from_result(result, cfg)

    def pair_geometry(
        self,
        states: tuple[PlanetState, ...],
        config: JyotishConfig | None = None,
        bhavas: tuple[Bhava, ...] | None = None,
    ) -> tuple[PairGeometry, ...]:
        """All planet-to-planet pair facts for the given states."""
        cfg = self._resolve_config(config)
        return _geometry.all_pairs(states, cfg, bhavas=bhavas)

    def events_between(
        self,
        start_utc_iso: str,
        end_utc_iso: str,
        bodies: tuple[BodyId, ...],
        kinds: tuple[TransitEventKind, ...] | None = None,
        config: JyotishConfig | None = None,
    ) -> tuple[TransitEvent, ...]:
        """Continuous-transit events in an ISO-UTC interval."""
        cfg = self._resolve_config(config)
        start_jd = iso_utc_to_jd(start_utc_iso)
        end_jd = iso_utc_to_jd(end_utc_iso)
        engine = ContinuousTransitEngine(
            self._position_provider(bodies, cfg)
        )
        return engine.events_between(start_jd, end_jd, bodies, kinds, cfg)

    def state_series(
        self,
        start_utc_iso: str,
        end_utc_iso: str,
        step_days: float,
        bodies: tuple[BodyId, ...],
        config: JyotishConfig | None = None,
    ) -> tuple[PlanetState, ...]:
        """Sampled continuous states over an ISO-UTC interval."""
        cfg = self._resolve_config(config)
        start_jd = iso_utc_to_jd(start_utc_iso)
        end_jd = iso_utc_to_jd(end_utc_iso)
        engine = ContinuousTransitEngine(self._position_provider(bodies, cfg))
        return engine.state_series(start_jd, end_jd, step_days, bodies, cfg)

    def position_at(
        self,
        julian_day_ut: float,
        bodies: tuple[BodyId, ...] | None = None,
        config: JyotishConfig | None = None,
    ) -> tuple[PlanetState, ...]:
        """Lower-level: planet states at a raw Julian Day (UT), timezone UTC."""
        cfg = self._resolve_config(config)
        iso = jd_to_iso_utc(julian_day_ut)
        date, time = _iso_to_civil(iso)
        return self.planetary_state(date, time, "UTC", 0.0, 0.0, bodies, cfg)

    def eclipses(
        self,
        start_utc_iso: str,
        end_utc_iso: str,
        kind: EclipseKind | None = None,
        config: JyotishConfig | None = None,
    ) -> tuple[EclipseEvent, ...]:
        """Eclipse facts in an ISO-UTC interval (data only, ADR-006)."""
        cfg = self._resolve_config(config)
        start_jd = iso_utc_to_jd(start_utc_iso)
        end_jd = iso_utc_to_jd(end_utc_iso)
        self._eclipse_registry.freeze()
        provider = self._eclipse_registry.default()
        events = provider.find_eclipses(start_jd, end_jd, kind, cfg)
        if not events:
            return ()
        # Attach Sun/Moon/node positions at each maximum (astronomy passthrough).
        result: list[EclipseEvent] = []
        for event in events:
            states = self.position_at(event.maximum_jd_ut, None, cfg)
            positions = {s.body: s for s in states}
            node_positions = tuple(
                positions[b] for b in (BodyId.RAHU, BodyId.KETU) if b in positions
            )
            solar_lunar = tuple(
                positions[b] for b in (BodyId.SUN, BodyId.MOON) if b in positions
            )
            from dataclasses import replace

            result.append(
                replace(
                    event,
                    node_positions=node_positions,
                    solar_lunar_positions=solar_lunar,
                )
            )
        return tuple(result)

    # ------------------------------------------------------------------ #
    # INDIVIDUAL mode
    # ------------------------------------------------------------------ #

    def chart(
        self, birth: BirthData, config: JyotishConfig | None = None
    ) -> NatalChart:
        """Natal chart from birth data (birth snapshot echoed, never stored)."""
        cfg = self._resolve_config(config)
        birth_date, birth_time = _parse_birth(birth)
        result = self._compute(
            birth_date, birth_time, birth.timezone, birth.latitude, birth.longitude, None, cfg
        )
        states = self._states_from_result(result, cfg)
        cusp_result = self._house_cusps(
            result.julian_day_ut, birth.latitude, birth.longitude, cfg
        )
        bhavas = compute_bhavas(cusp_result, states, cfg)
        lagna = derive_lagna(cusp_result.ascendant_deg, cfg, cfg.house_system, bhavas[0])
        metadata = (
            result.provider,
            ProviderMetadata(
                provider_id=cusp_result.provider.provider_id,
                library_name=cusp_result.provider.library_name,
                library_version=cusp_result.provider.library_version,
                ephemeris_version=cusp_result.provider.ephemeris_version,
            ),
        )
        return NatalChart(
            birth_snapshot=birth,
            lagna=lagna,
            bhavas=bhavas,
            planet_states=states,
            config=cfg,
            provider_metadata=metadata,
        )

    def transit_through_houses(
        self,
        birth: BirthData,
        transit_date: _dt.date,
        transit_time: _dt.time,
        transit_timezone: str,
        reference: TransitReferencePoint = TransitReferencePoint.LAGNA,
        config: JyotishConfig | None = None,
    ) -> TransitThroughHouses:
        """Transit instant against a natal chart, per an explicit reference."""
        cfg = self._resolve_config(config)
        natal = self.chart(birth, cfg)

        result = self._compute(
            transit_date,
            transit_time,
            transit_timezone,
            birth.latitude,
            birth.longitude,
            None,
            cfg,
        )
        transit_states = self._states_from_result(result, cfg)

        entries: list[HouseTransitEntry] = []
        for transit_state in transit_states:
            house_number, house_rashi, occupants = self._natal_house_for(
                natal, transit_state, reference, cfg
            )
            aspects = tuple(
                aspect
                for occupant in natal.planet_states
                if occupant.body in occupants
                for aspect in _geometry.pair_geometry(
                    transit_state, occupant, cfg
                ).aspects
            )
            entries.append(
                HouseTransitEntry(
                    body=transit_state.body,
                    natal_house_number=house_number,
                    natal_house_lord=_house_lord_for(house_rashi),
                    natal_occupants=occupants,
                    aspects_to_natal=aspects,
                    natal_house_rashi=house_rashi,
                )
            )

        return TransitThroughHouses(
            reference=reference,
            transit_instant_utc_iso=result.timestamp_utc_iso,
            planet_states=transit_states,
            entries=tuple(entries),
            birth_snapshot=birth,
            config=cfg,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _resolve_config(self, config: JyotishConfig | None) -> JyotishConfig:
        cfg = self._default_config if config is None else validate(config)
        if cfg.zodiac_mode.value == "SIDEREAL" and cfg.ayanamsa is None:
            raise InvalidConfigError(
                "zodiac_mode=SIDEREAL requires ayanamsa to be set (an explicit "
                "sidereal frame must always be computable)"
            )
        return cfg

    def _compute(
        self,
        date: _dt.date,
        time: _dt.time,
        timezone: str,
        latitude: float,
        longitude: float,
        bodies: tuple[BodyId, ...] | None,
        cfg: JyotishConfig,
    ) -> EphemerisResult:
        if date < _MIN_CIVIL_DATE:
            raise InvalidBirthDataError(
                f"date {date.isoformat()} is before the accepted range "
                f"({_MIN_CIVIL_DATE.isoformat()} onward)"
            )
        request = EphemerisRequest(
            date=date,
            time=time,
            timezone=timezone,
            latitude=latitude,
            longitude=longitude,
            bodies=bodies,
            config=_astronomy_config(cfg),
            provider_id=cfg.provider_id,
        )
        result = self._astronomy.compute(request)
        if (
            cfg.ephemeris_version is not None
            and result.provider.ephemeris_version != cfg.ephemeris_version
        ):
            raise ProviderCompatibilityError(
                f"ephemeris version pin {cfg.ephemeris_version!r} does not match "
                f"provider version {result.provider.ephemeris_version!r}"
            )
        return result

    def _states_from_result(
        self, result: EphemerisResult, cfg: JyotishConfig
    ) -> tuple[PlanetState, ...]:
        return tuple(
            _position.derive_planet_state(
                body_pos,
                cfg,
                result.timestamp_utc_iso,
                result.julian_day_ut,
                result.provider.provider_id,
                result.provider.ephemeris_version,
            )
            for body_pos in result.positions
        )

    def _position_provider(
        self, bodies: tuple[BodyId, ...], cfg: JyotishConfig
    ) -> Callable[[float], tuple[PlanetState, ...]]:
        def provider(jd_ut: float) -> tuple[PlanetState, ...]:
            return self.position_at(jd_ut, bodies, cfg)

        return provider

    def _house_cusps(
        self, jd_ut: float, latitude: float, longitude: float, cfg: JyotishConfig
    ) -> HouseCuspResult:
        self._house_registry.freeze()
        provider = self._house_registry.get_for(cfg.house_system)
        return provider.compute_cusps(jd_ut, latitude, longitude, cfg.house_system, cfg)

    def _natal_house_for(
        self,
        natal: NatalChart,
        transit_state: PlanetState,
        reference: TransitReferencePoint,
        cfg: JyotishConfig,
    ) -> tuple[int, RashiId, tuple[BodyId, ...]]:
        """Natal house number/rashi/occupants for a transit longitude."""
        if reference is TransitReferencePoint.LAGNA:
            anchor = natal.lagna.rashi
        elif reference is TransitReferencePoint.MOON:
            anchor = _body_rashi(natal, BodyId.MOON)
        elif reference is TransitReferencePoint.SUN:
            anchor = _body_rashi(natal, BodyId.SUN)
        elif reference is TransitReferencePoint.ASC:
            bhava = bhava_containing_longitude(natal.bhavas, transit_state.longitude_used)
            if bhava is None:
                raise UnsupportedReferencePointError(
                    f"transit longitude {transit_state.longitude_used} is outside "
                    f"all natal bhavas for reference {reference.value}"
                )
            return bhava.house_number, bhava.rashi, bhava.occupants
        else:
            # Robust to raw-string values (SPEC §14.2 / TEST-PLAN §5): any
            # value other than the four reference points is an
            # ``UnsupportedReferencePointError``, never an AttributeError.
            label = getattr(reference, "value", reference)
            raise UnsupportedReferencePointError(f"unknown reference {label!r}")

        anchor_index = _rashi_index(anchor)
        transit_index = _rashi_index(transit_state.rashi)
        from .rashi import RASHI_ORDER as _ORDER  # noqa: PLC0415

        house_number = (transit_index - anchor_index) % 12 + 1
        house_rashi = _ORDER[(anchor_index + house_number - 1) % 12]
        occupants = tuple(
            s.body for s in natal.planet_states if s.rashi == house_rashi
        )
        return house_number, house_rashi, occupants


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #


def _astronomy_config(cfg: JyotishConfig) -> CalculationConfig:
    return CalculationConfig(
        ayanamsa=cfg.ayanamsa,
        ephemeris_mode=EphemerisMode.SWIEPH,
        position_type=cfg.position_type,
        node_type=cfg.node_model,
        ephemeris_path=None,
        allow_fallback=True,
    )


def _parse_birth(birth: BirthData) -> tuple[_dt.date, _dt.time]:
    try:
        date = _dt.date.fromisoformat(birth.date)
        time = _dt.time.fromisoformat(birth.time)
    except ValueError as exc:
        raise InvalidBirthDataError(
            f"birth date/time malformed: date={birth.date!r} time={birth.time!r}"
        ) from exc
    if not (-90.0 <= birth.latitude <= 90.0 and math.isfinite(birth.latitude)):
        raise InvalidBirthDataError(f"birth latitude out of range: {birth.latitude}")
    if not (-180.0 <= birth.longitude <= 180.0 and math.isfinite(birth.longitude)):
        raise InvalidBirthDataError(f"birth longitude out of range: {birth.longitude}")
    return date, time


def _iso_to_civil(iso: str) -> tuple[_dt.date, _dt.time]:
    """Split an ISO-UTC ``Z`` string into civil date/time (UTC)."""
    body = iso[:-1] if iso.endswith("Z") else iso
    return _dt.date.fromisoformat(body[:10]), _dt.time.fromisoformat(body[11:].split("+")[0])


def _body_rashi(natal: NatalChart, body: BodyId) -> RashiId:
    for state in natal.planet_states:
        if state.body == body:
            return state.rashi
    raise JyotishError(f"natal chart is missing {body.value!r}")


def _rashi_index(rashi: RashiId) -> int:
    from .rashi import RASHI_ORDER as _ORDER  # noqa: PLC0415

    return _ORDER.index(rashi)


def _house_lord_for(rashi: RashiId) -> BodyId:
    from .rashi import lord_of

    return lord_of(rashi)


# Silence unused-import linters for re-exported symbols used by consumers.
_ = (AspectRelationship, LagnaState, whole_sign_cusps, _geometry, _position, EphemerisMode)

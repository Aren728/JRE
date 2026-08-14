"""Continuous transit engine (Specialist spec §15, ADR-005).

- Deterministic event search: fixed sampling step, unwrapped longitude,
  sign-change isolation, bisection to a fixed tolerance with a fixed
  iteration cap. Retrograde re-crossings each produce their own event.
- Bounded process-scoped memoization (LRU, 10 000 entries) keyed by the exact
  JD — a pure memo of a pure function, so determinism is unaffected.
- ``SearchMetadata.position_calls`` = the number of distinct JD evaluations
  the search requested (a pure function of the algorithm, identical across
  warm/cold cache states).

Pure ISO-UTC <-> Julian Day helpers live here per Specialist §23 (the same
documented Meeus formula the astronomy core uses).
"""

from __future__ import annotations

import datetime as _dt
from collections import OrderedDict
from collections.abc import Callable

from astronomy.models import BodyId, RetrogradeState

from . import nakshatra as _nakshatra
from . import rashi as _rashi
from .errors import TransitSearchError
from .models import (
    JyotishConfig,
    NakshatraId,
    Pada,
    PlanetState,
    RashiId,
    SearchMetadata,
    TransitEvent,
    TransitEventKind,
)

#: Fixed bisection iteration cap (ADR-005).
MAX_BISECTION_ITERATIONS = 60

#: Memoization bound (Specialist §15.1).
POSITION_CACHE_LIMIT = 10_000


# --------------------------------------------------------------------------- #
# Pure time helpers (Specialist §23) — Meeus, Astronomical Algorithms ch. 7
# --------------------------------------------------------------------------- #


def iso_utc_to_jd(iso_utc: str) -> float:
    """ISO 8601 UTC (``Z``) instant -> Julian Day (UT)."""
    value = _dt.datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=_dt.UTC)
    utc = value.astimezone(_dt.UTC)
    return _julian_day(
        utc.year, utc.month, utc.day, utc.hour, utc.minute,
        utc.second + utc.microsecond / 1e6,
    )


def jd_to_iso_utc(jd_ut: float) -> str:
    """Julian Day (UT) -> ISO 8601 UTC ``Z`` string (microsecond precision)."""
    jd = jd_ut + 0.5
    z = int(jd)
    f = jd - z
    a = z
    if z >= 2299161:  # Gregorian calendar
        alpha = int((z - 1867216.25) / 36524.25)
        a = z + 1 + alpha - alpha // 4
    b = a + 1524
    c = int((b - 122.1) / 365.25)
    d = int(365.25 * c)
    e = int((b - d) / 30.6001)
    day = b - d - int(30.6001 * e) + f
    month = e - 1 if e < 14 else e - 13
    year = c - 4716 if month > 2 else c - 4715

    day_int = int(day)
    frac = day - day_int
    total_seconds = frac * 86400.0
    hour = int(total_seconds // 3600)
    minute = int((total_seconds - hour * 3600) // 60)
    second = total_seconds - hour * 3600 - minute * 60
    micro = int(round((second - int(second)) * 1_000_000))
    sec_int = int(second)
    if micro >= 1_000_000:
        micro -= 1_000_000
        sec_int += 1
    if sec_int >= 60:
        sec_int = 0
        minute += 1
    if minute >= 60:
        minute = 0
        hour += 1
    if hour >= 24:
        hour = 0
        day_int += 1

    dt_value = _dt.datetime(
        year, month, day_int, hour, minute, sec_int, micro, tzinfo=_dt.UTC
    )
    text = dt_value.isoformat()
    if text.endswith("+00:00"):
        text = text[:-6] + "Z"
    return text


def _julian_day(year: int, month: int, day: int, hour: int, minute: int, second: float) -> float:
    """Meeus ch. 7 Gregorian JD formula (same as astronomy's pure formula)."""
    y, m = year, month
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (
        int(365.25 * (y + 4716))
        + int(30.6001 * (m + 1))
        + day
        + b
        - 1524.5
        + (hour + minute / 60.0 + second / 3600.0) / 24.0
    )


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #


class ContinuousTransitEngine:
    """Deterministic continuous-transit event engine."""

    def __init__(
        self,
        position_provider: Callable[[float], tuple[PlanetState, ...]] | None = None,
    ) -> None:
        #: Bound position provider; replaced by the service per query.
        self._position_provider: (
            Callable[[float], tuple[PlanetState, ...]] | None
        ) = position_provider
        self._cache: OrderedDict[float, tuple[PlanetState, ...]] = OrderedDict()
        self._query_keys: set[float] = set()

    def set_position_provider(self, provider: Callable[[float], tuple[PlanetState, ...]]) -> None:
        self._position_provider = provider

    # -- memoized position lookup ------------------------------------------- #

    def position_at(self, jd_ut: float) -> tuple[PlanetState, ...]:
        """Memoized planet states at a Julian Day (bounded LRU)."""
        if self._position_provider is None:
            raise RuntimeError("no position provider bound to the transit engine")
        self._query_keys.add(jd_ut)
        if jd_ut in self._cache:
            self._cache.move_to_end(jd_ut)
            return self._cache[jd_ut]
        states = self._position_provider(jd_ut)
        self._cache[jd_ut] = states
        self._cache.move_to_end(jd_ut)
        while len(self._cache) > POSITION_CACHE_LIMIT:
            self._cache.popitem(last=False)
        return states

    # -- event search -------------------------------------------------------- #

    def events_between(
        self,
        start_jd: float,
        end_jd: float,
        bodies: tuple[BodyId, ...],
        kinds: tuple[TransitEventKind, ...] | None,
        config: JyotishConfig,
    ) -> tuple[TransitEvent, ...]:
        """All transit events in the closed interval ``[start_jd, end_jd]``."""
        if start_jd > end_jd:
            raise TransitSearchError(f"start_jd {start_jd} must be <= end_jd {end_jd}")
        if not bodies:
            raise TransitSearchError("bodies must not be empty")
        self._query_keys = set()

        step_days = config.transit_sample_step_hours / 24.0
        n_samples = int((end_jd - start_jd) / step_days) + 1
        samples = [start_jd + i * step_days for i in range(n_samples)]
        samples = [s for s in samples if s <= end_jd]
        if samples[-1] < end_jd:
            samples.append(end_jd)

        wanted = set(kinds) if kinds is not None else set(TransitEventKind)

        events: list[TransitEvent] = []
        for body in bodies:
            series = [self._state_for(body, jd) for jd in samples]
            unwrapped = _unwrap_longitudes([s.longitude_used for s in series])

            if wanted & {
                TransitEventKind.RASHI_INGRESS,
                TransitEventKind.RASHI_EGRESS,
            }:
                for boundary in _rashi_boundaries(unwrapped):
                    events.extend(
                        self._boundary_events(
                            body, samples, unwrapped, boundary, config,
                            TransitEventKind.RASHI_INGRESS,
                        )
                    )

            if wanted & {
                TransitEventKind.NAKSHATRA_INGRESS,
                TransitEventKind.NAKSHATRA_EGRESS,
            }:
                for boundary in _arc_boundaries(_nakshatra.NAKSHATRA_ARC, unwrapped):
                    events.extend(
                        self._boundary_events(
                            body, samples, unwrapped, boundary, config,
                            TransitEventKind.NAKSHATRA_INGRESS,
                        )
                    )

            if wanted & {
                TransitEventKind.PADA_INGRESS,
                TransitEventKind.PADA_EGRESS,
            }:
                for boundary in _arc_boundaries(_nakshatra.PADA_ARC, unwrapped):
                    events.extend(
                        self._boundary_events(
                            body, samples, unwrapped, boundary, config,
                            TransitEventKind.PADA_INGRESS,
                        )
                    )

            if wanted & {
                TransitEventKind.STATION_RETROGRADE,
                TransitEventKind.STATION_DIRECT,
            }:
                events.extend(self._station_events(body, samples, series, config))

        events.sort(key=lambda e: (e.event_julian_day_ut, e.body.value, e.kind.value))
        return tuple(events)

    def state_series(
        self,
        start_jd: float,
        end_jd: float,
        step_days: float,
        bodies: tuple[BodyId, ...],
        config: JyotishConfig,
    ) -> tuple[PlanetState, ...]:
        """Sampled continuous planet states over an interval."""
        if step_days <= 0.0:
            raise TransitSearchError(f"step_days must be positive, got {step_days}")
        self._query_keys = set()
        n = max(1, int((end_jd - start_jd) / step_days) + 1)
        result: list[PlanetState] = []
        for i in range(n):
            jd = min(start_jd + i * step_days, end_jd)
            for state in self.position_at(jd):
                if state.body in bodies:
                    result.append(state)
        return tuple(result)

    # -- internals ------------------------------------------------------------ #

    def _state_for(self, body: BodyId, jd: float) -> PlanetState:
        for state in self.position_at(jd):
            if state.body == body:
                return state
        raise TransitSearchError(f"body {body.value!r} not present in position batch at {jd}")

    def _boundary_events(
        self,
        body: BodyId,
        samples: list[float],
        unwrapped: list[float],
        boundary: float,
        config: JyotishConfig,
        ingress_kind: TransitEventKind,
    ) -> list[TransitEvent]:
        """Find crossings of one (unwrapped) boundary; each sign change is an event."""
        f = [lam - boundary for lam in unwrapped]
        egress_kind = _egress_kind_for(ingress_kind)
        result: list[TransitEvent] = []
        for i in range(len(samples) - 1):
            f0, f1 = f[i], f[i + 1]
            if f0 == 0.0:
                # Sample landed exactly on the boundary: no bisection needed.
                state = self._state_for(body, samples[i])
                kind = ingress_kind if f1 > 0.0 else egress_kind
                result.append(self._make_event(body, samples[i], kind, boundary, config, state, 0))
            elif f0 * f1 < 0.0:
                jd, state, iterations = self._bisect(
                    samples[i], samples[i + 1], body, boundary, f0, config
                )
                kind = ingress_kind if f1 > f0 else egress_kind
                result.append(self._make_event(body, jd, kind, boundary, config, state, iterations))
        return result

    def _bisect(
        self,
        lo: float,
        hi: float,
        body: BodyId,
        boundary: float,
        f_lo: float,
        config: JyotishConfig,
    ) -> tuple[float, PlanetState, int]:
        """Bisect f(t) = λ*(t) − boundary to tolerance; returns (jd, state,
        iterations-used) so ``SearchMetadata.iterations`` reports the actual
        bisection count (DATA-CONTRACT §8.2)."""
        tolerance = config.transit_tolerance_jd
        iterations = 0
        while hi - lo > tolerance and iterations < MAX_BISECTION_ITERATIONS:
            mid = (lo + hi) / 2.0
            state = self._state_for(body, mid)
            f_mid = _unwrap_difference(state.longitude_used, boundary, f_lo)
            if f_mid == 0.0:
                return mid, state, iterations
            if (f_lo < 0.0) == (f_mid < 0.0):
                lo, f_lo = mid, f_mid
            else:
                hi = mid
            iterations += 1
        if iterations >= MAX_BISECTION_ITERATIONS:
            raise TransitSearchError(
                f"bisection failed to converge for {body.value!r} near boundary {boundary}"
            )
        state = self._state_for(body, (lo + hi) / 2.0)
        return (lo + hi) / 2.0, state, iterations

    def _station_events(
        self,
        body: BodyId,
        samples: list[float],
        series: list[PlanetState],
        config: JyotishConfig,
    ) -> list[TransitEvent]:
        result: list[TransitEvent] = []
        speeds = [s.speed_longitude for s in series]
        for i in range(len(samples) - 1):
            v0, v1 = speeds[i], speeds[i + 1]
            if v0 == 0.0:
                # Sample landed exactly on the station: no bisection needed.
                result.append(self._station_event(body, samples[i], series[i], config, v1 < 0.0, 0))
            elif v0 * v1 < 0.0:
                jd, state, iterations = self._bisect_speed(
                    samples[i], samples[i + 1], body, v0, config
                )
                result.append(self._station_event(body, jd, state, config, v1 < 0.0, iterations))
        return result

    def _bisect_speed(
        self, lo: float, hi: float, body: BodyId, v_lo: float, config: JyotishConfig
    ) -> tuple[float, PlanetState, int]:
        tolerance = config.transit_tolerance_jd
        iterations = 0
        while hi - lo > tolerance and iterations < MAX_BISECTION_ITERATIONS:
            mid = (lo + hi) / 2.0
            state = self._state_for(body, mid)
            v_mid = state.speed_longitude
            if v_mid == 0.0:
                return mid, state, iterations
            if (v_lo < 0.0) == (v_mid < 0.0):
                lo, v_lo = mid, v_mid
            else:
                hi = mid
            iterations += 1
        if iterations >= MAX_BISECTION_ITERATIONS:
            raise TransitSearchError(f"bisection failed to converge for station of {body.value!r}")
        state = self._state_for(body, (lo + hi) / 2.0)
        return (lo + hi) / 2.0, state, iterations

    def _station_event(
        self,
        body: BodyId,
        jd: float,
        state: PlanetState,
        config: JyotishConfig,
        retrograde_going: bool,
        iterations: int,
    ) -> TransitEvent:
        kind = (
            TransitEventKind.STATION_RETROGRADE
            if retrograde_going
            else TransitEventKind.STATION_DIRECT
        )
        return TransitEvent(
            body=body,
            kind=kind,
            event_julian_day_ut=jd,
            event_utc_iso=jd_to_iso_utc(jd),
            boundary_deg=None,
            reached=None,
            direction=RetrogradeState.STATIONARY,
            search_metadata=self._metadata(config, iterations),
        )

    def _make_event(
        self,
        body: BodyId,
        jd: float,
        kind: TransitEventKind,
        boundary: float,
        config: JyotishConfig,
        state: PlanetState,
        iterations: int,
    ) -> TransitEvent:
        boundary_mod = boundary % 360.0
        return TransitEvent(
            body=body,
            kind=kind,
            event_julian_day_ut=jd,
            event_utc_iso=jd_to_iso_utc(jd),
            boundary_deg=0.0 if boundary_mod == 0.0 else boundary_mod,
            reached=_reached_for(kind, boundary_mod),
            direction=state.retrograde,
            search_metadata=self._metadata(config, iterations),
        )

    def _metadata(self, config: JyotishConfig, iterations: int) -> SearchMetadata:
        """Determinism echo: ``iterations`` = the bisection iterations actually
        used for this event (0 when a sample landed exactly on the boundary),
        ``position_calls`` = distinct memo keys evaluated (DATA-CONTRACT §8.2)."""
        return SearchMetadata(
            algorithm="bisection-on-monotonic-segments",
            sample_step_hours=config.transit_sample_step_hours,
            tolerance_jd=config.transit_tolerance_jd,
            iterations=iterations,
            position_calls=len(self._query_keys),
        )


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #


def _unwrap_longitudes(longitudes: list[float]) -> list[float]:
    """Make the longitude series continuous by adding/subtracting 360."""
    result: list[float] = []
    carry = 0.0
    prev = longitudes[0]
    for value in longitudes:
        delta = value - prev
        while delta > 180.0:
            carry -= 360.0
            delta -= 360.0
        while delta < -180.0:
            carry += 360.0
            delta += 360.0
        result.append(value + carry)
        prev = value
    return result


def _unwrap_difference(longitude: float, boundary: float, reference: float) -> float:
    """Unwrap ``longitude - boundary`` to stay continuous with ``reference``.

    The sample spacing guarantees the true difference moves by well under
    180° per step, so anchoring to the previous sample's value is exact.
    """
    diff = longitude - boundary
    while diff - reference > 180.0:
        diff -= 360.0
    while reference - diff > 180.0:
        diff += 360.0
    return diff


def _rashi_boundaries(unwrapped: list[float]) -> list[float]:
    """All rashi boundaries (multiples of 30°) within the sampled range."""
    lo = min(unwrapped) - 1.0
    hi = max(unwrapped) + 1.0
    return [b * 30.0 for b in range(int(lo // 30.0), int(hi // 30.0) + 1)]


def _arc_boundaries(arc: float, unwrapped: list[float]) -> list[float]:
    """All nakshatra/pada boundaries (multiples of ``arc``) in the range."""
    lo = min(unwrapped) - 1.0
    hi = max(unwrapped) + 1.0
    return [b * arc for b in range(int(lo // arc), int(hi // arc) + 1)]


def _egress_kind_for(kind: TransitEventKind) -> TransitEventKind:
    return {
        TransitEventKind.RASHI_INGRESS: TransitEventKind.RASHI_EGRESS,
        TransitEventKind.NAKSHATRA_INGRESS: TransitEventKind.NAKSHATRA_EGRESS,
        TransitEventKind.PADA_INGRESS: TransitEventKind.PADA_EGRESS,
    }[kind]


def _reached_for(kind: TransitEventKind, boundary_mod: float) -> RashiId | NakshatraId | Pada:
    """What bucket the boundary crossing reaches (Rashi/Nakshatra/Pada)."""
    if kind in (TransitEventKind.RASHI_INGRESS, TransitEventKind.RASHI_EGRESS):
        return _rashi.rashi_of(boundary_mod)
    if kind in (TransitEventKind.NAKSHATRA_INGRESS, TransitEventKind.NAKSHATRA_EGRESS):
        return _nakshatra.nakshatra_of(boundary_mod)
    return _nakshatra.pada_of(boundary_mod)

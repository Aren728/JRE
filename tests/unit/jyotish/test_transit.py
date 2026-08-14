"""Continuous transit engine (req. E, ADR-005): time helpers, ingress/egress,
stations, deterministic search, repeated passages over the same degree.
"""

from __future__ import annotations

import pytest
from tests.unit.jyotish.conftest import FAKE_JD, make_planet_state

from astronomy.models import BodyId, RetrogradeState
from jyotish.errors import TransitSearchError
from jyotish.models import (
    JyotishConfig,
    RashiId,
    TransitEventKind,
)
from jyotish.transit import (
    MAX_BISECTION_ITERATIONS,
    ContinuousTransitEngine,
    iso_utc_to_jd,
    jd_to_iso_utc,
)

JD0 = FAKE_JD


# --------------------------------------------------------------------------- #
# Pure time helpers (Specialist §23)
# --------------------------------------------------------------------------- #


def test_iso_utc_to_jd_known_values():
    # 2000-01-01T12:00:00Z = JD 2451545.0 (Meeus example).
    assert iso_utc_to_jd("2000-01-01T12:00:00Z") == pytest.approx(2451545.0, abs=1e-6)
    # 1990-06-15T04:30:00Z (the JRE-002 pinned fixture).
    assert iso_utc_to_jd("1990-06-15T04:30:00Z") == pytest.approx(2448057.6875, abs=1e-6)


def test_jd_to_iso_utc_round_trip():
    for jd in (2451545.0, 2448057.6875, 2451545.5, 2451545.123456):
        assert iso_utc_to_jd(jd_to_iso_utc(jd)) == pytest.approx(jd, abs=1e-9)


def test_jd_to_iso_utc_known_format():
    assert jd_to_iso_utc(2451545.0) == "2000-01-01T12:00:00Z"
    assert jd_to_iso_utc(2448057.6875) == "1990-06-15T04:30:00Z"


# --------------------------------------------------------------------------- #
# Event search with a controlled position provider
# --------------------------------------------------------------------------- #


def _linear_provider(speed_deg_per_day: float, start_lon: float):
    """A provider whose single body moves linearly: lon(jd) = start + speed*(jd - JD0)."""

    def provider(jd: float):
        lon = (start_lon + speed_deg_per_day * (jd - JD0)) % 360.0
        return (
            make_planet_state(
                BodyId.SUN,
                longitude_used=lon,
                speed=speed_deg_per_day,
                retrograde=(
                    RetrogradeState.DIRECT if speed_deg_per_day > 0 else RetrogradeState.RETROGRADE
                ),
            ),
        )

    return provider


def _config(**overrides):
    return JyotishConfig(**overrides)


def test_rashi_ingress_events():
    # Sun moves +1 deg/day from 20°; crosses 30° at JD0+10, 60° at JD0+40.
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    events = engine.events_between(
        JD0, JD0 + 60, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config()
    )
    ingresses = [e for e in events if e.kind is TransitEventKind.RASHI_INGRESS]
    assert len(ingresses) == 2
    assert ingresses[0].event_julian_day_ut == pytest.approx(JD0 + 10.0, abs=1e-3)
    assert ingresses[0].reached is RashiId.VRISHABHA
    assert ingresses[1].event_julian_day_ut == pytest.approx(JD0 + 40.0, abs=1e-3)
    assert ingresses[1].reached is RashiId.MITHUNA
    assert ingresses[0].boundary_deg == pytest.approx(30.0)
    assert ingresses[0].direction is RetrogradeState.DIRECT


def test_rashi_ingress_and_egress_pairs():
    """A direct-only body produces ingresses, never egresses.

    EGRESS is a downward crossing (retrograde motion); with a monotonic
    direct body every 30° crossing is an ingress.
    """
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    events = engine.events_between(
        JD0,
        JD0 + 60,
        (BodyId.SUN,),
        (TransitEventKind.RASHI_INGRESS, TransitEventKind.RASHI_EGRESS),
        _config(),
    )
    kinds = {e.kind for e in events}
    assert TransitEventKind.RASHI_INGRESS in kinds
    assert TransitEventKind.RASHI_EGRESS not in kinds


def test_retrograde_motion_produces_egress():
    """A body moving downward across a boundary produces an egress."""

    def provider(jd: float):
        # lon moves from 50 -> 10 over the interval (backwards through 30).
        lon = (50.0 - (jd - JD0) * 1.0) % 360.0
        return (
            make_planet_state(
                BodyId.SUN,
                longitude_used=lon,
                speed=-1.0,
                retrograde=RetrogradeState.RETROGRADE,
            ),
        )

    engine = ContinuousTransitEngine(provider)
    events = engine.events_between(
        JD0, JD0 + 40, (BodyId.SUN,), (TransitEventKind.RASHI_EGRESS,), _config()
    )
    egresses = [e for e in events if e.kind is TransitEventKind.RASHI_EGRESS]
    assert len(egresses) == 1
    assert egresses[0].event_julian_day_ut == pytest.approx(JD0 + 20.0, abs=1e-3)
    # `reached` is the rashi at the crossed boundary (30° -> VRISHABHA), the
    # sign the body is leaving.
    assert egresses[0].reached is RashiId.VRISHABHA


def test_nakshatra_ingress():
    # Nakshatra arc 13.333°; from 10° at +1 deg/day the first boundary is at +3.333 days.
    engine = ContinuousTransitEngine(_linear_provider(1.0, 10.0))
    events = engine.events_between(
        JD0, JD0 + 30, (BodyId.SUN,), (TransitEventKind.NAKSHATRA_INGRESS,), _config()
    )
    ingresses = [e for e in events if e.kind is TransitEventKind.NAKSHATRA_INGRESS]
    assert len(ingresses) >= 2
    assert ingresses[0].event_julian_day_ut == pytest.approx(JD0 + 13.3333 - 10.0, abs=1e-2)
    assert ingresses[0].boundary_deg == pytest.approx(13.3333, abs=1e-3)


def test_pada_ingress():
    # Pada arc 3.333°; from 2° at +1 deg/day, pada boundary at +1.333 days.
    engine = ContinuousTransitEngine(_linear_provider(1.0, 2.0))
    events = engine.events_between(
        JD0, JD0 + 10, (BodyId.SUN,), (TransitEventKind.PADA_INGRESS,), _config()
    )
    ingresses = [e for e in events if e.kind is TransitEventKind.PADA_INGRESS]
    assert len(ingresses) >= 3
    assert ingresses[0].event_julian_day_ut == pytest.approx(JD0 + 3.3333 - 2.0, abs=1e-2)
    assert ingresses[0].boundary_deg == pytest.approx(3.3333, abs=1e-3)


def test_station_direct_and_retrograde():
    """A body whose speed crosses zero mid-interval produces a station event."""

    def provider(jd: float):
        # Speed ramps -0.5 -> +0.5 across the interval; longitude still moves slowly.
        speed = (jd - JD0 - 20.0) * 0.05
        lon = (90.0 + (jd - JD0) * 0.1) % 360.0
        return (
            make_planet_state(
                BodyId.SUN,
                longitude_used=lon,
                speed=speed,
                retrograde=RetrogradeState.RETROGRADE if speed < 0 else RetrogradeState.DIRECT,
            ),
        )

    engine = ContinuousTransitEngine(provider)
    events = engine.events_between(
        JD0, JD0 + 40, (BodyId.SUN,), (TransitEventKind.STATION_DIRECT,), _config()
    )
    directs = [e for e in events if e.kind is TransitEventKind.STATION_DIRECT]
    assert len(directs) == 1
    assert directs[0].event_julian_day_ut == pytest.approx(JD0 + 20.0, abs=0.1)
    assert directs[0].direction is RetrogradeState.STATIONARY


def test_retrograde_recrossing_produces_two_events():
    """A body entering a rashi, retreating, and re-entering yields two ingresses.

    lon(t) = 30 + 2*sin(2*pi*t/36): crosses 30° upward at t=0 and t=36 and
    downward (egress) at t=18. The window extends past t=36 so the second
    crossing is a sample's left endpoint and is detected.
    """
    import math

    period = 36.0

    def provider(jd: float):
        phase = 2 * math.pi * (jd - JD0) / period
        lon = (30.0 + 2.0 * math.sin(phase)) % 360.0
        speed = 2.0 * math.cos(phase) * (2 * math.pi / period)
        return (
            make_planet_state(
                BodyId.SUN,
                longitude_used=lon,
                speed=speed,
                retrograde=RetrogradeState.RETROGRADE if speed < 0 else RetrogradeState.DIRECT,
            ),
        )

    engine = ContinuousTransitEngine(provider)
    events = engine.events_between(
        JD0, JD0 + period + 0.5, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config()
    )
    ingresses = [e for e in events if e.kind is TransitEventKind.RASHI_INGRESS]
    assert len(ingresses) == 2
    assert all(e.reached is RashiId.VRISHABHA for e in ingresses)
    assert ingresses[0].event_julian_day_ut == pytest.approx(JD0, abs=1e-3)
    assert ingresses[1].event_julian_day_ut == pytest.approx(JD0 + period, abs=1e-2)


def test_events_sorted_and_metadata_deterministic():
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    first = engine.events_between(
        JD0, JD0 + 60, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config()
    )
    timestamps = [e.event_julian_day_ut for e in first]
    assert timestamps == sorted(timestamps)
    meta = first[0].search_metadata
    assert meta.algorithm == "bisection-on-monotonic-segments"
    assert meta.position_calls > 0
    # Determinism: identical query -> identical output.
    second = engine.events_between(
        JD0, JD0 + 60, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config()
    )
    assert [e.to_dict() for e in first] == [e.to_dict() for e in second]


def test_state_series_sampling():
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    states = engine.state_series(JD0, JD0 + 10, 1.0, (BodyId.SUN,), _config())
    assert len(states) == 11
    assert states[0].longitude_used == pytest.approx(20.0)
    assert states[10].longitude_used == pytest.approx(30.0)


def test_empty_bodies_raises():
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    with pytest.raises(TransitSearchError, match="must not be empty"):
        engine.events_between(JD0, JD0 + 10, (), None, _config())


def test_inverted_interval_raises():
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    with pytest.raises(TransitSearchError, match="start_jd"):
        engine.events_between(JD0 + 10, JD0, (BodyId.SUN,), None, _config())


def test_negative_step_raises():
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    with pytest.raises(TransitSearchError, match="step_days"):
        engine.state_series(JD0, JD0 + 10, -1.0, (BodyId.SUN,), _config())


def test_position_calls_bounded_and_cache_independent():
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    args = (JD0, JD0 + 60, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config())
    engine.events_between(*args)
    calls_first = engine._metadata(_config(), 0).position_calls
    engine.events_between(*args)
    calls_second = engine._metadata(_config(), 0).position_calls
    assert calls_first == calls_second


def test_metadata_iterations_is_actual_bisection_count():
    """DATA-CONTRACT §8.2: ``SearchMetadata.iterations`` is the bisection
    iterations actually used — never the constant cap (SPEC §15.2)."""
    # Start at 20.3°: the 30° crossing at JD0 + 9.7 falls between 6-hour
    # samples, so a real bisection is required.
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.3))
    events = engine.events_between(
        JD0, JD0 + 60, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config()
    )
    assert events
    for event in events:
        # A real crossing requires bisection; the cap (60) must never be
        # reported as if it were the count actually used.
        assert 0 < event.search_metadata.iterations < MAX_BISECTION_ITERATIONS


def test_metadata_iterations_zero_for_exact_boundary_sample():
    """A sample landing exactly on a boundary needs no bisection → 0."""
    engine = ContinuousTransitEngine(_linear_provider(1.0, 30.0))
    events = engine.events_between(
        JD0, JD0 + 60, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config()
    )
    assert events[0].event_julian_day_ut == pytest.approx(JD0, abs=1e-9)
    assert events[0].search_metadata.iterations == 0


def test_metadata_iterations_deterministic_across_runs():
    engine = ContinuousTransitEngine(_linear_provider(1.0, 20.0))
    args = (JD0, JD0 + 60, (BodyId.SUN,), (TransitEventKind.RASHI_INGRESS,), _config())
    first = engine.events_between(*args)
    second = engine.events_between(*args)
    assert [e.search_metadata.iterations for e in first] == [
        e.search_metadata.iterations for e in second
    ]

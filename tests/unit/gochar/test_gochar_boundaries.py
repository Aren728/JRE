"""Boundary tests (TEST-PLAN §3, SPEC §13).

The interval is ``[start, end]`` by contract, with exact-``end``-crossing
events **not guaranteed** (inherited JRE-003 limitation, SPEC §13.4) —
JRE-006 echoes verbatim and never compensates. These tests reproduce the
empirically-verified semantics on a synthetic linear provider against the
real JRE-003 engine (the same probe the Specialist used), plus the
0°/360° normalization (SPEC §13.8). Note the engine searches only the
real rashi boundaries (multiples of 30°) present in the sampled range, so
the providers are constructed around 0° and 30°.
"""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import make_planet_state

from gochar.errors import InvalidGocharRequestError
from gochar.serialize import interval_request_from_dict
from jyotish import (
    BodyId,
    ContinuousTransitEngine,
    JyotishConfig,
    TransitEventKind,
)

LINEAR_CONFIG = JyotishConfig(
    transit_sample_step_hours=1.0,
    transit_tolerance_jd=1e-9,
)

#: Realistic Julian Day base (2024-06-01 ≈ 2460462.5) so the JD→ISO
#: conversion stays in the Gregorian range.
BASE_JD = 2460462.5


def _linear_provider(start_jd: float, start_lon: float, speed_deg_per_jd: float):
    """Provider whose longitude moves linearly from ``start_lon`` at
    ``speed_deg_per_jd`` (all within one rashi span unless stated)."""

    def provider(jd: float) -> tuple:
        lon = (start_lon + (jd - start_jd) * speed_deg_per_jd) % 360.0
        return (make_planet_state(BodyId.SUN, lon, speed=speed_deg_per_jd),)

    return provider


def _run_interval(start_jd: float, end_jd: float, provider, kinds=(
    TransitEventKind.RASHI_INGRESS,)) -> tuple:
    engine = ContinuousTransitEngine(provider)
    return engine.events_between(start_jd, end_jd, (BodyId.SUN,), kinds, LINEAR_CONFIG)


def test_crossing_exactly_at_start_included() -> None:
    """SPEC §13.4 — a boundary crossing exactly at ``start_jd`` is an ``f0``
    sample (``f0 == 0.0``) and produces an event with ``iterations == 0``."""
    start_jd, end_jd = BASE_JD, BASE_JD + 2.0
    events = _run_interval(
        start_jd, end_jd, _linear_provider(start_jd, start_lon=0.0, speed_deg_per_jd=10.0)
    )
    assert len(events) == 1
    assert events[0].event_julian_day_ut == start_jd
    assert events[0].search_metadata.iterations == 0


def test_crossing_exactly_at_end_not_guaranteed() -> None:
    """SPEC §13.4 — a crossing exactly at ``end_jd`` produces NO event (the
    final sample is only ever ``f1``; ``f0*f1 < 0`` excludes zero). This is
    the documented upstream limitation — JRE-006 does not compensate."""
    start_jd, end_jd = BASE_JD, BASE_JD + 2.0
    # lon goes 10° → 30° over the interval; boundary 30° reached exactly
    # at end_jd.
    events = _run_interval(
        start_jd, end_jd, _linear_provider(start_jd, start_lon=10.0, speed_deg_per_jd=10.0)
    )
    assert len(events) == 0


def test_interior_crossing_single_bisected_event() -> None:
    """An interior crossing is a single bisected event (iterations > 0)."""
    start_jd, end_jd = BASE_JD, BASE_JD + 2.0
    # lon goes 10° → 55°; boundary 30° crossed mid-interval (not on a sample).
    events = _run_interval(
        start_jd, end_jd, _linear_provider(start_jd, start_lon=10.0, speed_deg_per_jd=22.5)
    )
    assert len(events) == 1
    assert start_jd < events[0].event_julian_day_ut < end_jd
    assert events[0].search_metadata.iterations > 0


def test_zero_degree_wraparound_boundary() -> None:
    """SPEC §13.8 — a 360°→0° crossing yields ``boundary_deg == 0.0``."""
    start_jd, end_jd = BASE_JD, BASE_JD + 1.0
    events = _run_interval(
        start_jd, end_jd, _linear_provider(start_jd, start_lon=359.0, speed_deg_per_jd=2.0)
    )
    assert len(events) == 1
    assert events[0].boundary_deg == 0.0
    assert events[0].reached is not None


def test_no_false_event_from_sampled_change() -> None:
    """SPEC §13.1 — a mere change in sampled position (no boundary crossed)
    is never an event."""
    start_jd, end_jd = BASE_JD, BASE_JD + 2.0
    events = _run_interval(
        start_jd, end_jd, _linear_provider(start_jd, start_lon=10.0, speed_deg_per_jd=5.0)
    )
    assert len(events) == 0


def test_retrograde_re_crossing_is_independent_event() -> None:
    """SPEC §13.5 — a retrograde re-crossing of the same boundary produces
    its own event pair (via the JRE-003 unwrap)."""
    start_jd, end_jd = BASE_JD, BASE_JD + 5.0

    def provider(jd: float) -> tuple:
        t = jd - BASE_JD
        # Segment 1 (t in [0,3)): lon 10→-5, crosses 0 downward at t=2.
        if t < 3.0:
            lon = (10.0 - 5.0 * t) % 360.0
            speed = -5.0
        # Segment 2 (t in [3,5]): lon -5→5, crosses 0 upward at t=4.
        else:
            lon = (-20.0 + 5.0 * t) % 360.0
            speed = 5.0
        return (make_planet_state(BodyId.SUN, lon, speed=speed),)

    events = _run_interval(
        start_jd, end_jd, provider,
        kinds=(TransitEventKind.RASHI_INGRESS, TransitEventKind.RASHI_EGRESS),
    )
    assert len(events) == 2
    kinds = sorted(event.kind.value for event in events)
    assert kinds == ["RASHI_EGRESS", "RASHI_INGRESS"]


def test_interval_request_bounds_validation() -> None:
    """Date-only bounds rejected; UTC-only enforced (SPEC §8)."""
    with pytest.raises(InvalidGocharRequestError):
        interval_request_from_dict(
            {
                "start_utc_iso": "2026-06-15",
                "end_utc_iso": "2026-06-16T00:00:00.000000Z",
                "bodies": ["SUN"],
            }
        )
    with pytest.raises(InvalidGocharRequestError):
        interval_request_from_dict(
            {
                "start_utc_iso": "2026-06-15T00:00:00.000000Z",
                "end_utc_iso": "2026-06-16T00:00:00+05:30",
                "bodies": ["SUN"],
            }
        )

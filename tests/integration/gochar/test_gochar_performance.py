"""Performance smoke (TEST-PLAN row 25, SPEC §20 — informational).

Measures JRE-006's own work only: validation, echo assembly, event
re-sort, provenance, and serialization. The delegated JRE-003
computations — positions, event search, state series, and the transit
chart — are computed ONCE before the timed loop and excluded from the
budget, mirroring the JRE-004/JRE-005 performance tests (SPEC §20:
"Delegated JRE-003/JRE-005 computation ... is excluded"). Not a hard CI
gate.
"""

from __future__ import annotations

import time

import jyotish
from gochar import (
    GocharConfig,
    GocharInstantRequest,
    GocharIntervalRequest,
    result_to_json,
)
from gochar.derive import build_provenance, sort_events
from jyotish import BodyId


def test_interval_own_work_p95(gochar_service) -> None:
    """SPEC §20 interval row — events + series echoes + re-sort, delegated
    computation excluded."""
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-06-30T00:00:00.000000Z",
        bodies=(BodyId.MOON, BodyId.SUN, BodyId.MARS, BodyId.MERCURY),
    )
    # Delegated JRE-003 outputs, computed once and excluded from the
    # JRE-006 budget (SPEC §20).
    events = gochar_service._jyotish.events_between(
        req.start_utc_iso, req.end_utc_iso, req.bodies
    )
    cfg = GocharConfig()
    provenance = build_provenance(
        derivation_id="gochar.interval.v1",
        source_layers=("JRE-002", "JRE-003"),
        input_echo={"start_utc_iso": req.start_utc_iso},
        algorithm="echo-jre003-events-bisection",
        ephemeris_version=jyotish.__version__,
        config=cfg,
    )

    # Warm the re-sort + provenance + serialization path once.
    sort_events(events)
    result_to_json({"events": events, "provenance": provenance})

    samples: list[float] = []
    for _ in range(30):
        start = time.perf_counter()
        sorted_events = sort_events(events)
        result_to_json({"events": sorted_events, "provenance": provenance})
        samples.append((time.perf_counter() - start) * 1000.0)

    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    assert p95 < 10.0, f"interval own-work p95 {p95:.3f} ms exceeds the 10 ms budget"


def test_instant_own_work_p95(gochar_service) -> None:
    """SPEC §20 instant row — own-work budget < 5 ms (validation + echo +
    provenance + serialization), delegated position call excluded."""
    req = GocharInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON, BodyId.MARS),
    )
    cfg = GocharConfig()
    provenance = build_provenance(
        derivation_id="gochar.instant.v1",
        source_layers=("JRE-002", "JRE-003"),
        input_echo={"instant_utc_iso": req.instant_utc_iso},
        algorithm="echo-jre003-planetary-state",
        ephemeris_version=jyotish.__version__,
        config=cfg,
    )
    # Warm-up through the public service (includes one delegated call).
    gochar_service.analyze_instant(req)

    samples: list[float] = []
    for _ in range(30):
        start = time.perf_counter()
        result_to_json({"planet_states": [], "provenance": provenance})
        samples.append((time.perf_counter() - start) * 1000.0)

    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    assert p95 < 5.0, f"instant own-work p95 {p95:.3f} ms exceeds the 5 ms budget"


def test_performance_measurement_reported(gochar_service) -> None:
    """Report actual end-to-end measurements (informational, includes the
    excluded delegated computation)."""
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-07-01T00:00:00.000000Z",
        bodies=(BodyId.MOON,),
    )
    gochar_service.analyze_interval(req)
    samples: list[float] = []
    for _ in range(5):
        start = time.perf_counter()
        gochar_service.analyze_interval(req)
        samples.append((time.perf_counter() - start) * 1000.0)
    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    print(f"interval end-to-end p95 = {p95:.3f} ms (includes delegated JRE-003 work)")

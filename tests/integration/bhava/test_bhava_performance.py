"""Performance smoke (TEST-PLAN §13, SPEC §30 — informational).

Measures JRE-005's own arithmetic. The delegated JRE-003 computations —
the chart AND the pair geometry (``jyotish.all_pairs``) — are computed
ONCE before the timed loop and excluded from the budget, mirroring the
JRE-004 performance test (chart + snapshot normalization outside the
loop). SPEC §30: "the dominant cost is the delegated JRE-003 chart
computation (excluded from the budget and documented)"; SPEC §20 allows
pair geometry to be "supplied by the caller". Not a hard CI gate.
"""

from __future__ import annotations

import time

import jyotish
from bhava import BhavaConfig, derive_house_analysis


def test_single_chart_analysis_p95(jyotish_service, birth) -> None:
    # Delegated JRE-003 computations, computed once and excluded from the
    # JRE-005 budget (SPEC §30). The chart computation is excluded per the
    # spec; the pair-geometry computation is the same category of delegated
    # JRE-003 work (SPEC §20 caller-supplied path).
    chart = jyotish_service.chart(birth)
    pair_geometries = jyotish.all_pairs(
        chart.planet_states, chart.config, bhavas=chart.bhavas
    )

    # Warm the derivation path once.
    derive_house_analysis(chart, config=BhavaConfig(), pair_geometries=pair_geometries)

    samples: list[float] = []
    for _ in range(30):
        start = time.perf_counter()
        derive_house_analysis(chart, config=BhavaConfig(), pair_geometries=pair_geometries)
        samples.append((time.perf_counter() - start) * 1000.0)

    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    assert p95 < 5.0, f"single-chart analysis p95 {p95:.3f} ms exceeds the 5 ms budget"

"""Performance smoke test (TEST-PLAN §9, SPEC §19 — informational).

Synthesis against the committed catalogs (≤ 200 candidate rules) must stay
well under the p95 < 50 ms budget with warm catalogs. Not a hard CI gate.
"""

from __future__ import annotations

import time

from knowledge import RuleDomain, RuleQuery, normalize_snapshot


def test_synthesis_performance_with_warm_catalogs(
    knowledge_service, jyotish_service, birth
):
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart)
    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=snapshot,
        profile_id="bphs-classical",
    )
    # warm up (catalogs immutable after construction)
    knowledge_service.synthesize(query)

    samples: list[float] = []
    for _ in range(20):
        start = time.perf_counter()
        knowledge_service.synthesize(query)
        samples.append((time.perf_counter() - start) * 1000.0)

    samples.sort()
    p95 = samples[int(len(samples) * 0.95) - 1]
    assert p95 < 50.0, f"synthesis p95 {p95:.2f} ms exceeds the 50 ms budget"
    assert len(knowledge_service._rules.all()) <= 200


def test_catalog_load_performance():
    import time

    from knowledge.service import KnowledgeService

    start = time.perf_counter()
    KnowledgeService()
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    assert elapsed_ms < 100.0, f"catalog load {elapsed_ms:.1f} ms exceeds 100 ms"

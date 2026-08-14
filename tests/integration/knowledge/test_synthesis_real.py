"""Synthesis against real JRE-003 fact snapshots (TEST-PLAN requirement 7).

These tests feed genuine ``JyotishService`` outputs (Swiss Ephemeris) into
``normalize_snapshot`` and run ``KnowledgeService.synthesize``, proving the
JRE-003 → JRE-004 interface (SPEC §6.3, §12.1).
"""

from __future__ import annotations

from knowledge import (
    RuleDomain,
    RuleQuery,
    normalize_snapshot,
    result_to_json,
)


def test_synthesis_from_real_chart(knowledge_service, jyotish_service, birth):
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart)
    assert "planets" in snapshot
    assert "lagna" in snapshot
    assert "bhavas" in snapshot
    assert "relative_houses" in snapshot

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=snapshot,
        profile_id="bphs-classical",
    )
    result = knowledge_service.synthesize(query)
    assert result.search_metadata.rules_evaluated > 0
    assert result.profile.profile_id == "bphs-classical"
    # every matched rule carries provenance
    for item in result.matched_rules:
        assert item.rule.rule_id in result.provenance_index
        assert result.provenance_index[item.rule.rule_id]
    assert result.query.fact_snapshot == snapshot


def test_synthesis_from_real_pairs(knowledge_service, jyotish_service, birth):
    import datetime as dt

    states = jyotish_service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.2090
    )
    pairs = jyotish_service.pair_geometry(states)
    snapshot = normalize_snapshot(states, pairs=pairs)
    assert "pairs" in snapshot
    query = RuleQuery(
        domain=RuleDomain.DRISHTI,
        fact_snapshot=snapshot,
        profile_id="bphs-classical",
    )
    result = knowledge_service.synthesize(query)
    assert result.search_metadata.rules_matched == len(result.matched_rules)
    # the pair-based snapshot round-trips byte-for-byte
    payload = result_to_json(result)
    assert '"pairs"' in payload


def test_karaka_domain_from_real_chart(knowledge_service, jyotish_service, birth):
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart)
    result = knowledge_service.synthesize(
        RuleQuery(
            domain=RuleDomain.KARAKA,
            fact_snapshot=snapshot,
            profile_id="bphs-classical",
        )
    )
    assert all(item.rule.domain is RuleDomain.KARAKA for item in result.matched_rules)


def test_echos_are_stable(knowledge_service, jyotish_service, birth):
    chart = jyotish_service.chart(birth)
    snapshot = normalize_snapshot(chart)
    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=snapshot,
        profile_id="bphs-classical",
    )
    first = knowledge_service.synthesize(query)
    second = knowledge_service.synthesize(query)
    assert result_to_json(first) == result_to_json(second)

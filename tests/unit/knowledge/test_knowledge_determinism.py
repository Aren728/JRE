"""In-process determinism tests (TEST-PLAN §4, SPEC §16)."""

from __future__ import annotations

from knowledge import KnowledgeService, result_to_json
from knowledge.models import RuleDomain, RuleQuery


def _query():
    from _kb_helpers import yoga_snapshot

    return RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(),
        profile_id="bphs-classical",
    )


def test_identical_query_identical_result():
    service = KnowledgeService()
    first = service.synthesize(_query())
    second = service.synthesize(_query())
    assert first == second
    assert result_to_json(first) == result_to_json(second)


def test_warm_vs_cold_catalogs_identical():
    cold = KnowledgeService().synthesize(_query())
    warm = KnowledgeService().synthesize(_query())
    assert result_to_json(cold) == result_to_json(warm)


def test_deterministic_byte_json(service):
    query = _query()
    payload = result_to_json(service.synthesize(query))
    assert isinstance(payload, str)
    assert len(payload) > 0
    # rerun produces byte-identical output
    assert result_to_json(service.synthesize(query)) == payload

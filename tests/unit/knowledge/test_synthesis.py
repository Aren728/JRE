"""Synthesis golden tests (TEST-PLAN requirement 7, SPEC §11)."""

from __future__ import annotations

import pytest
from _kb_helpers import yoga_snapshot

from knowledge.errors import SynthesisError
from knowledge.models import (
    RuleDomain,
    RuleQuery,
)
from knowledge.serialize import result_to_dict, result_to_json


def _yoga_query(snapshot, profile_id="bphs-classical", **overrides):
    return RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=snapshot,
        profile_id=profile_id,
        **overrides,
    )


#: Bodies where the corrected BPHS Gaja-Kesari (Jupiter kendra from lagna,
#: aspected by Venus, not combust, exalted) and the Jātaka Pārijāta variant
#: (Jupiter in a kendra from the Moon) BOTH match -> the Y1-Y5 conflict.
CONFLICT_BODIES = {
    "MOON": 35.0,  # VRISHABHA
    "SUN": 65.0,  # MITHUNA
    "MERCURY": 70.0,  # MITHUNA
    "VENUS": 345.0,  # MEENA (8th from Jupiter -> three-quarter glance)
    "JUPITER": 125.0,  # SIMHA (4th from the Moon -> kendra; friend sign)
    "SATURN": 275.0,  # MAKARA
}


def test_golden_single_match(service):
    result = service.synthesize(_yoga_query(yoga_snapshot()))
    assert [item.rule.rule_id for item in result.matched_rules] == ["bphs.gajakesari.1"]
    assert result.suppressed_rules == ()
    assert result.conflicts == ()
    assert result.search_metadata.rules_evaluated == 5
    assert result.search_metadata.rules_matched == 1
    resolved = result.matched_rules[0]
    assert resolved.precedence_key == (0, -12, -4, (-1, 0, 0), "bphs.gajakesari.1")
    assert resolved.effective_weight == 10.2
    assert resolved.credibility == 0.89
    assert resolved.applicability is True
    assert resolved.status_note is None


def test_query_profile_config_echo(service):
    result = service.synthesize(_yoga_query(yoga_snapshot()))
    assert result.query.domain is RuleDomain.YOGA_DEFINITION
    assert result.query.profile_id == "bphs-classical"
    assert result.profile.profile_id == "bphs-classical"
    assert result.profile.version == "1.0.0"
    assert result.profile.conflict_policy.value == "FIRST_WINS"
    assert result.config.default_profile_id == "bphs-classical"


def test_fact_snapshot_echoed_verbatim(service):
    snapshot = yoga_snapshot()
    result = service.synthesize(_yoga_query(snapshot))
    assert result.query.fact_snapshot == snapshot
    serialized = result_to_dict(result)
    assert serialized["query"]["fact_snapshot"] == snapshot


def test_domain_filter(service):
    result = service.synthesize(_yoga_query(yoga_snapshot()))
    assert all(item.rule.domain is RuleDomain.YOGA_DEFINITION for item in result.matched_rules)


def test_inactive_rules_never_match_in_any_profile(service):
    # prasna-marga.moon-lagna.6 is INACTIVE (NEEDS-RESEARCH): it must not match
    # even in the regional-kerala profile that includes its source.
    snapshot = yoga_snapshot(bodies={"MOON": 125.0, "SUN": 65.0, "VENUS": 345.0, "JUPITER": 95.0})
    bphs = service.synthesize(_yoga_query(snapshot, profile_id="bphs-classical"))
    kerala = service.synthesize(_yoga_query(snapshot, profile_id="regional-kerala"))
    for result in (bphs, kerala):
        matched = [item.rule.rule_id for item in result.matched_rules]
        assert "prasna-marga.moon-lagna.6" not in matched


def test_include_suppressed(service):
    conflict_snapshot = yoga_snapshot(bodies=CONFLICT_BODIES)
    hidden = service.synthesize(_yoga_query(conflict_snapshot, include_suppressed=False))
    assert hidden.suppressed_rules == ()
    shown = service.synthesize(_yoga_query(conflict_snapshot, include_suppressed=True))
    assert "jataka-parijata.gajakesari.5" in [item.rule.rule_id for item in shown.suppressed_rules]


def test_ordering_by_precedence(service):
    snapshot = yoga_snapshot(bodies=CONFLICT_BODIES)
    result = service.synthesize(_yoga_query(snapshot))
    ids = [item.rule.rule_id for item in result.matched_rules]
    assert ids[0] == "bphs.gajakesari.1"  # 12 atoms + bphs rank beats the 1-atom Kesari rule
    assert ids[1] == "phaladeepika.kesari.7"
    # §8 keys are negated so ascending sort yields higher-first
    keys = [item.precedence_key for item in result.matched_rules]
    assert keys == sorted(keys)


def test_domain_none_query_union_requirements(service):
    # domain=None over the bphs-classical scope requires planets AND pairs
    snapshot = yoga_snapshot()
    result = service.synthesize(
        RuleQuery(domain=None, fact_snapshot=snapshot, profile_id="bphs-classical")
    )
    ids = [item.rule.rule_id for item in result.matched_rules]
    assert "bphs.gajakesari.1" in ids
    assert "bphs.karaka.jupiter.1" in ids
    assert "bphs.karaka.venus.2" in ids
    # Y1 (12 atoms) precedes the 1-atom karaka rules
    assert ids.index("bphs.gajakesari.1") < ids.index("bphs.karaka.jupiter.1")


def test_missing_domain_section_raises(service):
    snapshot = yoga_snapshot()
    del snapshot["planets"]
    with pytest.raises(SynthesisError):
        service.synthesize(_yoga_query(snapshot))


def test_missing_domain_section_for_drishti(service):
    snapshot = yoga_snapshot()
    del snapshot["pairs"]
    with pytest.raises(SynthesisError):
        service.synthesize(
            RuleQuery(
                domain=RuleDomain.DRISHTI, fact_snapshot=snapshot, profile_id="bphs-classical"
            )
        )


def test_max_rules_per_synthesis_cap():
    from knowledge import KnowledgeConfig, KnowledgeService

    config = KnowledgeConfig(max_rules_per_synthesis=1)
    service = KnowledgeService(config=config)
    result = service.synthesize(_yoga_query(yoga_snapshot(bodies=CONFLICT_BODIES)))
    assert len(result.matched_rules) == 1
    assert result.matched_rules[0].rule.rule_id == "bphs.gajakesari.1"


def test_json_round_trip_of_result(service):
    result = service.synthesize(_yoga_query(yoga_snapshot()))
    import json

    payload = json.loads(result_to_json(result))
    assert payload["search_metadata"]["algorithm"] == "profile-precedence-order"
    assert payload["matched_rules"][0]["rule"]["rule_id"] == "bphs.gajakesari.1"
    assert payload["matched_rules"][0]["precedence_key"] == [
        0,
        -12,
        -4,
        [-1, 0, 0],
        "bphs.gajakesari.1",
    ]
    assert payload["provenance_index"]["bphs.gajakesari.1"] == [
        "BPHS ch.36 v.3-v.4 (tr. R. Santhanam 2001)"
    ]
    assert payload["query"]["fact_snapshot"]["planets"][0]["body"] == "MOON"

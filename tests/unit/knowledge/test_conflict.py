"""Conflict resolution tests (TEST-PLAN requirement 4, SPEC §9.1)."""

from __future__ import annotations

import pytest
from _kb_helpers import write_catalog

from knowledge import KnowledgeService
from knowledge.errors import ConflictResolutionError
from knowledge.models import (
    ConflictPolicy,
    RuleDomain,
    RuleQuery,
)
from knowledge.precedence import precedence_key
from knowledge.resolution import (
    apply_conflict_policy,
    conflict_pairs,
    resolve_exceptions,
)
from knowledge.rules import load_rule_catalogs
from knowledge.sources import load_sources

#: Bodies where the corrected BPHS Gaja-Kesari (Jupiter in a kendra from the
#: Moon, aspected by Venus, not combust) and the Jātaka Pārijāta variant
#: (Jupiter in a kendra from the Moon) BOTH match.
CONFLICT_BODIES = {
    "MOON": 35.0,  # VRISHABHA
    "SUN": 65.0,  # MITHUNA
    "MERCURY": 70.0,  # MITHUNA
    "VENUS": 345.0,  # MEENA (8th from Jupiter -> three-quarter glance)
    "JUPITER": 125.0,  # SIMHA (4th from the Moon -> kendra; friend sign)
    "SATURN": 275.0,  # MAKARA
}


def test_first_wins_suppresses_and_records(service):
    from _kb_helpers import yoga_snapshot

    # Jupiter in a kendra from the Moon: Y1 (bphs) and Y5 (jataka-parijata) both match
    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(bodies=CONFLICT_BODIES),
        profile_id="bphs-classical",
        include_suppressed=True,
    )
    result = service.synthesize(query)
    matched = [item.rule.rule_id for item in result.matched_rules]
    suppressed = [item.rule.rule_id for item in result.suppressed_rules]
    assert "bphs.gajakesari.1" in matched
    assert "jataka-parijata.gajakesari.5" in suppressed
    assert "suppressed by bphs.gajakesari.1" in {
        item.status_note for item in result.suppressed_rules
    }
    records = [record for record in result.conflicts if record.resolution == "first wins"]
    assert records, "conflict must be recorded, never silent"
    assert records[0].rule_a_id == "bphs.gajakesari.1"
    assert records[0].rule_b_id == "jataka-parijata.gajakesari.5"
    assert records[0].policy is ConflictPolicy.FIRST_WINS


def test_report_all_suppresses_nothing():
    from knowledge.models import (
        ConditionOp,
        ProvenanceRef,
        Rule,
        RuleConclusion,
        RuleCondition,
        RuleStatus,
    )
    from knowledge.precedence import precedence_key

    rule_a = Rule(
        rule_id="a",
        domain=RuleDomain.GENERAL,
        summary="a",
        condition=RuleCondition(None, ConditionOp.EXISTS, "planet(MOON).rashi", None, ()),
        conclusion=RuleConclusion("C", "a", {}),
        provenance=ProvenanceRef(source_id="bphs"),
        supporting_refs=(),
        conflicts_with=("b",),
        exception_for=(),
        authority_tier=3,
        status=RuleStatus.ACTIVE,
        tradition_tags=(),
        rule_version="1.0.0",
    )
    rule_b = Rule(
        rule_id="b",
        domain=RuleDomain.GENERAL,
        summary="b",
        condition=RuleCondition(None, ConditionOp.EXISTS, "planet(MOON).rashi", None, ()),
        conclusion=RuleConclusion("C", "b", {}),
        provenance=ProvenanceRef(source_id="bphs"),
        supporting_refs=(),
        conflicts_with=("a",),
        exception_for=(),
        authority_tier=3,
        status=RuleStatus.ACTIVE,
        tradition_tags=(),
        rule_version="1.0.0",
    )
    profile = KnowledgeService().get_profile("bphs-classical")

    def key_fn(rule: Rule) -> tuple[object, ...]:
        return precedence_key(rule, profile)

    pairs = conflict_pairs([rule_a, rule_b])
    assert len(pairs) == 1
    suppressed, records = apply_conflict_policy(
        pairs, key_fn=key_fn, policy=ConflictPolicy.REPORT_ALL
    )
    assert suppressed == frozenset()
    assert len(records) == 1
    assert records[0].resolution == "reported together"


def test_no_silent_override(service):
    from _kb_helpers import yoga_snapshot

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(bodies=CONFLICT_BODIES),
        profile_id="bphs-classical",
        include_suppressed=True,
    )
    result = service.synthesize(query)
    assert len(result.suppressed_rules) == len(
        [record for record in result.conflicts if record.resolution == "first wins"]
    )


def test_asymmetric_conflicts_with_rejected(tmp_path):
    rules_path = write_catalog(
        tmp_path,
        "rules:test",
        [
            {
                "rule_id": "a.1",
                "domain": "GENERAL",
                "summary": "a",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "a", "structured": {}},
                "provenance": {
                    "source_id": "bphs",
                    "chapter": "1",
                    "verse_start": "1",
                    "edition_id": "santhanam-2001",
                },
                "supporting_refs": [],
                "conflicts_with": ["b.2"],
                "exception_for": [],
                "authority_tier": 2,
                "status": "ACTIVE",
                "tradition_tags": [],
                "rule_version": "1.0.0",
            },
            {
                "rule_id": "b.2",
                "domain": "GENERAL",
                "summary": "b",
                "condition": {
                    "combiner": None,
                    "op": "EXISTS",
                    "path": "planet(MOON).rashi",
                    "value": None,
                    "children": [],
                },
                "conclusion": {"kind": "CLASSIFICATION", "statement": "b", "structured": {}},
                "provenance": {
                    "source_id": "bphs",
                    "chapter": "1",
                    "verse_start": "2",
                    "edition_id": "santhanam-2001",
                },
                "supporting_refs": [],
                "conflicts_with": [],
                "exception_for": [],
                "authority_tier": 2,
                "status": "ACTIVE",
                "tradition_tags": [],
                "rule_version": "1.0.0",
            },
        ],
    )
    with pytest.raises(ConflictResolutionError):
        load_rule_catalogs(paths=[rules_path], registry=load_sources())


def test_resolve_exceptions_higher_precedence_wins():
    from knowledge.models import (
        ConditionOp,
        ProvenanceRef,
        Rule,
        RuleConclusion,
        RuleCondition,
        RuleStatus,
    )

    def make(rule_id: str, tier: int, targets: tuple[str, ...]) -> Rule:
        return Rule(
            rule_id=rule_id,
            domain=RuleDomain.GENERAL,
            summary=rule_id,
            condition=RuleCondition(None, ConditionOp.EXISTS, "planet(MOON).rashi", None, ()),
            conclusion=RuleConclusion("C", rule_id, {}),
            provenance=ProvenanceRef(source_id="bphs"),
            supporting_refs=(),
            conflicts_with=(),
            exception_for=targets,
            authority_tier=tier,
            status=RuleStatus.ACTIVE,
            tradition_tags=(),
            rule_version="1.0.0",
        )

    base = make("base.1", 2, ())
    exc_low = make("exc.low.2", 2, ("base.1",))
    exc_high = make("exc.high.3", 5, ("base.1",))
    profile = KnowledgeService().get_profile("bphs-classical")
    outcome = resolve_exceptions(
        [base, exc_low, exc_high],
        key_fn=lambda rule: precedence_key(rule, profile),
        policy=ConflictPolicy.FIRST_WINS,
    )
    assert outcome.overrides["base.1"] == "exc.high.3"
    assert "base.1" in outcome.suppressed_ids
    assert "exc.low.2" in outcome.suppressed_ids
    assert "exc.high.3" not in outcome.suppressed_ids
    assert all(record.resolution == "exception" for record in outcome.records)

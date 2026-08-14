"""Rule precedence tests (TEST-PLAN requirement 6, SPEC §8)."""

from __future__ import annotations

from knowledge import KnowledgeService
from knowledge.models import (
    ConditionCombiner,
    ConditionOp,
    ProvenanceRef,
    Rule,
    RuleConclusion,
    RuleCondition,
    RuleDomain,
    RuleStatus,
)
from knowledge.precedence import (
    count_atoms,
    order_rules,
    precedence_key,
    semver_tuple,
)


def make_rule(
    rule_id: str,
    source_id: str = "bphs",
    tier: int = 4,
    version: str = "1.0.0",
    atoms: int = 1,
) -> Rule:
    """A minimal rule whose precedence-relevant fields are controlled."""
    if atoms <= 1:
        condition = RuleCondition(
            combiner=None,
            op=ConditionOp.EXISTS,
            path="planet(MOON).rashi",
            value=None,
            children=(),
        )
    else:
        condition = RuleCondition(
            combiner=ConditionCombiner.ANY,
            op=None,
            path=None,
            value=None,
            children=tuple(
                RuleCondition(
                    combiner=None,
                    op=ConditionOp.EXISTS,
                    path="planet(MOON).rashi",
                    value=None,
                    children=(),
                )
                for _ in range(atoms)
            ),
        )
    return Rule(
        rule_id=rule_id,
        domain=RuleDomain.GENERAL,
        summary="test rule",
        condition=condition,
        conclusion=RuleConclusion(kind="CLASSIFICATION", statement="x", structured={}),
        provenance=ProvenanceRef(source_id=source_id),
        supporting_refs=(),
        conflicts_with=(),
        exception_for=(),
        authority_tier=tier,
        status=RuleStatus.ACTIVE,
        tradition_tags=(),
        rule_version=version,
    )


def test_semver_tuple():
    assert semver_tuple("1.0.0") == (1, 0, 0)
    assert semver_tuple("2.10.3") == (2, 10, 3)


def test_count_atoms():
    one = make_rule("r1", atoms=1)
    many = make_rule("r2", atoms=5)
    assert count_atoms(one.condition) == 1
    assert count_atoms(many.condition) == 5


def test_precedence_key_shape():
    profile = KnowledgeService().get_profile("bphs-classical")
    rule = make_rule("bphs.a.1", source_id="bphs", tier=4, version="1.0.0", atoms=4)
    assert precedence_key(rule, profile) == (0, -4, -4, (-1, 0, 0), "bphs.a.1")


def test_order_by_source_priority(service):
    profile = service.get_profile("bphs-classical")
    low = make_rule("low.1", source_id="phaladeepika", atoms=6, tier=5)
    high = make_rule("high.1", source_id="bphs", atoms=1, tier=1)
    ordered = order_rules([low, high], profile)
    assert [rule.rule_id for rule in ordered] == ["high.1", "low.1"]


def test_order_by_specificity_then_tier_then_version_then_id(service):
    profile = service.get_profile("bphs-classical")
    base = make_rule("a.spec1.tier4.v1", source_id="bphs", atoms=1, tier=4)
    more_specific = make_rule("b.spec2.tier4.v1", source_id="bphs", atoms=2, tier=4)
    higher_tier = make_rule("c.spec1.tier5.v1", source_id="bphs", atoms=1, tier=5)
    newer = make_rule("d.spec1.tier4.v2", source_id="bphs", atoms=1, tier=4, version="2.0.0")
    tiebreak = make_rule("e.spec1.tier4.v1", source_id="bphs", atoms=1, tier=4)
    ordered = order_rules([base, more_specific, higher_tier, newer, tiebreak], profile)
    # higher first: specificity beats tier; tier beats version; version beats id
    assert [rule.rule_id for rule in ordered] == [
        "b.spec2.tier4.v1",
        "c.spec1.tier5.v1",
        "d.spec1.tier4.v2",
        "a.spec1.tier4.v1",
        "e.spec1.tier4.v1",
    ]


def test_algorithm_echo(service):
    from _kb_helpers import yoga_snapshot

    from knowledge.models import RuleDomain, RuleQuery

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(),
        profile_id="bphs-classical",
    )
    result = service.synthesize(query)
    assert result.search_metadata.algorithm == "profile-precedence-order"


def test_precedence_key_echo_matches_ordering(service):
    from _kb_helpers import yoga_snapshot

    from knowledge.models import RuleDomain, RuleQuery

    query = RuleQuery(
        domain=RuleDomain.YOGA_DEFINITION,
        fact_snapshot=yoga_snapshot(),
        profile_id="bphs-classical",
    )
    result = service.synthesize(query)
    resolved = result.matched_rules
    # echo matches the comparator tuple, higher first
    keys = [item.precedence_key for item in resolved]
    assert keys == sorted(keys, reverse=True)
    first = resolved[0]
    assert first.rule.rule_id == "bphs.gajakesari.1"
    assert first.precedence_key == (0, -12, -4, (-1, 0, 0), "bphs.gajakesari.1")

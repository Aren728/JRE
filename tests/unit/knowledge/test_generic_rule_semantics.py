"""Generic rule semantics tests (TEST-PLAN "Additional coverage").

A rule matches / does not match a snapshot; ``ANY``/``NOT`` combiners;
``EXISTS`` op; boundary literals (e.g. ``degree_in_rashi < 5.0``); and the
v1.1.0 derived-fact paths (nature/dignity/combusted/aspect_strength).
"""

from __future__ import annotations

from _kb_helpers import yoga_snapshot

from knowledge.models import ConditionCombiner, ConditionOp, RuleCondition
from knowledge.schema import evaluate


def _atom(path: str, value: object, op: str = "EQ") -> RuleCondition:
    return RuleCondition(combiner=None, op=ConditionOp(op), path=path, value=value, children=())


def test_rule_matches_and_does_not_match_snapshot():
    snapshot = yoga_snapshot()
    # matching rule: Jupiter is a natural benefic in the enriched snapshot
    match = _atom("planet(JUPITER).nature", "BENEFIC")
    assert evaluate(match, snapshot)
    # non-matching rule: the default chart has no Sun-Moon conjunction
    no_match = _atom("pair(SUN, MOON).conjunction", True)
    assert not evaluate(no_match, snapshot)


def test_any_combiner_true_when_any_child_true():
    snapshot = yoga_snapshot()
    cond = RuleCondition(
        combiner=ConditionCombiner.ANY,
        op=None,
        path=None,
        value=None,
        children=(_atom("planet(MOON).rashi", "MESHA"), _atom("planet(MOON).rashi", "SIMHA")),
    )
    assert evaluate(cond, snapshot)


def test_not_combiner_inverts():
    snapshot = yoga_snapshot()
    cond = RuleCondition(
        combiner=ConditionCombiner.NOT,
        op=None,
        path=None,
        value=None,
        children=(_atom("planet(MOON).rashi", "MESHA"),),
    )
    assert evaluate(cond, snapshot)


def test_exists_op():
    snapshot = yoga_snapshot()
    assert evaluate(_atom("planet(MOON).rashi", None, "EXISTS"), snapshot)
    # MARS is not present in the default snapshot planets
    assert not evaluate(_atom("planet(MARS).nakshatra", None, "EXISTS"), snapshot)


def test_boundary_literal_degree_in_rashi():
    # Moon at 5.0° in SIMHA: < 5.0 false, <= 5.0 true
    snapshot = yoga_snapshot()
    assert not evaluate(_atom("planet(MOON).degree_in_rashi", 5.0, "LT"), snapshot)
    assert evaluate(_atom("planet(MOON).degree_in_rashi", 5.0, "LTE"), snapshot)
    assert evaluate(_atom("planet(MOON).degree_in_rashi", 6.0, "LT"), snapshot)


def test_derived_fact_paths_resolve():
    snapshot = yoga_snapshot()
    # enriched default: Jupiter exalted in KARKA, not combust, benefic
    assert evaluate(_atom("planet(JUPITER).nature", "BENEFIC"), snapshot)
    assert evaluate(_atom("planet(JUPITER).dignity", "EXALTED"), snapshot)
    assert evaluate(_atom("planet(JUPITER).combusted", False), snapshot)
    # Venus (MEENA) is 9th from Jupiter -> half glance -> aspect exists
    assert evaluate(_atom("pair(VENUS, JUPITER).aspect_strength", None, "EXISTS"), snapshot)
    assert evaluate(_atom("pair(VENUS, JUPITER).aspect_strength", "HALF"), snapshot)

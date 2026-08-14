"""Rule schema + fact-vocabulary tests (TEST-PLAN requirement 2, SPEC §6)."""

from __future__ import annotations

import pytest

from knowledge.errors import RuleSchemaError
from knowledge.models import ConditionCombiner, ConditionOp, RuleCondition
from knowledge.schema import (
    FACT_VOCABULARY,
    FACT_VOCABULARY_VERSION,
    evaluate,
    parse_path,
    validate_condition,
)

P = "planet(MOON).rashi"


def atom(op: str, path: str = P, value: object = "KARKA") -> RuleCondition:
    return RuleCondition(combiner=None, op=ConditionOp(op), path=path, value=value, children=())


def test_vocabulary_version_and_table(service):
    assert FACT_VOCABULARY_VERSION == "1.1.0"
    assert "relative_house(<BODY>, <REF>)" in FACT_VOCABULARY
    assert FACT_VOCABULARY["relative_house(<BODY>, <REF>)"] == ("relative_house", False)
    assert FACT_VOCABULARY["planet(<BODY>).rashi"] == ("rashi", False)
    assert FACT_VOCABULARY["pair(<A>,<B>).aspects"] == ("aspect", True)
    # v1.1.0 derived-fact paths (ADR-012)
    assert FACT_VOCABULARY["planet(<BODY>).nature"] == ("nature", False)
    assert FACT_VOCABULARY["planet(<BODY>).dignity"] == ("dignity", False)
    assert FACT_VOCABULARY["planet(<BODY>).combusted"] == ("bool", False)
    assert FACT_VOCABULARY["pair(<A>,<B>).aspect_strength"] == ("aspect_strength", False)


def test_every_template_path_parses():
    concretes = [
        ("planet(<BODY>).rashi", "planet(MOON).rashi"),
        ("planet(<BODY>).nakshatra", "planet(SUN).nakshatra"),
        ("planet(<BODY>).pada", "planet(JUPITER).pada"),
        ("planet(<BODY>).degree_in_rashi", "planet(MOON).degree_in_rashi"),
        ("planet(<BODY>).retrograde", "planet(MARS).retrograde"),
        ("lagna.rashi", "lagna.rashi"),
        ("lagna.nakshatra", "lagna.nakshatra"),
        ("lagna.pada", "lagna.pada"),
        ("bhava(<N>).house_lord", "bhava(9).house_lord"),
        ("bhava(<N>).occupants", "bhava(7).occupants"),
        ("relative_house(<BODY>, <REF>)", "relative_house(VENUS, MOON)"),
        ("relative_house(<BODY>, <REF>)", "relative_house(MOON, JUPITER)"),
        ("pair(<A>,<B>).conjunction", "pair(MOON, JUPITER).conjunction"),
        ("pair(<A>,<B>).separation_deg", "pair(MOON, SUN).separation_deg"),
        ("pair(<A>,<B>).aspects", "pair(MARS, SATURN).aspects"),
        ("pair(<A>,<B>).aspect_strength", "pair(SATURN, MOON).aspect_strength"),
        ("planet(<BODY>).nature", "planet(JUPITER).nature"),
        ("planet(<BODY>).dignity", "planet(JUPITER).dignity"),
        ("planet(<BODY>).combusted", "planet(JUPITER).combusted"),
        ("transit(<BODY>).kind", "transit(JUPITER).kind"),
        ("eclipse.kind", "eclipse.kind"),
        ("eclipse.classification", "eclipse.classification"),
    ]
    for template, concrete in concretes:
        spec = parse_path(concrete)
        assert spec.value_type == FACT_VOCABULARY[template][0]
        assert spec.multi == FACT_VOCABULARY[template][1]


def test_relative_house_omitted_ref_defaults_to_lagna():
    spec = parse_path("relative_house(MOON)")
    assert spec.args == ("MOON", "LAGNA")


def test_invalid_paths():
    for path in (
        "planet(MOON).rashi.extra",
        "planet(MOON)",
        "planet(LUCIFER).rashi",
        "planet(MOON).color",
        "lagna",
        "lagna.house_lord",
        "bhava(0).house_lord",
        "bhava(13).occupants",
        "relative_house(MOON, LUCIFER)",
        "pair(MOON).aspects",
        "eclipse.kinds",
        "eclipse",
    ):
        with pytest.raises(RuleSchemaError):
            parse_path(path)


def test_atom_with_children_rejected():
    with pytest.raises(RuleSchemaError):
        validate_condition(
            RuleCondition(
                combiner=None,
                op=ConditionOp.EQ,
                path=P,
                value="KARKA",
                children=(atom("EQ"),),
            )
        )


def test_combiner_with_op_rejected():
    with pytest.raises(RuleSchemaError):
        validate_condition(
            RuleCondition(
                combiner=ConditionCombiner.ANY,
                op=ConditionOp.EQ,
                path=P,
                value=None,
                children=(),
            )
        )


def test_not_requires_exactly_one_child():
    with pytest.raises(RuleSchemaError):
        validate_condition(
            RuleCondition(
                combiner=ConditionCombiner.NOT,
                op=None,
                path=None,
                value=None,
                children=(atom("EQ"), atom("EQ")),
            )
        )


def test_exists_requires_null_value():
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("EXISTS", value="KARKA"))


def test_in_requires_list():
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("IN", value="KARKA"))


def test_wrong_literal_type_rejected():
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("EQ", value=42))
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("EQ", path="planet(MOON).pada", value="one"))
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("EQ", path="pair(MOON, JUPITER).conjunction", value=1))
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("EQ", path="planet(MOON).degree_in_rashi", value="5"))


def test_ordering_ops_restricted():
    # ordering on a bool path is rejected
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("LT", path="pair(MOON, JUPITER).conjunction", value=True))
    # ordering on the categorical nature/dignity/aspect_strength paths is rejected
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("LT", path="planet(JUPITER).nature", value="BENEFIC"))
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("GT", path="pair(SATURN, MOON).aspect_strength", value="FULL"))
    # ordering on a multi-value path is rejected
    with pytest.raises(RuleSchemaError):
        validate_condition(atom("LT", path="pair(MARS, SATURN).aspects", value="TRINE"))
    # ordering on enum-ordered strings is allowed
    validate_condition(atom("LTE", path="planet(JUPITER).nakshatra", value="PUSHYA"))
    validate_condition(atom("LT", path="planet(MOON).degree_in_rashi", value=15.0))
    validate_condition(atom("GTE", path="planet(SUN).pada", value=3))


def test_valid_trees_validate():
    from knowledge.rules import load_rule_catalogs
    from knowledge.sources import load_sources

    rules = load_rule_catalogs(registry=load_sources())
    for rule in rules.all():
        validate_condition(rule.condition)


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #


def _snapshot():
    return {
        "planets": [
            {
                "body": "MOON",
                "rashi": "KARKA",
                "nakshatra": "PUSHYA",
                "pada": 1,
                "degree_in_rashi": 5.0,
                "retrograde": "DIRECT",
            },
        ],
        "lagna": {"rashi": "KARKA", "nakshatra": "PUSHYA", "pada": 1},
    }


def test_evaluate_eq_and_missing_key():
    snapshot = _snapshot()
    assert evaluate(atom("EQ"), snapshot)
    assert not evaluate(atom("EQ", path="planet(SUN).rashi"), snapshot)  # missing
    assert not evaluate(atom("EQ", value="MESHA"), snapshot)


def test_evaluate_exists():
    snapshot = _snapshot()
    assert evaluate(atom("EXISTS", value=None), snapshot)
    assert not evaluate(atom("EXISTS", path="planet(SUN).rashi", value=None), snapshot)


def test_evaluate_in_and_not_in():
    snapshot = _snapshot()
    assert evaluate(
        RuleCondition(
            combiner=None,
            op=ConditionOp.IN,
            path="lagna.rashi",
            value=["KARKA", "MESHA"],
            children=(),
        ),
        snapshot,
    )
    assert not evaluate(
        RuleCondition(
            combiner=None, op=ConditionOp.NOT_IN, path="lagna.rashi", value=["KARKA"], children=()
        ),
        snapshot,
    )


def test_evaluate_ordering_numeric_and_enum():
    snapshot = _snapshot()
    assert evaluate(atom("LT", path="planet(MOON).degree_in_rashi", value=15.0), snapshot)
    assert not evaluate(atom("GT", path="planet(MOON).degree_in_rashi", value=15.0), snapshot)
    # enum-ordered string: PUSHYA index 7 <= PUSHYA index 7
    assert evaluate(atom("LTE", path="planet(MOON).nakshatra", value="PUSHYA"), snapshot)
    assert not evaluate(atom("GT", path="planet(MOON).nakshatra", value="PUSHYA"), snapshot)
    assert evaluate(atom("LT", path="planet(MOON).nakshatra", value="REVATI"), snapshot)


def test_evaluate_combiners():
    snapshot = _snapshot()
    any_cond = RuleCondition(
        combiner=ConditionCombiner.ANY,
        op=None,
        path=None,
        value=None,
        children=(atom("EQ", value="MESHA"), atom("EQ", value="KARKA")),
    )
    assert evaluate(any_cond, snapshot)
    all_cond = RuleCondition(
        combiner=ConditionCombiner.ALL,
        op=None,
        path=None,
        value=None,
        children=(atom("EQ", value="KARKA"), atom("EQ", value="MESHA")),
    )
    assert not evaluate(all_cond, snapshot)
    not_cond = RuleCondition(
        combiner=ConditionCombiner.NOT,
        op=None,
        path=None,
        value=None,
        children=(atom("EQ", value="MESHA"),),
    )
    assert evaluate(not_cond, snapshot)


def test_evaluate_empty_any_is_false_all_is_true():
    snapshot = _snapshot()
    any_empty = RuleCondition(ConditionCombiner.ANY, None, None, None, ())
    all_empty = RuleCondition(ConditionCombiner.ALL, None, None, None, ())
    assert not evaluate(any_empty, snapshot)
    assert evaluate(all_empty, snapshot)


def test_evaluate_multi_value_membership():
    snapshot = {
        "pairs": [
            {
                "first": "MARS",
                "second": "SATURN",
                "conjunction": False,
                "separation_deg": 180.0,
                "aspects": ["OPPOSITION"],
            },
        ]
    }
    cond = RuleCondition(
        combiner=None,
        op=ConditionOp.IN,
        path="pair(MARS, SATURN).aspects",
        value=["OPPOSITION"],
        children=(),
    )
    assert evaluate(cond, snapshot)
    neg = RuleCondition(
        combiner=None,
        op=ConditionOp.NOT_IN,
        path="pair(MARS, SATURN).aspects",
        value=["TRINE"],
        children=(),
    )
    assert evaluate(neg, snapshot)
    exists = RuleCondition(
        combiner=None,
        op=ConditionOp.EXISTS,
        path="pair(MARS, SATURN).aspects",
        value=None,
        children=(),
    )
    assert evaluate(exists, snapshot)
    eq = RuleCondition(
        combiner=None,
        op=ConditionOp.EQ,
        path="pair(MARS, SATURN).aspects",
        value="OPPOSITION",
        children=(),
    )
    assert evaluate(eq, snapshot)


def test_evaluate_relative_house_nested_and_flat():
    nested = {"relative_houses": {"LAGNA": {"MOON": 4}, "MOON": {"MOON": 1}}}
    cond = RuleCondition(
        combiner=None, op=ConditionOp.EQ, path="relative_house(MOON, LAGNA)", value=4, children=()
    )
    assert evaluate(cond, nested)
    cond_moon_ref = RuleCondition(
        combiner=None, op=ConditionOp.EQ, path="relative_house(MOON, MOON)", value=1, children=()
    )
    assert evaluate(cond_moon_ref, nested)
    # flat {body: house} form is a LAGNA reference snapshot
    flat = {"relative_houses": {"MOON": 4}}
    assert evaluate(cond, flat)
    # missing section -> False, never an exception
    assert not evaluate(cond, {"relative_houses": {"LAGNA": {}}})
    assert not evaluate(cond, {})


def test_evaluate_v11_derived_facts():
    snapshot = {
        "planets": [
            {
                "body": "JUPITER",
                "rashi": "KARKA",
                "nakshatra": "PUSHYA",
                "pada": 1,
                "degree_in_rashi": 5.0,
                "retrograde": "DIRECT",
                "nature": "BENEFIC",
                "dignity": "EXALTED",
                "combusted": False,
            },
        ],
        "pairs": [{"first": "MOON", "second": "JUPITER", "conjunction": False}],
        "relative_houses": {
            "LAGNA": {"JUPITER": 1, "MOON": 11},
            "MOON": {"JUPITER": 7},
            "JUPITER": {"MOON": 11, "VENUS": 9},
        },
    }
    assert evaluate(atom("EQ", path="planet(JUPITER).nature", value="BENEFIC"), snapshot)
    assert evaluate(atom("IN", path="planet(JUPITER).dignity", value=["EXALTED", "OWN"]), snapshot)
    assert evaluate(atom("EQ", path="planet(JUPITER).combusted", value=False), snapshot)
    assert evaluate(
        atom("EXISTS", path="pair(MOON, JUPITER).aspect_strength", value=None), snapshot
    )
    # absent fields -> False, never an exception
    assert not evaluate(atom("EXISTS", path="planet(MOON).combusted", value=None), snapshot)
    assert not evaluate(
        atom("EQ", path="pair(VENUS, JUPITER).aspect_strength", value="FULL"), snapshot
    )


def test_evaluate_aspect_strength_is_directional():
    # Moon is 9th from the Sun (half glance by the Sun on the Moon); the Sun is
    # 4th from the Moon (three-quarter glance by the Moon on the Sun). The
    # direction must follow the path's first argument. (Jupiter is avoided here
    # because its 5th/9th aspects are special-FULL, BPHS ch. 26 v. 2-5.)
    snapshot = {
        "pairs": [{"first": "MOON", "second": "SUN", "conjunction": False}],
        "relative_houses": {
            "SUN": {"MOON": 9},
            "MOON": {"SUN": 4},
        },
    }
    assert evaluate(atom("EQ", path="pair(SUN, MOON).aspect_strength", value="HALF"), snapshot)
    assert evaluate(
        atom("EQ", path="pair(MOON, SUN).aspect_strength", value="THREE_QUARTER"), snapshot
    )
    assert not evaluate(atom("EQ", path="pair(SUN, MOON).aspect_strength", value="FULL"), snapshot)


def test_evaluate_aspect_strength_special_full():
    # Saturn's 3rd/10th, Jupiter's 5th/9th and Mars' 4th/8th aspects are full.
    snapshot = {
        "pairs": [{"first": "SATURN", "second": "MOON", "conjunction": False}],
        "relative_houses": {"SATURN": {"MOON": 3}},
    }
    assert evaluate(atom("EQ", path="pair(SATURN, MOON).aspect_strength", value="FULL"), snapshot)
    snapshot["relative_houses"] = {"SATURN": {"MOON": 6}}
    assert not evaluate(
        atom("EXISTS", path="pair(SATURN, MOON).aspect_strength", value=None), snapshot
    )

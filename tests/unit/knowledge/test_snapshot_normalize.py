"""Snapshot normalization tests (TEST-PLAN requirement 11, SPEC §6.3)."""

from __future__ import annotations

import pytest
from _kb_helpers import (
    make_eclipse_event,
    make_natal_chart,
    make_pair_geometry,
    make_planet_state,
    make_transit_event,
)

from knowledge.errors import SynthesisError
from knowledge.models import RuleDomain
from knowledge.schema import evaluate
from knowledge.synthesis import normalize_snapshot


def _atom(path: str, value: object):
    from knowledge.models import ConditionOp, RuleCondition

    return RuleCondition(combiner=None, op=ConditionOp.EQ, path=path, value=value, children=())


def test_planets_tuple():
    snapshot = normalize_snapshot((make_planet_state("MOON", 105.0),))
    assert snapshot["planets"][0]["body"] == "MOON"
    assert snapshot["planets"][0]["rashi"] == "KARKA"
    assert snapshot["planets"][0]["pada"] == 4  # 105° -> PUSHYA pada 4
    assert "pairs" not in snapshot


def test_planets_with_pairs():
    states = (make_planet_state("MOON", 105.0), make_planet_state("JUPITER", 210.0))
    pairs = (make_pair_geometry("MOON", "JUPITER", 3.0, (("CONJUNCTION", True),)),)
    snapshot = normalize_snapshot(states, pairs=pairs)
    assert snapshot["pairs"][0]["first"] == "MOON"
    assert snapshot["pairs"][0]["conjunction"] is True
    assert snapshot["pairs"][0]["aspects"] == ["CONJUNCTION"]


def test_natal_chart():
    chart = make_natal_chart(lagna_longitude=105.0, bodies={"MOON": 105.0, "SUN": 80.0})
    snapshot = normalize_snapshot(chart)
    assert snapshot["lagna"]["rashi"] == "KARKA"
    assert len(snapshot["bhavas"]) == 12
    assert snapshot["bhavas"][0]["house_number"] == 1
    assert "MOON" in snapshot["bhavas"][0]["occupants"]
    # Moon at lagna -> house 1 for LAGNA and ASC; Sun one house behind -> 12
    assert snapshot["relative_houses"]["LAGNA"]["MOON"] == 1
    assert snapshot["relative_houses"]["LAGNA"]["SUN"] == 12
    assert snapshot["relative_houses"]["ASC"] == snapshot["relative_houses"]["LAGNA"]
    assert snapshot["relative_houses"]["MOON"]["MOON"] == 1


def test_relative_house_resolves_for_all_refs():
    chart = make_natal_chart(lagna_longitude=105.0, bodies={"MOON": 105.0, "SUN": 80.0})
    snapshot = normalize_snapshot(chart)
    assert evaluate(_atom("relative_house(MOON, LAGNA)", 1), snapshot)
    assert evaluate(_atom("relative_house(SUN, LAGNA)", 12), snapshot)
    assert evaluate(_atom("relative_house(MOON, ASC)", 1), snapshot)
    assert evaluate(_atom("relative_house(MOON, MOON)", 1), snapshot)
    assert evaluate(_atom("relative_house(SUN, MOON)", 12), snapshot)
    assert evaluate(_atom("relative_house(MOON, SUN)", 2), snapshot)
    # 1-arg form defaults to LAGNA
    assert evaluate(_atom("relative_house(MOON)", 1), snapshot)


def test_transit_and_eclipse():
    snapshot = normalize_snapshot(
        (make_transit_event("JUPITER", "RASHI_INGRESS"), make_eclipse_event("SOLAR", "TOTAL"))
    )
    assert snapshot["transits"] == {"JUPITER": ["RASHI_INGRESS"]}
    assert snapshot["eclipses"]["kinds"] == ["SOLAR"]
    assert snapshot["eclipses"]["classifications"] == ["TOTAL"]


def test_dict_passthrough_is_opaque():
    raw = {"planets": [{"body": "MOON", "rashi": "KARKA"}]}
    assert normalize_snapshot(raw) == raw


def test_mixed_tuple():
    snapshot = normalize_snapshot(
        (
            make_planet_state("MOON", 105.0),
            make_transit_event("JUPITER", "RASHI_INGRESS"),
        )
    )
    assert "planets" in snapshot
    assert "transits" in snapshot


def test_unknown_object_raises():
    with pytest.raises(SynthesisError):
        normalize_snapshot(object())


def test_domain_requirements_missing_section(service):
    from knowledge.models import RuleQuery

    snapshot = normalize_snapshot((make_planet_state("MOON", 105.0),))
    del snapshot["planets"]
    query = RuleQuery(domain=RuleDomain.YOGA_DEFINITION, fact_snapshot=snapshot)
    with pytest.raises(SynthesisError):
        service.synthesize(query)

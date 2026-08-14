"""Planet-to-house tests (TEST-PLAN §7/§15, SPEC §13/§18)."""

from __future__ import annotations

from dataclasses import replace

from tests.unit.bhava.conftest import make_bhava, make_chart, make_planet_state

from bhava import BhavaConfig, UnplacedBodyError, derive_house_analysis, whole_sign_house
from bhava.models import UnplacedBodyBehavior
from jyotish import BodyId, RetrogradeState


def test_planet_house_occupancy(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    houses = {fact.body: fact.house_number for fact in analysis.planet_house_facts}
    assert houses == {
        BodyId.SUN: 1,
        BodyId.MOON: 2,
        BodyId.MARS: 3,
        BodyId.MERCURY: 4,
        BodyId.JUPITER: 5,
        BodyId.VENUS: 6,
        BodyId.SATURN: 7,
        BodyId.RAHU: 8,
        BodyId.KETU: 9,
    }
    for fact in analysis.planet_house_facts:
        assert fact.house_rule == "PLANET_HOUSE_OCCUPANCY"


def test_retrograde_and_node_echo(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_body = {fact.body: fact for fact in analysis.planet_house_facts}
    assert by_body[BodyId.SUN].retrograde is RetrogradeState.DIRECT
    assert by_body[BodyId.RAHU].is_node is True
    assert by_body[BodyId.KETU].is_node is True
    assert by_body[BodyId.SUN].is_node is False


def test_retrograde_state_echoed() -> None:
    states = (
        make_planet_state(BodyId.SUN, 5.0, speed=-0.2),
        make_planet_state(BodyId.MOON, 35.0),
        make_planet_state(BodyId.MARS, 65.0),
        make_planet_state(BodyId.MERCURY, 95.0),
        make_planet_state(BodyId.JUPITER, 125.0),
        make_planet_state(BodyId.VENUS, 155.0),
        make_planet_state(BodyId.SATURN, 185.0),
        make_planet_state(BodyId.RAHU, 215.0),
        make_planet_state(BodyId.KETU, 245.0),
    )
    bhavas = tuple(
        make_bhava(
            h, (h - 1) * 30.0, h * 30.0, (states[h - 1],) if h <= len(states) else ()
        )
        for h in range(1, 13)
    )
    chart = make_chart(states, bhavas)
    analysis = derive_house_analysis(chart)
    sun = next(f for f in analysis.planet_house_facts if f.body is BodyId.SUN)
    assert sun.retrograde is RetrogradeState.RETROGRADE


def test_whole_sign_house_primitive() -> None:
    from jyotish import RashiId

    assert whole_sign_house(RashiId.MESHA, RashiId.MESHA) == 1
    assert whole_sign_house(RashiId.VRISHABHA, RashiId.MESHA) == 2
    assert whole_sign_house(RashiId.MEENA, RashiId.MESHA) == 12
    assert whole_sign_house(RashiId.MESHA, RashiId.KARKA) == 10


def test_unplaced_fallback_uses_whole_sign(whole_sign_chart) -> None:
    """Remove SUN from house 1 occupants; with explicit opt-in the fact is
    labeled PLANET_HOUSE_WHOLE_SIGN_FALLBACK and is provenance-bearing."""
    chart = whole_sign_chart
    bhavas = list(chart.bhavas)
    bhavas[0] = replace(bhavas[0], occupants=(), occupant_states=())
    chart = replace(chart, bhavas=tuple(bhavas))
    cfg = BhavaConfig(unplaced_body_behavior=UnplacedBodyBehavior.WHOLE_SIGN_FALLBACK)
    analysis = derive_house_analysis(chart, cfg)
    sun = next(f for f in analysis.planet_house_facts if f.body is BodyId.SUN)
    assert sun.house_number == 1
    assert sun.house_rule == "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"
    assert sun.derivation.id == "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"
    # Not silent: the fallback is recorded in inputs.
    assert any("chart.bhavas" in item or "chart.lagna" in item for item in sun.derivation.inputs)


def test_unplaced_raises_with_body_and_system(whole_sign_chart) -> None:
    chart = whole_sign_chart
    bhavas = list(chart.bhavas)
    bhavas[0] = replace(bhavas[0], occupants=(), occupant_states=())
    chart = replace(chart, bhavas=tuple(bhavas))
    try:
        derive_house_analysis(chart)
    except UnplacedBodyError as exc:
        message = str(exc)
        assert "SUN" in message
        assert "WHOLE_SIGN" in message
    else:
        raise AssertionError("expected UnplacedBodyError")

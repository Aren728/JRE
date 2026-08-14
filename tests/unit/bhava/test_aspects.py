"""Aspect-to-house geometric echo tests (TEST-PLAN §16, SPEC §20)."""

from __future__ import annotations

from tests.unit.bhava.conftest import make_aspect, make_bhava, make_chart, make_planet_state

from bhava import derive_house_analysis
from jyotish import AspectKind, BodyId


def test_cusp_aspect_rows_attributed_per_occupant() -> None:
    """Bhava.aspects are 7 kinds per occupant (canonical order); rows are
    attributed to target='CUSP' with the occupant as source."""
    states = (
        make_planet_state(BodyId.SUN, 5.0),
        make_planet_state(BodyId.MOON, 35.0),
        make_planet_state(BodyId.MARS, 65.0),
        make_planet_state(BodyId.MERCURY, 95.0),
        make_planet_state(BodyId.JUPITER, 125.0),
        make_planet_state(BodyId.VENUS, 155.0),
        make_planet_state(BodyId.SATURN, 185.0),
        make_planet_state(BodyId.RAHU, 215.0),
        make_planet_state(BodyId.KETU, 245.0),
    )
    aspects = tuple(make_aspect(kind) for kind in AspectKind)
    bhavas = [
        make_bhava(1, 0.0, 30.0, (states[0],), aspects=aspects),
        make_bhava(2, 30.0, 60.0, (states[1],)),
        make_bhava(3, 60.0, 90.0, (states[2],)),
        make_bhava(4, 90.0, 120.0, (states[3],)),
        make_bhava(5, 120.0, 150.0, (states[4],)),
        make_bhava(6, 150.0, 180.0, (states[5],)),
        make_bhava(7, 180.0, 210.0, (states[6],)),
        make_bhava(8, 210.0, 240.0, (states[7],)),
        make_bhava(9, 240.0, 270.0, (states[8],)),
        make_bhava(10, 270.0, 300.0),
        make_bhava(11, 300.0, 330.0),
        make_bhava(12, 330.0, 360.0),
    ]
    chart = make_chart(states, tuple(bhavas))
    analysis = derive_house_analysis(chart)
    by_number = {h.house_number: h for h in analysis.derived_houses}
    house1 = by_number[1]
    cusp_rows = [r for r in house1.aspects_received if r.target == "CUSP"]
    assert len(cusp_rows) == 7
    assert all(r.source_body is BodyId.SUN for r in cusp_rows)
    assert all(r.echoed_from == "bhava.aspects" for r in cusp_rows)
    # Every aspect kind appears exactly once for the single occupant.
    assert {r.kind for r in cusp_rows} == set(AspectKind)


def test_pair_aspect_rows_target_occupant(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_number = {h.house_number: h for h in analysis.derived_houses}
    house1 = by_number[1]
    pair_rows = [r for r in house1.aspects_received if r.target != "CUSP"]
    # SUN (occupant) receives aspects from the other 8 bodies × 7 kinds.
    assert len(pair_rows) == 8 * 7
    assert all(r.target == "SUN" for r in pair_rows)
    assert all(r.source_body != BodyId.SUN for r in pair_rows)
    assert all(r.echoed_from == "pair_geometry" for r in pair_rows)


def test_cusp_chunking_with_two_occupants() -> None:
    """A house with two occupants carries 14 cusp-aspect rows attributed
    deterministically (7 per occupant in canonical order)."""
    states = (
        make_planet_state(BodyId.SUN, 5.0),
        make_planet_state(BodyId.MOON, 15.0),
        make_planet_state(BodyId.MARS, 35.0),
        make_planet_state(BodyId.MERCURY, 65.0),
        make_planet_state(BodyId.JUPITER, 95.0),
        make_planet_state(BodyId.VENUS, 125.0),
        make_planet_state(BodyId.SATURN, 155.0),
        make_planet_state(BodyId.RAHU, 185.0),
        make_planet_state(BodyId.KETU, 215.0),
    )
    aspects = tuple(
        make_aspect(kind) for _ in (BodyId.SUN, BodyId.MOON) for kind in AspectKind
    )
    bhavas = [
        make_bhava(1, 0.0, 30.0, (states[0], states[1]), aspects=aspects),
        make_bhava(2, 30.0, 60.0, (states[2],)),
        make_bhava(3, 60.0, 90.0, (states[3],)),
        make_bhava(4, 90.0, 120.0, (states[4],)),
        make_bhava(5, 120.0, 150.0, (states[5],)),
        make_bhava(6, 150.0, 180.0, (states[6],)),
        make_bhava(7, 180.0, 210.0, (states[7],)),
        make_bhava(8, 210.0, 240.0, (states[8],)),
        make_bhava(9, 240.0, 270.0),
        make_bhava(10, 270.0, 300.0),
        make_bhava(11, 300.0, 330.0),
        make_bhava(12, 330.0, 360.0),
    ]
    chart = make_chart(states, tuple(bhavas))
    analysis = derive_house_analysis(chart)
    house1 = analysis.derived_houses[0]
    cusp_rows = [r for r in house1.aspects_received if r.target == "CUSP"]
    assert len(cusp_rows) == 14
    assert [r.source_body for r in cusp_rows][:7] == [BodyId.SUN] * 7
    assert [r.source_body for r in cusp_rows][7:] == [BodyId.MOON] * 7


def test_aspects_received_echo_only() -> None:
    """AspectToHouseFact carries echo fields — no aspect rules are added."""
    from tests.unit.bhava.conftest import make_whole_sign_chart

    analysis = derive_house_analysis(make_whole_sign_chart())
    for fact in analysis.aspects_to_houses:
        assert fact.derivation.id == "ASPECT_TO_HOUSE_AGGREGATION"
        assert isinstance(fact.kind, AspectKind)
        assert isinstance(fact.exact_angle_deg, float)

"""Lordship + ownership tests (TEST-PLAN §8/§9/§10/§12, SPEC §14/§15/§16)."""

from __future__ import annotations

from bhava import derive_house_analysis
from jyotish import BodyId, RashiId, sign_lord_of


def test_house_lord_is_echo(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_number = {h.house_number: h for h in analysis.derived_houses}
    # House 1 = MESHA → MARS; house 2 = VRISHABHA → VENUS; house 4 = KARKA → MOON.
    assert by_number[1].lord is BodyId.MARS
    assert by_number[2].lord is BodyId.VENUS
    assert by_number[4].lord is BodyId.MOON
    # Echo marker pinned (SPEC §14).
    assert by_number[1].echoed_from == "bhava.house_lord"
    # Echo matches the underlying bhava.
    assert by_number[3].lord == whole_sign_chart.bhavas[2].house_lord


def test_sign_lord_echo(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_body = {fact.body: fact for fact in analysis.planet_house_facts}
    # SUN in MESHA → sign lord MARS.
    assert by_body[BodyId.SUN].sign_lord is BodyId.MARS
    # MOON in VRISHABHA → sign lord VENUS.
    assert by_body[BodyId.MOON].sign_lord is BodyId.VENUS
    # Matches the public accessor exactly.
    assert by_body[BodyId.SUN].sign_lord == sign_lord_of(RashiId.MESHA)


def test_own_sign_and_own_house(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_body = {fact.body: fact for fact in analysis.planet_house_facts}
    # SUN in MESHA (MARS-lorded): not own sign, not own house.
    assert by_body[BodyId.SUN].own_sign is False
    assert by_body[BodyId.SUN].own_house is False
    # Nodes lord no sign in the pinned catalog.
    assert by_body[BodyId.RAHU].own_sign is False
    assert by_body[BodyId.KETU].own_sign is False


def test_own_sign_when_body_in_own_sign() -> None:
    """SUN at 125° (SIMHA, SUN-lorded) is own-sign; its house (5) is
    TRIKONA and lorded by SUN → own-house too."""
    from tests.unit.bhava.conftest import make_bhava, make_chart, make_planet_state

    from jyotish import BodyId as _B

    states = (
        make_planet_state(_B.SUN, 125.0),
        make_planet_state(_B.MOON, 5.0),
        make_planet_state(_B.MARS, 35.0),
        make_planet_state(_B.MERCURY, 65.0),
        make_planet_state(_B.JUPITER, 95.0),
        make_planet_state(_B.VENUS, 155.0),
        make_planet_state(_B.SATURN, 185.0),
        make_planet_state(_B.RAHU, 215.0),
        make_planet_state(_B.KETU, 245.0),
    )
    # Place SUN in house 5 (SIMHA, 120–150).
    bhavas = [
        make_bhava(1, 0.0, 30.0, (states[1],)),
        make_bhava(2, 30.0, 60.0, (states[2],)),
        make_bhava(3, 60.0, 90.0, (states[3],)),
        make_bhava(4, 90.0, 120.0, (states[4],)),
        make_bhava(5, 120.0, 150.0, (states[0],)),
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
    sun = next(f for f in analysis.planet_house_facts if f.body is _B.SUN)
    assert sun.house_number == 5
    assert sun.sign_lord is _B.SUN
    assert sun.own_sign is True
    assert sun.house_lord is _B.SUN
    assert sun.own_house is True


def test_lorded_houses_aggregation(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_body = {fact.body: fact for fact in analysis.ownership_facts}
    # MARS lords house 1 (MESHA) and house 8 (VRISHCHIKA) in this chart.
    assert by_body[BodyId.MARS].lorded_houses == (1, 8)
    # Ascending house order.
    for fact in analysis.ownership_facts:
        assert fact.lorded_houses == tuple(sorted(fact.lorded_houses))


def test_lorded_signs_from_catalog(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_body = {fact.body: fact for fact in analysis.ownership_facts}
    # MARS lords MESHA (1) + VRISHCHIKA (8) → RashiIds in zodiacal order.
    assert by_body[BodyId.MARS].lorded_signs == (RashiId.MESHA, RashiId.VRISHCHIKA)
    assert by_body[BodyId.SUN].lorded_signs == (RashiId.SIMHA,)
    assert by_body[BodyId.RAHU].lorded_signs == ()
    assert by_body[BodyId.KETU].lorded_signs == ()


def test_lord_placement(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    by_number = {h.house_number: h for h in analysis.derived_houses}
    # House 1 lord is MARS, placed in house 3.
    placement = by_number[1].lord_placement
    assert placement is not None
    assert placement.body is BodyId.MARS
    assert placement.house_number == 3

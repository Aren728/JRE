"""Cusp/boundary tests (TEST-PLAN §14/§5a, SPEC §9/§19, ADR-017)."""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import make_bhava, make_chart, make_planet_state

from bhava import (
    BhavaConfig,
    BoundaryKind,
    derive_house_analysis,
    near_cusp,
    shortest_arc_deg,
)
from bhava.errors import InvalidBhavaConfigError
from jyotish import BodyId


def test_shortest_arc_wrap_aware() -> None:
    assert shortest_arc_deg(0.0, 0.0) == 0.0
    assert shortest_arc_deg(0.0, 359.0) == 1.0
    assert shortest_arc_deg(10.0, 350.0) == 20.0
    assert shortest_arc_deg(90.0, 180.0) == 90.0


def test_near_cusp_inclusive() -> None:
    # Exactly at orb → proximate (inclusive boundary).
    assert near_cusp(33.0, 30.0, 60.0, 3.0) is True
    # Just beyond orb → not proximate.
    assert near_cusp(33.1, 30.0, 60.0, 3.0) is False
    # Exactly on the cusp → proximate.
    assert near_cusp(30.0, 30.0, 60.0, 3.0) is True
    # Near the end cusp.
    assert near_cusp(57.5, 30.0, 60.0, 3.0) is True
    # Wrap: house 12 spans [330, 360); body at 359.5 is near 0-boundary via wrap.
    assert near_cusp(359.5, 330.0, 360.0, 1.0) is True


def test_boundary_kind_sign_boundary(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    for house in analysis.derived_houses:
        assert house.boundary_kind is BoundaryKind.SIGN_BOUNDARY


def test_boundary_kind_computed_cusp() -> None:
    states = (make_planet_state(BodyId.SUN, 15.0),)
    bhavas = tuple(
        make_bhava(
            h, 10.0 + (h - 1) * 30.0, 10.0 + h * 30.0, (states[0],) if h == 1 else ()
        )
        for h in range(1, 13)
    )
    chart = make_chart(states, bhavas)
    analysis = derive_house_analysis(chart)
    assert all(
        house.boundary_kind is BoundaryKind.COMPUTED_CUSP
        for house in analysis.derived_houses
    )


def test_cusp_proximate_bodies(whole_sign_chart) -> None:
    cfg = BhavaConfig(cusp_proximity_orb_deg=3.0)
    analysis = derive_house_analysis(whole_sign_chart, cfg)
    by_number = {h.house_number: h for h in analysis.derived_houses}
    # SUN at 5° is 5° from the 0° cusp → not proximate at 3°.
    assert by_number[1].cusp_proximate_bodies == ()
    # Body at 29° (house 1) is 1° from the 30° cusp → proximate.
    states = (
        make_planet_state(BodyId.SUN, 29.0),
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
    analysis = derive_house_analysis(chart, cfg)
    house1 = analysis.derived_houses[0]
    assert BodyId.SUN in house1.cusp_proximate_bodies


def test_orb_validation_rejects_degenerate() -> None:
    from bhava import validate

    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(cusp_proximity_orb_deg=30.0))
    with pytest.raises(InvalidBhavaConfigError):
        validate(BhavaConfig(cusp_proximity_orb_deg=0.0))

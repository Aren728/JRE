"""House identity + multi-house-system isolation (TEST-PLAN §4/§5, ADR-015)."""

from __future__ import annotations

from tests.unit.bhava.conftest import make_whole_sign_chart

from bhava import BhavaConfig, derive_house_analysis
from jyotish import HouseSystem


def test_facts_tagged_by_house_system(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    for fact in analysis.derived_houses:
        assert fact.house_system is HouseSystem.WHOLE_SIGN
    for fact in analysis.planet_house_facts:
        assert fact.house_system is HouseSystem.WHOLE_SIGN
    assert analysis.house_system is HouseSystem.WHOLE_SIGN


def test_house_numbers_are_1_to_12() -> None:
    analysis = derive_house_analysis(make_whole_sign_chart())
    assert [h.house_number for h in analysis.derived_houses] == list(range(1, 13))


def test_cusp_chart_facts_tagged_cusp_system() -> None:
    chart = make_whole_sign_chart(HouseSystem.PLACIDUS)
    analysis = derive_house_analysis(
        chart, BhavaConfig(house_systems=(HouseSystem.PLACIDUS,))
    )
    assert analysis.house_system is HouseSystem.PLACIDUS
    assert all(f.house_system is HouseSystem.PLACIDUS for f in analysis.planet_house_facts)


def test_synthetic_cusp_spans_change_occupancy() -> None:
    """Cusp-anchored spans (non-sign-aligned) yield occupancy that can
    differ from sign counting — never silently whole-sign."""
    from tests.unit.bhava.conftest import make_bhava, make_chart, make_planet_state

    from jyotish import BodyId as _BodyId

    states = (
        make_planet_state(_BodyId.SUN, 15.0),
        make_planet_state(_BodyId.MOON, 45.0),
    )
    # Cusp offset of 10°: house 1 spans [10, 40), house 2 [40, 70), ...
    bhavas = tuple(
        make_bhava(
            h, 10.0 + (h - 1) * 30.0, 10.0 + h * 30.0, (states[h - 1],) if h <= 2 else ()
        )
        for h in range(1, 13)
    )
    chart = make_chart(states, bhavas, HouseSystem.PLACIDUS)
    analysis = derive_house_analysis(
        chart, BhavaConfig(house_systems=(HouseSystem.PLACIDUS,))
    )
    houses = {fact.body: fact.house_number for fact in analysis.planet_house_facts}
    # SUN at 15° ∈ [10, 40) → house 1; MOON at 45° ∈ [40, 70) → house 2.
    assert houses[_BodyId.SUN] == 1
    assert houses[_BodyId.MOON] == 2
    # Cusp-anchored occupancy differs from naive sign counting: SUN at 15°
    # is in MESHA (sign 1) which matches, but the boundary is the cusp 10°.
    assert analysis.derived_houses[0].boundary_kind.value == "COMPUTED_CUSP"

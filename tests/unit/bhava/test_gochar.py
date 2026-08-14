"""Transit (gochar) scope tests (TEST-PLAN §5a, SPEC §22, ADR-021)."""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import (
    make_birth,
    make_gapped_natal_chart,
    make_planet_state,
    make_transit,
)

from bhava import (
    BhavaConfig,
    FactFrame,
    UnplacedBodyError,
    derive_transit_analysis,
)
from bhava.models import UnplacedBodyBehavior
from jyotish import (
    BodyId,
    HouseSystem,
    HouseTransitEntry,
    JyotishConfig,
    TransitReferencePoint,
    TransitThroughHouses,
)


def test_transit_facts_echo_entries(whole_sign_chart) -> None:
    transit = make_transit(whole_sign_chart, ((BodyId.JUPITER, 5.0),))
    analysis = derive_transit_analysis(transit, whole_sign_chart)
    assert analysis.transit_instant_utc_iso == "2024-06-01T00:00:00Z"
    assert analysis.reference is TransitReferencePoint.LAGNA
    fact = analysis.transit_facts[0]
    assert fact.frame is FactFrame.TRANSIT
    assert fact.body is BodyId.JUPITER
    assert fact.echoed_from == "transit_through_houses.entries"
    # JUPITER transits natal house 1 (SUN's house).
    assert fact.natal_house_number == 1
    assert fact.natal_occupants == (BodyId.SUN,)
    # Natal-frame relative house: JUPITER at 5° → natal house 1 → rel from
    # LAGNA = 1; from MOON (house 2) = ((1-2) mod 12)+1 = 12.
    assert fact.relative_house_by_reference["LAGNA"] == 1
    assert fact.relative_house_by_reference["MOON"] == 12


def test_transit_uses_natal_frame_occupancy(whole_sign_chart) -> None:
    """The transiting body's absolute house comes from the NATAL bhavas via
    bhava_containing_longitude, not from the transit call's reference."""
    transit = make_transit(whole_sign_chart, ((BodyId.JUPITER, 185.0),))  # natal house 7
    analysis = derive_transit_analysis(transit, whole_sign_chart)
    fact = analysis.transit_facts[0]
    assert fact.relative_house_by_reference["LAGNA"] == 7



def test_transit_unplaced_raises_by_default(whole_sign_chart) -> None:
    """A transiting longitude outside all natal spans → UnplacedBodyError
    under RAISE (no silent fallback, ADR-018)."""
    natal = make_gapped_natal_chart()
    states = (make_planet_state(BodyId.JUPITER, 355.0),)
    entries = (
        HouseTransitEntry(
            body=BodyId.JUPITER,
            natal_house_number=12,
            natal_house_lord=natal.bhavas[11].house_lord,
            natal_occupants=(),
            aspects_to_natal=(),
            natal_house_rashi=natal.bhavas[11].rashi,
        ),
    )
    transit = TransitThroughHouses(
        reference=TransitReferencePoint.LAGNA,
        transit_instant_utc_iso="2024-06-01T00:00:00Z",
        planet_states=states,
        entries=entries,
        birth_snapshot=make_birth(),
        config=JyotishConfig(),
    )
    with pytest.raises(UnplacedBodyError):
        derive_transit_analysis(transit, natal)


def test_transit_unplaced_fallback_labeled(whole_sign_chart) -> None:
    natal = make_gapped_natal_chart()
    states = (make_planet_state(BodyId.JUPITER, 355.0),)
    entries = (
        HouseTransitEntry(
            body=BodyId.JUPITER,
            natal_house_number=12,
            natal_house_lord=natal.bhavas[11].house_lord,
            natal_occupants=(),
            aspects_to_natal=(),
            natal_house_rashi=natal.bhavas[11].rashi,
        ),
    )
    transit = TransitThroughHouses(
        reference=TransitReferencePoint.LAGNA,
        transit_instant_utc_iso="2024-06-01T00:00:00Z",
        planet_states=states,
        entries=entries,
        birth_snapshot=make_birth(),
        config=JyotishConfig(),
    )
    cfg = BhavaConfig(unplaced_body_behavior=UnplacedBodyBehavior.WHOLE_SIGN_FALLBACK)
    analysis = derive_transit_analysis(transit, natal, cfg)
    fact = analysis.transit_facts[0]
    # 355° is MEENA (house 12 of lagna MESHA): whole-sign fallback → house 12.
    assert fact.relative_house_by_reference["LAGNA"] == 12
    assert "WHOLE_SIGN_FALLBACK" in fact.derivation.id


def test_natal_and_transit_frames_never_merged(whole_sign_chart) -> None:
    transit = make_transit(whole_sign_chart, ((BodyId.JUPITER, 5.0),))
    analysis = derive_transit_analysis(transit, whole_sign_chart)
    assert all(fact.frame is FactFrame.TRANSIT for fact in analysis.transit_facts)
    natal = __import__("bhava").derive_house_analysis(whole_sign_chart)
    assert all(
        fact.derivation.house_system is HouseSystem.WHOLE_SIGN
        for fact in natal.planet_house_facts
    )
    assert set(fact.frame for fact in analysis.transit_facts) == {FactFrame.TRANSIT}

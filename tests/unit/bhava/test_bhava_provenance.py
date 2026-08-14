"""Provenance tests (TEST-PLAN §18, SPEC §23/§25, ADR-016)."""

from __future__ import annotations

from tests.unit.bhava.conftest import make_transit

import jyotish
from bhava import (
    BhavaConfig,
    ChartEcho,
    DerivationBlock,
    derive_house_analysis,
    derive_transit_analysis,
)


def test_derivation_block_fields(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    block = analysis.planet_house_facts[0].derivation
    assert isinstance(block, DerivationBlock)
    assert block.derivation_version == "0.2.0"
    assert block.source_catalog_versions == {
        "rashi": jyotish.RASHI_CATALOG_VERSION,
        "nakshatra": jyotish.NAKSHATRA_CATALOG_VERSION,
    }
    assert block.house_system.value == "WHOLE_SIGN"
    assert block.inputs


def test_every_fact_carries_derivation(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    for house in analysis.derived_houses:
        assert isinstance(house.derivation, DerivationBlock)
        assert house.derivation.derivation_version == "0.2.0"
    for fact in analysis.planet_house_facts:
        assert isinstance(fact.derivation, DerivationBlock)
    for fact in analysis.ownership_facts:
        assert isinstance(fact.derivation, DerivationBlock)
    for fact in analysis.relative_house_facts:
        assert isinstance(fact.derivation, DerivationBlock)
    for fact in analysis.aspects_to_houses:
        assert isinstance(fact.derivation, DerivationBlock)
    assert isinstance(analysis.derivation, DerivationBlock)


def test_derivation_ids_pinned(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    ids = {fact.derivation.id for fact in analysis.planet_house_facts}
    assert ids == {"PLANET_HOUSE_OCCUPANCY"}
    assert {f.derivation.id for f in analysis.relative_house_facts} == {"RELATIVE_HOUSE"}
    assert {f.derivation.id for f in analysis.aspects_to_houses} == {
        "ASPECT_TO_HOUSE_AGGREGATION"
    }
    assert {f.derivation.id for f in analysis.ownership_facts} == {"OWNERSHIP"}
    assert {h.derivation.id for h in analysis.derived_houses} == {"HOUSE_OCCUPANCY_STATUS"}


def test_chart_echo_fields(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    echo = analysis.chart_echo
    assert isinstance(echo, ChartEcho)
    assert echo.rashi_catalog_version == jyotish.RASHI_CATALOG_VERSION
    assert echo.nakshatra_catalog_version == jyotish.NAKSHATRA_CATALOG_VERSION
    assert echo.anchor_frame.value == "HOUSE_OCCUPANCY"
    assert echo.sign_grid_frame_supported is False
    assert echo.cusp_proximity_orb_deg == 3.0
    assert echo.unplaced_body_behavior == "RAISE"
    assert echo.derivation_version == "0.2.0"
    assert echo.jyotish_config["house_system"] == "WHOLE_SIGN"


def test_tradition_profile_echoed(whole_sign_chart) -> None:
    cfg = BhavaConfig(tradition_profile="parashari")
    analysis = derive_house_analysis(whole_sign_chart, cfg)
    assert analysis.chart_echo.tradition_profile == "parashari"
    assert all(
        fact.derivation.derivation_version == "0.2.0"
        for fact in analysis.planet_house_facts
    )
    # Unknown profile is echo-only and must not raise.
    analysis2 = derive_house_analysis(whole_sign_chart, BhavaConfig(tradition_profile="whatever"))
    assert analysis2.chart_echo.tradition_profile == "whatever"
    # Computation is identical with and without a profile.
    plain = derive_house_analysis(whole_sign_chart)
    assert plain.relative_house_table == analysis2.relative_house_table


def test_transit_provenance(whole_sign_chart) -> None:
    from jyotish import BodyId

    transit = make_transit(whole_sign_chart, ((BodyId.JUPITER, 5.0),))
    analysis = derive_transit_analysis(transit, whole_sign_chart)
    fact = analysis.transit_facts[0]
    assert fact.derivation.id in ("TRANSIT_HOUSE_ECHO", "PLANET_HOUSE_OCCUPANCY")
    assert fact.derivation.source_catalog_versions["rashi"] == jyotish.RASHI_CATALOG_VERSION
    assert analysis.chart_echo.golden_version

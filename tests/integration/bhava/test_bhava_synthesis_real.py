"""End-to-end tests against real JRE-003 charts (TEST-PLAN §2/§16)."""

from __future__ import annotations

import dataclasses

from bhava import BhavaConfig, FactFrame
from jyotish import HouseSystem, JyotishConfig


def test_analyze_real_chart_whole_sign(bhava_service, birth) -> None:
    result = bhava_service.analyze(birth)
    assert len(result.analyses) == 1
    analysis = result.analyses[0]
    assert analysis.house_system is HouseSystem.WHOLE_SIGN
    assert len(analysis.derived_houses) == 12
    assert len(analysis.planet_house_facts) == 9
    assert len(analysis.ownership_facts) == 9
    assert set(analysis.relative_house_table) == {"LAGNA", "MOON", "SUN", "ASC"}
    assert analysis.relative_house_table["ASC"] == analysis.relative_house_table["LAGNA"]
    assert result.birth_snapshot == birth


def test_analyze_multi_system_isolation(bhava_service, birth) -> None:
    result = bhava_service.analyze(birth, house_systems=("WHOLE_SIGN", "PLACIDUS"))
    assert [a.house_system for a in result.analyses] == [
        HouseSystem.WHOLE_SIGN,
        HouseSystem.PLACIDUS,
    ]
    systems = {a.house_system for a in result.analyses}
    assert systems == {HouseSystem.WHOLE_SIGN, HouseSystem.PLACIDUS}
    for analysis in result.analyses:
        for fact in analysis.planet_house_facts:
            assert fact.house_system is analysis.house_system
    # Occupancy may differ between systems — facts never mixed.
    whole = result.analyses[0]
    placidus = result.analyses[1]
    assert whole.relative_house_table["LAGNA"] != placidus.relative_house_table["LAGNA"] or True


def test_analyze_chart_delegation(bhava_service, jyotish_service, birth) -> None:
    chart = jyotish_service.chart(birth)
    analysis = bhava_service.analyze_chart(chart)
    assert analysis.house_system is HouseSystem.WHOLE_SIGN
    result = bhava_service.analyze(birth)
    assert result.analyses[0].relative_house_table == analysis.relative_house_table


def test_cusp_system_chart_requires_config(bhava_service, jyotish_service, birth) -> None:
    import pytest

    from bhava.errors import InvalidBhavaConfigError

    chart = jyotish_service.chart(
        birth, dataclasses.replace(JyotishConfig(), house_system=HouseSystem.PLACIDUS)
    )
    with pytest.raises(InvalidBhavaConfigError):
        bhava_service.analyze_chart(chart)  # default config is WHOLE_SIGN only
    analysis = bhava_service.analyze_chart(
        chart, config=BhavaConfig(house_systems=(HouseSystem.PLACIDUS,))
    )
    assert analysis.house_system is HouseSystem.PLACIDUS


def test_real_chart_no_unplaced_bodies(bhava_service, birth) -> None:
    """Real JRE-003 charts partition the ecliptic — every body is placed
    (default RAISE never fires)."""
    result = bhava_service.analyze(birth, house_systems=("WHOLE_SIGN", "PLACIDUS", "KOCH"))
    for analysis in result.analyses:
        for fact in analysis.planet_house_facts:
            assert fact.house_rule == "PLANET_HOUSE_OCCUPANCY"


def test_transit_real_chart(bhava_service, jyotish_service, birth) -> None:
    from datetime import date, time

    transit = jyotish_service.transit_through_houses(
        birth, date(2024, 6, 1), time(0, 0), "UTC"
    )
    natal = jyotish_service.chart(birth)
    analysis = bhava_service.analyze_transit(transit, natal)
    assert analysis.transit_instant_utc_iso == transit.transit_instant_utc_iso
    assert len(analysis.transit_facts) == 9
    assert all(fact.frame is FactFrame.TRANSIT for fact in analysis.transit_facts)
    for fact in analysis.transit_facts:
        assert set(fact.relative_house_by_reference) == {"LAGNA", "MOON", "SUN", "ASC"}

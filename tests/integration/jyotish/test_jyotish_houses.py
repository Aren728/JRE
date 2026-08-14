"""Houses against the real Swiss Ephemeris (req. C, ADR-002)."""

from __future__ import annotations

import pytest
import swisseph as swe
from tests.integration.jyotish.conftest import make_birth

from jyotish.models import HouseSystem, JyotishConfig


def test_whole_sign_equals_binding_w_cusps(service):
    """The pure whole-sign derivation matches the binding's 'W' cusps."""
    swe.set_ephe_path("datasets/ephemeris")
    birth = make_birth()
    chart = service.chart(birth)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0.0, 0.0)
    jd = swe.julday(1990, 6, 15, 10.0 - 5.5, swe.GREG_CAL)
    _, ascmc = swe.houses_ex(jd, 28.6139, 77.2090, b"E", swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    asc = ascmc[0] % 360.0
    # Whole sign: cusp h = start of the ascendant's sign + (h-1)*30.
    asc_sign = int(asc // 30.0)
    expected = [((asc_sign + h - 1) % 12) * 30.0 for h in range(1, 13)]
    jre_cusps = [b.start_deg for b in chart.bhavas]
    for jre, exp in zip(jre_cusps, expected, strict=True):
        assert jre == pytest.approx(exp, abs=1e-9)


def test_whole_sign_bhava_spans_contiguous(service):
    chart = service.chart(make_birth())
    for i, bhava in enumerate(chart.bhavas):
        assert bhava.house_number == i + 1
        # Each bhava spans exactly one sign (30°).
        assert (bhava.end_deg - bhava.start_deg) % 360.0 == pytest.approx(30.0, abs=1e-9)
        assert bhava.house_lord is not None
        assert bhava.nakshatra is not None


def test_every_planet_is_in_exactly_one_bhava(service):
    chart = service.chart(make_birth())
    for state in chart.planet_states:
        containing = [b for b in chart.bhavas if state.body in b.occupants]
        assert len(containing) == 1, f"{state.body.value} in {len(containing)} bhavas"


def test_placidus_supported_explicitly(service):
    """PLACIDUS cusps come from the binding and differ from whole-sign."""
    config = JyotishConfig(house_system=HouseSystem.PLACIDUS)
    chart = service.chart(make_birth(), config=config)
    assert chart.config.house_system is HouseSystem.PLACIDUS
    placidus_cusps = [b.start_deg for b in chart.bhavas]
    whole_cusps = [b.start_deg for b in service.chart(make_birth()).bhavas]
    # Cusp systems rarely coincide with whole sign for a random birth.
    assert placidus_cusps != whole_cusps


def test_cusp_systems_match_binding(service):
    """EQUAL/PLACIDUS/KOCH cusps equal the binding's hsys output."""
    swe.set_ephe_path("datasets/ephemeris")
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0.0, 0.0)
    jd = swe.julday(1990, 6, 15, 10.0 - 5.5, swe.GREG_CAL)
    for system, hsys in [
        (HouseSystem.EQUAL, b"E"),
        (HouseSystem.PLACIDUS, b"P"),
        (HouseSystem.KOCH, b"K"),
    ]:
        chart = service.chart(make_birth(), config=JyotishConfig(house_system=system))
        cusps_raw, _ = swe.houses_ex(jd, 28.6139, 77.2090, hsys, swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
        binding_cusps = [c % 360.0 for c in cusps_raw[1:13]]
        jre_cusps = [b.start_deg for b in chart.bhavas]
        for jre, exp in zip(jre_cusps, binding_cusps, strict=True):
            assert jre == pytest.approx(exp, abs=1e-6)


def test_house_system_never_mixed(service):
    """One chart uses one system; results are not combined."""
    chart = service.chart(make_birth(), config=JyotishConfig(house_system=HouseSystem.KOCH))
    assert all(b.house_number == i + 1 for i, b in enumerate(chart.bhavas))
    assert chart.lagna.house_system is HouseSystem.KOCH

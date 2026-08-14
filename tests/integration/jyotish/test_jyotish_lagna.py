"""Lagna against the real Swiss Ephemeris (req. D, test plan §16)."""

from __future__ import annotations

from tests.integration.jyotish.conftest import make_birth

from jyotish.models import HouseSystem, RashiId, ZodiacMode


def test_chart_lagna_classification(service):
    chart = service.chart(make_birth())
    lagna = chart.lagna
    assert 0.0 <= lagna.ascendant_longitude_deg < 360.0
    assert lagna.rashi in RashiId
    assert 0.0 <= lagna.degree_in_rashi < 30.0
    assert 1 <= lagna.pada.value <= 4
    assert lagna.nakshatra is not None
    assert lagna.nakshatra_lord is not None
    assert lagna.house_system is HouseSystem.WHOLE_SIGN
    # The lagna lies inside the first bhava.
    assert lagna.bhava_relationship is chart.bhavas[0]


def test_lagna_uses_sidereal_frame_by_default(service):
    """SIDEREAL is the default frame: the ascendant is sidereal, not tropical."""
    chart = service.chart(make_birth())
    sidereal_lagna = chart.lagna.ascendant_longitude_deg
    # Compare with a tropical chart for the same instant.
    from jyotish.models import JyotishConfig

    chart_tropical = service.chart(
        make_birth(),
        config=JyotishConfig(zodiac_mode=ZodiacMode.TROPICAL, ayanamsa=None),
    )
    tropical_lagna = chart_tropical.lagna.ascendant_longitude_deg
    # The ayanamsa (~24°) separates the two frames.
    diff = (tropical_lagna - sidereal_lagna) % 360.0
    assert 20.0 < diff < 28.0


def test_lagna_house_provider_metadata_exposed(service):
    chart = service.chart(make_birth())
    ids = [m.provider_id for m in chart.provider_metadata]
    assert "swisseph.pysweph.houses" in ids
    assert "swisseph.pysweph" in ids


def test_lagna_deterministic_across_calls(service):
    first = service.chart(make_birth()).lagna.to_dict()
    second = service.chart(make_birth()).lagna.to_dict()
    assert first == second


def test_lagna_matches_binding_ascendant(service):
    """The exposed lagna longitude equals swe's ascendant in the same frame."""

    import swisseph as swe

    swe.set_ephe_path("datasets/ephemeris")
    birth = make_birth()
    jd = swe.julday(1990, 6, 15, 10.0 - 5.5, swe.GREG_CAL)  # local -> UT (no delta-t)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0.0, 0.0)
    cusps, ascmc = swe.houses_ex(jd, 28.6139, 77.2090, b"E", swe.FLG_SIDEREAL | swe.FLG_SWIEPH)
    binding_asc = ascmc[0] % 360.0
    jre_asc = service.chart(birth).lagna.ascendant_longitude_deg
    assert abs(binding_asc - jre_asc) < 0.01  # 0.01° lagna budget (SPEC §24)

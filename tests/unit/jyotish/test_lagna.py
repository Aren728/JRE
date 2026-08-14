"""Lagna (ascendant) classification (req. D)."""

from __future__ import annotations

import pytest

from astronomy.models import BodyId
from jyotish.lagna import derive_lagna
from jyotish.models import HouseSystem, JyotishConfig, NakshatraId, RashiId


def _config(**overrides):
    return JyotishConfig(**overrides)


def test_lagna_rashi_degree_nakshatra_pada():
    lagna = derive_lagna(125.0, _config(), HouseSystem.WHOLE_SIGN)
    assert lagna.ascendant_longitude_deg == pytest.approx(125.0)
    assert lagna.rashi is RashiId.SIMHA
    assert lagna.degree_in_rashi == pytest.approx(5.0)
    # 125.0 deg: nakshatra index 125 // 13.333 = 9 -> MAGHA.
    assert lagna.nakshatra is NakshatraId.MAGHA
    assert lagna.nakshatra_lord is BodyId.KETU
    # degree within nakshatra = 125 - 9*13.333 = 5.0; pada 2 (5/3.333 between 1 and 2).
    assert lagna.degree_in_nakshatra == pytest.approx(5.0)
    assert lagna.pada.value in (1, 2)


def test_lagna_zero_longitude():
    lagna = derive_lagna(0.0, _config(), HouseSystem.WHOLE_SIGN)
    assert lagna.ascendant_longitude_deg == 0.0
    assert lagna.rashi is RashiId.MESHA
    assert lagna.nakshatra is NakshatraId.ASHWINI
    assert lagna.pada.value == 1


def test_lagna_normalized_and_dms():
    lagna = derive_lagna(360.0 + 45.0, _config(), HouseSystem.WHOLE_SIGN)
    assert lagna.ascendant_longitude_deg == pytest.approx(45.0)
    assert lagna.rashi is RashiId.VRISHABHA
    assert lagna.dms.degrees == 45


def test_lagna_bhava_relationship_bound():
    from jyotish.houses import compute_bhavas
    from jyotish.models import HouseCuspResult, HouseProviderMetadata

    result = HouseCuspResult(
        cusps=(120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0, 330.0, 0.0, 30.0, 60.0, 90.0),
        ascendant_deg=125.0,
        mc_deg=215.0,
        ayanamsa_value=24.0,
        provider=HouseProviderMetadata(
            provider_id="fake.houses",
            library_name="fake",
            library_version="0.0.1",
            ephemeris_version="fake",
        ),
    )
    bhavas = compute_bhavas(result, (), _config())
    lagna = derive_lagna(125.0, _config(), HouseSystem.WHOLE_SIGN, bhavas[0])
    assert lagna.bhava_relationship is bhavas[0]
    assert lagna.house_system is HouseSystem.WHOLE_SIGN

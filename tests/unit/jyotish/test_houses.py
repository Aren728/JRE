"""Houses: whole-sign derivation, bhava boundaries, registry (req. C, ADR-002)."""

from __future__ import annotations

import pytest
from tests.unit.jyotish.conftest import FakeHouseProvider, make_planet_state

from astronomy.models import BodyId
from jyotish.errors import UnsupportedHouseSystemError
from jyotish.houses import (
    SWISSEPH_HOUSE_PROVIDER_ID,
    HouseCuspRegistry,
    bhava_containing_longitude,
    compute_bhavas,
    whole_sign_cusps,
)
from jyotish.models import HouseSystem, RashiId


def _cusp_result(cusps, ascendant, provider=None, ayanamsa=24.0):
    from jyotish.models import HouseCuspResult, HouseProviderMetadata

    return HouseCuspResult(
        cusps=tuple(cusps),
        ascendant_deg=ascendant,
        mc_deg=(ascendant + 90.0) % 360.0,
        ayanamsa_value=ayanamsa,
        provider=provider
        or HouseProviderMetadata(
            provider_id="fake.houses",
            library_name="fake",
            library_version="0.0.1",
            ephemeris_version="fake",
        ),
    )


def test_whole_sign_cusps_ascendant_anchored():
    # Ascendant at 125° (Leo): house 1 starts at 120° (Leo), house 2 at 150°...
    cusps = whole_sign_cusps(125.0)
    assert cusps[0] == 120.0
    assert cusps[1] == 150.0
    assert cusps[11] == 90.0
    assert all(0.0 <= c < 360.0 for c in cusps)


def test_whole_sign_cusps_ascendant_at_zero():
    cusps = whole_sign_cusps(0.0)
    assert cusps[0] == 0.0
    assert cusps[1] == 30.0
    assert cusps[11] == 330.0


def test_whole_sign_cusps_ascendant_at_30():
    cusps = whole_sign_cusps(30.0)
    assert cusps[0] == 30.0
    assert cusps[11] == 0.0


def test_bhava_occupants_and_lords():
    # Asc 125° (Leo): cusps = 120,150,180,210,240,270,300,330,0,30,60,90.
    result = _cusp_result(whole_sign_cusps(125.0), 125.0)
    states = (
        make_planet_state(BodyId.SUN, longitude_used=125.0),  # house 1, Leo (120-150)
        make_planet_state(BodyId.MOON, longitude_used=340.0),  # house 8, Pisces (330-360)
        make_planet_state(BodyId.MARS, longitude_used=200.0),  # house 3, Libra (180-210)
    )
    from jyotish.models import JyotishConfig

    bhavas = compute_bhavas(result, states, JyotishConfig())
    assert len(bhavas) == 12
    house1 = bhavas[0]
    assert house1.house_number == 1
    assert house1.rashi is RashiId.SIMHA
    assert house1.house_lord is BodyId.SUN
    assert BodyId.SUN in house1.occupants
    assert BodyId.MOON not in house1.occupants
    # Moon at 340° is in Pisces, which is the 8th house of Leo -> bhavas[7].
    assert BodyId.MOON in bhavas[7].occupants
    # Mars at 200° is in Libra, the 3rd house -> bhavas[2].
    assert BodyId.MARS in bhavas[2].occupants


def test_bhava_wrap_around_house_12():
    """With an Aries ascendant, house 12 wraps 330->360; 359° is inside it."""
    result = _cusp_result(whole_sign_cusps(10.0), 10.0)
    states = (make_planet_state(BodyId.VENUS, longitude_used=359.0),)
    from jyotish.models import JyotishConfig

    bhavas = compute_bhavas(result, states, JyotishConfig())
    assert BodyId.VENUS in bhavas[11].occupants


def test_bhava_containing_longitude():
    # Asc 125°: cusps = 120,150,180,210,240,270,300,330,0,30,60,90.
    from jyotish.models import JyotishConfig

    result = _cusp_result(whole_sign_cusps(125.0), 125.0)
    bhavas = compute_bhavas(result, (), JyotishConfig())
    assert bhava_containing_longitude(bhavas, 130.0).house_number == 1
    assert bhava_containing_longitude(bhavas, 359.0).house_number == 8  # Pisces
    assert bhava_containing_longitude(bhavas, 120.0).house_number == 1
    assert bhava_containing_longitude(bhavas, 150.0).house_number == 2
    assert bhava_containing_longitude(bhavas, 95.0).house_number == 12  # 90-120


def test_bhava_aspects_cusp_to_occupant():
    from jyotish.models import AspectKind, JyotishConfig

    result = _cusp_result(whole_sign_cusps(125.0), 125.0)
    # Sun at 122° is an occupant of house 1; its separation from the cusp
    # (120°) is 2° -> a conjunction within orb.
    states = (make_planet_state(BodyId.SUN, longitude_used=122.0),)
    bhavas = compute_bhavas(result, states, JyotishConfig())
    aspects = bhavas[0].aspects
    conjunction = next(a for a in aspects if a.kind is AspectKind.CONJUNCTION)
    assert conjunction.within_orb is True
    assert conjunction.distance_from_exact_deg == pytest.approx(2.0)


def test_registry_freeze_and_lookup():
    registry = HouseCuspRegistry()
    provider = FakeHouseProvider()
    registry.register(provider, tuple(HouseSystem))
    assert registry.get_for(HouseSystem.WHOLE_SIGN) is provider
    assert registry.provider_ids == ("fake.houses",)
    registry.freeze()
    with pytest.raises(RuntimeError, match="frozen"):
        registry.register(FakeHouseProvider(), tuple(HouseSystem))


def test_registry_unknown_system_raises():
    registry = HouseCuspRegistry()
    with pytest.raises(UnsupportedHouseSystemError, match="no provider registered"):
        registry.get_for(HouseSystem.PLACIDUS)


def test_registry_raw_string_system_raises_typed_error():
    """A raw string where a ``HouseSystem`` is expected must raise
    ``UnsupportedHouseSystemError`` (TEST-PLAN §5) — never an AttributeError
    while formatting the message."""
    registry = HouseCuspRegistry()
    with pytest.raises(UnsupportedHouseSystemError, match="no provider registered"):
        registry.get_for("BOGUS")  # type: ignore[arg-type]


def test_default_house_provider_id_stable():
    assert SWISSEPH_HOUSE_PROVIDER_ID == "swisseph.pysweph.houses"

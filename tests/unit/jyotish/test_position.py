"""PlanetState derivation: frame selection, normalization, classification.

Core precision rule: the unrounded longitude double feeds rashi/nakshatra/
pada/degree computations — never a rounded value (Specialist §8, §18).
"""

from __future__ import annotations

import pytest

from astronomy.models import BodyId, BodyPosition, PositionType, RetrogradeState
from jyotish.models import RashiId, ZodiacMode
from jyotish.position import classify_longitude, derive_planet_state


def _body_pos(
    longitude_tropical: float = 120.0,
    longitude_sidereal: float | None = None,
    latitude: float = 0.0,
    speed: float = 1.0,
    retrograde: RetrogradeState = RetrogradeState.DIRECT,
) -> BodyPosition:
    return BodyPosition(
        body=BodyId.JUPITER,
        longitude_tropical=longitude_tropical,
        longitude_sidereal=longitude_sidereal,
        latitude=latitude,
        distance_au=5.2,
        speed_longitude=speed,
        speed_latitude=0.0,
        speed_distance=0.0,
        retrograde=retrograde,
        position_type=PositionType.APPARENT,
        ayanamsa_value=24.0 if longitude_sidereal is not None else None,
    )


def _config(**overrides):
    from jyotish.models import JyotishConfig

    return JyotishConfig(**overrides)


def test_sidereal_mode_uses_sidereal_longitude():
    state = derive_planet_state(
        _body_pos(longitude_tropical=120.0, longitude_sidereal=96.0),
        _config(),
        "2000-01-01T00:00:00Z",
        2451545.0,
        "fake",
        "18",
    )
    assert state.longitude_used == pytest.approx(96.0)
    assert state.rashi is RashiId.KARKA  # 96 deg = 3×30 + 6


def test_tropical_mode_uses_tropical_longitude():
    state = derive_planet_state(
        _body_pos(longitude_tropical=120.0, longitude_sidereal=96.0),
        _config(zodiac_mode=ZodiacMode.TROPICAL),
        "2000-01-01T00:00:00Z",
        2451545.0,
        "fake",
        "18",
    )
    assert state.longitude_used == pytest.approx(120.0)
    assert state.rashi is RashiId.SIMHA


def test_sidereal_mode_requires_sidereal_value():
    with pytest.raises(ValueError, match="longitude_sidereal is None"):
        derive_planet_state(
            _body_pos(longitude_tropical=120.0, longitude_sidereal=None),
            _config(),
            "2000-01-01T00:00:00Z",
            2451545.0,
            "fake",
            "18",
        )


def test_longitude_normalized_to_unit_interval():
    state = derive_planet_state(
        _body_pos(longitude_tropical=480.0, longitude_sidereal=456.0),
        _config(),
        "2000-01-01T00:00:00Z",
        2451545.0,
        "fake",
        "18",
    )
    assert 0.0 <= state.longitude_used < 360.0
    assert 0.0 <= state.longitude_tropical < 360.0
    assert 0.0 <= state.longitude_sidereal < 360.0


def test_unrounded_classification_near_boundary():
    """29.9999999 and 30.0 are in different rashis — no rounding first.

    SIDEREAL is the default mode, so the used longitude is the sidereal one.
    """
    a = derive_planet_state(
        _body_pos(longitude_tropical=53.9999999, longitude_sidereal=29.9999999),
        _config(),
        "2000-01-01T00:00:00Z",
        2451545.0,
        "fake",
        "18",
    )
    b = derive_planet_state(
        _body_pos(longitude_tropical=54.0, longitude_sidereal=30.0),
        _config(),
        "2000-01-01T00:00:00Z",
        2451545.0,
        "fake",
        "18",
    )
    assert a.rashi is RashiId.MESHA
    assert b.rashi is RashiId.VRISHABHA
    assert a.degree_in_rashi == pytest.approx(29.9999999)
    assert b.degree_in_rashi == pytest.approx(0.0)


def test_retrograde_and_speed_passthrough():
    state = derive_planet_state(
        _body_pos(
            longitude_tropical=200.0, longitude_sidereal=176.0,
            speed=-0.5, retrograde=RetrogradeState.RETROGRADE,
        ),
        _config(),
        "2000-01-01T00:00:00Z",
        2451545.0,
        "fake",
        "18",
    )
    assert state.speed_longitude == -0.5
    assert state.retrograde is RetrogradeState.RETROGRADE


def test_metadata_passthrough():
    state = derive_planet_state(
        _body_pos(longitude_sidereal=10.0),
        _config(),
        "2000-01-01T12:30:00Z",
        2451545.0208,
        "swisseph.pysweph",
        "18",
    )
    assert state.provider_id == "swisseph.pysweph"
    assert state.ephemeris_version == "18"
    assert state.timestamp_utc_iso == "2000-01-01T12:30:00Z"


def test_dms_is_presentational_rounding():
    """DMS comes from the rounded value; classification from the raw value."""
    state = derive_planet_state(
        _body_pos(longitude_tropical=143.2566, longitude_sidereal=119.2566),
        _config(),
        "2000-01-01T00:00:00Z",
        2451545.0,
        "fake",
        "18",
    )
    assert state.dms.degrees == 119
    assert state.dms.minutes == 15
    # The classification still uses the unrounded 119.2566.
    assert state.longitude_used == pytest.approx(119.2566)


def test_classify_longitude_placeholder():
    state = classify_longitude(350.0, _config())
    assert state.longitude_used == pytest.approx(350.0)
    assert state.rashi is RashiId.MEENA
    assert state.body is BodyId.SUN
    assert state.speed_longitude == 0.0

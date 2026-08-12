"""Unit tests for the pure data model (no Swiss Ephemeris required)."""

import dataclasses
import datetime as dt

import pytest

from astronomy.models import (
    CANONICAL_BODIES,
    Ayanamsa,
    BodyId,
    BodyPosition,
    CalculationConfig,
    EphemerisMode,
    EphemerisRequest,
    EphemerisResult,
    NodeType,
    PositionType,
    ProviderMetadata,
    ProviderRun,
    RetrogradeState,
    classify_retrograde,
)


def test_canonical_bodies_are_all_nine_in_order():
    assert CANONICAL_BODIES == (
        BodyId.SUN,
        BodyId.MOON,
        BodyId.MARS,
        BodyId.MERCURY,
        BodyId.JUPITER,
        BodyId.VENUS,
        BodyId.SATURN,
        BodyId.RAHU,
        BodyId.KETU,
    )


def test_enum_values_are_stable_strings():
    assert BodyId.SUN.value == "SUN"
    assert RetrogradeState.RETROGRADE.value == "RETROGRADE"
    assert Ayanamsa.LAHIRI.value == "LAHIRI"
    assert EphemerisMode.SWIEPH.value == "SWIEPH"
    assert PositionType.APPARENT.value == "APPARENT"
    assert NodeType.MEAN.value == "MEAN"


def test_config_defaults_match_spec():
    config = CalculationConfig()
    assert config.ayanamsa is Ayanamsa.LAHIRI
    assert config.ephemeris_mode is EphemerisMode.SWIEPH
    assert config.position_type is PositionType.APPARENT
    assert config.node_type is NodeType.MEAN
    assert config.allow_fallback is True
    assert config.ephemeris_path is None
    assert config.ayanamsa_override is None


def test_models_are_immutable():
    config = CalculationConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.ayanamsa = None  # type: ignore[misc]


def test_config_dict_round_trip():
    config = CalculationConfig(
        ayanamsa=Ayanamsa.RAMAN,
        ayanamsa_override=(2451545.0, 24.0),
        ephemeris_mode=EphemerisMode.MOSEPH,
        position_type=PositionType.TRUE,
        node_type=NodeType.TRUE,
        ephemeris_path="/tmp/ephe",
        allow_fallback=False,
    )
    restored = CalculationConfig.from_dict(config.to_dict())
    assert restored == config


def test_request_dict_round_trip():
    request = EphemerisRequest(
        date=dt.date(2000, 1, 1),
        time=dt.time(12, 0, 0),
        timezone="Asia/Kolkata",
        latitude=28.6,
        longitude=77.2,
        bodies=(BodyId.SUN, BodyId.MOON),
        config=CalculationConfig(),
        provider_id="swisseph.pysweph",
    )
    restored = EphemerisRequest.from_dict(request.to_dict())
    assert restored == request


def test_request_all_bodies_serializes_null():
    request = EphemerisRequest(
        date=dt.date(2000, 1, 1),
        time=dt.time(0, 0, 0),
        timezone="UTC",
        latitude=0.0,
        longitude=0.0,
    )
    assert request.to_dict()["bodies"] is None


def test_classify_retrograde():
    assert classify_retrograde(1.0) is RetrogradeState.DIRECT
    assert classify_retrograde(-1.0) is RetrogradeState.RETROGRADE
    assert classify_retrograde(0.0) is RetrogradeState.STATIONARY
    assert classify_retrograde(1e-12) is RetrogradeState.STATIONARY


def test_result_dict_shape():
    request = EphemerisRequest(
        date=dt.date(2000, 1, 1),
        time=dt.time(12, 0, 0),
        timezone="UTC",
        latitude=0.0,
        longitude=0.0,
    )
    position = BodyPosition(
        body=BodyId.SUN,
        longitude_tropical=280.0,
        longitude_sidereal=256.0,
        latitude=0.0,
        distance_au=0.983,
        speed_longitude=1.019,
        speed_latitude=0.0,
        speed_distance=0.0,
        retrograde=RetrogradeState.DIRECT,
        position_type=PositionType.APPARENT,
        ayanamsa_value=24.0,
    )
    run = ProviderRun(
        positions=(position,),
        ephemeris_mode=EphemerisMode.SWIEPH,
        ephemeris_files=("sepl_18.se1", "semo_18.se1"),
    )
    result = EphemerisResult(
        request_snapshot=request,
        timestamp_utc_iso="2000-01-01T12:00:00Z",
        timestamp_local_iso="2000-01-01T12:00:00+00:00",
        julian_day_ut=2451545.0,
        positions=(position,),
        provider=ProviderMetadata(
            provider_id="swisseph.pysweph",
            library_name="pysweph",
            library_version="2.10.3.6",
            ephemeris_version="18",
        ),
        provider_run=run,
        config=CalculationConfig(),
    )
    d = result.to_dict()
    assert set(d) == {
        "request_snapshot",
        "timestamp_utc_iso",
        "timestamp_local_iso",
        "julian_day_ut",
        "positions",
        "provider",
        "provider_run",
        "config",
    }
    assert d["positions"] == d["provider_run"]["positions"]
    assert d["request_snapshot"]["bodies"] is None
    assert d["provider_run"]["ephemeris_mode"] == "SWIEPH"

"""Unit tests for JSON serialization (round-trip and schema shape)."""

import datetime as dt
import json

from astronomy.models import (
    BodyId,
    BodyPosition,
    CalculationConfig,
    EphemerisMode,
    EphemerisRequest,
    EphemerisResult,
    PositionType,
    ProviderMetadata,
    ProviderRun,
    RetrogradeState,
)
from astronomy.serialize import (
    config_from_dict,
    json_to_result,
    request_from_dict,
    result_to_json,
)


def _sample_result() -> EphemerisResult:
    request = EphemerisRequest(
        date=dt.date(2000, 1, 1),
        time=dt.time(12, 0, 0, 123456),
        timezone="UTC",
        latitude=0.0,
        longitude=0.0,
    )
    position = BodyPosition(
        body=BodyId.SUN,
        longitude_tropical=280.3689186698997,
        longitude_sidereal=256.5118263161909,
        latitude=0.0002273534758712041,
        distance_au=0.9833276253625055,
        speed_longitude=1.0194341629435535,
        speed_latitude=-5.876111779464568e-07,
        speed_distance=-7.3507779749e-05,
        retrograde=RetrogradeState.DIRECT,
        position_type=PositionType.APPARENT,
        ayanamsa_value=23.857092353708822,
    )
    run = ProviderRun(
        positions=(position,),
        ephemeris_mode=EphemerisMode.SWIEPH,
        ephemeris_files=("sepl_18.se1", "semo_18.se1"),
    )
    return EphemerisResult(
        request_snapshot=request,
        timestamp_utc_iso="2000-01-01T12:00:00.123456Z",
        timestamp_local_iso="2000-01-01T12:00:00.123456+00:00",
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


def test_float_exact_round_trip():
    payload = result_to_json(_sample_result())
    data = json.loads(payload)
    assert data["positions"][0]["longitude_tropical"] == 280.3689186698997
    assert data["julian_day_ut"] == 2451545.0


def test_json_to_result_round_trip():
    result = _sample_result()
    restored = json_to_result(result_to_json(result))
    assert restored == result


def test_request_dict_round_trip_via_serialize():
    request = EphemerisRequest(
        date=dt.date(1990, 6, 15),
        time=dt.time(10, 0, 0),
        timezone="Asia/Kolkata",
        latitude=28.6139,
        longitude=77.209,
    )
    assert request_from_dict(json.loads(json.dumps(request.to_dict()))) == request


def test_config_dict_round_trip_via_serialize():
    config = CalculationConfig(ephemeris_mode=EphemerisMode.MOSEPH, allow_fallback=False)
    assert config_from_dict(json.loads(json.dumps(config.to_dict()))) == config


def test_schema_shape_of_result_payload():
    data = json.loads(result_to_json(_sample_result()))
    # Contract field names, snake_case, enum strings, nulls preserved.
    assert "request_snapshot" in data
    assert data["provider_run"]["ephemeris_mode"] == "SWIEPH"
    assert data["provider_run"]["ephemeris_files"] == ["sepl_18.se1", "semo_18.se1"]
    assert data["positions"][0]["retrograde"] == "DIRECT"
    assert data["positions"][0]["position_type"] == "APPARENT"
    assert data["config"]["ayanamsa"] == "LAHIRI"
    assert data["request_snapshot"]["bodies"] is None
    assert data["provider_run"]["positions"] == data["positions"]


def test_no_astrology_fields_in_payload():
    data = json.loads(result_to_json(_sample_result()))
    payload = json.dumps(data).lower()
    forbidden_terms = (
        "rashi", "nakshatra", "bhava", "yoga", "dasha",
        "gochar", "benefic", "malefic", "house", "prediction",
    )
    for forbidden in forbidden_terms:
        assert forbidden not in payload

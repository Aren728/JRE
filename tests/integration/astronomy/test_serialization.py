"""QA requirement 15: serialization produces stable, machine-readable output.

Runs the real provider end-to-end and asserts the JSON output shape, float
round-trip, enum stringification, null handling and determinism.
"""

from __future__ import annotations

import json

from tests.integration.astronomy.conftest import make_request

from astronomy.serialize import json_to_result, result_to_json

FORBIDDEN_INTERPRETATION_TERMS = (
    "rashi",
    "nakshatra",
    "bhava",
    "yoga",
    "dasha",
    "gochar",
    "benefic",
    "malefic",
    "house",
    "prediction",
)


def test_serialization_stable_across_calls(service):
    first = result_to_json(service.compute(make_request()))
    second = result_to_json(service.compute(make_request()))
    assert first == second


def test_serialization_round_trips(service):
    result = service.compute(make_request())
    payload = result_to_json(result)
    restored = json_to_result(payload)
    assert restored == result


def test_serialization_float_round_trip(service):
    payload = result_to_json(service.compute(make_request()))
    data = json.loads(payload)
    # JSON decodes to the identical double.
    for pos in data["positions"]:
        lon = json.loads(json.dumps(pos["longitude_tropical"]))
        assert lon == pos["longitude_tropical"]
    assert data["julian_day_ut"] == 2448057.6875


def test_serialization_shape(service):
    data = json.loads(result_to_json(service.compute(make_request())))
    assert set(data) == {
        "request_snapshot",
        "timestamp_utc_iso",
        "timestamp_local_iso",
        "julian_day_ut",
        "positions",
        "provider",
        "provider_run",
        "config",
    }
    assert data["timestamp_utc_iso"] == "1990-06-15T04:30:00Z"
    assert data["provider"]["provider_id"] == "swisseph.pysweph"
    assert data["provider_run"]["ephemeris_mode"] == "SWIEPH"
    assert data["provider_run"]["ephemeris_files"] == ["sepl_18.se1", "semo_18.se1"]
    assert data["config"]["ayanamsa"] == "LAHIRI"
    assert data["config"]["ephemeris_mode"] == "SWIEPH"
    assert data["request_snapshot"]["timezone"] == "Asia/Kolkata"
    assert data["positions"] == data["provider_run"]["positions"]


def test_serialization_contains_no_astrology(service):
    payload = json.dumps(json.loads(result_to_json(service.compute(make_request())))).lower()
    for term in FORBIDDEN_INTERPRETATION_TERMS:
        assert term not in payload, f"interpretation term {term!r} leaked into payload"

"""Serialization + request-parser tests (TEST-PLAN §11/§17, SPEC §26)."""

from __future__ import annotations

import json

import pytest

from bhava import (
    analysis_request_from_dict,
    derive_house_analysis,
    result_to_dict,
    result_to_json,
    transit_request_from_dict,
)
from bhava.errors import InvalidAnalysisRequestError, UnsupportedReferenceError
from jyotish import TransitReferencePoint


def test_result_json_round_trip(whole_sign_chart) -> None:
    analysis = derive_house_analysis(whole_sign_chart)
    payload = json.loads(result_to_json(analysis))
    # Every double round-trips exactly (Python round-trip repr).
    assert payload["house_system"] == "WHOLE_SIGN"
    assert len(payload["derived_houses"]) == 12
    assert payload["empty_house_count"] == 3
    assert payload["relative_house_table"]["LAGNA"]["SUN"] == 1


def test_result_to_dict_is_deterministic(whole_sign_chart) -> None:
    a = result_to_dict(derive_house_analysis(whole_sign_chart))
    b = result_to_dict(derive_house_analysis(whole_sign_chart))
    assert a == b
    assert json.dumps(a) == json.dumps(b)


def test_analysis_request_from_dict() -> None:
    request = {
        "birth": {
            "date": "1990-06-15",
            "time": "10:00:00",
            "timezone": "Asia/Kolkata",
            "latitude": 28.6139,
            "longitude": 77.209,
        },
        "house_systems": ["WHOLE_SIGN", "PLACIDUS"],
        "references": ["LAGNA", "MOON", "SUN", "ASC"],
        "config": {"cusp_proximity_orb_deg": 3.0, "unplaced_body_behavior": "RAISE"},
    }
    parsed = analysis_request_from_dict(request)
    assert parsed["birth"].timezone == "Asia/Kolkata"
    assert [s.value for s in parsed["house_systems"]] == ["WHOLE_SIGN", "PLACIDUS"]
    assert [r.value for r in parsed["references"]] == ["LAGNA", "MOON", "SUN", "ASC"]
    assert parsed["config"].cusp_proximity_orb_deg == 3.0


def test_analysis_request_unknown_house_system() -> None:
    from bhava.errors import InvalidBhavaConfigError

    with pytest.raises(InvalidBhavaConfigError):
        analysis_request_from_dict(
            {
                "birth": {
                    "date": "1990-06-15",
                    "time": "10:00:00",
                    "timezone": "UTC",
                    "latitude": 0.0,
                    "longitude": 0.0,
                },
                "house_systems": ["NONSENSE"],
            }
        )


def test_analysis_request_unknown_reference() -> None:
    with pytest.raises(UnsupportedReferenceError):
        analysis_request_from_dict(
            {
                "birth": {
                    "date": "1990-06-15",
                    "time": "10:00:00",
                    "timezone": "UTC",
                    "latitude": 0.0,
                    "longitude": 0.0,
                },
                "references": ["NONE"],
            }
        )


def test_analysis_request_missing_birth() -> None:
    with pytest.raises(InvalidAnalysisRequestError):
        analysis_request_from_dict({})


def test_transit_request_from_dict() -> None:
    request = {
        "transit": {
            "birth": {
                "date": "1990-06-15",
                "time": "10:00:00",
                "timezone": "Asia/Kolkata",
                "latitude": 28.6139,
                "longitude": 77.209,
            },
            "transit_instant_utc_iso": "2024-06-01T00:00:00Z",
            "reference": "LAGNA",
        },
        "natal_chart": {"opaque": "caller-supplied NatalChart"},
    }
    parsed = transit_request_from_dict(request)
    assert parsed["transit"]["transit_instant_utc_iso"] == "2024-06-01T00:00:00Z"
    assert parsed["transit"]["reference"] is TransitReferencePoint.LAGNA
    assert parsed["natal_chart"] == {"opaque": "caller-supplied NatalChart"}


def test_transit_request_missing_natal_chart() -> None:
    with pytest.raises(InvalidAnalysisRequestError):
        transit_request_from_dict(
            {
                "transit": {
                    "birth": {
                        "date": "1990-06-15",
                        "time": "10:00:00",
                        "timezone": "UTC",
                        "latitude": 0.0,
                        "longitude": 0.0,
                    },
                    "transit_instant_utc_iso": "2024-06-01T00:00:00Z",
                }
            }
        )


def test_transit_request_unknown_reference() -> None:
    with pytest.raises(UnsupportedReferenceError):
        transit_request_from_dict(
            {
                "transit": {
                    "birth": {
                        "date": "1990-06-15",
                        "time": "10:00:00",
                        "timezone": "UTC",
                        "latitude": 0.0,
                        "longitude": 0.0,
                    },
                    "transit_instant_utc_iso": "2024-06-01T00:00:00Z",
                    "reference": "NONE",
                },
                "natal_chart": {},
            }
        )

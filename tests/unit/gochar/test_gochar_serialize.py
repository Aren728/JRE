"""Serialization tests (TEST-PLAN §2 row 20, §8, SPEC §21, DC §6-§7).

``result_to_dict`` ↔ ``result_to_json`` round-trip is value-identical;
requests round-trip through ``*_request_from_dict`` with full validation;
the generated JSON Schema enforces ``additionalProperties=false`` at every
object level, pinned enum strings, and the ISO-8601 UTC microsecond
pattern; malformed input raises the exact typed errors; no information
loss (every ``TransitEvent`` field incl. ``SearchMetadata`` survives).
"""

from __future__ import annotations

import json

import pytest

import gochar
from gochar import (
    GocharConfig,
    GocharInstantRequest,
    GocharIntervalRequest,
    GocharService,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
)
from gochar.errors import InvalidGocharConfigError, InvalidGocharRequestError
from gochar.serialize import (
    instant_request_from_dict,
    interval_request_from_dict,
    natal_request_from_dict,
)
from jyotish import BirthData, BodyId

BIRTH = BirthData(
    date="1990-06-15",
    time="10:00:00",
    timezone="Asia/Kolkata",
    latitude=28.6139,
    longitude=77.2090,
)


def test_result_dict_json_round_trip(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_instant(
        GocharInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    d1 = result_to_dict(result)
    d2 = json.loads(result_to_json(result))
    assert d1 == d2
    assert result_to_json(result) == result_to_json(result)


def test_interval_result_json_round_trip(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-15T00:00:00.000000Z",
            bodies=(BodyId.MOON,),
        )
    )
    assert result_to_dict(result) == json.loads(result_to_json(result))


def test_requests_round_trip_with_validation() -> None:
    inst = instant_request_from_dict(
        {"instant_utc_iso": "2026-06-15T12:00:00.000000Z", "bodies": ["SUN"]}
    )
    assert inst.bodies == (BodyId.SUN,)
    assert inst.config is None

    natal = natal_request_from_dict(
        {
            "birth": {
                "date": "1990-06-15",
                "time": "10:00:00",
                "timezone": "Asia/Kolkata",
                "latitude": 28.6139,
                "longitude": 77.2090,
            },
            "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
            "bodies": ["SUN", "MOON"],
            "reference_point": "MOON",
            "config": {"aspect_echo": False},
        }
    )
    assert natal.birth == BIRTH
    assert natal.bodies == (BodyId.SUN, BodyId.MOON)
    assert natal.reference_point == "MOON"
    assert natal.config is not None and natal.config.aspect_echo is False

    interval = interval_request_from_dict(
        {
            "start_utc_iso": "2026-06-01T00:00:00.000000Z",
            "end_utc_iso": "2026-06-15T00:00:00.000000Z",
            "bodies": ["SUN"],
            "natal_anchor": {
                "date": "1990-06-15",
                "time": "10:00:00",
                "timezone": "Asia/Kolkata",
                "latitude": 28.6139,
                "longitude": 77.2090,
            },
        }
    )
    assert interval.natal_anchor == BIRTH


def test_malformed_request_inputs_typed_errors() -> None:
    with pytest.raises(InvalidGocharRequestError):
        instant_request_from_dict({"bodies": ["SUN"]})  # missing instant
    with pytest.raises(InvalidGocharRequestError):
        instant_request_from_dict(
            {"instant_utc_iso": "2026-06-15T12:00:00.000000Z", "bodies": []}
        )
    with pytest.raises(InvalidGocharRequestError):
        natal_request_from_dict(
            {"instant_utc_iso": "2026-06-15T12:00:00.000000Z", "bodies": ["SUN"]}
        )  # missing birth
    with pytest.raises(InvalidGocharConfigError):
        instant_request_from_dict(
            {
                "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
                "bodies": ["SUN"],
                "config": {"house_system": "BOGUS"},
            }
        )
    with pytest.raises(InvalidGocharRequestError):
        instant_request_from_dict(
            {"instant_utc_iso": "2026-06-15T12:00:00.000000Z", "bodies": ["PLUTO"]}
        )


def test_schema_additional_properties_rejected() -> None:
    payload = {
        "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
        "planet_states": [],
        "pair_geometry": None,
        "config_echo": {},
        "provenance": {},
        "surprise_key": 1,
    }
    with pytest.raises(InvalidGocharRequestError, match="additional"):
        validate_schema(payload, schema_for("GocharInstantResult"))


def test_schema_required_properties() -> None:
    payload = {
        "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
        "planet_states": [],
        "pair_geometry": None,
        "config_echo": {},
        # provenance missing
    }
    with pytest.raises(InvalidGocharRequestError, match="provenance"):
        validate_schema(payload, schema_for("GocharInstantResult"))


def test_schema_enum_constraint() -> None:
    payload = {
        "reference_point": "MIDHEAVEN",
        "house_system": "WHOLE_SIGN",
        "sample_step_hours": 24.0,
        "aspect_echo": True,
        "natal_house_series": False,
        "tradition_profile": None,
        "version": "0.2.0",
    }
    with pytest.raises(InvalidGocharRequestError, match="enum"):
        validate_schema(payload, schema_for("GocharConfig"))


def test_schema_iso_utc_pattern() -> None:
    payload = {
        "start_utc_iso": "2026-06-15",  # date-only
        "end_utc_iso": "2026-06-15T12:00:00.000000Z",
        "bodies": ["SUN"],
        "events": [],
        "state_samples": [],
        "natal_house_series": None,
        "natal_anchor": None,
        "provenance": {},
    }
    with pytest.raises(InvalidGocharRequestError, match="does not match"):
        validate_schema(payload, schema_for("GocharIntervalResult"))


def test_no_information_loss_on_events(fake_service) -> None:
    """DC §7 / TEST-PLAN §8 — every TransitEvent field incl.
    SearchMetadata survives serialization."""
    from tests.unit.gochar.conftest import make_event

    from gochar import GocharIntervalRequest
    from jyotish import TransitEventKind

    events = (
        make_event(
            body=BodyId.MOON,
            kind=TransitEventKind.NAKSHATRA_INGRESS,
            event_julian_day_ut=2460462.5,
            event_utc_iso="2024-06-15T12:00:00.000000Z",
            boundary_deg=120.0,
        ),
    )
    fake_service._events = events
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2024-06-01T00:00:00.000000Z",
            end_utc_iso="2024-06-30T00:00:00.000000Z",
            bodies=(BodyId.MOON,),
        )
    )
    payload = result_to_dict(result)
    event = payload["events"][0]
    assert set(event) == {
        "body",
        "kind",
        "event_julian_day_ut",
        "event_utc_iso",
        "boundary_deg",
        "reached",
        "direction",
        "search_metadata",
    }
    assert event["search_metadata"]["iterations"] == 3
    assert event["search_metadata"]["position_calls"] == 4
    assert event["boundary_deg"] == 120.0


def test_config_dict_round_trip() -> None:
    cfg = GocharConfig(reference_point="SUN", sample_step_hours=12.0)
    assert gochar.config_from_dict(cfg.to_dict()) == cfg


def test_schema_draft_shape() -> None:
    schema = schema_for("GocharInstantResult")
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "required" in schema
    assert "properties" in schema

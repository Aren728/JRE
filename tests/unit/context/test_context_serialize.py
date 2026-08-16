"""Serialization tests (TEST-PLAN §2 row 20, §8, SPEC §21, DC §6-§7).

``result_to_dict`` ↔ ``result_to_json`` round-trip is value-identical;
requests round-trip through the ``*_request_from_dict`` parsers and the
canonical ``context_request_from_dict`` boundary with full validation;
the generated JSON Schema enforces ``additionalProperties=false`` at
every object level, pinned enum strings, and the ISO-8601 UTC microsecond
pattern; malformed input raises the exact typed errors; no information
loss (every snapshot section survives). V1 has no candidate-request
parser.
"""

from __future__ import annotations

import json

import pytest

import context
from context import (
    ContextConfig,
    ContextInstantRequest,
    ContextRequest,
    ContextService,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
)
from context.errors import InvalidContextConfigError, InvalidContextRequestError
from context.serialize import (
    context_request_from_dict,
    eclipse_request_from_dict,
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


def test_result_dict_json_round_trip(fake_jyotish, fake_bhava) -> None:
    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    d1 = result_to_dict(result)
    d2 = json.loads(result_to_json(result))
    assert d1 == d2
    assert result_to_json(result) == result_to_json(result)


def test_natal_result_json_round_trip(fake_jyotish, fake_bhava) -> None:
    from context import ContextNatalRequest

    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_natal(ContextNatalRequest(birth=BIRTH))
    assert result_to_dict(result) == json.loads(result_to_json(result))
    payload = result_to_dict(result)
    assert payload["natal_chart"] is not None
    assert payload["planet_states"] is not None
    assert payload["house_analyses"] is not None
    assert payload["provenance"]["source_layers"] == ["JRE-002", "JRE-003", "JRE-005"]


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
            "include_house_analysis": True,
            "time_precision": "HOUR_KNOWN",
            "config": {"house_system": "EQUAL"},
        }
    )
    assert natal.birth == BIRTH
    assert natal.include_house_analysis is True
    assert natal.time_precision == "HOUR_KNOWN"
    assert natal.config is not None and natal.config.house_system == "EQUAL"

    interval = interval_request_from_dict(
        {
            "start_utc_iso": "2026-06-01T00:00:00.000000Z",
            "end_utc_iso": "2026-06-15T00:00:00.000000Z",
            "bodies": ["SUN"],
        }
    )
    assert interval.bodies == (BodyId.SUN,)

    eclipse = eclipse_request_from_dict(
        {
            "start_utc_iso": "2026-06-01T00:00:00.000000Z",
            "end_utc_iso": "2026-06-15T00:00:00.000000Z",
            "kind": "SOLAR",
        }
    )
    from jyotish import EclipseKind

    assert eclipse.kind is EclipseKind.SOLAR

    # The canonical request boundary parses any frozen V1 capability.
    canonical = context_request_from_dict(
        {
            "capability": "instant",
            "capability_version": "0.1.0",
            "analysis_request_id": "req-1",
            "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
            "bodies": ["SUN"],
        }
    )
    assert isinstance(canonical, ContextInstantRequest)
    assert isinstance(canonical, ContextRequest)
    assert canonical.capability == "instant"
    assert canonical.capability_version == "0.1.0"
    assert canonical.analysis_request_id == "req-1"
    assert canonical.bodies == (BodyId.SUN,)

    canonical_natal = context_request_from_dict(
        {
            "capability": "natal",
            "birth": {
                "date": "1990-06-15",
                "time": "10:00:00",
                "timezone": "Asia/Kolkata",
                "latitude": 28.6139,
                "longitude": 77.2090,
            },
        }
    )
    assert isinstance(canonical_natal, ContextRequest)
    assert canonical_natal.capability == "natal"


def test_malformed_request_inputs_typed_errors() -> None:
    with pytest.raises(InvalidContextRequestError):
        instant_request_from_dict({"bodies": ["SUN"]})  # missing instant
    with pytest.raises(InvalidContextRequestError):
        instant_request_from_dict(
            {"instant_utc_iso": "2026-06-15T12:00:00.000000Z", "bodies": []}
        )
    with pytest.raises(InvalidContextRequestError):
        natal_request_from_dict(
            {"instant_utc_iso": "2026-06-15T12:00:00.000000Z", "bodies": ["SUN"]}
        )  # missing birth
    with pytest.raises(InvalidContextConfigError):
        instant_request_from_dict(
            {
                "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
                "bodies": ["SUN"],
                "config": {"house_system": "BOGUS"},
            }
        )
    with pytest.raises(InvalidContextRequestError):
        eclipse_request_from_dict(
            {
                "start_utc_iso": "2026-06-01T00:00:00.000000Z",
                "end_utc_iso": "2026-06-15T00:00:00.000000Z",
                "kind": "BOGUS",
            }
        )
    with pytest.raises(InvalidContextRequestError, match="capability"):
        context_request_from_dict({"capability": "bogus"})
    with pytest.raises(InvalidContextRequestError):
        context_request_from_dict({"capability": "natal"})  # missing birth
    with pytest.raises(InvalidContextRequestError, match="does not match"):
        instant_request_from_dict(
            {
                "capability": "natal",
                "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
                "bodies": ["SUN"],
            }
        )


def test_schema_additional_properties_rejected() -> None:
    payload = {
        "snapshot_version": "0.1.0",
        "natal_chart": None,
        "planet_states": [],
        "pair_geometry": None,
        "house_analyses": None,
        "transit_events": None,
        "state_samples": None,
        "gochar_instant": None,
        "gochar_natal": None,
        "gochar_interval": None,
        "eclipses": None,
        "provenance": {},
        "version": "0.1.0",
        "surprise_key": 1,
    }
    with pytest.raises(InvalidContextRequestError, match="additional"):
        validate_schema(payload, schema_for("CanonicalFactSnapshot"))


def test_schema_required_properties() -> None:
    payload = {
        "snapshot_version": "0.1.0",
        # natal_chart missing
    }
    with pytest.raises(InvalidContextRequestError, match="natal_chart"):
        validate_schema(payload, schema_for("CanonicalFactSnapshot"))


def test_schema_enum_constraint() -> None:
    payload = {
        "snapshot_version": "0.1.0",
        "default_time_precision": "WHEN_IN_DOUBT",
        "house_system": "WHOLE_SIGN",
        "tradition_profile": None,
        "version": "0.1.0",
    }
    with pytest.raises(InvalidContextRequestError, match="enum"):
        validate_schema(payload, schema_for("ContextConfig"))


def test_schema_iso_utc_pattern() -> None:
    payload = {
        "capability": "instant",
        "capability_version": "0.1.0",
        "analysis_request_id": None,
        "instant_utc_iso": "2026-06-15",  # date-only
        "bodies": ["SUN"],
        "config": None,
    }
    with pytest.raises(InvalidContextRequestError, match="does not match"):
        validate_schema(payload, schema_for("ContextInstantRequest"))


def test_schema_canonical_request() -> None:
    schema = schema_for("ContextRequest")
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert {"capability", "capability_version", "analysis_request_id"} <= set(
        schema["required"]
    )
    payload = {
        "capability": "instant",
        "capability_version": "0.1.0",
        "analysis_request_id": None,
        "config": None,
        "surprise": 1,
    }
    with pytest.raises(InvalidContextRequestError, match="additional"):
        validate_schema(payload, schema)


def test_schema_instant_request_includes_capability_contract() -> None:
    schema = schema_for("ContextInstantRequest")
    assert "capability" in schema["properties"]
    assert "capability_version" in schema["properties"]
    payload = {
        "capability": "instant",
        "capability_version": "0.1.0",
        "analysis_request_id": None,
        "instant_utc_iso": "2026-06-15T12:00:00.000000Z",
        "bodies": ["SUN"],
        "config": None,
    }
    validate_schema(payload, schema)  # valid canonical instant request


def test_schema_draft_shape() -> None:
    schema = schema_for("CanonicalFactSnapshot")
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert "required" in schema
    assert "properties" in schema
    with pytest.raises(InvalidContextRequestError):
        schema_for("BOGUS")


def test_config_dict_round_trip() -> None:
    cfg = ContextConfig(house_system="EQUAL")
    assert context.config_from_dict(cfg.to_dict()) == cfg

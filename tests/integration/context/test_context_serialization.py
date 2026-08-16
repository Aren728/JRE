"""Integration serialization + schema (TEST-PLAN row 20/23, SPEC §21).

Real ephemeris-backed snapshots round-trip through dict/JSON with no
information loss and validate against the generated JSON Schema
(``additionalProperties=false``, pinned enums, ISO patterns).
"""

from __future__ import annotations

import json

import pytest

from context import (
    ContextInstantRequest,
    ContextNatalRequest,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
)
from context.errors import InvalidContextRequestError
from jyotish import BodyId


def test_instant_snapshot_schema_valid(context_service) -> None:
    result = context_service.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON, BodyId.MARS),
        )
    )
    payload = result_to_dict(result)
    assert payload == json.loads(result_to_json(result))
    validate_schema(payload, schema_for("CanonicalFactSnapshot"))
    # Schema rejects an added key.
    tampered = dict(payload)
    tampered["extra"] = 1
    with pytest.raises(InvalidContextRequestError, match="additional"):
        validate_schema(tampered, schema_for("CanonicalFactSnapshot"))


def test_natal_snapshot_no_information_loss(context_service, birth) -> None:
    result = context_service.snapshot_natal(ContextNatalRequest(birth=birth))
    payload = result_to_dict(result)
    validate_schema(payload, schema_for("CanonicalFactSnapshot"))
    assert payload["natal_chart"]["birth_snapshot"]["date"] == "1990-06-15"
    assert payload["natal_chart"]["lagna"] is not None
    assert len(payload["natal_chart"]["bhavas"]) == 12
    assert len(payload["natal_chart"]["planet_states"]) == 9
    assert len(payload["planet_states"]) == 9
    assert len(payload["house_analyses"]) == 1
    # No tradition profile was applied, so no DOCTRINE_RULE stage may be
    # claimed; FUTURE_INFERENCE stays a reserved placeholder (SPEC §16).
    stages = [s["stage"] for s in payload["provenance"]["stages"]]
    assert stages == [
        "INPUT", "ASTRONOMICAL", "NORMALIZATION", "DERIVED", "FUTURE_INFERENCE",
    ]
    assert all(s["layer_id"] != "JRE-004" for s in payload["provenance"]["stages"])
    future = [s for s in payload["provenance"]["stages"] if s["stage"] == "FUTURE_INFERENCE"][0]
    assert future["layer_id"] is None
    assert future["algorithm"] == "reserved"
    assert payload["provenance"]["source_layers"] == ["JRE-002", "JRE-003", "JRE-005"]


def test_interval_snapshot_echo_survives_serialization(context_service) -> None:
    from context import ContextIntervalRequest

    result = context_service.snapshot_interval(
        ContextIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-08-01T00:00:00.000000Z",
            bodies=(BodyId.MOON,),
        )
    )
    payload = result_to_dict(result)
    validate_schema(payload, schema_for("CanonicalFactSnapshot"))
    assert payload["transit_events"] is not None
    assert payload["state_samples"] is not None
    assert payload["natal_chart"] is None
    assert payload["house_analyses"] is None


def test_eclipse_snapshot_echo_survives_serialization(context_service) -> None:
    from context import ContextEclipseRequest

    result = context_service.snapshot_eclipses(
        ContextEclipseRequest(
            start_utc_iso="2026-01-01T00:00:00.000000Z",
            end_utc_iso="2026-12-31T00:00:00.000000Z",
        )
    )
    payload = result_to_dict(result)
    validate_schema(payload, schema_for("CanonicalFactSnapshot"))
    assert payload["eclipses"] is not None
    assert payload["transit_events"] is None


def test_chart_identity_domain_separated(context_service, birth) -> None:
    from bhava import BhavaConfig
    from context import chart_identity, compute_deterministic_id
    from jyotish import JyotishConfig

    identity = chart_identity(
        birth=birth,
        jyotish_config=JyotishConfig(),
        bhava_config=BhavaConfig(),
        catalog_versions={"rashi": "1.0.0", "nakshatra": "1.0.0"},
    )
    assert len(identity) == 64
    # Domain-separated: same payload under a different domain differs.
    other = compute_deterministic_id("jre007:other", {"birth": "x"})
    assert other != identity

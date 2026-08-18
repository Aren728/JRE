"""Serialization tests (normative specification §20, §26).

Deterministic ``result -> dict`` / ``result -> JSON`` round-trips with no
information loss; method identity, definition version, provenance and
boundary convention survive serialization; the generated Draft 2020-12
schemas enforce ``additionalProperties=false`` and pinned enums; request
parsing validates rather than trusting external fingerprints.
"""

from __future__ import annotations

import json

import pytest
from tests.unit.varga.conftest import make_state

from jyotish import BodyId, RashiId
from varga import (
    VargaService,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
    varga_request_from_dict,
)
from varga.errors import InvalidVargaRequestError


def test_result_dict_json_round_trip() -> None:
    svc = VargaService()
    chart = svc.compute_varga_chart(
        (
            make_state(RashiId.MESHA, 5.0, body=BodyId.SUN),
            make_state(RashiId.MAKARA, 13.4166666667, body=BodyId.MOON),
        ),
        "D60",
    )
    d1 = result_to_dict(chart)
    d2 = json.loads(result_to_json(chart))
    assert d1 == d2
    assert result_to_json(chart) == result_to_json(chart)  # deterministic


def test_no_information_loss() -> None:
    svc = VargaService()
    chart = svc.compute_varga_chart(
        (make_state(RashiId.SIMHA, 25.0, body=BodyId.MARS),), "D20"
    )
    payload = result_to_dict(chart)
    assert payload["method_id"] == "d20-bphs-v1"
    assert payload["varga_id"] == "D20"
    assert payload["varga_chart_identity"]
    assert payload["varga_definition_identity"]
    assert payload["positions"][0]["provenance"]["source_citations"]
    assert payload["positions"][0]["division_index"] == 17
    assert payload["positions"][0]["segment_lower_deg"] == 24.0
    assert payload["positions"][0]["segment_upper_deg"] == 25.5


def test_variant_method_identity_survives_serialization() -> None:
    svc = VargaService()
    variant = svc.compute_varga_chart(
        (make_state(RashiId.SIMHA, 25.0),), "D20", method_id="d20-saravali-variant-v1"
    )
    payload = result_to_dict(variant)
    assert payload["method_id"] == "d20-saravali-variant-v1"
    assert payload["positions"][0]["provenance"]["varga_method_id"] == (
        "d20-saravali-variant-v1"
    )


def test_schema_additional_properties_rejected() -> None:
    payload = {
        "varga_id": "D9",
        "method_id": "d9-bphs-v1",
        "definition_version": "0.1.0",
        "positions": [],
        "varga_definition_identity": "abc",
        "varga_chart_identity": "abc",
        "context_chart_identity": None,
        "provenance": {},
        "surprise_key": 1,
    }
    with pytest.raises(InvalidVargaRequestError, match="additional"):
        validate_schema(payload, schema_for("VargaChart"))


def test_schema_required_properties() -> None:
    with pytest.raises(InvalidVargaRequestError, match="varga_id"):
        validate_schema({"positions": []}, schema_for("VargaChart"))


def test_schema_enum_constraint() -> None:
    payload = {
        "catalog_version": "0.1.0",
        "version": "0.1.0",
        "default_boundary_convention": "OPEN_LOW",
        "default_zodiac_mode": "SIDEREAL",
        "default_ayanamsa": "LAHIRI",
    }
    with pytest.raises(InvalidVargaRequestError, match="enum"):
        validate_schema(payload, schema_for("VargaConfig"))


def test_schema_draft_shape() -> None:
    for name in (
        "VargaConfig",
        "VargaDefinition",
        "VargaCalculationMethod",
        "VargaPosition",
        "VargaChart",
        "VargaProvenance",
        "SourceCitation",
        "ModalityStartParams",
        "RelativeModalityParams",
        "OddEvenStartParams",
        "ExplicitTableParams",
        "IntervalEntry",
        "FixedStartParams",
    ):
        schema = schema_for(name)
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert "required" in schema
        assert "properties" in schema
    with pytest.raises(InvalidVargaRequestError):
        schema_for("BOGUS")


def test_schema_has_no_any_payload() -> None:
    """The frozen V1 contract has no unconstrained payload (contrast the
    JRE-007 FactEnvelope requirement): every schema property is typed."""
    for name in (
        "VargaDefinition",
        "VargaCalculationMethod",
        "VargaPosition",
        "VargaChart",
        "VargaProvenance",
    ):
        schema = schema_for(name)
        for key, fragment in schema["properties"].items():
            assert fragment.get("type") != "any", f"{name}.{key} is unconstrained"


def test_request_parsing_validates() -> None:
    states = (make_state(RashiId.MESHA, 5.0),)
    parsed = varga_request_from_dict(
        {
            "states": list(states),
            "varga_id": "D9",
            "method_id": None,
            "context_chart_identity": None,
        }
    )
    assert parsed["states"] == states
    assert parsed["varga_id"] == "D9"


def test_request_parsing_rejects_bad_input() -> None:
    with pytest.raises(InvalidVargaRequestError):
        varga_request_from_dict({"varga_id": "D9"})  # states missing
    with pytest.raises(InvalidVargaRequestError):
        varga_request_from_dict({"states": [], "varga_id": "D9"})
    with pytest.raises(InvalidVargaRequestError):
        varga_request_from_dict({"states": [{}], "varga_id": "D9"})
    with pytest.raises(InvalidVargaRequestError):
        varga_request_from_dict({"states": [make_state()], "varga_id": ""})
    with pytest.raises(InvalidVargaRequestError):
        varga_request_from_dict(
            {"states": [make_state()], "varga_id": "D9", "context_chart_identity": ""}
        )


def test_config_dict_round_trip() -> None:
    import varga

    cfg = varga.VargaConfig(default_zodiac_mode="TROPICAL")
    assert varga.varga_config_from_dict(cfg.to_dict()) == cfg

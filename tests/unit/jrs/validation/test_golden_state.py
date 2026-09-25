"""JRS-091: Unit tests for the Deterministic Golden-State contract.

Verifies canonical serialization determinism, stage-hash domain
separation, manifest round-trip integrity, mismatch detection, and
strict schema validation.
"""

from __future__ import annotations

import json

import pytest

from jrs.validation.golden_state import (
    CANONICAL_STAGE_IDS,
    GOLDEN_STATE_SCHEMA_VERSION,
    GoldenStateMismatchError,
    GoldenStateManifest,
    GoldenStateValidator,
    build_manifest,
    canonical_payload,
    stage_hash,
)


# ── Canonical serialization ─────────────────────────────────────────────────


def test_canonical_payload_is_key_order_independent() -> None:
    a = {"b": 1, "a": {"d": 2.5, "c": [1, 2]}}
    b = {"a": {"c": [1, 2], "d": 2.5}, "b": 1}
    assert canonical_payload(a) == canonical_payload(b)


def test_canonical_payload_float_rounding() -> None:
    assert canonical_payload({"x": 1.2345678}) == canonical_payload({"x": 1.234568})
    assert canonical_payload({"x": 1.2345678}) == '{"x":1.234568}'


def test_canonical_payload_tuple_becomes_list() -> None:
    assert canonical_payload({"t": (1, 2)}) == canonical_payload({"t": [1, 2]})


def test_canonical_payload_bool_not_canonicalized_as_float() -> None:
    assert canonical_payload({"flag": True}) == '{"flag":true}'


def test_canonical_payload_unicode_preserved() -> None:
    assert canonical_payload({"s": "ké"}) == '{"s":"ké"}'


# ── Stage hashing ────────────────────────────────────────────────────────────


def test_stage_hash_is_deterministic() -> None:
    payload = {"planets": {"MARS": {"lon": 123.456789}}}
    assert stage_hash("chart", payload) == stage_hash("chart", payload)
    assert len(stage_hash("chart", payload)) == 64


def test_stage_hash_domain_separation_by_stage_id() -> None:
    payload = {"same": "payload"}
    assert stage_hash("chart", payload) != stage_hash("jre_facts", payload)


def test_stage_hash_changes_with_schema_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {"same": "payload"}
    before = stage_hash("chart", payload)
    monkeypatch.setattr(
        "jrs.validation.golden_state.GOLDEN_STATE_SCHEMA_VERSION", "9.9.9"
    )
    assert stage_hash("chart", payload) != before


# ── Manifest construction ────────────────────────────────────────────────────


def _sample_payloads() -> dict[str, dict[str, object]]:
    return {
        "report": {"verdict": "HIT", "strength": 0.81234567},
        "chart": {"lagna": "MESHA", "planets": {"SUN": {"lon": 10.5}}},
        "jre_facts": {"dignity_map": {"SUN": "EXALTED"}},
    }


def test_build_manifest_orders_canonical_stages_first() -> None:
    manifest = build_manifest("v1.0.0-beta", "chart_001_pilot", _sample_payloads())
    ids = manifest.stage_ids()
    assert ids == ("chart", "jre_facts", "report")


def test_build_manifest_deterministic() -> None:
    m1 = build_manifest("v1.0.0-beta", "f", _sample_payloads())
    m2 = build_manifest("v1.0.0-beta", "f", _sample_payloads())
    assert m1 == m2
    assert json.dumps(m1.to_dict(), sort_keys=True) == json.dumps(
        m2.to_dict(), sort_keys=True
    )


def test_build_manifest_requires_payloads() -> None:
    with pytest.raises(ValueError, match="at least one stage"):
        build_manifest("v1.0.0-beta", "f", {})


def test_custom_stage_ids_sort_after_canonical() -> None:
    manifest = build_manifest(
        "v1.0.0-beta",
        "f",
        {"zeta": {"a": 1}, "chart": {"b": 2}, "alpha": {"c": 3}},
    )
    assert manifest.stage_ids() == ("chart", "alpha", "zeta")


def test_engine_version_change_changes_hashes() -> None:
    # engine_version is NOT in the hash preimage (schema_version + stage_id
    # are), but manifests built under different engine versions stay
    # distinct records; hash stability across engine versions is what makes
    # cross-version diffs meaningful.
    m1 = build_manifest("v1.0.0-beta", "f", {"chart": {"x": 1}})
    m2 = build_manifest("v1.0.0-rc1", "f", {"chart": {"x": 1}})
    assert m1.engine_version != m2.engine_version
    assert m1.hash_of("chart") == m2.hash_of("chart")


# ── Serialization round-trip ─────────────────────────────────────────────────


def test_manifest_round_trip() -> None:
    manifest = build_manifest("v1.0.0-beta", "chart_001_pilot", _sample_payloads())
    restored = GoldenStateManifest.from_dict(manifest.to_dict())
    assert restored == manifest


def test_from_dict_rejects_missing_fields() -> None:
    with pytest.raises(ValueError, match="missing field"):
        GoldenStateManifest.from_dict({"schema_version": "1.0.0"})


def test_from_dict_rejects_schema_version_mismatch() -> None:
    data = build_manifest("v1.0.0-beta", "f", _sample_payloads()).to_dict()
    data["schema_version"] = "0.0.1"
    with pytest.raises(ValueError, match="schema mismatch"):
        GoldenStateManifest.from_dict(data)


def test_from_dict_rejects_bad_hash_format() -> None:
    data = build_manifest("v1.0.0-beta", "f", _sample_payloads()).to_dict()
    data["stages"][0]["payload_hash"] = "DEADBEEF"
    with pytest.raises(ValueError, match="64 lowercase hex"):
        GoldenStateManifest.from_dict(data)


def test_from_dict_rejects_malformed_stage_record() -> None:
    data = build_manifest("v1.0.0-beta", "f", _sample_payloads()).to_dict()
    data["stages"][0] = {"stage_id": "chart"}
    with pytest.raises(ValueError, match="malformed stage record"):
        GoldenStateManifest.from_dict(data)


# ── Verification ─────────────────────────────────────────────────────────────


def test_verify_all_passes_on_identical_payloads() -> None:
    payloads = _sample_payloads()
    manifest = build_manifest("v1.0.0-beta", "f", payloads)
    verified = GoldenStateValidator(manifest).verify_all(payloads)
    assert verified == ("chart", "jre_facts", "report")


def test_verify_stage_detects_divergence() -> None:
    manifest = build_manifest("v1.0.0-beta", "f", _sample_payloads())
    drifted = _sample_payloads()
    drifted["chart"]["lagna"] = "VRISHABHA"  # non-determinism crept in
    with pytest.raises(GoldenStateMismatchError, match="stage 'chart'"):
        GoldenStateValidator(manifest).verify_stage("chart", drifted["chart"])


def test_verify_all_reports_first_divergence_in_manifest_order() -> None:
    payloads = _sample_payloads()
    manifest = build_manifest("v1.0.0-beta", "f", payloads)
    drifted = _sample_payloads()
    drifted["report"]["strength"] = 0.9999
    drifted["jre_facts"]["dignity_map"] = {}
    with pytest.raises(GoldenStateMismatchError, match="stage 'jre_facts'"):
        GoldenStateValidator(manifest).verify_all(drifted)


def test_verify_all_rejects_unknown_stage() -> None:
    manifest = build_manifest("v1.0.0-beta", "f", {"chart": {"x": 1}})
    with pytest.raises(KeyError, match="not recorded"):
        GoldenStateValidator(manifest).verify_all({"rogue_stage": {"y": 2}})


def test_partial_verification_skips_missing_stages() -> None:
    payloads = _sample_payloads()
    manifest = build_manifest("v1.0.0-beta", "f", payloads)
    subset = {"chart": payloads["chart"]}
    verified = GoldenStateValidator(manifest).verify_all(subset)
    assert verified == ("chart",)


def test_hash_of_unknown_stage_raises_key_error() -> None:
    manifest = build_manifest("v1.0.0-beta", "f", {"chart": {"x": 1}})
    with pytest.raises(KeyError):
        manifest.hash_of("dasha")


# ── Contract sanity ──────────────────────────────────────────────────────────


def test_canonical_stage_ids_are_ordered() -> None:
    assert CANONICAL_STAGE_IDS == (
        "chart",
        "jre_facts",
        "dasha",
        "yogas",
        "ashtakavarga",
        "gochara",
        "multi_varga",
        "dasha_transit",  # Phase 5E: permissive dasha/transit gate
        "report",
    )


def test_default_schema_version_matches_contract() -> None:
    manifest = build_manifest("v1.0.0-beta", "f", {"chart": {"x": 1}})
    assert manifest.schema_version == GOLDEN_STATE_SCHEMA_VERSION

"""Models + config tests (TEST-PLAN §2 row 1-3, SPEC §5/§16, DC §3-§5).

V1 boundary (frozen): ``ContextConfig`` carries NO candidate-generation
fields; the capability manifest and fact envelope are the V1 accounting
model; ``ContextRequest`` is the canonical request contract with frozen
capability ids, requested-minimum version compatibility, and
``check_capability`` deterministic constraints; ``config/context.toml`` is
authoritative (a missing file fails deterministically);
``compute_deterministic_id`` is the domain-separated content-addressed
identity primitive.
"""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import make_birth, make_planet_state

import context
from context import (
    CAPABILITIES,
    CAPABILITY_IDS,
    CAPABILITY_VERSION,
    CONTEXT_VERSION,
    GOLDEN_VERSION,
    PROVENANCE_STAGES,
    TIME_PRECISION_VALUES,
    CanonicalContext,
    CapabilityDescriptor,
    CapabilityManifest,
    CapabilityState,
    ContextConfig,
    ContextInstantRequest,
    ContextNatalRequest,
    ContextRequest,
    FactEnvelope,
    FactKind,
    check_capability,
    compute_deterministic_id,
    validate,
)
from context.config import load_config
from context.errors import InvalidContextConfigError, InvalidContextRequestError
from jyotish import BodyId


def test_config_defaults() -> None:
    cfg = ContextConfig()
    assert cfg.snapshot_version == "0.1.0"
    assert cfg.default_time_precision == "EXACT"
    assert cfg.house_system == "WHOLE_SIGN"
    assert cfg.tradition_profile is None
    assert cfg.version == CONTEXT_VERSION
    # V1: no candidate-generation fields exist on the config.
    for name in ContextConfig.__dataclass_fields__:
        assert "candidate" not in name.lower()


def test_config_dict_round_trip() -> None:
    cfg = ContextConfig(house_system="EQUAL", default_time_precision="HOUR_KNOWN")
    assert context.config_from_dict(cfg.to_dict()) == cfg


def test_config_invalid_values() -> None:
    with pytest.raises(InvalidContextConfigError):
        ContextConfig(default_time_precision="BOGUS")
    with pytest.raises(InvalidContextConfigError):
        ContextConfig(house_system="BOGUS")
    with pytest.raises(InvalidContextConfigError):
        ContextConfig(tradition_profile="")
    with pytest.raises(InvalidContextConfigError):
        ContextConfig(version="")
    with pytest.raises(InvalidContextConfigError):
        ContextConfig(snapshot_version="")


def test_config_from_dict_validation() -> None:
    with pytest.raises(InvalidContextConfigError):
        ContextConfig.from_dict({"default_time_precision": "BOGUS"})
    with pytest.raises(InvalidContextConfigError):
        ContextConfig.from_dict({"house_system": "BOGUS"})


def test_toml_defaults_match_dataclass(tmp_path) -> None:
    cfg = load_config()
    assert cfg == ContextConfig()
    assert validate(cfg) is cfg


def test_toml_missing_field_is_error(tmp_path) -> None:
    from context.config import DEFAULT_CONFIG_PATH

    assert DEFAULT_CONFIG_PATH.is_file(), "config/context.toml must exist"
    raw = DEFAULT_CONFIG_PATH.read_text(encoding="utf-8")
    stripped = raw.replace("snapshot_version = \"0.1.0\"\n", "")
    path = tmp_path / "context.toml"
    path.write_text(stripped, encoding="utf-8")
    with pytest.raises(InvalidContextConfigError, match="snapshot_version"):
        load_config(path)


def test_toml_missing_file_is_error(tmp_path) -> None:
    """A missing authoritative TOML fails deterministically — no hidden
    fallback defaults (SPEC §5/§22)."""
    with pytest.raises(InvalidContextConfigError, match="missing authoritative"):
        load_config(tmp_path / "does-not-exist.toml")
    # Programmatic config remains valid without the file.
    assert ContextConfig() == ContextConfig(
        snapshot_version="0.1.0", default_time_precision="EXACT", house_system="WHOLE_SIGN"
    )


def test_time_precision_pinned() -> None:
    assert TIME_PRECISION_VALUES == ("EXACT", "HOUR_KNOWN", "DATE_ONLY", "UNKNOWN")


def test_provenance_stages_pinned() -> None:
    assert PROVENANCE_STAGES == (
        "INPUT",
        "ASTRONOMICAL",
        "NORMALIZATION",
        "DERIVED",
        "DOCTRINE_RULE",
        "FUTURE_INFERENCE",
    )


def test_golden_version_pinned() -> None:
    assert GOLDEN_VERSION == "0.1.0"


def test_capability_states() -> None:
    assert CapabilityState.AVAILABLE.value == "AVAILABLE"
    assert CapabilityState.NOT_REQUESTED.value == "NOT_REQUESTED"
    assert CapabilityState.UNAVAILABLE.value == "UNAVAILABLE"


def test_capability_manifest_defaults() -> None:
    manifest = CapabilityManifest()
    for field in manifest.__dataclass_fields__:
        assert getattr(manifest, field) is CapabilityState.NOT_REQUESTED


def test_capability_contract_frozen() -> None:
    assert CAPABILITY_VERSION == "0.1.0"
    assert CAPABILITY_IDS == ("instant", "natal", "interval", "eclipse")
    assert set(CAPABILITIES) == set(CAPABILITY_IDS)
    for capability_id in CAPABILITY_IDS:
        descriptor = CAPABILITIES[capability_id]
        assert isinstance(descriptor, CapabilityDescriptor)
        assert descriptor.id == capability_id
        assert descriptor.version == CAPABILITY_VERSION
        assert descriptor.requires, f"capability {capability_id!r} must declare inputs"


def test_capability_descriptor_requirements() -> None:
    assert CAPABILITIES["instant"].requires == ("instant_utc_iso", "bodies")
    assert CAPABILITIES["natal"].requires == ("birth",)
    assert CAPABILITIES["interval"].requires == ("start_utc_iso", "end_utc_iso", "bodies")
    assert CAPABILITIES["eclipse"].requires == ("start_utc_iso", "end_utc_iso")


def test_canonical_request_is_base_of_wrappers() -> None:
    request = ContextInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z", bodies=(BodyId.SUN,)
    )
    assert isinstance(request, ContextRequest)
    assert request.capability == "instant"
    assert request.capability_version == CAPABILITY_VERSION
    assert request.analysis_request_id is None
    natal = ContextNatalRequest(birth=make_birth())
    assert isinstance(natal, ContextRequest)
    assert natal.capability == "natal"
    assert natal.capability_version == CAPABILITY_VERSION


def test_canonical_request_unknown_capability_rejected() -> None:
    with pytest.raises(InvalidContextRequestError, match="capability"):
        ContextRequest(capability="bogus")
    with pytest.raises(InvalidContextRequestError, match="capability"):
        ContextRequest(capability="")
    with pytest.raises(InvalidContextRequestError, match="capability_version"):
        ContextRequest(capability="instant", capability_version="")


def test_check_capability_version_compatibility() -> None:
    base = dict(instant_utc_iso="2026-06-15T12:00:00.000000Z", bodies=(BodyId.SUN,))
    check_capability(ContextInstantRequest(**base))  # default minimum is compatible
    check_capability(ContextInstantRequest(**base, capability_version="0.0.9"))  # older ok
    with pytest.raises(InvalidContextRequestError, match="version"):
        check_capability(ContextInstantRequest(**base, capability_version="1.0.0"))
    with pytest.raises(InvalidContextRequestError, match="version"):
        check_capability(ContextInstantRequest(**base, capability_version="v1"))


def test_check_capability_missing_required_inputs() -> None:
    """Invalid capability constraints: a bare canonical request cannot serve
    a capability whose required inputs it does not carry."""
    with pytest.raises(InvalidContextRequestError, match="instant_utc_iso"):
        check_capability(ContextRequest(capability="instant"))
    with pytest.raises(InvalidContextRequestError, match="birth"):
        check_capability(ContextRequest(capability="natal"))


def test_fact_kinds() -> None:
    assert FactKind.PLANET_STATE.value == "PLANET_STATE"
    assert FactKind.PAIR_GEOMETRY.value == "PAIR_GEOMETRY"
    assert FactKind.HOUSE_ANALYSIS.value == "HOUSE_ANALYSIS"
    assert FactKind.TRANSIT_EVENT.value == "TRANSIT_EVENT"
    assert FactKind.ECLIPSE_EVENT.value == "ECLIPSE_EVENT"
    assert FactKind.LAGNA_STATE.value == "LAGNA_STATE"


def test_fact_envelope() -> None:
    from context import CanonicalProvenance, ProvenanceStage

    provenance = CanonicalProvenance(
        stages=(ProvenanceStage(stage="INPUT", layer_id="JRE-007"),),
        source_layers=("JRE-007",),
        assembly_algorithm="assemble-instant-v1",
        snapshot_version="0.1.0",
    )
    # payload is the FactKind-keyed lower-layer fact type (typed union),
    # never an unconstrained Any.
    state = make_planet_state()
    envelope = FactEnvelope(
        fact_id=compute_deterministic_id("jre007:fact", {"body": "SUN"}),
        kind=FactKind.PLANET_STATE,
        capability="instant",
        provenance=provenance,
        payload=state,
    )
    assert envelope.kind is FactKind.PLANET_STATE
    assert envelope.payload == state


def test_canonical_context_container() -> None:
    from jyotish import BirthData

    birth = BirthData(
        date="1990-06-15",
        time="10:00:00",
        timezone="Asia/Kolkata",
        latitude=28.6139,
        longitude=77.2090,
    )
    ctx = CanonicalContext(
        context_id="ctx-1",
        analysis_request_id="req-1",
        purpose="natal",
        birth_snapshot=birth,
        configuration=ContextConfig(),
        chart_identity="abc123",
        tradition_profile_identity=None,
        requested_capabilities=CapabilityManifest(),
        source_layers=("JRE-002", "JRE-003"),
    )
    assert ctx.context_id == "ctx-1"
    assert ctx.birth_snapshot == birth
    assert ctx.version == CONTEXT_VERSION


def test_compute_deterministic_id_domain_separated() -> None:
    data = {"bodies": ["SUN", "MOON"], "lon": 5.0}
    a = compute_deterministic_id("jre007:chart", data)
    b = compute_deterministic_id("jre007:chart", data)
    assert a == b  # deterministic
    assert len(a) == 64  # sha256 hex
    other = compute_deterministic_id("jre007:fact", data)
    assert other != a  # domain-separated
    changed = compute_deterministic_id("jre007:chart", {"bodies": ["SUN"]})
    assert changed != a  # content-addressed


def test_invalid_request_error_taxonomy() -> None:
    from context import ContextError, InvalidContextRequestError

    assert issubclass(InvalidContextRequestError, ContextError)
    err = InvalidContextRequestError("boom")
    assert str(err) == "boom"

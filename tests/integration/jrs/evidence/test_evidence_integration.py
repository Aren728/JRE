"""Integration tests for the Evidence framework against the sample fixture."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jrs.evidence.config import load_evidence_config
from jrs.evidence.models import (
    ClassicalSource,
    EvidenceChain,
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
)
from jrs.evidence.serialize import (
    evidence_chain_from_dict,
    evidence_record_from_dict,
    result_to_json,
)
from jrs.evidence.service import EvidenceService

_FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "fixtures" / "evidence"


@pytest.fixture
def marriage_data() -> dict:
    """Load sample_marriage_evidence.json."""
    path = _FIXTURES_DIR / "sample_marriage_evidence.json"
    with path.open() as f:
        return json.load(f)


@pytest.fixture
def svc_with_fixture(marriage_data: dict) -> EvidenceService:
    """Create an EvidenceService pre-loaded with the sample fixture."""
    svc = EvidenceService()
    for ev_data in marriage_data["evidence"]:
        record = evidence_record_from_dict(ev_data)
        svc.register_evidence(record)
    return svc


class TestFixtureLoading:
    """Integration tests for loading the sample fixture."""

    def test_fixture_exists(self) -> None:
        path = _FIXTURES_DIR / "sample_marriage_evidence.json"
        assert path.exists()

    def test_fixture_has_sources(self, marriage_data: dict) -> None:
        assert len(marriage_data["sources"]) == 2

    def test_fixture_has_rules(self, marriage_data: dict) -> None:
        assert len(marriage_data["rules"]) == 2

    def test_fixture_has_evidence(self, marriage_data: dict) -> None:
        assert len(marriage_data["evidence"]) == 4

    def test_fixture_evidence_ids(self, marriage_data: dict) -> None:
        ids = {e["evidence_id"] for e in marriage_data["evidence"]}
        assert ids == {"E-1042", "E-1043", "E-1077", "E-1085"}


class TestFixtureDeserialization:
    """Integration tests for deserializing fixture data."""

    def test_deserialize_sources(self, marriage_data: dict) -> None:
        sources = [ClassicalSource(**s) for s in marriage_data["sources"]]
        assert len(sources) == 2
        assert sources[0].source_id == "BPHS"

    def test_deserialize_records(self, marriage_data: dict) -> None:
        records = [evidence_record_from_dict(e) for e in marriage_data["evidence"]]
        assert len(records) == 4
        ids = {r.evidence_id for r in records}
        assert ids == {"E-1042", "E-1043", "E-1077", "E-1085"}

    def test_record_directions(self, marriage_data: dict) -> None:
        records = [evidence_record_from_dict(e) for e in marriage_data["evidence"]]
        directions = {r.evidence_id: r.direction for r in records}
        assert directions["E-1042"] is EvidenceDirection.SUPPORT
        assert directions["E-1077"] is EvidenceDirection.CONTRADICT
        assert directions["E-1085"] is EvidenceDirection.MITIGATE


class TestEvidenceChainResolution:
    """Integration tests for resolving evidence chains from the fixture."""

    def test_resolve_e1042(
        self,
        svc_with_fixture: EvidenceService,
    ) -> None:
        chain = svc_with_fixture.get_evidence_chain("E-1042")
        assert chain.record.evidence_id == "E-1042"
        assert chain.record.direction is EvidenceDirection.SUPPORT
        assert len(chain.contradictions) == 1
        assert chain.contradictions[0].evidence_id == "E-1077"
        assert len(chain.mitigations) == 1
        assert chain.mitigations[0].evidence_id == "E-1085"

    def test_resolve_e1043(
        self,
        svc_with_fixture: EvidenceService,
    ) -> None:
        chain = svc_with_fixture.get_evidence_chain("E-1043")
        assert chain.record.evidence_id == "E-1043"
        assert len(chain.contradictions) == 0
        assert len(chain.mitigations) == 0

    def test_resolve_e1077(
        self,
        svc_with_fixture: EvidenceService,
    ) -> None:
        chain = svc_with_fixture.get_evidence_chain("E-1077")
        assert chain.record.evidence_id == "E-1077"
        assert chain.record.direction is EvidenceDirection.CONTRADICT
        assert len(chain.contradictions) == 0
        assert len(chain.mitigations) == 1
        assert chain.mitigations[0].evidence_id == "E-1085"
        # E-1042 contradicts E-1077, so E-1042 should be in supporting
        assert len(chain.supporting) == 1
        assert chain.supporting[0].evidence_id == "E-1042"

    def test_resolve_e1085(
        self,
        svc_with_fixture: EvidenceService,
    ) -> None:
        chain = svc_with_fixture.get_evidence_chain("E-1085")
        assert chain.record.evidence_id == "E-1085"
        assert chain.record.direction is EvidenceDirection.MITIGATE
        # E-1085 mitigates both E-1042 and E-1077
        assert len(chain.supporting) == 2
        supporting_ids = {r.evidence_id for r in chain.supporting}
        assert "E-1042" in supporting_ids
        assert "E-1077" in supporting_ids


class TestNoCircularReferences:
    """Integration test: verify the fixture has no circular references."""

    def test_no_cycles(
        self,
        svc_with_fixture: EvidenceService,
    ) -> None:
        cycles = svc_with_fixture.validate_registry()
        assert cycles == []


class TestConfigLoading:
    """Integration tests for config loading."""

    def test_loads_default_config(self) -> None:
        config = load_evidence_config()
        assert config.version == "1.0"
        assert "BPHS" in config.source_weights
        assert config.source_weights["BPHS"] == 1.0

    def test_strength_multipliers_loaded(self) -> None:
        config = load_evidence_config()
        assert "HIGH" in config.strength_multipliers
        assert "MODERATE" in config.strength_multipliers

    def test_max_chain_depth(self) -> None:
        config = load_evidence_config()
        assert config.max_chain_depth == 10


class TestSerializationRoundTrip:
    """Integration tests for serialization round-trip."""

    def test_chain_round_trip(
        self,
        svc_with_fixture: EvidenceService,
    ) -> None:
        chain = svc_with_fixture.get_evidence_chain("E-1042")
        d = chain.to_dict()
        restored = evidence_chain_from_dict(d)
        assert restored.record.evidence_id == "E-1042"
        assert len(restored.contradictions) == len(chain.contradictions)
        assert len(restored.mitigations) == len(chain.mitigations)

    def test_chain_json_serializable(
        self,
        svc_with_fixture: EvidenceService,
    ) -> None:
        chain = svc_with_fixture.get_evidence_chain("E-1042")
        json_str = result_to_json(chain)
        parsed = json.loads(json_str)
        assert parsed["record"]["evidence_id"] == "E-1042"
        assert len(parsed["contradictions"]) == 1

    def test_record_json_serializable(
        self,
        marriage_data: dict,
    ) -> None:
        record = evidence_record_from_dict(marriage_data["evidence"][0])
        json_str = result_to_json(
            EvidenceChain(record=record),
        )
        parsed = json.loads(json_str)
        assert parsed["record"]["evidence_id"] == "E-1042"

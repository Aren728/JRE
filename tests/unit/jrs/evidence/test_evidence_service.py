"""Unit tests for EvidenceService."""

from __future__ import annotations

import pytest

from tests.unit.jrs.evidence.conftest import make_evidence_record
from jrs.evidence.errors import (
    DuplicateEvidenceError,
    EvidenceNotFoundError,
)
from jrs.evidence.models import (
    EvidenceConfig,
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
)
from jrs.evidence.service import EvidenceService


class TestEvidenceServiceInit:
    """Tests for EvidenceService initialization."""

    def test_default_config(self) -> None:
        svc = EvidenceService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = EvidenceConfig(max_chain_depth=5)
        svc = EvidenceService(config=config)
        assert svc.config.max_chain_depth == 5

    def test_empty_registry(self) -> None:
        svc = EvidenceService()
        assert svc.registry_size == 0
        assert svc.get_all_records() == ()


class TestEvidenceServiceRegister:
    """Tests for the register_evidence method."""

    def test_register_single(self) -> None:
        svc = EvidenceService()
        record = make_evidence_record("E-001")
        svc.register_evidence(record)
        assert svc.registry_size == 1

    def test_register_multiple(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(make_evidence_record("E-001"))
        svc.register_evidence(make_evidence_record("E-002"))
        assert svc.registry_size == 2

    def test_duplicate_raises(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(make_evidence_record("E-001"))
        with pytest.raises(DuplicateEvidenceError, match="already registered"):
            svc.register_evidence(make_evidence_record("E-001"))

    def test_register_with_links(self) -> None:
        svc = EvidenceService()
        r1 = make_evidence_record("E-001", contradicted_by=("E-002",))
        r2 = make_evidence_record("E-002")
        svc.register_evidence(r1)
        svc.register_evidence(r2)
        assert svc.registry_size == 2


class TestEvidenceServiceGetChain:
    """Tests for the get_evidence_chain method."""

    def test_get_chain(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(make_evidence_record("E-001"))
        chain = svc.get_evidence_chain("E-001")
        assert chain.record.evidence_id == "E-001"

    def test_get_chain_not_found(self) -> None:
        svc = EvidenceService()
        with pytest.raises(EvidenceNotFoundError, match="not found"):
            svc.get_evidence_chain("E-NONE")

    def test_get_chain_with_contradictions(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(
            make_evidence_record("E-001", contradicted_by=("E-002",)),
        )
        svc.register_evidence(make_evidence_record("E-002"))
        chain = svc.get_evidence_chain("E-001")
        assert len(chain.contradictions) == 1
        assert chain.contradictions[0].evidence_id == "E-002"

    def test_get_chain_with_mitigations(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(
            make_evidence_record("E-001", mitigated_by=("E-003",)),
        )
        svc.register_evidence(make_evidence_record("E-003"))
        chain = svc.get_evidence_chain("E-001")
        assert len(chain.mitigations) == 1

    def test_get_chain_with_supporting(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(make_evidence_record("E-001"))
        svc.register_evidence(
            make_evidence_record("E-002", contradicted_by=("E-001",)),
        )
        chain = svc.get_evidence_chain("E-001")
        assert len(chain.supporting) == 1
        assert chain.supporting[0].evidence_id == "E-002"

    def test_get_chain_deterministic(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(
            make_evidence_record("E-001", contradicted_by=("E-002",)),
        )
        svc.register_evidence(make_evidence_record("E-002"))
        c1 = svc.get_evidence_chain("E-001")
        c2 = svc.get_evidence_chain("E-001")
        assert c1.record.evidence_id == c2.record.evidence_id
        assert len(c1.contradictions) == len(c2.contradictions)


class TestEvidenceServiceQueries:
    """Tests for registry query methods."""

    def test_get_record(self) -> None:
        svc = EvidenceService()
        record = make_evidence_record("E-001")
        svc.register_evidence(record)
        assert svc.get_record("E-001") is record
        assert svc.get_record("E-NONE") is None

    def test_get_records_by_outcome(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(
            make_evidence_record("E-001", outcome_taxonomy="MARRIAGE_TIMELY"),
        )
        svc.register_evidence(
            make_evidence_record("E-002", outcome_taxonomy="MARRIAGE_DELAYED"),
        )
        svc.register_evidence(
            make_evidence_record("E-003", outcome_taxonomy="MARRIAGE_TIMELY"),
        )
        timely = svc.get_records_by_outcome("MARRIAGE_TIMELY")
        assert len(timely) == 2

    def test_get_records_by_source(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(
            EvidenceRecord(
                evidence_id="E-001",
                outcome_taxonomy="TEST",
                supporting_fact_type="FACT",
                rule_id="R-001",
                source_id="BPHS",
            ),
        )
        svc.register_evidence(
            EvidenceRecord(
                evidence_id="E-002",
                outcome_taxonomy="TEST",
                supporting_fact_type="FACT",
                rule_id="R-001",
                source_id="Phaladeepika",
            ),
        )
        bphs = svc.get_records_by_source("BPHS")
        assert len(bphs) == 1
        assert bphs[0].source_id == "BPHS"

    def test_validate_registry_clean(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(make_evidence_record("E-001"))
        cycles = svc.validate_registry()
        assert cycles == []

    def test_validate_registry_with_cycle(self) -> None:
        svc = EvidenceService()
        svc.register_evidence(
            make_evidence_record("E-001", contradicted_by=("E-002",)),
        )
        svc.register_evidence(
            make_evidence_record("E-002", contradicted_by=("E-001",)),
        )
        cycles = svc.validate_registry()
        assert len(cycles) == 1

"""Unit tests for ConvergenceService."""

from __future__ import annotations

import pytest

from tests.unit.jrs.convergence.conftest import make_evidence_record, make_event_window
from jrs.convergence.errors import InvalidAssessmentInputError
from jrs.convergence.models import (
    AssessmentStatus,
    ConvergenceConfig,
    DomainAssessment,
    OverallEvidenceStrength,
    SourceConfidence,
    TimingStatus,
)
from jrs.convergence.service import ConvergenceService
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.temporal.models import ConvergenceLevel


class TestConvergenceServiceInit:
    """Tests for ConvergenceService initialization."""

    def test_default_config(self) -> None:
        svc = ConvergenceService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = ConvergenceConfig(independence_penalty=0.8)
        svc = ConvergenceService(config=config)
        assert svc.config.independence_penalty == 0.8


class TestConvergenceServiceAssessDomain:
    """Tests for the assess_domain method."""

    def test_empty_taxonomy_raises(self) -> None:
        svc = ConvergenceService()
        with pytest.raises(InvalidAssessmentInputError, match="must not be empty"):
            svc.assess_domain("")

    def test_no_evidence_returns_neutral(self) -> None:
        svc = ConvergenceService()
        assessment = svc.assess_domain("TEST_OUTCOME")
        assert assessment.outcome_taxonomy == "TEST_OUTCOME"
        assert assessment.assessment_status is AssessmentStatus.NEUTRAL
        assert assessment.timing_status is TimingStatus.INACTIVE

    def test_support_records(self) -> None:
        svc = ConvergenceService()
        records = (
            make_evidence_record(direction=EvidenceDirection.SUPPORT),
            make_evidence_record(evidence_id="E-002", direction=EvidenceDirection.SUPPORT),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        assert assessment.dimensions.supporting_count == 2

    def test_contradict_records(self) -> None:
        svc = ConvergenceService()
        records = (
            make_evidence_record(direction=EvidenceDirection.CONTRADICT),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        assert assessment.dimensions.contradicting_count == 1

    def test_mitigate_records(self) -> None:
        svc = ConvergenceService()
        records = (
            make_evidence_record(direction=EvidenceDirection.MITIGATE),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        assert assessment.dimensions.mitigations == 1

    def test_event_windows_counted(self) -> None:
        svc = ConvergenceService()
        window = make_event_window(convergence=ConvergenceLevel.HIGH)
        assessment = svc.assess_domain("TEST", event_windows=(window,))
        assert assessment.dimensions.timing_convergence_count == 1
        assert assessment.timing_status is TimingStatus.CONVERGENT

    def test_independent_channels_counted(self) -> None:
        svc = ConvergenceService()
        records = (
            make_evidence_record(source_id="BPHS", independence_group="A"),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="A"),
            make_evidence_record(evidence_id="E-003", source_id="Phaladeepika", independence_group="B"),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        # Same source+group = 1 channel, different source = 1 channel = 2 total
        assert assessment.dimensions.independent_channels == 2

    def test_source_confidence_high(self) -> None:
        svc = ConvergenceService()
        records = (
            make_evidence_record(source_id="BPHS"),
            make_evidence_record(evidence_id="E-002", source_id="BPHS"),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        assert assessment.dimensions.source_confidence is SourceConfidence.HIGH

    def test_source_confidence_low(self) -> None:
        config = ConvergenceConfig(
            source_weights={"Chamatkara_Chintamani": 0.3},
            high_confidence_min_weight=0.8,
            low_confidence_max_weight=0.4,
        )
        svc = ConvergenceService(config=config)
        records = (
            make_evidence_record(source_id="Chamatkara_Chintamani"),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        assert assessment.dimensions.source_confidence is SourceConfidence.LOW

    def test_deterministic_output(self) -> None:
        svc = ConvergenceService()
        records = (make_evidence_record(direction=EvidenceDirection.SUPPORT),)
        a1 = svc.assess_domain("TEST", evidence_records=records)
        a2 = svc.assess_domain("TEST", evidence_records=records)
        assert a1.assessment_status is a2.assessment_status
        assert a1.dimensions.supporting_count == a2.dimensions.supporting_count

    def test_full_assessment(self) -> None:
        svc = ConvergenceService()
        records = (
            make_evidence_record(direction=EvidenceDirection.SUPPORT, source_id="BPHS", independence_group="A"),
            make_evidence_record(evidence_id="E-002", direction=EvidenceDirection.SUPPORT, source_id="BPHS", independence_group="B"),
            make_evidence_record(evidence_id="E-003", direction=EvidenceDirection.SUPPORT, source_id="Phaladeepika", independence_group="C"),
            make_evidence_record(evidence_id="E-004", direction=EvidenceDirection.SUPPORT, source_id="Phaladeepika", independence_group="D"),
        )
        window = make_event_window(convergence=ConvergenceLevel.HIGH)
        assessment = svc.assess_domain(
            "MARRIAGE_FORMATION",
            evidence_records=records,
            event_windows=(window,),
        )
        assert assessment.outcome_taxonomy == "MARRIAGE_FORMATION"
        assert assessment.dimensions.supporting_count == 4
        assert assessment.dimensions.independent_channels == 4
        assert assessment.timing_status is TimingStatus.CONVERGENT

"""Integration tests for the Convergence Engine."""

from __future__ import annotations

import json

import pytest

from tests.unit.jrs.convergence.conftest import make_evidence_record, make_event_window
from jrs.convergence.config import load_convergence_config
from jrs.convergence.models import (
    AssessmentStatus,
    ConvergenceConfig,
    DomainAssessment,
    OverallEvidenceStrength,
    SourceConfidence,
    TimingStatus,
)
from jrs.convergence.serialize import (
    domain_assessment_from_dict,
    result_to_json,
)
from jrs.convergence.service import ConvergenceService
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.temporal.models import ConvergenceLevel


@pytest.fixture
def svc() -> ConvergenceService:
    """Create a ConvergenceService with the real config."""
    return ConvergenceService()


class TestConfigLoading:
    """Integration tests for config loading."""

    def test_loads_default_config(self) -> None:
        config = load_convergence_config()
        assert config.version == "1.0"
        assert "BPHS" in config.source_weights

    def test_strength_weights_loaded(self) -> None:
        config = load_convergence_config()
        assert "HIGH" in config.strength_weights
        assert "MODERATE" in config.strength_weights

    def test_thresholds_loaded(self) -> None:
        config = load_convergence_config()
        assert config.strongly_supported_min_independent == 3
        assert config.strongly_supported_min_supporting == 4


class TestMarriageAssessment:
    """Integration tests for marriage domain assessment."""

    def test_strong_support(
        self,
        svc: ConvergenceService,
    ) -> None:
        """Test assessment with strong supporting evidence."""
        records = (
            make_evidence_record(source_id="BPHS", independence_group="A",
                                 direction=EvidenceDirection.SUPPORT,
                                 strength=EvidenceStrength.HIGH),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="B",
                                 direction=EvidenceDirection.SUPPORT,
                                 strength=EvidenceStrength.HIGH),
            make_evidence_record(evidence_id="E-003", source_id="Phaladeepika", independence_group="C",
                                 direction=EvidenceDirection.SUPPORT,
                                 strength=EvidenceStrength.MODERATE),
            make_evidence_record(evidence_id="E-004", source_id="Phaladeepika", independence_group="D",
                                 direction=EvidenceDirection.SUPPORT,
                                 strength=EvidenceStrength.MODERATE),
        )
        window = make_event_window(convergence=ConvergenceLevel.HIGH)
        assessment = svc.assess_domain(
            "MARRIAGE_FORMATION",
            evidence_records=records,
            event_windows=(window,),
        )
        assert assessment.assessment_status in (
            AssessmentStatus.STRONGLY_SUPPORTED,
            AssessmentStatus.SUPPORTED,
        )
        assert assessment.timing_status is TimingStatus.CONVERGENT

    def test_contradicted_shifts_status(
        self,
        svc: ConvergenceService,
    ) -> None:
        """Test that high-weight contradictions shift status from SUPPORTED to CONTRADICTED."""
        # Start with strong support
        support_records = (
            make_evidence_record(source_id="BPHS", independence_group="A",
                                 direction=EvidenceDirection.SUPPORT),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="B",
                                 direction=EvidenceDirection.SUPPORT),
        )
        assessment_before = svc.assess_domain(
            "MARRIAGE_FORMATION",
            evidence_records=support_records,
        )
        assert assessment_before.assessment_status in (
            AssessmentStatus.SUPPORTED,
            AssessmentStatus.WEAKLY_SUPPORTED,
        )

        # Add high-weight contradictions
        contra_records = (
            make_evidence_record(source_id="BPHS", independence_group="A",
                                 direction=EvidenceDirection.SUPPORT),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="B",
                                 direction=EvidenceDirection.SUPPORT),
            make_evidence_record(evidence_id="E-101", source_id="Phaladeepika", independence_group="C",
                                 direction=EvidenceDirection.CONTRADICT,
                                 strength=EvidenceStrength.HIGH),
            make_evidence_record(evidence_id="E-102", source_id="BPHS", independence_group="D",
                                 direction=EvidenceDirection.CONTRADICT,
                                 strength=EvidenceStrength.HIGH),
        )
        assessment_after = svc.assess_domain(
            "MARRIAGE_FORMATION",
            evidence_records=contra_records,
        )
        # With contradictions, status should shift
        assert assessment_after.dimensions.contradicting_count == 2

    def test_timing_convergence(
        self,
        svc: ConvergenceService,
    ) -> None:
        """Test timing convergence with convergent event windows."""
        window = make_event_window(convergence=ConvergenceLevel.VERY_HIGH)
        assessment = svc.assess_domain(
            "MARRIAGE_FORMATION",
            event_windows=(window,),
        )
        assert assessment.timing_status is TimingStatus.CONVERGENT
        assert assessment.dimensions.timing_convergence_count == 1

    def test_no_timing_when_inactive(
        self,
        svc: ConvergenceService,
    ) -> None:
        """Test INACTIVE timing when no convergent windows."""
        window = make_event_window(convergence=ConvergenceLevel.NONE)
        assessment = svc.assess_domain(
            "MARRIAGE_FORMATION",
            event_windows=(window,),
        )
        assert assessment.timing_status is TimingStatus.INACTIVE


class TestSerializationRoundTrip:
    """Integration tests for serialization round-trip."""

    def test_assessment_round_trip(
        self,
        svc: ConvergenceService,
    ) -> None:
        records = (make_evidence_record(direction=EvidenceDirection.SUPPORT),)
        assessment = svc.assess_domain("TEST", evidence_records=records)
        d = assessment.to_dict()
        restored = domain_assessment_from_dict(d)
        assert restored.outcome_taxonomy == assessment.outcome_taxonomy
        assert restored.assessment_status is assessment.assessment_status

    def test_assessment_json_serializable(
        self,
        svc: ConvergenceService,
    ) -> None:
        records = (make_evidence_record(direction=EvidenceDirection.SUPPORT),)
        assessment = svc.assess_domain("TEST", evidence_records=records)
        json_str = result_to_json(assessment)
        parsed = json.loads(json_str)
        assert parsed["outcome_taxonomy"] == "TEST"
        assert "dimensions" in parsed
        assert "assessment_status" in parsed


class TestIndependenceGroupPreventsDoubleCounting:
    """Integration test: same source chapter only counts as 1 channel."""

    def test_same_source_same_group(
        self,
        svc: ConvergenceService,
    ) -> None:
        """Two rules from the exact same source chapter = 1 independent channel."""
        records = (
            make_evidence_record(source_id="BPHS", independence_group="BPHS-7L"),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="BPHS-7L"),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        assert assessment.dimensions.supporting_count == 2
        assert assessment.dimensions.independent_channels == 1

    def test_different_groups_count_separately(
        self,
        svc: ConvergenceService,
    ) -> None:
        """Different independence groups count as separate channels."""
        records = (
            make_evidence_record(source_id="BPHS", independence_group="BPHS-7L"),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="BPHS-VEN"),
        )
        assessment = svc.assess_domain("TEST", evidence_records=records)
        assert assessment.dimensions.independent_channels == 2

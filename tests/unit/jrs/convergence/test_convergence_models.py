"""Unit tests for convergence engine models and classification logic."""

from __future__ import annotations

import json

import pytest

from tests.unit.jrs.convergence.conftest import make_evidence_record, make_event_window
from jrs.convergence.models import (
    AssessmentStatus,
    ConvergenceConfig,
    DomainAssessment,
    EvidenceDimensions,
    OverallEvidenceStrength,
    SOURCE_CONFIDENCE_VALUES,
    SourceConfidence,
    TimingStatus,
    classify_assessment_status,
    classify_overall_strength,
    classify_timing_status,
    compute_weighted_support_score,
    count_independent_channels,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.temporal.models import ConvergenceLevel


class TestAssessmentStatus:
    """Tests for the AssessmentStatus enum."""

    def test_all_statuses_have_string_values(self) -> None:
        for s in AssessmentStatus:
            assert isinstance(s.value, str)
            assert s.value == s.name

    def test_status_count(self) -> None:
        assert len(AssessmentStatus) == 6

    def test_status_from_value(self) -> None:
        assert AssessmentStatus("SUPPORTED") is AssessmentStatus.SUPPORTED
        assert AssessmentStatus("NEUTRAL") is AssessmentStatus.NEUTRAL

    def test_invalid_status(self) -> None:
        with pytest.raises(ValueError):
            AssessmentStatus("INVALID")


class TestTimingStatus:
    """Tests for the TimingStatus enum."""

    def test_timing_count(self) -> None:
        assert len(TimingStatus) == 3

    def test_timing_from_value(self) -> None:
        assert TimingStatus("CONVERGENT") is TimingStatus.CONVERGENT
        assert TimingStatus("INACTIVE") is TimingStatus.INACTIVE


class TestOverallEvidenceStrength:
    """Tests for the OverallEvidenceStrength enum."""

    def test_strength_count(self) -> None:
        assert len(OverallEvidenceStrength) == 3

    def test_strength_from_value(self) -> None:
        assert OverallEvidenceStrength("STRONG") is OverallEvidenceStrength.STRONG
        assert OverallEvidenceStrength("WEAK") is OverallEvidenceStrength.WEAK


class TestSourceConfidence:
    """Tests for the SourceConfidence enum."""

    def test_confidence_count(self) -> None:
        assert len(SourceConfidence) == 3

    def test_confidence_values(self) -> None:
        assert SOURCE_CONFIDENCE_VALUES[SourceConfidence.HIGH] == 1.0
        assert SOURCE_CONFIDENCE_VALUES[SourceConfidence.LOW] == 0.3


class TestEvidenceDimensions:
    """Tests for the EvidenceDimensions model."""

    def test_creation(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=3,
            independent_channels=2,
            contradicting_count=1,
        )
        assert dims.supporting_count == 3
        assert dims.independent_channels == 2
        assert dims.contradicting_count == 1

    def test_defaults(self) -> None:
        dims = EvidenceDimensions()
        assert dims.supporting_count == 0
        assert dims.source_confidence is SourceConfidence.MODERATE

    def test_frozen(self) -> None:
        dims = EvidenceDimensions(supporting_count=1)
        with pytest.raises(AttributeError):
            dims.supporting_count = 2  # type: ignore[misc]

    def test_to_dict(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=3,
            independent_channels=2,
            source_confidence=SourceConfidence.HIGH,
        )
        d = dims.to_dict()
        assert d["supporting_count"] == 3
        assert d["source_confidence"] == "HIGH"

    def test_to_dict_deterministic(self) -> None:
        dims = EvidenceDimensions(supporting_count=1)
        d1 = dims.to_dict()
        d2 = dims.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestCountIndependentChannels:
    """Tests for the count_independent_channels function."""

    def test_no_records(self) -> None:
        assert count_independent_channels(()) == 0

    def test_single_record(self) -> None:
        records = (make_evidence_record(independence_group="GRP-1"),)
        assert count_independent_channels(records) == 1

    def test_same_source_same_group(self) -> None:
        """Two records from same source+group should count as 1 channel."""
        records = (
            make_evidence_record(source_id="BPHS", independence_group="GRP-1"),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="GRP-1"),
        )
        assert count_independent_channels(records) == 1

    def test_same_source_different_group(self) -> None:
        """Two records from same source but different groups count as 2."""
        records = (
            make_evidence_record(source_id="BPHS", independence_group="GRP-1"),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="GRP-2"),
        )
        assert count_independent_channels(records) == 2

    def test_different_source_same_group(self) -> None:
        """Two records from different sources but same group count as 2."""
        records = (
            make_evidence_record(source_id="BPHS", independence_group="GRP-1"),
            make_evidence_record(evidence_id="E-002", source_id="Phaladeepika", independence_group="GRP-1"),
        )
        assert count_independent_channels(records) == 2

    def test_multiple_records(self) -> None:
        records = (
            make_evidence_record(source_id="BPHS", independence_group="A"),
            make_evidence_record(evidence_id="E-002", source_id="BPHS", independence_group="A"),
            make_evidence_record(evidence_id="E-003", source_id="BPHS", independence_group="B"),
            make_evidence_record(evidence_id="E-004", source_id="Phaladeepika", independence_group="C"),
        )
        # (BPHS,A), (BPHS,B), (Phaladeepika,C) = 3 channels
        assert count_independent_channels(records) == 3


class TestComputeWeightedSupportScore:
    """Tests for the compute_weighted_support_score function."""

    def test_no_records(self) -> None:
        assert compute_weighted_support_score(()) == 0.0

    def test_single_record(self) -> None:
        records = (make_evidence_record(strength=EvidenceStrength.HIGH, source_id="BPHS"),)
        score = compute_weighted_support_score(
            records,
            strength_weights={"HIGH": 0.8},
            source_weights={"BPHS": 1.0},
        )
        assert abs(score - 0.8) < 0.01

    def test_multiple_records(self) -> None:
        records = (
            make_evidence_record(strength=EvidenceStrength.HIGH, source_id="BPHS"),
            make_evidence_record(evidence_id="E-002", strength=EvidenceStrength.MODERATE, source_id="BPHS"),
        )
        score = compute_weighted_support_score(
            records,
            strength_weights={"HIGH": 0.8, "MODERATE": 0.6},
            source_weights={"BPHS": 1.0},
        )
        # 0.8*1.0 + 0.6*1.0 = 1.4
        assert abs(score - 1.4) < 0.01


class TestClassifyAssessmentStatus:
    """Tests for the classify_assessment_status function."""

    def test_neutral_when_empty(self) -> None:
        dims = EvidenceDimensions()
        assert classify_assessment_status(dims) is AssessmentStatus.NEUTRAL

    def test_weakly_supported(self) -> None:
        dims = EvidenceDimensions(supporting_count=1)
        assert classify_assessment_status(dims) is AssessmentStatus.WEAKLY_SUPPORTED

    def test_supported(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=3,
            independent_channels=2,
        )
        assert classify_assessment_status(dims) is AssessmentStatus.SUPPORTED

    def test_strongly_supported(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=5,
            independent_channels=3,
        )
        assert classify_assessment_status(dims) is AssessmentStatus.STRONGLY_SUPPORTED

    def test_contradicted(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=1,
            independent_channels=1,
            contradicting_count=2,
        )
        assert classify_assessment_status(dims) is AssessmentStatus.CONTRADICTED

    def test_strongly_contradicted(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=1,
            contradicting_count=3,
        )
        assert classify_assessment_status(dims) is AssessmentStatus.STRONGLY_CONTRADICTED

    def test_contradicted_overrides_supported_when_equal(self) -> None:
        """When supporting == contradicting, contradiction wins."""
        dims = EvidenceDimensions(
            supporting_count=2,
            independent_channels=2,
            contradicting_count=2,
        )
        assert classify_assessment_status(dims) is AssessmentStatus.CONTRADICTED

    def test_custom_config(self) -> None:
        config = ConvergenceConfig(
            supported_min_independent=1,
            supported_min_supporting=1,
        )
        dims = EvidenceDimensions(supporting_count=1, independent_channels=1)
        assert classify_assessment_status(dims, config) is AssessmentStatus.SUPPORTED


class TestClassifyTimingStatus:
    """Tests for the classify_timing_status function."""

    def test_inactive_when_zero(self) -> None:
        assert classify_timing_status(0) is TimingStatus.INACTIVE

    def test_convergent_when_one(self) -> None:
        assert classify_timing_status(1) is TimingStatus.CONVERGENT

    def test_convergent_when_many(self) -> None:
        assert classify_timing_status(5) is TimingStatus.CONVERGENT


class TestClassifyOverallStrength:
    """Tests for the classify_overall_strength function."""

    def test_weak_when_empty(self) -> None:
        dims = EvidenceDimensions()
        assert classify_overall_strength(dims) is OverallEvidenceStrength.WEAK

    def test_moderate(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=2,
            independent_channels=2,
        )
        assert classify_overall_strength(dims) is OverallEvidenceStrength.MODERATE

    def test_strong(self) -> None:
        dims = EvidenceDimensions(
            supporting_count=5,
            independent_channels=4,
            source_confidence=SourceConfidence.HIGH,
        )
        assert classify_overall_strength(dims) is OverallEvidenceStrength.STRONG

    def test_contradiction_reduces_strength(self) -> None:
        # Without contradictions: strong
        dims_no_contra = EvidenceDimensions(
            supporting_count=5,
            independent_channels=4,
            contradicting_count=0,
            source_confidence=SourceConfidence.HIGH,
        )
        strength_no_contra = classify_overall_strength(dims_no_contra)

        # With contradictions: should be equal or lower
        dims_with_contra = EvidenceDimensions(
            supporting_count=5,
            independent_channels=4,
            contradicting_count=3,
            source_confidence=SourceConfidence.HIGH,
        )
        strength_with_contra = classify_overall_strength(dims_with_contra)

        # Contradictions should reduce or maintain the strength level
        assert strength_with_contra.value <= strength_no_contra.value


class TestDomainAssessment:
    """Tests for the DomainAssessment model."""

    def test_creation(self) -> None:
        assessment = DomainAssessment(
            outcome_taxonomy="TEST",
            assessment_status=AssessmentStatus.SUPPORTED,
        )
        assert assessment.outcome_taxonomy == "TEST"
        assert assessment.assessment_status is AssessmentStatus.SUPPORTED

    def test_frozen(self) -> None:
        assessment = DomainAssessment(outcome_taxonomy="TEST")
        with pytest.raises(AttributeError):
            assessment.outcome_taxonomy = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        assessment = DomainAssessment(
            outcome_taxonomy="TEST",
            timing_status=TimingStatus.CONVERGENT,
            overall_evidence_strength=OverallEvidenceStrength.STRONG,
        )
        d = assessment.to_dict()
        assert d["outcome_taxonomy"] == "TEST"
        assert d["timing_status"] == "CONVERGENT"
        assert d["overall_evidence_strength"] == "STRONG"

    def test_to_dict_deterministic(self) -> None:
        assessment = DomainAssessment(outcome_taxonomy="TEST")
        d1 = assessment.to_dict()
        d2 = assessment.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

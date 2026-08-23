"""Test fixtures for JRS-064 Rectification Integration."""

from __future__ import annotations

import pytest

from jrs.convergence.models import (
    AssessmentStatus,
    DomainAssessment,
    EvidenceDimensions,
    OverallEvidenceStrength,
    SourceConfidence,
    TimingStatus,
)
from jrs.rectification.models import KnownEvent

# ── KnownEvent Factories ─────────────────────────────────────────────────────


@pytest.fixture()
def marriage_known_event() -> KnownEvent:
    """A known marriage event with expected SUPPORTED status."""
    return KnownEvent(
        event_description="Marriage in June 2015",
        domain_label="MARRIAGE",
        expected_outcome="MARRIAGE_FORMATION",
        expected_assessment_status="SUPPORTED",
        expected_timing_status="CONVERGENT",
    )


@pytest.fixture()
def career_known_event() -> KnownEvent:
    """A known career event with expected STRONGLY_SUPPORTED status."""
    return KnownEvent(
        event_description="Promotion in March 2018",
        domain_label="CAREER",
        expected_outcome="CAREER_ADVANCEMENT",
        expected_assessment_status="STRONGLY_SUPPORTED",
        expected_timing_status="CONVERGENT",
    )


@pytest.fixture()
def wealth_known_event() -> KnownEvent:
    """A known wealth event with expected WEAKLY_SUPPORTED status."""
    return KnownEvent(
        event_description="Financial loss in 2020",
        domain_label="WEALTH",
        expected_outcome="SUDDEN_FINANCIAL_LOSS",
        expected_assessment_status="WEAKLY_SUPPORTED",
        expected_timing_status="CONVERGENT",
    )


# ── DomainAssessment Factories ──────────────────────────────────────────────


@pytest.fixture()
def marriage_assessment_supported() -> DomainAssessment:
    """A marriage assessment with SUPPORTED status — matches ground truth."""
    return DomainAssessment(
        outcome_taxonomy="MARRIAGE_FORMATION",
        dimensions=EvidenceDimensions(
            supporting_count=3,
            independent_channels=2,
            contradicting_count=0,
            mitigations=0,
            timing_convergence_count=1,
            source_confidence=SourceConfidence.HIGH,
        ),
        assessment_status=AssessmentStatus.SUPPORTED,
        timing_status=TimingStatus.CONVERGENT,
        overall_evidence_strength=OverallEvidenceStrength.MODERATE,
    )


@pytest.fixture()
def marriage_assessment_neutral() -> DomainAssessment:
    """A marriage assessment with NEUTRAL status — poor match."""
    return DomainAssessment(
        outcome_taxonomy="MARRIAGE_FORMATION",
        dimensions=EvidenceDimensions(
            supporting_count=0,
            independent_channels=0,
            contradicting_count=1,
            mitigations=0,
            timing_convergence_count=0,
            source_confidence=SourceConfidence.LOW,
        ),
        assessment_status=AssessmentStatus.NEUTRAL,
        timing_status=TimingStatus.INACTIVE,
        overall_evidence_strength=OverallEvidenceStrength.WEAK,
    )


@pytest.fixture()
def career_assessment_strongly_supported() -> DomainAssessment:
    """A career assessment with STRONGLY_SUPPORTED status."""
    return DomainAssessment(
        outcome_taxonomy="CAREER_ADVANCEMENT",
        dimensions=EvidenceDimensions(
            supporting_count=5,
            independent_channels=4,
            contradicting_count=0,
            mitigations=0,
            timing_convergence_count=2,
            source_confidence=SourceConfidence.HIGH,
        ),
        assessment_status=AssessmentStatus.STRONGLY_SUPPORTED,
        timing_status=TimingStatus.CONVERGENT,
        overall_evidence_strength=OverallEvidenceStrength.STRONG,
    )


@pytest.fixture()
def career_assessment_weak() -> DomainAssessment:
    """A career assessment with WEAKLY_SUPPORTED status — poor match."""
    return DomainAssessment(
        outcome_taxonomy="CAREER_ADVANCEMENT",
        dimensions=EvidenceDimensions(
            supporting_count=1,
            independent_channels=1,
            contradicting_count=2,
            mitigations=0,
            timing_convergence_count=0,
            source_confidence=SourceConfidence.LOW,
        ),
        assessment_status=AssessmentStatus.WEAKLY_SUPPORTED,
        timing_status=TimingStatus.INACTIVE,
        overall_evidence_strength=OverallEvidenceStrength.WEAK,
    )


@pytest.fixture()
def wealth_assessment_weakly_supported() -> DomainAssessment:
    """A wealth assessment with WEAKLY_SUPPORTED status — matches ground truth."""
    return DomainAssessment(
        outcome_taxonomy="SUDDEN_FINANCIAL_LOSS",
        dimensions=EvidenceDimensions(
            supporting_count=1,
            independent_channels=1,
            contradicting_count=0,
            mitigations=0,
            timing_convergence_count=1,
            source_confidence=SourceConfidence.MODERATE,
        ),
        assessment_status=AssessmentStatus.WEAKLY_SUPPORTED,
        timing_status=TimingStatus.CONVERGENT,
        overall_evidence_strength=OverallEvidenceStrength.WEAK,
    )


@pytest.fixture()
def wealth_assessment_contradicted() -> DomainAssessment:
    """A wealth assessment with CONTRADICTED status — wrong outcome."""
    return DomainAssessment(
        outcome_taxonomy="WEALTH_ACCUMULATION",
        dimensions=EvidenceDimensions(
            supporting_count=0,
            independent_channels=0,
            contradicting_count=3,
            mitigations=0,
            timing_convergence_count=0,
            source_confidence=SourceConfidence.LOW,
        ),
        assessment_status=AssessmentStatus.CONTRADICTED,
        timing_status=TimingStatus.INACTIVE,
        overall_evidence_strength=OverallEvidenceStrength.WEAK,
    )


# ── Composite Pipeline Outputs ───────────────────────────────────────────────


@pytest.fixture()
def good_pipeline_output(
    marriage_assessment_supported: DomainAssessment,
    career_assessment_strongly_supported: DomainAssessment,
) -> dict[str, DomainAssessment]:
    """Pipeline output for a well-rectified birth time (low mismatch)."""
    return {
        "MARRIAGE": marriage_assessment_supported,
        "CAREER": career_assessment_strongly_supported,
    }


@pytest.fixture()
def poor_pipeline_output(
    marriage_assessment_neutral: DomainAssessment,
    career_assessment_weak: DomainAssessment,
) -> dict[str, DomainAssessment]:
    """Pipeline output for a poorly-rectified birth time (high mismatch)."""
    return {
        "MARRIAGE": marriage_assessment_neutral,
        "CAREER": career_assessment_weak,
    }


@pytest.fixture()
def mixed_pipeline_output(
    marriage_assessment_supported: DomainAssessment,
    career_assessment_weak: DomainAssessment,
) -> dict[str, DomainAssessment]:
    """Pipeline output with mixed quality — some match, some don't."""
    return {
        "MARRIAGE": marriage_assessment_supported,
        "CAREER": career_assessment_weak,
    }

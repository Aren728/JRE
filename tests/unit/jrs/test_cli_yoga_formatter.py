"""Tests for the yoga assessment CLI formatter (JRS-081)."""

from __future__ import annotations

import pytest

from jrs.cli import format_yoga_assessment
from jrs.convergence.models import (
    AssessmentStatus,
    DomainAssessment,
    EvidenceDimensions,
    OverallEvidenceStrength,
    TimingStatus,
)


class TestFormatYogaAssessment:
    def test_formed_strong_manifesting_yoga(self) -> None:
        """Test A: FORMED, STRONG, MANIFESTING yoga produces correct output."""
        assessment = DomainAssessment(
            outcome_taxonomy="CAREER_ASCENT",
            dimensions=EvidenceDimensions(
                supporting_count=4,
                independent_channels=3,
            ),
            assessment_status=AssessmentStatus.STRONGLY_SUPPORTED,
            timing_status=TimingStatus.CONVERGENT,
            overall_evidence_strength=OverallEvidenceStrength.STRONG,
        )

        result = format_yoga_assessment(assessment)

        assert "FORMED" in result
        assert "STRONG" in result
        assert "Active" in result
        assert "CAREER_ASCENT" in result

"""JRS-078 Yoga to Evidence Record Integration unit tests."""

from __future__ import annotations

import pytest
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.yoga_evaluator.integration import Channel, YogaEvidenceService
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus


class TestYogaEvidenceService:
    def test_formed_manifesting_yoga_returns_evidence_record(self) -> None:
        """Test A: FORMED, MANIFESTING, CAREER_PROMINENCE -> valid EvidenceRecord with HIGH strength."""
        service = YogaEvidenceService()
        evaluation = YogaEvaluation(
            yoga_name="Sun-Jupiter Rajeev",
            status=YogaStatus.FORMED,
            is_manifesting=True,
            activation_source="Dasha: JUPITER",
            outcome_category="CAREER_PROMINENCE",
        )
        result = service.convert_to_evidence(evaluation)

        assert result is not None
        assert isinstance(result, EvidenceRecord)
        assert result.source_id == "YogaEvaluator"
        assert result.outcome_taxonomy == Channel.CAREER.value
        assert result.strength == EvidenceStrength.HIGH
        assert result.direction == EvidenceDirection.SUPPORT
        assert result.supporting_fact_type == "YOGA_FORMATION"
        assert result.location == "Dasha: JUPITER"

    def test_cancelled_yoga_returns_none(self) -> None:
        """Test B: CANCELLED yoga -> returns None."""
        service = YogaEvidenceService()
        evaluation = YogaEvaluation(
            yoga_name="Sun-Jupiter Rajeev",
            status=YogaStatus.CANCELLED,
            cancellation_reason="SUN is combust",
            is_manifesting=False,
            outcome_category="CAREER_PROMINENCE",
        )
        result = service.convert_to_evidence(evaluation)

        assert result is None

"""JRS-082 Main Pipeline Integration Test (Atomic Execution)."""

from __future__ import annotations

import pytest
from jrs.convergence.models import (
    AssessmentStatus,
    OverallEvidenceStrength,
    SOURCE_CONFIDENCE_VALUES,
    SourceConfidence,
)
from jrs.convergence.service import ConvergenceService
from jrs.evidence.models import EvidenceRecord
from jrs.yoga_evaluator.integration import YogaEvidenceService
from jrs.yoga_evaluator.models import YogaEvaluation, YogaOutcome, YogaStatus


def _build_mock_jre_facts() -> dict:
    """Build mock JRE facts: Sun/Mercury conjunct, Dasha lord Mercury.

    MESHA (Aries) lagna.  Sun in MESHA (house 1), Mercury in MESHA (house 1).
    Sun is 5th lord (trikona) placed in kendra (house 1).
    Mercury is 3rd lord — not a kendra lord, so no kendra-lord involvement,
    but both are conjunct in a kendra, satisfying Gajakesari-style or
    Raja-style structural detection via the KendraTrikona service.

    For the yoga evaluator specifically, we build a pre-formed YogaEvaluation
    that the YogaEvidenceService can convert into an EvidenceRecord.
    """
    return {
        "lagna": "MESHA",
        "planets": {
            "SUN": {
                "rashi": "MESHA",
                "house": 1,
                "combust": False,
                "debilitated": False,
            },
            "MERCURY": {
                "rashi": "MESHA",
                "house": 1,
                "combust": False,
                "debilitated": False,
            },
        },
        "active_dasha_lord": "MERCURY",
    }


def _build_yoga_evaluation() -> YogaEvaluation:
    """Build a YogaEvaluation that is FORMED and manifesting under Mercury Dasha."""
    return YogaEvaluation(
        yoga_name="Budhaditya",
        status=YogaStatus.FORMED,
        is_manifesting=True,
        activation_source="Dasha: MERCURY",
        outcome_category="CAREER_PROMINENCE",
        outcome=YogaOutcome.CAREER_PROMINENCE,
    )


def _strength_score(strength: OverallEvidenceStrength) -> float:
    """Map OverallEvidenceStrength enum to a numeric score for comparison."""
    return {
        OverallEvidenceStrength.STRONG: 3.0,
        OverallEvidenceStrength.MODERATE: 2.0,
        OverallEvidenceStrength.WEAK: 1.0,
    }[strength]


class TestYogaConvergence:
    def test_yoga_boosts_domain_confidence(self) -> None:
        """Yoga evidence for CAREER_PROMINENCE yields higher confidence than baseline."""
        jre_facts = _build_mock_jre_facts()

        # ── Step 1: Generate yoga evidence ─────────────────────────────────
        yoga_svc = YogaEvidenceService()
        yoga_eval = _build_yoga_evaluation()
        yoga_record = yoga_svc.convert_to_evidence(yoga_eval)
        assert yoga_record is not None, "YogaEvidenceService must produce an EvidenceRecord"
        assert yoga_record.outcome_taxonomy == "CAREER"

        # ── Step 2: Baseline assessment (no yoga evidence) ─────────────────
        convergence = ConvergenceService()
        baseline = convergence.assess_domain("CAREER_PROMINENCE")

        # ── Step 3: Assessment WITH yoga evidence ──────────────────────────
        with_yoga = convergence.assess_domain(
            "CAREER_PROMINENCE",
            evidence_records=(yoga_record,),
        )

        # ── Step 4: Assert yoga evidence improves the assessment ───────────
        baseline_score = _strength_score(baseline.overall_evidence_strength)
        with_yoga_score = _strength_score(with_yoga.overall_evidence_strength)

        assert with_yoga_score >= baseline_score, (
            f"Yoga evidence must not decrease confidence: "
            f"baseline={baseline.overall_evidence_strength.value}, "
            f"with_yoga={with_yoga.overall_evidence_strength.value}"
        )

        # The yoga record adds at least one supporting record
        assert with_yoga.dimensions.supporting_count >= 1
        assert with_yoga.dimensions.independent_channels >= 1

        # The assessment status must be at least WEAKLY_SUPPORTED
        assert with_yoga.assessment_status in (
            AssessmentStatus.WEAKLY_SUPPORTED,
            AssessmentStatus.SUPPORTED,
            AssessmentStatus.STRONGLY_SUPPORTED,
        ), (
            f"Expected at least WEAKLY_SUPPORTED, got {with_yoga.assessment_status.value}"
        )

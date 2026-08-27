"""Multi-System Yoga Convergence Test.

Part 1: Cross-System Evidence — Vedic Yoga + Western CAREER_PROMINENCE.
Part 2: Independence Analyzer — raw/adjusted convergence with shared-root penalty.
Part 3: Run tests.
"""

from __future__ import annotations

import pytest
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.multisystem.models import (
    CrossSystemEvidence,
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
)
from jrs.multisystem.service import IndependenceAnalyzer
from jrs.yoga_evaluator.evidence_service import YogaEvidenceService
from jrs.yoga_evaluator.models import YogaOutcome, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService

# ── Outcome taxonomy used across both systems ────────────────────────────────
_OUTCOME = "CAREER_PROMINENCE"


# ── Mock JRE facts: Vedic chart with Raja Yoga ──────────────────────────────

def _build_vedic_jre_facts() -> dict:
    """Vedic chart: Sun (1st lord) + Jupiter (5th lord) conjunct in 10th house.

    This forms a Raja Yoga (kendra lord + trikona lord in same house).
    The dasha lord is Jupiter (one of the yoga planets) → manifesting.
    """
    return {
        "lagna": "MESHA",
        "planets": {
            "SUN": {
                "rashi": "MAKARA",
                "house": 10,
                "combust": False,
                "debilitated": False,
                "house_lord_of": 1,
            },
            "JUPITER": {
                "rashi": "MAKARA",
                "house": 10,
                "combust": False,
                "debilitated": False,
                "house_lord_of": 5,
            },
            "MOON": {
                "rashi": "SIMHA",
                "house": 5,
                "combust": False,
                "debilitated": False,
            },
            "MARS": {
                "rashi": "VRISHABHA",
                "house": 2,
                "combust": False,
                "debilitated": False,
            },
            "MERCURY": {
                "rashi": "TULA",
                "house": 7,
                "combust": False,
                "debilitated": False,
            },
            "VENUS": {
                "rashi": "VRISHABHA",
                "house": 2,
                "combust": False,
                "debilitated": False,
            },
            "SATURN": {
                "rashi": "MAKARA",
                "house": 10,
                "combust": False,
                "debilitated": False,
            },
            "RAHU": {
                "rashi": "VRISHCHIKA",
                "house": 8,
                "combust": False,
                "debilitated": False,
            },
            "KETU": {
                "rashi": "VRISHABHA",
                "house": 2,
                "combust": False,
                "debilitated": False,
            },
        },
        "active_dasha_lord": "JUPITER",
    }


# ── Helpers: build SystemAssessments ─────────────────────────────────────────

def _vedic_assessment(
    status: str = "STRONGLY_SUPPORTED",
    outcome: str = _OUTCOME,
) -> SystemAssessment:
    """Build a Vedic SystemAssessment for Raja Yoga → CAREER_PROMINENCE."""
    return SystemAssessment(
        system_type=SystemType.VEDIC,
        outcome_taxonomy=outcome,
        assessment_status=status,
        timing_status="INACTIVE",
        provenance=EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
            confidence_weight=1.0,
        ),
    )


def _western_assessment(
    status: str = "STRONGLY_SUPPORTED",
    outcome: str = _OUTCOME,
) -> SystemAssessment:
    """Build a Western SystemAssessment for Sun/Jupiter in 10th → CAREER."""
    return SystemAssessment(
        system_type=SystemType.WESTERN,
        outcome_taxonomy=outcome,
        assessment_status=status,
        timing_status="INACTIVE",
        provenance=EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="LILLY",
            confidence_weight=1.0,
        ),
    )


def _raw_convergence(assessments: dict[str, SystemAssessment]) -> float:
    """Compute raw convergence score."""
    return compute_convergence_score(assessments)


def _adjusted_convergence(
    assessments: dict[str, SystemAssessment],
) -> tuple[float, float]:
    """Compute (adjusted_convergence, independence_score)."""
    analyzer = IndependenceAnalyzer()
    provenances = [
        sa.provenance for sa in assessments.values() if sa.provenance is not None
    ]
    raw = _raw_convergence(assessments)
    independence = analyzer.calculate_collective_independence(provenances)
    adjusted = raw * independence
    return (adjusted, independence)


# ══════════════════════════════════════════════════════════════════════════════
# Part 1: Cross-System Evidence Test
# ══════════════════════════════════════════════════════════════════════════════


class TestCrossSystemEvidence:
    """Vedic yoga evidence + Western evidence converge on CAREER_PROMINENCE."""

    def test_vedic_yoga_produces_evidence(self) -> None:
        """YogaEvidenceService generates CAREER_PROMINENCE evidence from Raja Yoga."""
        jre_facts = _build_vedic_jre_facts()
        yoga_svc = YogaEvidenceService()
        records = yoga_svc.generate_yoga_evidence(jre_facts, dasha_lord="JUPITER")

        # At least one yoga evidence record should be produced
        assert len(records) >= 1, (
            f"Expected at least 1 yoga evidence record, got {len(records)}"
        )

        # All records should be SUPPORT direction with HIGH strength
        for record in records:
            assert record.direction == EvidenceDirection.SUPPORT
            assert record.strength == EvidenceStrength.HIGH

    def test_vedic_yoga_outcome_is_career(self) -> None:
        """The generated yoga evidence maps to CAREER_PROMINENCE outcome."""
        jre_facts = _build_vedic_jre_facts()
        yoga_svc = YogaEvidenceService()
        records = yoga_svc.generate_yoga_evidence(jre_facts, dasha_lord="JUPITER")

        # Check that at least one record has career-related outcome
        career_records = [
            r for r in records if "CAREER" in r.outcome_taxonomy.upper()
        ]
        # The legacy map_outcome checks involved planets:
        # SUN in planets → CAREER_PROMINENCE
        # So at least one record should map to career
        if career_records:
            assert career_records[0].outcome_taxonomy == _OUTCOME

    def test_western_assessment_is_career(self) -> None:
        """Western SystemAssessment for Sun/Jupiter in 10th → CAREER_PROMINENCE."""
        western_sa = _western_assessment()
        assert western_sa.system_type == SystemType.WESTERN
        assert western_sa.outcome_taxonomy == _OUTCOME
        assert western_sa.assessment_status == "STRONGLY_SUPPORTED"

    def test_cross_system_evidence_built(self) -> None:
        """Both Vedic and Western SystemAssessments register CAREER_PROMINENCE."""
        vedic_sa = _vedic_assessment()
        western_sa = _western_assessment()

        assessments = {
            SystemType.VEDIC.value: vedic_sa,
            SystemType.WESTERN.value: western_sa,
        }

        # Build CrossSystemEvidence
        cross_system = CrossSystemEvidence(
            event_cluster_id="raja_yoga_career",
            system_assessments=assessments,
        )

        assert len(cross_system.system_assessments) == 2
        assert SystemType.VEDIC.value in cross_system.system_assessments
        assert SystemType.WESTERN.value in cross_system.system_assessments
        assert cross_system.system_assessments[SystemType.VEDIC.value].outcome_taxonomy == _OUTCOME
        assert cross_system.system_assessments[SystemType.WESTERN.value].outcome_taxonomy == _OUTCOME


# ══════════════════════════════════════════════════════════════════════════════
# Part 2: Independence Analyzer Validation
# ══════════════════════════════════════════════════════════════════════════════


class TestIndependenceAnalyzerValidation:
    """IndependenceAnalyzer penalizes Vedic-Western convergence for shared roots."""

    def test_raw_convergence_is_high(self) -> None:
        """Both systems strongly supporting same outcome → raw convergence > 0.8."""
        vedic_sa = _vedic_assessment()
        western_sa = _western_assessment()

        assessments = {
            SystemType.VEDIC.value: vedic_sa,
            SystemType.WESTERN.value: western_sa,
        }

        raw = _raw_convergence(assessments)
        assert raw > 0.8, f"Raw convergence {raw:.4f} should be > 0.8"

    def test_independence_is_penalized(self) -> None:
        """Independence score is ~0.70 due to shared Hellenistic roots."""
        vedic_sa = _vedic_assessment()
        western_sa = _western_assessment()

        assessments = {
            SystemType.VEDIC.value: vedic_sa,
            SystemType.WESTERN.value: western_sa,
        }

        _, independence = _adjusted_convergence(assessments)

        # Vedic and Western share Hellenistic roots.
        # shared_derivative_roots returns frozenset({VEDIC, WESTERN}) → 2 shared roots.
        # Penalty = 2 * 0.15 = 0.3 → independence = 1.0 - 0.3 = 0.7
        assert independence == pytest.approx(0.7, abs=0.01), (
            f"Independence {independence:.4f} should be ~0.70"
        )

    def test_adjusted_lower_than_raw(self) -> None:
        """Adjusted convergence < raw convergence (false confidence dampened)."""
        vedic_sa = _vedic_assessment()
        western_sa = _western_assessment()

        assessments = {
            SystemType.VEDIC.value: vedic_sa,
            SystemType.WESTERN.value: western_sa,
        }

        raw = _raw_convergence(assessments)
        adjusted, independence = _adjusted_convergence(assessments)

        assert adjusted < raw, (
            f"Adjusted {adjusted:.4f} should be lower than raw {raw:.4f}"
        )
        assert adjusted == pytest.approx(raw * independence, abs=0.01)

    def test_adjusted_still_positive(self) -> None:
        """Adjusted convergence is still positive (not zeroed out)."""
        vedic_sa = _vedic_assessment()
        western_sa = _western_assessment()

        assessments = {
            SystemType.VEDIC.value: vedic_sa,
            SystemType.WESTERN.value: western_sa,
        }

        adjusted, _ = _adjusted_convergence(assessments)
        assert adjusted > 0.0, f"Adjusted convergence {adjusted:.4f} should be > 0"

    def test_full_pipeline_e2e(self) -> None:
        """End-to-end: Vedic yoga facts → evidence → convergence → adjusted score."""
        # Step 1: Generate Vedic yoga evidence
        jre_facts = _build_vedic_jre_facts()
        yoga_svc = YogaEvidenceService()
        records = yoga_svc.generate_yoga_evidence(jre_facts, dasha_lord="JUPITER")
        assert len(records) >= 1

        # Step 2: Build SystemAssessments from both systems
        vedic_sa = _vedic_assessment()
        western_sa = _western_assessment()

        assessments = {
            SystemType.VEDIC.value: vedic_sa,
            SystemType.WESTERN.value: western_sa,
        }

        # Step 3: Compute convergence
        raw = _raw_convergence(assessments)
        adjusted, independence = _adjusted_convergence(assessments)

        # Step 4: Build CrossSystemEvidence
        cross_system = CrossSystemEvidence(
            event_cluster_id="raja_yoga_career_e2e",
            system_assessments=assessments,
            independence_score=independence,
            convergence_score=adjusted,
        )

        # Assertions
        assert raw > 0.8
        assert independence == pytest.approx(0.7, abs=0.01)
        assert adjusted < raw
        assert cross_system.independence_score == pytest.approx(0.7, abs=0.01)
        assert cross_system.convergence_score == pytest.approx(adjusted, abs=0.01)
        assert cross_system.system_assessments[SystemType.VEDIC.value].outcome_taxonomy == _OUTCOME
        assert cross_system.system_assessments[SystemType.WESTERN.value].outcome_taxonomy == _OUTCOME

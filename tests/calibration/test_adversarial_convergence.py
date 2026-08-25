"""JRS-074 Adversarial Convergence Tests — Controlled Convergence Scenarios.

Since real-world charts might result in silent systems, these tests manually
inject mock SystemAssessments into the convergence pipeline to force specific
mathematical outcomes and verify the independence-adjusted convergence
formula behaves correctly.

Three controlled scenarios:
1. Forced Agreement: Vedic + Western both support → raw convergence increases,
   but adjusted convergence is penalized by shared-root independence penalty.
2. Forced Contradiction: Vedic supports, Western contradicts → final
   convergence drops significantly.
3. Forced Silence: Vedic supports, Western/Numerology produce empty evidence →
   final score matches the single-system Vedic score.
"""

from __future__ import annotations

import pytest

from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
)
from jrs.multisystem.service import IndependenceAnalyzer

# ── Helpers ──────────────────────────────────────────────────────────────────

_OUTCOME = "WEALTH_ACCUMULATION"


def _vedic_sa(
    status: str = "STRONGLY_SUPPORTED",
    outcome: str = _OUTCOME,
) -> SystemAssessment:
    """Build a Vedic SystemAssessment."""
    return SystemAssessment(
        system_type=SystemType.VEDIC,
        outcome_taxonomy=outcome,
        assessment_status=status,
        timing_status="INACTIVE",
        provenance=EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        ),
    )


def _western_sa(
    status: str = "STRONGLY_SUPPORTED",
    outcome: str = _OUTCOME,
) -> SystemAssessment:
    """Build a Western SystemAssessment."""
    return SystemAssessment(
        system_type=SystemType.WESTERN,
        outcome_taxonomy=outcome,
        assessment_status=status,
        timing_status="INACTIVE",
        provenance=EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="LILLY",
        ),
    )


def _numerology_sa(
    status: str = "STRONGLY_SUPPORTED",
    outcome: str = _OUTCOME,
) -> SystemAssessment:
    """Build a Numerology SystemAssessment."""
    return SystemAssessment(
        system_type=SystemType.NUMEROLOGY,
        outcome_taxonomy=outcome,
        assessment_status=status,
        timing_status="INACTIVE",
        provenance=EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        ),
    )


def _convergence_score(
    assessments: dict[str, SystemAssessment],
) -> float:
    """Compute raw convergence from assessments."""
    result: float = compute_convergence_score(assessments)
    return result


def _adjusted_convergence(
    assessments: dict[str, SystemAssessment],
) -> tuple[float, float]:
    """Compute (adjusted_convergence, independence_score) for assessments."""
    analyzer = IndependenceAnalyzer()
    provenances = [
        sa.provenance
        for sa in assessments.values()
        if sa.provenance is not None
    ]
    raw = _convergence_score(assessments)
    independence = analyzer.calculate_collective_independence(provenances)
    adjusted = raw * independence
    return (adjusted, independence)


# ── Test 1: Forced Agreement ─────────────────────────────────────────────────


class TestForcedAgreement:
    """Vedic and Western both strongly support the same outcome.

    Expected: raw convergence increases (both agree), but adjusted
    convergence is penalized because Vedic and Western share
    Hellenistic roots (independence < 1.0).
    """

    def test_raw_convergence_is_high(self) -> None:
        """Both systems strongly supporting should yield high raw convergence."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_SUPPORTED")
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }

        raw = _convergence_score(assessments)
        # Both agree on outcome (0.5) + status (0.3) + timing (0.2) = 1.0
        assert raw == pytest.approx(1.0, abs=0.01)

    def test_adjusted_is_penalized(self) -> None:
        """Adjusted convergence should be lower than raw due to shared roots."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_SUPPORTED")
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }

        raw = _convergence_score(assessments)
        adjusted, independence = _adjusted_convergence(assessments)

        # Independence should be < 1.0 (shared Hellenistic roots)
        assert independence < 1.0
        assert independence > 0.0
        # Adjusted = raw * independence, so adjusted < raw
        assert adjusted < raw
        assert adjusted == pytest.approx(raw * independence, abs=0.01)

    def test_independence_score_is_correct(self) -> None:
        """Vedic-Western independence should reflect shared roots penalty."""
        vedic = _vedic_sa()
        western = _western_sa()
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }

        _, independence = _adjusted_convergence(assessments)
        # Vedic and Western share Hellenistic roots.
        # shared_derivative_roots returns frozenset({VEDIC, WESTERN})
        # → 2 system types in the set → 2 shared roots.
        # IndependenceAnalyzer: penalty = 2 * 0.15 = 0.3
        # independence = 1.0 - 0.3 = 0.7
        assert independence == pytest.approx(0.7, abs=0.01)

    def test_three_system_agreement(self) -> None:
        """Adding Numerology (independent) should raise average independence."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_SUPPORTED")
        numerology = _numerology_sa("STRONGLY_SUPPORTED")

        two_systems = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }
        three_systems = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
            SystemType.NUMEROLOGY.value: numerology,
        }

        _, indep_two = _adjusted_convergence(two_systems)
        _, indep_three = _adjusted_convergence(three_systems)

        # Numerology is independent, so adding it raises the average
        assert indep_three > indep_two


# ── Test 2: Forced Contradiction ─────────────────────────────────────────────


class TestForcedContradiction:
    """Vedic supports, Western contradicts the same outcome.

    Expected: raw convergence drops (systems disagree), and the final
    convergence score is significantly lower than the agreement case.
    """

    def test_raw_convergence_is_low(self) -> None:
        """Contradicting systems should yield low raw convergence."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_CONTRADICTED")
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }

        raw = _convergence_score(assessments)
        # Outcome matches (0.5) + status disagrees (0.0) + timing (0.2)
        assert raw == pytest.approx(0.7, abs=0.01)

    def test_contradiction_drops_score(self) -> None:
        """Contradiction scenario should have much lower score than agreement."""
        agreement_assessments = {
            SystemType.VEDIC.value: _vedic_sa("STRONGLY_SUPPORTED"),
            SystemType.WESTERN.value: _western_sa("STRONGLY_SUPPORTED"),
        }
        contradiction_assessments = {
            SystemType.VEDIC.value: _vedic_sa("STRONGLY_SUPPORTED"),
            SystemType.WESTERN.value: _western_sa("STRONGLY_CONTRADICTED"),
        }

        raw_agreement = _convergence_score(agreement_assessments)
        raw_contradiction = _convergence_score(contradiction_assessments)

        # Contradiction should score significantly lower
        assert raw_contradiction < raw_agreement
        assert raw_contradiction <= raw_agreement - 0.2

    def test_adjusted_contradiction_is_very_low(self) -> None:
        """Adjusted convergence for contradiction should be very low."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_CONTRADICTED")
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }

        raw = _convergence_score(assessments)
        adjusted, independence = _adjusted_convergence(assessments)

        # Even though raw is moderate, adjusted is further dampened
        assert adjusted < raw
        assert adjusted == pytest.approx(raw * independence, abs=0.01)

    def test_contradiction_with_numerology_supporting(self) -> None:
        """Vedic + Numerology support, Western contradicts.

        Numerology's independence from Vedic means the average independence
        stays higher than Vedic-Western alone, but the raw convergence
        still drops due to Western's contradiction.
        """
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_CONTRADICTED")
        numerology = _numerology_sa("STRONGLY_SUPPORTED")

        two_assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }
        three_assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
            SystemType.NUMEROLOGY.value: numerology,
        }

        _, indep_two = _adjusted_convergence(two_assessments)
        _, indep_three = _adjusted_convergence(three_assessments)

        # Numerology raises average independence (it's independent of both)
        assert indep_three > indep_two

        # But raw convergence is still hurt by Western's contradiction
        raw_two = _convergence_score(two_assessments)
        raw_three = _convergence_score(three_assessments)
        # Adding a supporting system should raise raw convergence
        # (more agreement on average)
        assert raw_three >= raw_two


# ── Test 3: Forced Silence ───────────────────────────────────────────────────


class TestForcedSilence:
    """Vedic supports, but Western/Numerology return empty evidence.

    Expected: The final score should remain identical to the single-system
    Vedic score, since silent systems don't participate in convergence.
    """

    def test_single_system_vedic_score(self) -> None:
        """Baseline: single Vedic system convergence score."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        assessments = {SystemType.VEDIC.value: vedic}

        raw = _convergence_score(assessments)
        # Single system: score based on status only
        assert raw == pytest.approx(1.0, abs=0.01)

    def test_vedic_only_matches_single(self) -> None:
        """When only Vedic has an assessment, convergence = single system."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        # Only Vedic in the dict (Western/Numerology "silent")
        assessments = {SystemType.VEDIC.value: vedic}

        raw = _convergence_score(assessments)
        adjusted, independence = _adjusted_convergence(assessments)

        # Single system: independence = confidence_weight = 1.0
        assert independence == 1.0
        # Adjusted = raw * 1.0 = raw
        assert adjusted == pytest.approx(raw, abs=0.01)

    def test_silence_preserves_vedic_score(self) -> None:
        """Adding silent systems (not in assessments dict) doesn't change score."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        vedic_only = {SystemType.VEDIC.value: vedic}

        raw_single = _convergence_score(vedic_only)
        adjusted_single, indep_single = _adjusted_convergence(vedic_only)

        # Simulating "silence" by not including Western/Num in dict
        # (same as vedic_only since they produce no SystemAssessment)
        assert raw_single == pytest.approx(1.0, abs=0.01)
        assert indep_single == 1.0
        assert adjusted_single == pytest.approx(raw_single, abs=0.01)

    def test_vedic_with_western_neutral(self) -> None:
        """If Western returns NO_MATCH/NEUTRAL, convergence should drop."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western_neutral = SystemAssessment(
            system_type=SystemType.WESTERN,
            outcome_taxonomy="NO_MATCH",
            assessment_status="NEUTRAL",
            timing_status="INACTIVE",
            provenance=EvidenceProvenance(
                system_type=SystemType.WESTERN,
                source_tradition="PTOLEMY",
            ),
        )
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western_neutral,
        }

        raw = _convergence_score(assessments)
        # Vedic outcome=WEALTH_ACCUMULATION, Western outcome=NO_MATCH
        # → outcome_match=False (0.0), status mismatch (0.0), timing (0.2)
        # Pairwise score = 0.2
        assert raw == pytest.approx(0.2, abs=0.01)

        adjusted, independence = _adjusted_convergence(assessments)
        assert adjusted < raw

    def test_vedic_with_numerology_neutral(self) -> None:
        """If Numerology returns NEUTRAL, convergence drops but independence stays high."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        num_neutral = SystemAssessment(
            system_type=SystemType.NUMEROLOGY,
            outcome_taxonomy="NO_MATCH",
            assessment_status="NEUTRAL",
            timing_status="INACTIVE",
            provenance=EvidenceProvenance(
                system_type=SystemType.NUMEROLOGY,
                source_tradition="PYTHAGOREAN",
            ),
        )
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.NUMEROLOGY.value: num_neutral,
        }

        raw = _convergence_score(assessments)
        adjusted, independence = _adjusted_convergence(assessments)

        # Numerology is independent of Vedic, so independence = 1.0
        assert independence == 1.0
        # But convergence is hurt by status mismatch
        assert raw < 1.0
        assert adjusted == pytest.approx(raw, abs=0.01)


# ── Determinism Tests ────────────────────────────────────────────────────────


class TestConvergenceDeterminism:
    """Verify that all convergence calculations are deterministic."""

    def test_same_inputs_same_output(self) -> None:
        """Identical assessments should always produce identical scores."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_SUPPORTED")
        assessments = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }

        adj1, indep1 = _adjusted_convergence(assessments)
        adj2, indep2 = _adjusted_convergence(assessments)

        assert adj1 == adj2
        assert indep1 == indep2

    def test_order_independence(self) -> None:
        """Dict key order should not affect the convergence score."""
        vedic = _vedic_sa("STRONGLY_SUPPORTED")
        western = _western_sa("STRONGLY_SUPPORTED")
        numerology = _numerology_sa("STRONGLY_SUPPORTED")

        # Two different orderings of the same assessments
        order_a = {
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
            SystemType.NUMEROLOGY.value: numerology,
        }
        order_b = {
            SystemType.NUMEROLOGY.value: numerology,
            SystemType.VEDIC.value: vedic,
            SystemType.WESTERN.value: western,
        }

        adj_a, indep_a = _adjusted_convergence(order_a)
        adj_b, indep_b = _adjusted_convergence(order_b)

        assert adj_a == adj_b
        assert indep_a == indep_b

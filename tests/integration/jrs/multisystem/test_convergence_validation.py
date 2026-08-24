"""Integration tests for JRS-068: Multi-System Convergence Validation.

Feeds Vedic and Western assessments into the IndependenceAnalyzer and
CrossSystemEvidence builder, asserting mathematical invariants across 8
canonical scenarios.

CONSTRAINT: Purely validation — no production code changes.
"""

from __future__ import annotations

import pytest

from jrs.multisystem.models import (
    CrossSystemEvidence,
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
    compute_independence_score,
    shared_derivative_roots,
)
from jrs.multisystem.service import IndependenceAnalyzer

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_provenance(
    system: SystemType,
    tradition: str,
    confidence: float = 1.0,
) -> EvidenceProvenance:
    """Build a minimal EvidenceProvenance."""
    return EvidenceProvenance(
        system_type=system,
        source_tradition=tradition,
        confidence_weight=confidence,
    )


def _make_assessment(
    system: SystemType,
    outcome: str,
    status: str,
    timing: str = "INACTIVE",
) -> SystemAssessment:
    """Build a minimal SystemAssessment."""
    return SystemAssessment(
        system_type=system,
        outcome_taxonomy=outcome,
        assessment_status=status,
        timing_status=timing,
    )


def _build_cross_system(
    analyzer: IndependenceAnalyzer,
    cluster_id: str,
    provenances: dict[SystemType, EvidenceProvenance],
    assessments: dict[str, SystemAssessment],
) -> CrossSystemEvidence:
    """Shorthand: build CrossSystemEvidence and return it."""
    return analyzer.build_cross_system_evidence(
        event_cluster_id=cluster_id,
        provenances=provenances,
        assessments=assessments,
    )


def _expected_pairwise_independence(
    a: EvidenceProvenance, b: EvidenceProvenance
) -> float:
    """Reproduce the default IndependenceAnalyzer pairwise calculation.

    base_score=1.0, self_reference_penalty=0.5,
    shared_root_penalty_per_shared=0.15.
    """
    if a.system_type == b.system_type:
        return max(0.0, 1.0 - 0.5)  # 0.5

    shared = shared_derivative_roots(a.system_type, b.system_type)
    penalty = len(shared) * 0.15
    return max(0.0, min(1.0, 1.0 - penalty))


# ── Scenario 1: Same underlying astronomical evidence ────────────────────────
# Vedic and Western share derivative roots (Hellenistic astrology).
# The system must penalize independence for this shared lineage.


class TestScenario1SameAstronomicalEvidence:
    """Vedic + Western share roots → independence is penalized."""

    def test_pairwise_independence_penalized(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_western = _make_provenance(SystemType.WESTERN, "Tetrabiblos")

        pairwise = analyzer.calculate_pairwise_independence(prov_vedic, prov_western)
        assert pairwise < 1.0
        assert pairwise > 0.0
        # shared_derivative_roots returns frozenset({VEDIC, WESTERN}) len=2
        # penalty = 2 * 0.15 = 0.30 → independence = 0.70
        assert pairwise == pytest.approx(0.70)

    def test_collective_independence_penalized(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_western = _make_provenance(SystemType.WESTERN, "Tetrabiblos")

        collective = analyzer.calculate_collective_independence(
            [prov_vedic, prov_western]
        )
        assert collective < 1.0
        assert collective == pytest.approx(0.70)

    def test_cross_system_evidence_shows_penalized_independence(self) -> None:
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED"),
            "WESTERN": _make_assessment(
                SystemType.WESTERN, "CAREER_GROWTH", "SUPPORTED"
            ),
        }
        result = _build_cross_system(analyzer, "cluster-s1", provenances, assessments)
        assert result.independence_score == pytest.approx(0.70)
        assert result.independence_score < 1.0


# ── Scenario 2: Shared derivative doctrine ──────────────────────────────────
# The derivative_roots mapping shows Vedic ↔ Western and Vedic ↔ Nadi share
# roots.  Any pair with shared roots must receive a penalty.


class TestScenario2SharedDerivativeDoctrine:
    """Shared derivative roots between systems must reduce independence."""

    def test_vedic_western_shared_roots(self) -> None:
        shared = shared_derivative_roots(SystemType.VEDIC, SystemType.WESTERN)
        assert SystemType.VEDIC in shared
        assert SystemType.WESTERN in shared

    def test_vedic_nadi_shared_roots(self) -> None:
        shared = shared_derivative_roots(SystemType.VEDIC, SystemType.NADI)
        assert SystemType.VEDIC in shared
        assert SystemType.NADI in shared

    def test_pairwise_independence_for_shared_root_pair(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_nadi = _make_provenance(SystemType.NADI, "NadiGrantha")

        pairwise = analyzer.calculate_pairwise_independence(prov_vedic, prov_nadi)
        assert pairwise < 1.0
        # shared_derivative_roots returns frozenset({VEDIC, NADI}) len=2
        # penalty = 2 * 0.15 = 0.30 → independence = 0.70
        assert pairwise == pytest.approx(0.70)

    def test_adjusted_convergence_lower_than_raw(self) -> None:
        """Penalized independence must dampen convergence below raw score."""
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_western = _make_provenance(SystemType.WESTERN, "Tetrabiblos")

        raw_convergence = 0.9
        adjusted, independence = analyzer.analyze_convergence(
            [prov_vedic, prov_western], raw_convergence
        )
        assert independence < 1.0
        assert adjusted < raw_convergence
        assert adjusted == pytest.approx(raw_convergence * independence)


# ── Scenario 3: Genuinely independent evidence ──────────────────────────────
# Numerology and Vastu share no derivative roots; independence must be 1.0.


class TestScenario3GenuinelyIndependentEvidence:
    """No shared roots → full independence preserved."""

    def test_pairwise_independence_is_one(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")

        pairwise = analyzer.calculate_pairwise_independence(prov_num, prov_vastu)
        assert pairwise == 1.0

    def test_collective_independence_is_one(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")

        collective = analyzer.calculate_collective_independence([prov_num, prov_vastu])
        assert collective == 1.0

    def test_adjusted_convergence_preserves_raw(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")

        raw = 0.75
        adjusted, independence = analyzer.analyze_convergence(
            [prov_num, prov_vastu], raw
        )
        assert independence == 1.0
        assert adjusted == pytest.approx(raw)

    def test_cross_system_evidence_full_independence(self) -> None:
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.NUMEROLOGY: _make_provenance(
                SystemType.NUMEROLOGY, "Pythagorean"
            ),
            SystemType.VASTU: _make_provenance(SystemType.VASTU, "Manasara"),
        }
        assessments = {
            "NUMEROLOGY": _make_assessment(
                SystemType.NUMEROLOGY, "PARTNERSHIP_HARMONY", "SUPPORTED"
            ),
            "VASTU": _make_assessment(
                SystemType.VASTU, "PARTNERSHIP_HARMONY", "SUPPORTED"
            ),
        }
        result = _build_cross_system(analyzer, "cluster-s3", provenances, assessments)
        assert result.independence_score == 1.0


# ── Scenario 4: Vedic supports / Western contradicts ────────────────────────
# When two systems disagree on outcome, the contradiction is retained in the
# convergence score (raw convergence is low).


class TestScenario4VedicSupportsWesternContradicts:
    """Disagreement between systems produces low convergence."""

    def test_raw_convergence_is_low(self) -> None:
        """Opposing assessment_status values yield low pairwise agreement."""
        assmt_vedic = _make_assessment(
            SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED"
        )
        assmt_western = _make_assessment(
            SystemType.WESTERN, "CAREER_GROWTH", "CONTRADICTED"
        )
        assessments = {
            "VEDIC": assmt_vedic,
            "WESTERN": assmt_western,
        }
        raw_convergence = compute_convergence_score(assessments)
        # _pairwise_agreement: outcome match=0.5 + status mismatch=0.0 + timing match=0.2 = 0.7
        assert raw_convergence == pytest.approx(0.7)

    def test_contradiction_retained_after_adjustment(self) -> None:
        """Even after independence dampening, the convergence remains low."""
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(
                SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED"
            ),
            "WESTERN": _make_assessment(
                SystemType.WESTERN, "CAREER_GROWTH", "CONTRADICTED"
            ),
        }
        result = _build_cross_system(analyzer, "cluster-s4", provenances, assessments)
        # convergence_score is adjusted: raw(0.7) * independence(0.7) = 0.49
        assert result.convergence_score < 0.7
        assert result.convergence_score > 0.0
        # independence penalizes VEDIC-WESTERN
        assert result.independence_score == pytest.approx(0.70)

    def test_build_cross_system_preserves_contradiction(self) -> None:
        """The built CrossSystemEvidence encodes the contradiction."""
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(
                SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED"
            ),
            "WESTERN": _make_assessment(
                SystemType.WESTERN, "CAREER_GROWTH", "CONTRADICTED"
            ),
        }
        result = _build_cross_system(analyzer, "cluster-s4b", provenances, assessments)
        # Raw convergence is 0.7; adjusted = 0.7 * 0.7 = 0.49
        assert result.convergence_score == pytest.approx(0.7 * 0.7)
        assert result.convergence_score < 0.7


# ── Scenario 5: Both systems support ────────────────────────────────────────
# When both agree, raw convergence is high, but adjusted convergence is
# dampened by the independence penalty for shared-derivative-root systems.


class TestScenario5BothSystemsSupport:
    """Agreement boosts raw convergence; independence dampens adjusted score."""

    def test_raw_convergence_high(self) -> None:
        assmt_vedic = _make_assessment(
            SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED", "CONVERGENT"
        )
        assmt_western = _make_assessment(
            SystemType.WESTERN, "CAREER_GROWTH", "SUPPORTED", "CONVERGENT"
        )
        assessments = {
            "VEDIC": assmt_vedic,
            "WESTERN": assmt_western,
        }
        raw = compute_convergence_score(assessments)
        # Full match: outcome 0.5 + status 0.3 + timing 0.2 = 1.0
        assert raw == pytest.approx(1.0)

    def test_adjusted_convergence_dampened(self) -> None:
        """Raw convergence 1.0 is dampened by VEDIC-WESTERN independence."""
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(
                SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED", "CONVERGENT"
            ),
            "WESTERN": _make_assessment(
                SystemType.WESTERN, "CAREER_GROWTH", "SUPPORTED", "CONVERGENT"
            ),
        }
        result = _build_cross_system(analyzer, "cluster-s5", provenances, assessments)
        # convergence_score = raw(1.0) * independence(0.7) = 0.7
        assert result.convergence_score == pytest.approx(0.70)
        assert result.convergence_score < 1.0
        assert result.independence_score == pytest.approx(0.70)

    def test_adjusted_lte_raw(self) -> None:
        """Adjusted convergence must never exceed raw convergence."""
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(
                SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED", "CONVERGENT"
            ),
            "WESTERN": _make_assessment(
                SystemType.WESTERN, "CAREER_GROWTH", "SUPPORTED", "CONVERGENT"
            ),
        }
        raw = compute_convergence_score(assessments)
        result = _build_cross_system(analyzer, "cluster-s5b", provenances, assessments)
        assert result.convergence_score <= raw


# ── Scenario 6: One system has no evidence ──────────────────────────────────
# When only one system contributes assessments, no artificial convergence
# is generated.


class TestScenario6OneSystemNoEvidence:
    """Single system → convergence based on that system only, no false agreement."""

    def test_single_system_convergence(self) -> None:
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
        }
        assessments = {
            "VEDIC": _make_assessment(
                SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED"
            ),
        }
        result = _build_cross_system(analyzer, "cluster-s6", provenances, assessments)
        # Single system: convergence = _status_to_score("SUPPORTED") = 0.8
        assert result.convergence_score == pytest.approx(0.8)
        # Single provenance: independence = confidence_weight = 1.0
        assert result.independence_score == pytest.approx(1.0)

    def test_no_cross_system_agreement(self) -> None:
        """With only one assessment, there is no pairwise agreement metric."""
        assmt = _make_assessment(SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED")
        assessments = {"VEDIC": assmt}
        raw = compute_convergence_score(assessments)
        # Single-assessment convergence is just the status score
        assert raw == pytest.approx(0.8)

    def test_two_systems_one_empty_assessments(self) -> None:
        """Two provenances but only one assessment: no artificial convergence."""
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(
                SystemType.VEDIC, "CAREER_GROWTH", "SUPPORTED"
            ),
            # WESTERN has no assessment
        }
        result = _build_cross_system(analyzer, "cluster-s6b", provenances, assessments)
        # Single-assessment convergence = 0.8; independence = penalized
        assert result.convergence_score < 0.8
        assert result.independence_score == pytest.approx(0.70)


# ── Scenario 7: Different provenance, same outcome ──────────────────────────
# Numerology and Vastu reach the same conclusion from completely independent
# traditions.  Convergence is retained (not dampened).


class TestScenario7DifferentProvenanceSameOutcome:
    """Independent systems converging → convergence is fully preserved."""

    def test_full_independence_preserved(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")

        independence = analyzer.calculate_collective_independence([prov_num, prov_vastu])
        assert independence == 1.0

    def test_convergence_not_dampened(self) -> None:
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.NUMEROLOGY: _make_provenance(
                SystemType.NUMEROLOGY, "Pythagorean"
            ),
            SystemType.VASTU: _make_provenance(SystemType.VASTU, "Manasara"),
        }
        assessments = {
            "NUMEROLOGY": _make_assessment(
                SystemType.NUMEROLOGY, "PARTNERSHIP_HARMONY", "SUPPORTED", "CONVERGENT"
            ),
            "VASTU": _make_assessment(
                SystemType.VASTU, "PARTNERSHIP_HARMONY", "SUPPORTED", "CONVERGENT"
            ),
        }
        raw = compute_convergence_score(assessments)
        result = _build_cross_system(analyzer, "cluster-s7", provenances, assessments)
        # Full agreement: raw = 1.0; independence = 1.0; adjusted = 1.0
        assert raw == pytest.approx(1.0)
        assert result.convergence_score == pytest.approx(1.0)
        assert result.independence_score == 1.0

    def test_adjusted_equals_raw_for_independent_systems(self) -> None:
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.NUMEROLOGY: _make_provenance(
                SystemType.NUMEROLOGY, "Pythagorean"
            ),
            SystemType.VASTU: _make_provenance(SystemType.VASTU, "Manasara"),
        }
        assessments = {
            "NUMEROLOGY": _make_assessment(
                SystemType.NUMEROLOGY, "CAREER_GROWTH", "SUPPORTED"
            ),
            "VASTU": _make_assessment(
                SystemType.VASTU, "CAREER_GROWTH", "SUPPORTED"
            ),
        }
        raw = compute_convergence_score(assessments)
        result = _build_cross_system(analyzer, "cluster-s7b", provenances, assessments)
        assert result.convergence_score == pytest.approx(raw)


# ── Scenario 8: Same provenance duplicated under different labels ───────────
# Two "systems" that are actually the same SystemType must NOT count as
# independent evidence.  The system must recognize the shared root and penalize.


class TestScenario8SameProvenanceDifferentLabels:
    """Same system type duplicated → MUST NOT count as independent evidence."""

    def test_self_reference_heavily_penalized(self) -> None:
        """Two entries of the same SystemType → independence = 0.5."""
        analyzer = IndependenceAnalyzer()
        prov_a = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_b = _make_provenance(SystemType.VEDIC, "BPHS")

        pairwise = analyzer.calculate_pairwise_independence(prov_a, prov_b)
        assert pairwise == pytest.approx(0.5)

    def test_self_reference_below_half(self) -> None:
        """Independence for same system must be strictly below 1.0."""
        analyzer = IndependenceAnalyzer()
        prov_a = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_b = _make_provenance(SystemType.VEDIC, "JyotishShastra")

        pairwise = analyzer.calculate_pairwise_independence(prov_a, prov_b)
        assert pairwise < 1.0
        assert pairwise == pytest.approx(0.5)

    def test_collective_independence_penalized(self) -> None:
        """Collective score with duplicate system types must be penalized."""
        analyzer = IndependenceAnalyzer()
        prov_a = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_b = _make_provenance(SystemType.VEDIC, "BPHS")

        collective = analyzer.calculate_collective_independence([prov_a, prov_b])
        assert collective == pytest.approx(0.5)

    def test_module_level_compute_also_penalizes(self) -> None:
        """The module-level compute_independence_score also penalizes."""
        prov_a = EvidenceProvenance(
            system_type=SystemType.VEDIC, source_tradition="BPHS"
        )
        prov_b = EvidenceProvenance(
            system_type=SystemType.VEDIC, source_tradition="BPHS"
        )
        score = compute_independence_score((prov_a, prov_b))
        assert score == pytest.approx(0.1)

    def test_cross_system_evidence_penalized_independence(self) -> None:
        """build_cross_system_evidence penalizes same-type entries."""
        analyzer = IndependenceAnalyzer()
        # Use two entries with same SystemType in the provenances dict;
        # dict keys are unique, so we simulate via list-based analyze_convergence
        prov_a = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_b = _make_provenance(SystemType.VEDIC, "BPHS")

        raw_convergence = 0.9
        adjusted, independence = analyzer.analyze_convergence(
            [prov_a, prov_b], raw_convergence
        )
        assert independence == pytest.approx(0.5)
        assert adjusted == pytest.approx(raw_convergence * 0.5)
        assert adjusted < raw_convergence

    def test_different_labels_same_system_not_independent(self) -> None:
        """Different tradition labels but same SystemType = not independent."""
        analyzer = IndependenceAnalyzer()
        prov_a = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_b = _make_provenance(SystemType.VEDIC, "Phaladeepika")

        pairwise = analyzer.calculate_pairwise_independence(prov_a, prov_b)
        # Same SystemType → self_reference_penalty applied
        assert pairwise == pytest.approx(0.5)
        assert pairwise < 1.0


# ── Deterministic ID Stability ──────────────────────────────────────────────


class TestDeterministicIdStability:
    """deterministic_id must be stable across identical invocations."""

    def test_same_inputs_same_id(self) -> None:
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(SystemType.VEDIC, "CAREER", "SUPPORTED"),
            "WESTERN": _make_assessment(SystemType.WESTERN, "CAREER", "SUPPORTED"),
        }
        r1 = _build_cross_system(analyzer, "det-1", provenances, assessments)
        r2 = _build_cross_system(analyzer, "det-1", provenances, assessments)
        assert r1.deterministic_id == r2.deterministic_id

    def test_different_inputs_different_id(self) -> None:
        analyzer = IndependenceAnalyzer()
        provs_a = {SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS")}
        provs_b = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assmts_a = {
            "VEDIC": _make_assessment(SystemType.VEDIC, "CAREER", "SUPPORTED"),
        }
        assmts_b = {
            "VEDIC": _make_assessment(SystemType.VEDIC, "CAREER", "SUPPORTED"),
            "WESTERN": _make_assessment(SystemType.WESTERN, "CAREER", "SUPPORTED"),
        }
        r1 = _build_cross_system(analyzer, "det-2", provs_a, assmts_a)
        r2 = _build_cross_system(analyzer, "det-2", provs_b, assmts_b)
        assert r1.deterministic_id != r2.deterministic_id

    def test_id_is_sha256_hex(self) -> None:
        """deterministic_id must be a 64-char hex string (SHA-256)."""
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
        }
        assessments = {
            "VEDIC": _make_assessment(SystemType.VEDIC, "CAREER", "SUPPORTED"),
        }
        result = _build_cross_system(analyzer, "det-3", provenances, assessments)
        assert len(result.deterministic_id) == 64
        # Must be valid hex
        int(result.deterministic_id, 16)


# ── Mathematical Invariant: adjusted ≤ raw ─────────────────────────────────


class TestMathematicalInvariants:
    """Cross-cutting mathematical invariants across all scenarios."""

    @pytest.mark.parametrize(
        ("systems", "outcome", "status_a", "status_b"),
        [
            (
                (SystemType.VEDIC, SystemType.WESTERN),
                "CAREER_GROWTH",
                "SUPPORTED",
                "SUPPORTED",
            ),
            (
                (SystemType.VEDIC, SystemType.WESTERN),
                "CAREER_GROWTH",
                "SUPPORTED",
                "CONTRADICTED",
            ),
            (
                (SystemType.NUMEROLOGY, SystemType.VASTU),
                "PARTNERSHIP",
                "SUPPORTED",
                "SUPPORTED",
            ),
            (
                (SystemType.VEDIC, SystemType.NADI),
                "WEALTH",
                "STRONGLY_SUPPORTED",
                "SUPPORTED",
            ),
        ],
    )
    def test_adjusted_convergence_lte_raw(
        self,
        systems: tuple[SystemType, SystemType],
        outcome: str,
        status_a: str,
        status_b: str,
    ) -> None:
        """adjusted_convergence <= raw_convergence for all system pairs."""
        analyzer = IndependenceAnalyzer()
        sys_a, sys_b = systems
        provenances = {
            sys_a: _make_provenance(sys_a, f"tradition-{sys_a.value}"),
            sys_b: _make_provenance(sys_b, f"tradition-{sys_b.value}"),
        }
        assessments = {
            sys_a.value: _make_assessment(sys_a, outcome, status_a),
            sys_b.value: _make_assessment(sys_b, outcome, status_b),
        }
        raw = compute_convergence_score(assessments)
        result = _build_cross_system(
            analyzer, f"invariant-{sys_a.value}-{sys_b.value}", provenances, assessments
        )
        assert result.convergence_score <= raw

    def test_independence_score_in_unit_interval(self) -> None:
        """Independence score must always be in [0.0, 1.0]."""
        analyzer = IndependenceAnalyzer()
        systems = [
            (SystemType.VEDIC, "BPHS"),
            (SystemType.WESTERN, "Tetrabiblos"),
            (SystemType.NUMEROLOGY, "Pythagorean"),
            (SystemType.VASTU, "Manasara"),
            (SystemType.NADI, "NadiGrantha"),
            (SystemType.PALMISTRY, "Cheiromancy"),
        ]
        provenances = [_make_provenance(s, t) for s, t in systems]
        collective = analyzer.calculate_collective_independence(provenances)
        assert 0.0 <= collective <= 1.0

    def test_convergence_score_in_unit_interval(self) -> None:
        """Convergence score must always be in [0.0, 1.0]."""
        analyzer = IndependenceAnalyzer()
        provenances = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assessments = {
            "VEDIC": _make_assessment(SystemType.VEDIC, "CAREER", "SUPPORTED"),
            "WESTERN": _make_assessment(SystemType.WESTERN, "CAREER", "SUPPORTED"),
        }
        result = _build_cross_system(analyzer, "inv-interval", provenances, assessments)
        assert 0.0 <= result.convergence_score <= 1.0
        assert 0.0 <= result.independence_score <= 1.0

    def test_empty_provenances_yields_zero(self) -> None:
        """No provenances → zero convergence and independence."""
        analyzer = IndependenceAnalyzer()
        adjusted, independence = analyzer.analyze_convergence([], 0.5)
        assert adjusted == 0.0
        assert independence == 0.0

    def test_higher_independence_means_less_dampening(self) -> None:
        """More independent systems → convergence is less dampened."""
        analyzer = IndependenceAnalyzer()

        # VEDIC + WESTERN: penalized independence
        prov_vw = [
            _make_provenance(SystemType.VEDIC, "BPHS"),
            _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        ]
        adj_vw, ind_vw = analyzer.analyze_convergence(prov_vw, 0.8)

        # NUMEROLOGY + VASTU: full independence
        prov_nv = [
            _make_provenance(SystemType.NUMEROLOGY, "Pythagorean"),
            _make_provenance(SystemType.VASTU, "Manasara"),
        ]
        adj_nv, ind_nv = analyzer.analyze_convergence(prov_nv, 0.8)

        assert ind_vw < ind_nv
        assert adj_vw < adj_nv

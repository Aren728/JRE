"""Tests for Multi-System Evidence Graph data models."""

from __future__ import annotations

import pytest

from jrs.multisystem.models import (
    CrossSystemEvidence,
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
    compute_independence_score,
    compute_pairwise_independence,
    shared_derivative_roots,
)


class TestSystemType:
    """Tests for SystemType enum."""

    def test_has_six_members(self) -> None:
        assert len(SystemType) == 6

    def test_vedic_exists(self) -> None:
        assert SystemType.VEDIC.value == "VEDIC"

    def test_western_exists(self) -> None:
        assert SystemType.WESTERN.value == "WESTERN"

    def test_nadi_exists(self) -> None:
        assert SystemType.NADI.value == "NADI"

    def test_numerology_exists(self) -> None:
        assert SystemType.NUMEROLOGY.value == "NUMEROLOGY"

    def test_vastu_exists(self) -> None:
        assert SystemType.VASTU.value == "VASTU"

    def test_palmistry_exists(self) -> None:
        assert SystemType.PALMISTRY.value == "PALMISTRY"


class TestSharedDerivativeRoots:
    """Tests for shared_derivative_roots function."""

    def test_vedic_and_western_share_roots(self) -> None:
        shared = shared_derivative_roots(SystemType.VEDIC, SystemType.WESTERN)
        assert SystemType.VEDIC in shared
        assert SystemType.WESTERN in shared

    def test_vedic_and_numerology_no_shared_roots(self) -> None:
        shared = shared_derivative_roots(SystemType.VEDIC, SystemType.NUMEROLOGY)
        assert len(shared) == 0

    def test_numerology_and_vastu_no_shared_roots(self) -> None:
        shared = shared_derivative_roots(SystemType.NUMEROLOGY, SystemType.VASTU)
        assert len(shared) == 0

    def test_nadi_and_vedic_share_roots(self) -> None:
        shared = shared_derivative_roots(SystemType.NADI, SystemType.VEDIC)
        assert len(shared) > 0

    def test_palmistry_isolated(self) -> None:
        shared = shared_derivative_roots(SystemType.PALMISTRY, SystemType.VEDIC)
        assert len(shared) == 0

    def test_symmetric(self) -> None:
        a = shared_derivative_roots(SystemType.VEDIC, SystemType.WESTERN)
        b = shared_derivative_roots(SystemType.WESTERN, SystemType.VEDIC)
        assert a == b


class TestEvidenceProvenance:
    """Tests for EvidenceProvenance dataclass."""

    def test_construction(self) -> None:
        prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        assert prov.system_type == SystemType.VEDIC
        assert prov.source_tradition == "BPHS"
        assert prov.derivative_roots == ()
        assert prov.confidence_weight == 1.0

    def test_with_derivative_roots(self) -> None:
        prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
            derivative_roots=(SystemType.VEDIC, SystemType.WESTERN),
        )
        assert len(prov.derivative_roots) == 2

    def test_invalid_confidence_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence_weight must be in"):
            EvidenceProvenance(
                system_type=SystemType.VEDIC,
                source_tradition="BPHS",
                confidence_weight=1.5,
            )

    def test_negative_confidence_weight_raises(self) -> None:
        with pytest.raises(ValueError, match="confidence_weight must be in"):
            EvidenceProvenance(
                system_type=SystemType.VEDIC,
                source_tradition="BPHS",
                confidence_weight=-0.1,
            )

    def test_to_dict(self) -> None:
        prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
            derivative_roots=(SystemType.VEDIC, SystemType.WESTERN),
            confidence_weight=0.9,
        )
        d = prov.to_dict()
        assert d["system_type"] == "VEDIC"
        assert d["source_tradition"] == "BPHS"
        assert d["derivative_roots"] == ["VEDIC", "WESTERN"]
        assert d["confidence_weight"] == 0.9

    def test_frozen(self) -> None:
        prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        with pytest.raises(AttributeError):
            prov.system_type = SystemType.WESTERN  # type: ignore[misc]


class TestSystemAssessment:
    """Tests for SystemAssessment dataclass."""

    def test_construction(self) -> None:
        assmt = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_GROWTH",
            assessment_status="SUPPORTED",
        )
        assert assmt.system_type == SystemType.VEDIC
        assert assmt.timing_status == "INACTIVE"

    def test_to_dict(self) -> None:
        assmt = SystemAssessment(
            system_type=SystemType.WESTERN,
            outcome_taxonomy="PARTNERSHIP_HARMONY",
            assessment_status="STRONGLY_SUPPORTED",
            timing_status="CONVERGENT",
        )
        d = assmt.to_dict()
        assert d["system_type"] == "WESTERN"
        assert d["timing_status"] == "CONVERGENT"


class TestComputePairwiseIndependence:
    """Tests for compute_pairwise_independence function."""

    def test_same_system_low_independence(self) -> None:
        prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        score = compute_pairwise_independence(prov, prov)
        assert score < 0.5

    def test_vedic_western_moderate_independence(self) -> None:
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        prov_western = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="Tetrabiblos",
        )
        score = compute_pairwise_independence(prov_vedic, prov_western)
        # Shared roots should reduce below 1.0
        assert 0.0 < score < 1.0

    def test_vedic_numerology_high_independence(self) -> None:
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="Pythagorean",
        )
        score = compute_pairwise_independence(prov_vedic, prov_num)
        assert score == 1.0

    def test_numerology_vastu_high_independence(self) -> None:
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="Pythagorean",
        )
        prov_vastu = EvidenceProvenance(
            system_type=SystemType.VASTU,
            source_tradition="Manasara",
        )
        score = compute_pairwise_independence(prov_num, prov_vastu)
        assert score == 1.0


class TestComputeIndependenceScore:
    """Tests for compute_independence_score function."""

    def test_empty_returns_zero(self) -> None:
        score = compute_independence_score(())
        assert score == 0.0

    def test_single_returns_confidence(self) -> None:
        prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
            confidence_weight=0.8,
        )
        score = compute_independence_score((prov,))
        assert score == 0.8

    def test_two_independent_systems_high(self) -> None:
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="Pythagorean",
        )
        prov_vastu = EvidenceProvenance(
            system_type=SystemType.VASTU,
            source_tradition="Manasara",
        )
        score = compute_independence_score((prov_num, prov_vastu))
        assert score == 1.0

    def test_two_shared_root_systems_lower(self) -> None:
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        prov_western = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="Tetrabiblos",
        )
        score = compute_independence_score((prov_vedic, prov_western))
        assert score < 1.0

    def test_three_systems_average_pairwise(self) -> None:
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="Pythagorean",
        )
        prov_vastu = EvidenceProvenance(
            system_type=SystemType.VASTU,
            source_tradition="Manasara",
        )
        score = compute_independence_score((prov_vedic, prov_num, prov_vastu))
        # 3 pairs: VEDIC-NUM (1.0), VEDIC-VASTU (1.0), NUM-VASTU (1.0) = 1.0
        assert score == 1.0


class TestComputeConvergenceScore:
    """Tests for compute_convergence_score function."""

    def test_empty_returns_zero(self) -> None:
        score = compute_convergence_score({})
        assert score == 0.0

    def test_single_supported(self) -> None:
        assmt = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_GROWTH",
            assessment_status="SUPPORTED",
        )
        score = compute_convergence_score({"VEDIC": assmt})
        assert score > 0.0

    def test_two_agreeing_systems_high(self) -> None:
        assmt_vedic = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_GROWTH",
            assessment_status="SUPPORTED",
            timing_status="CONVERGENT",
        )
        assmt_num = SystemAssessment(
            system_type=SystemType.NUMEROLOGY,
            outcome_taxonomy="CAREER_GROWTH",
            assessment_status="SUPPORTED",
            timing_status="CONVERGENT",
        )
        score = compute_convergence_score(
            {"VEDIC": assmt_vedic, "NUMEROLOGY": assmt_num}
        )
        assert score == 1.0

    def test_two_disagreeing_systems_lower(self) -> None:
        assmt_vedic = SystemAssessment(
            system_type=SystemType.VEDIC,
            outcome_taxonomy="CAREER_GROWTH",
            assessment_status="SUPPORTED",
            timing_status="CONVERGENT",
        )
        assmt_num = SystemAssessment(
            system_type=SystemType.NUMEROLOGY,
            outcome_taxonomy="CAREER_STAGNATION",
            assessment_status="CONTRADICTED",
            timing_status="INACTIVE",
        )
        score = compute_convergence_score(
            {"VEDIC": assmt_vedic, "NUMEROLOGY": assmt_num}
        )
        assert score < 0.5


class TestCrossSystemEvidence:
    """Tests for CrossSystemEvidence dataclass."""

    def test_construction_with_deterministic_id(self) -> None:
        cse = CrossSystemEvidence(
            event_cluster_id="cluster-001",
            independence_score=1.0,
            convergence_score=0.8,
        )
        assert cse.deterministic_id != ""
        assert len(cse.deterministic_id) == 64  # SHA-256 hex

    def test_deterministic_id_same_inputs(self) -> None:
        cse1 = CrossSystemEvidence(
            event_cluster_id="cluster-001",
            independence_score=1.0,
            convergence_score=0.8,
        )
        cse2 = CrossSystemEvidence(
            event_cluster_id="cluster-001",
            independence_score=1.0,
            convergence_score=0.8,
        )
        assert cse1.deterministic_id == cse2.deterministic_id

    def test_different_inputs_different_id(self) -> None:
        cse1 = CrossSystemEvidence(
            event_cluster_id="cluster-001",
            independence_score=1.0,
            convergence_score=0.8,
        )
        cse2 = CrossSystemEvidence(
            event_cluster_id="cluster-002",
            independence_score=1.0,
            convergence_score=0.8,
        )
        assert cse1.deterministic_id != cse2.deterministic_id

    def test_to_dict(self) -> None:
        cse = CrossSystemEvidence(
            event_cluster_id="cluster-001",
            independence_score=0.9,
            convergence_score=0.7,
        )
        d = cse.to_dict()
        assert d["event_cluster_id"] == "cluster-001"
        assert d["independence_score"] == 0.9
        assert d["convergence_score"] == 0.7
        assert len(d["deterministic_id"]) == 64

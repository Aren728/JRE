"""Tests for Multi-System Evidence Graph service."""

from __future__ import annotations

import pytest

from jrs.multisystem.errors import ProvenanceError
from jrs.multisystem.models import (
    CrossSystemEvidence,
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
)
from jrs.multisystem.service import IndependenceAnalyzer


def _make_provenance(
    system: SystemType,
    tradition: str = "test",
    roots: tuple[SystemType, ...] = (),
) -> EvidenceProvenance:
    return EvidenceProvenance(
        system_type=system,
        source_tradition=tradition,
        derivative_roots=roots,
    )


class TestIndependenceAnalyzerPairwise:
    """Tests for IndependenceAnalyzer pairwise calculations."""

    def test_same_system_low(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov = _make_provenance(SystemType.VEDIC, "BPHS")
        score = analyzer.calculate_pairwise_independence(prov, prov)
        assert score < 0.6

    def test_independent_systems_high(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")
        score = analyzer.calculate_pairwise_independence(prov_num, prov_vastu)
        assert score == 1.0

    def test_vedic_western_moderate(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_western = _make_provenance(SystemType.WESTERN, "Tetrabiblos")
        score = analyzer.calculate_pairwise_independence(prov_vedic, prov_western)
        assert 0.0 < score < 1.0


class TestIndependenceAnalyzerCollective:
    """Tests for IndependenceAnalyzer collective calculations."""

    def test_empty_list(self) -> None:
        analyzer = IndependenceAnalyzer()
        score = analyzer.calculate_collective_independence([])
        assert score == 1.0

    def test_single_provenance(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov = _make_provenance(SystemType.VEDIC, "BPHS")
        score = analyzer.calculate_collective_independence([prov])
        assert score == prov.confidence_weight

    def test_two_independent(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")
        score = analyzer.calculate_collective_independence([prov_num, prov_vastu])
        assert score == 1.0

    def test_two_shared_roots(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_western = _make_provenance(SystemType.WESTERN, "Tetrabiblos")
        score = analyzer.calculate_collective_independence([prov_vedic, prov_western])
        assert score < 1.0

    def test_three_systems_average(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")
        score = analyzer.calculate_collective_independence(
            [prov_vedic, prov_num, prov_vastu]
        )
        # All pairs are independent: 3 pairs * 1.0 / 3 = 1.0
        assert score == 1.0


class TestIndependenceAnalyzerConvergence:
    """Tests for IndependenceAnalyzer.analyze_convergence."""

    def test_empty_provenances(self) -> None:
        analyzer = IndependenceAnalyzer()
        adjusted, independence = analyzer.analyze_convergence([], 0.8)
        assert adjusted == 0.0
        assert independence == 0.0

    def test_independent_systems_preserve(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_num = _make_provenance(SystemType.NUMEROLOGY, "Pythagorean")
        prov_vastu = _make_provenance(SystemType.VASTU, "Manasara")
        adjusted, independence = analyzer.analyze_convergence(
            [prov_num, prov_vastu], 0.8
        )
        assert independence == 1.0
        assert adjusted == pytest.approx(0.8)

    def test_shared_roots_dampen(self) -> None:
        analyzer = IndependenceAnalyzer()
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_western = _make_provenance(SystemType.WESTERN, "Tetrabiblos")
        adjusted, independence = analyzer.analyze_convergence(
            [prov_vedic, prov_western], 0.8
        )
        assert independence < 1.0
        assert adjusted < 0.8


class TestIndependenceAnalyzerBuildEvidence:
    """Tests for IndependenceAnalyzer.build_cross_system_evidence."""

    def test_builds_valid_evidence(self) -> None:
        analyzer = IndependenceAnalyzer()
        provs = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.NUMEROLOGY: _make_provenance(
                SystemType.NUMEROLOGY, "Pythagorean"
            ),
        }
        assmts = {
            "VEDIC": SystemAssessment(
                system_type=SystemType.VEDIC,
                outcome_taxonomy="CAREER_GROWTH",
                assessment_status="SUPPORTED",
            ),
            "NUMEROLOGY": SystemAssessment(
                system_type=SystemType.NUMEROLOGY,
                outcome_taxonomy="CAREER_GROWTH",
                assessment_status="SUPPORTED",
            ),
        }
        result = analyzer.build_cross_system_evidence(
            event_cluster_id="cluster-001",
            provenances=provs,
            assessments=assmts,
        )
        assert isinstance(result, CrossSystemEvidence)
        assert result.event_cluster_id == "cluster-001"
        assert result.independence_score == 1.0
        assert result.deterministic_id != ""

    def test_builds_shared_roots_lower_independence(self) -> None:
        analyzer = IndependenceAnalyzer()
        provs = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
            SystemType.WESTERN: _make_provenance(SystemType.WESTERN, "Tetrabiblos"),
        }
        assmts = {
            "VEDIC": SystemAssessment(
                system_type=SystemType.VEDIC,
                outcome_taxonomy="CAREER_GROWTH",
                assessment_status="SUPPORTED",
            ),
            "WESTERN": SystemAssessment(
                system_type=SystemType.WESTERN,
                outcome_taxonomy="CAREER_GROWTH",
                assessment_status="SUPPORTED",
            ),
        }
        result = analyzer.build_cross_system_evidence(
            event_cluster_id="cluster-002",
            provenances=provs,
            assessments=assmts,
        )
        assert result.independence_score < 1.0

    def test_empty_provenances_raises(self) -> None:
        analyzer = IndependenceAnalyzer()
        with pytest.raises(ProvenanceError, match="At least one provenance"):
            analyzer.build_cross_system_evidence(
                event_cluster_id="cluster-003",
                provenances={},
                assessments={},
            )

    def test_deterministic_id_same_inputs(self) -> None:
        analyzer = IndependenceAnalyzer()
        provs = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
        }
        assmts = {
            "VEDIC": SystemAssessment(
                system_type=SystemType.VEDIC,
                outcome_taxonomy="CAREER_GROWTH",
                assessment_status="SUPPORTED",
            ),
        }
        r1 = analyzer.build_cross_system_evidence("c1", provs, assmts)
        r2 = analyzer.build_cross_system_evidence("c1", provs, assmts)
        assert r1.deterministic_id == r2.deterministic_id

    def test_deterministic_id_different_inputs(self) -> None:
        analyzer = IndependenceAnalyzer()
        provs = {
            SystemType.VEDIC: _make_provenance(SystemType.VEDIC, "BPHS"),
        }
        assmts = {
            "VEDIC": SystemAssessment(
                system_type=SystemType.VEDIC,
                outcome_taxonomy="CAREER_GROWTH",
                assessment_status="SUPPORTED",
            ),
        }
        r1 = analyzer.build_cross_system_evidence("c1", provs, assmts)
        r2 = analyzer.build_cross_system_evidence("c2", provs, assmts)
        assert r1.deterministic_id != r2.deterministic_id


class TestIndependenceAnalyzerCustomConfig:
    """Tests for IndependenceAnalyzer with custom configuration."""

    def test_higher_self_penalty(self) -> None:
        analyzer = IndependenceAnalyzer(self_reference_penalty=0.8)
        prov = _make_provenance(SystemType.VEDIC, "BPHS")
        score = analyzer.calculate_pairwise_independence(prov, prov)
        assert score == pytest.approx(0.2)

    def test_higher_shared_root_penalty(self) -> None:
        analyzer = IndependenceAnalyzer(shared_root_penalty_per_shared=0.4)
        prov_vedic = _make_provenance(SystemType.VEDIC, "BPHS")
        prov_western = _make_provenance(SystemType.WESTERN, "Tetrabiblos")
        score = analyzer.calculate_pairwise_independence(prov_vedic, prov_western)
        # Should be lower than default penalty
        default_analyzer = IndependenceAnalyzer()
        default_score = default_analyzer.calculate_pairwise_independence(
            prov_vedic, prov_western
        )
        assert score <= default_score

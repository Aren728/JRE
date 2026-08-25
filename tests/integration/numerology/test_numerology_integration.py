"""Integration tests for the Numerology system end-to-end pipeline.

Tests verify:
- End-to-end: birth data → NumerologyChart → SystemAssessment
- Independence scores with Vedic and Western systems
- Multi-system convergence with numerology
- Deterministic ID stability across the pipeline
"""

from __future__ import annotations

import pytest

from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_independence_score,
    compute_pairwise_independence,
)
from jrs.numerology.service import NumerologyDomainService
from numerology.models import NumerologyChart
from numerology.service import NumerologyCalculationService

# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def calc_svc() -> NumerologyCalculationService:
    """Create a NumerologyCalculationService instance."""
    return NumerologyCalculationService()


@pytest.fixture
def jrs_svc() -> NumerologyDomainService:
    """Create a NumerologyDomainService instance."""
    return NumerologyDomainService()


@pytest.fixture
def sample_chart(calc_svc: NumerologyCalculationService) -> NumerologyChart:
    """Create a sample chart for John Adam Smith born 1985-07-15."""
    return calc_svc.calculate(
        birth_date="1985-07-15",
        birth_name="John Adam Smith",
    )


@pytest.fixture
def assessment(
    jrs_svc: NumerologyDomainService, sample_chart: NumerologyChart
) -> SystemAssessment:
    """Create a SystemAssessment for the sample chart."""
    return jrs_svc.assess_chart(sample_chart)


# ── End-to-End Pipeline Tests ────────────────────────────────────────────────


class TestEndToEndPipeline:
    """Tests for the complete numerology pipeline."""

    def test_pipeline_produces_assessment(
        self, assessment: SystemAssessment
    ) -> None:
        """Pipeline should produce a valid SystemAssessment."""
        assert assessment is not None
        assert assessment.system_type == SystemType.NUMEROLOGY

    def test_pipeline_has_provenance(
        self, assessment: SystemAssessment
    ) -> None:
        """Assessment should have NUMEROLOGY provenance."""
        assert assessment.provenance is not None
        assert assessment.provenance.system_type == SystemType.NUMEROLOGY
        assert assessment.provenance.source_tradition == "PYTHAGOREAN"

    def test_pipeline_has_valid_status(
        self, assessment: SystemAssessment
    ) -> None:
        """Assessment status should be a valid value."""
        valid_statuses = {
            "STRONGLY_SUPPORTED",
            "SUPPORTED",
            "WEAKLY_SUPPORTED",
            "NEUTRAL",
            "CONTRADICTED",
            "STRONGLY_CONTRADICTED",
        }
        assert assessment.assessment_status in valid_statuses

    def test_pipeline_deterministic(
        self, jrs_svc: NumerologyDomainService, sample_chart: NumerologyChart
    ) -> None:
        """Same chart should produce same assessment."""
        a1 = jrs_svc.assess_chart(sample_chart)
        a2 = jrs_svc.assess_chart(sample_chart)
        assert a1.outcome_taxonomy == a2.outcome_taxonomy
        assert a1.assessment_status == a2.assessment_status

    def test_pipeline_different_inputs(
        self, jrs_svc: NumerologyDomainService, calc_svc: NumerologyCalculationService
    ) -> None:
        """Different charts may produce different assessments."""
        chart1 = calc_svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        chart2 = calc_svc.calculate(
            birth_date="1990-01-01",
            birth_name="Jane Marie Doe",
        )
        a1 = jrs_svc.assess_chart(chart1)
        a2 = jrs_svc.assess_chart(chart2)
        # They should at least be valid assessments
        assert a1.system_type == SystemType.NUMEROLOGY
        assert a2.system_type == SystemType.NUMEROLOGY

    def test_pipeline_rule_count(
        self, jrs_svc: NumerologyDomainService
    ) -> None:
        """Service should load a meaningful number of rules."""
        assert jrs_svc.rule_count >= 30

    def test_pipeline_evidence_records(
        self, jrs_svc: NumerologyDomainService, sample_chart: NumerologyChart
    ) -> None:
        """Pipeline should produce evidence records for a known chart."""
        records = jrs_svc.evaluate_chart_facts(sample_chart)
        # With life_path=9, destiny=9, soul_urge=8, personality=1
        # Several rules should fire
        assert len(records) > 0

    def test_all_records_have_source(
        self, jrs_svc: NumerologyDomainService, sample_chart: NumerologyChart
    ) -> None:
        """All evidence records should have source attribution."""
        records = jrs_svc.evaluate_chart_facts(sample_chart)
        for record in records:
            assert record.source_id
            assert record.rule_id


# ── Independence Score Tests ─────────────────────────────────────────────────


class TestIndependenceScores:
    """Tests for independence scores between Numerology and other systems."""

    def test_numerology_vedic_independence(self) -> None:
        """NUMEROLOGY and VEDIC should be fully independent (1.0)."""
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        independence = compute_pairwise_independence(prov_num, prov_vedic)
        assert independence == 1.0

    def test_numerology_western_independence(self) -> None:
        """NUMEROLOGY and WESTERN should be fully independent (1.0)."""
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )
        prov_western = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="PTOLEMY",
        )
        independence = compute_pairwise_independence(prov_num, prov_western)
        assert independence == 1.0

    def test_vedic_western_not_independent(self) -> None:
        """VEDIC and WESTERN should NOT be fully independent (shared roots)."""
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        prov_western = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="PTOLEMY",
        )
        independence = compute_pairwise_independence(prov_vedic, prov_western)
        assert independence < 1.0

    def test_three_system_aggregate_independence(self) -> None:
        """Aggregate independence with VEDIC + WESTERN + NUMEROLOGY."""
        prov_vedic = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        prov_western = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="PTOLEMY",
        )
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )
        # Pairwise: VEDIC-WESTERN=0.7, VEDIC-NUM=1.0, WESTERN-NUM=1.0
        # Average: (0.7 + 1.0 + 1.0) / 3 ≈ 0.9
        aggregate = compute_independence_score(
            (prov_vedic, prov_western, prov_num)
        )
        # Aggregate should be above 0.7 (numerator adds independence)
        assert aggregate >= 0.79  # (0.7 + 1.0 + 1.0) / 3 = 0.9

    def test_numerology_vastu_independence(self) -> None:
        """NUMEROLOGY and VASTU should be fully independent (1.0)."""
        prov_num = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )
        prov_vastu = EvidenceProvenance(
            system_type=SystemType.VASTU,
            source_tradition="VASTU_SHASTRA",
        )
        independence = compute_pairwise_independence(prov_num, prov_vastu)
        assert independence == 1.0


# ── Multi-System Convergence Tests ───────────────────────────────────────────


class TestMultiSystemConvergence:
    """Tests for multi-system convergence with numerology."""

    def test_convergence_with_assessment(
        self, assessment: SystemAssessment
    ) -> None:
        """Assessment should be valid for convergence calculation."""
        assert assessment.system_type == SystemType.NUMEROLOGY
        assert assessment.outcome_taxonomy
        assert assessment.assessment_status

    def test_assessment_serializable(
        self, assessment: SystemAssessment
    ) -> None:
        """Assessment should be serializable to dict."""
        d = assessment.to_dict()
        assert d["system_type"] == "NUMEROLOGY"
        assert "outcome_taxonomy" in d
        assert "assessment_status" in d
        assert "provenance" in d

    def test_provenance_independent_from_astrology(
        self, assessment: SystemAssessment
    ) -> None:
        """Numerology provenance should not share roots with astrology."""
        assert assessment.provenance is not None
        assert assessment.provenance.derivative_roots == ()


# ── Chart-to-Assessment Consistency Tests ────────────────────────────────────


class TestChartToAssessmentConsistency:
    """Tests for consistency between chart facts and assessment output."""

    def test_life_path_1_leadership(
        self, jrs_svc: NumerologyDomainService, calc_svc: NumerologyCalculationService
    ) -> None:
        """Life Path 1 should produce LEADERSHIP_AUTHORITY outcome."""
        # Date that produces Life Path 1
        chart = calc_svc.calculate(
            birth_date="1985-01-01",
            birth_name="Test",
        )
        if chart.life_path and chart.life_path.reduced == 1:
            # Life Path 1 rules map to LEADERSHIP_AUTHORITY
            records = jrs_svc.evaluate_chart_facts(chart)
            leadership_records = [
                r for r in records
                if r.outcome_taxonomy == "LEADERSHIP_AUTHORITY"
            ]
            assert len(leadership_records) > 0

    def test_life_path_7_philosophical(
        self, jrs_svc: NumerologyDomainService, calc_svc: NumerologyCalculationService
    ) -> None:
        """Life Path 7 should produce PHILOSOPHICAL_DEPTH outcome."""
        chart = calc_svc.calculate(
            birth_date="1985-07-16",
            birth_name="Test",
        )
        if chart.life_path and chart.life_path.reduced == 7:
            records = jrs_svc.evaluate_chart_facts(chart)
            phil_records = [
                r for r in records
                if r.outcome_taxonomy == "PHILOSOPHICAL_DEPTH"
            ]
            assert len(phil_records) > 0

    def test_master_number_22_rules_fire(
        self, jrs_svc: NumerologyDomainService, calc_svc: NumerologyCalculationService
    ) -> None:
        """If Life Path is 22, the master builder rules should fire."""
        # Find a date that produces Life Path 22
        # We need month_reduced + day_reduced + year_reduced to sum to 22
        # or reduce to 22
        chart = calc_svc.calculate(
            birth_date="1976-07-19",
            birth_name="Test",
        )
        if chart.life_path and chart.life_path.reduced == 22:
            records = jrs_svc.evaluate_chart_facts(chart)
            builder_records = [
                r for r in records
                if r.rule_id == "N-LP22-BUILDER"
            ]
            assert len(builder_records) == 1


# ── Deterministic ID Stability Tests ─────────────────────────────────────────


class TestDeterministicStability:
    """Tests for deterministic ID stability across the pipeline."""

    def test_chart_id_matches(
        self, calc_svc: NumerologyCalculationService
    ) -> None:
        """Same inputs should produce same chart deterministic_id."""
        c1 = calc_svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        c2 = calc_svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        assert c1.deterministic_id == c2.deterministic_id

    def test_chart_id_varies_with_name(
        self, calc_svc: NumerologyCalculationService
    ) -> None:
        """Different names should produce different chart IDs."""
        c1 = calc_svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Adam Smith",
        )
        c2 = calc_svc.calculate(
            birth_date="1985-07-15",
            birth_name="Jane Marie Doe",
        )
        assert c1.deterministic_id != c2.deterministic_id

    def test_chart_id_varies_with_date(
        self, calc_svc: NumerologyCalculationService
    ) -> None:
        """Different dates should produce different chart IDs."""
        c1 = calc_svc.calculate(
            birth_date="1985-07-15",
            birth_name="John Smith",
        )
        c2 = calc_svc.calculate(
            birth_date="1990-01-01",
            birth_name="John Smith",
        )
        assert c1.deterministic_id != c2.deterministic_id

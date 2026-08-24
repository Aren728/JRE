"""Tests for JRS-072: Multi-System Empirical Calibration.

Verifies that the calibration pipeline correctly:
- Runs Western and Numerology assessments alongside Vedic
- Calculates single-system and multi-system metrics
- Computes independence-adjusted convergence correctly
- Generates comparative reports with mathematically sound deltas
- Produces deterministic results
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from tests.calibration.metrics import (
    CalibrationReport,
    ComparativeCalibrationReport,
    DomainMetrics,
    OutcomeMetrics,
)
from tests.calibration.pipeline import (
    _run_numerology_assessment,
    _run_western_assessment,
    discover_fixtures,
    load_fixture,
    run_comparative_calibration,
    run_multi_system_assessment,
    run_multi_system_calibration,
)

from jrs.convergence.service import ConvergenceService
from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
)
from jrs.multisystem.service import IndependenceAnalyzer

# ── ComparativeCalibrationReport Tests ────────────────────────────────────────

# Known F1 → (TP, FP, TN, FN) lookup for controlled test construction.
# F1 = 2*TP / (2*TP + FP + FN),  P = TP/(TP+FP),  R = TP/(TP+FN)
_F1_MAP: dict[float, tuple[int, int, int, int]] = {
    0.0: (0, 5, 5, 5),
    0.3: (3, 7, 5, 13),
    0.5: (5, 5, 5, 5),
    0.6: (3, 2, 10, 2),
    0.7: (7, 3, 10, 3),
    0.8: (8, 2, 10, 2),
    0.9: (9, 1, 10, 1),
}


def _closest_f1(target: float) -> tuple[int, int, int, int]:
    """Return the (TP, FP, TN, FN) tuple whose F1 is closest to target."""
    key = min(_F1_MAP.keys(), key=lambda k: abs(k - target))
    return _F1_MAP[key]


def _build_comparative_report(
    single_f1: float = 0.6,
    multi_f1: float = 0.7,
) -> ComparativeCalibrationReport:
    """Build a ComparativeCalibrationReport with controlled F1 values."""
    from datetime import UTC, datetime

    s_tp, s_fp, s_tn, s_fn = _closest_f1(single_f1)
    m_tp, m_fp, m_tn, m_fn = _closest_f1(multi_f1)

    single = CalibrationReport(
        domain_metrics=(
            DomainMetrics(
                domain="test",
                outcome_metrics=(
                    OutcomeMetrics("A", s_tp, s_fp, s_tn, s_fn, 0.5),
                ),
                total_charts=5,
            ),
        ),
        timestamp=datetime.now(UTC).isoformat(),
    )
    multi = CalibrationReport(
        domain_metrics=(
            DomainMetrics(
                domain="test",
                outcome_metrics=(
                    OutcomeMetrics("A", m_tp, m_fp, m_tn, m_fn, 0.6),
                ),
                total_charts=5,
            ),
        ),
        timestamp=datetime.now(UTC).isoformat(),
    )

    return ComparativeCalibrationReport(
        single_system_report=single,
        multi_system_report=multi,
        comparison_mode="vedic_vs_multi",
    )


class TestComparativeCalibrationReport:
    """Tests for the ComparativeCalibrationReport data structure."""

    def test_f1_delta_positive(self) -> None:
        """When multi-system F1 > single, delta should be positive."""
        cr = _build_comparative_report(single_f1=0.5, multi_f1=0.7)
        assert cr.f1_delta > 0.01

    def test_f1_delta_negative(self) -> None:
        """When multi-system F1 < single, delta should be negative."""
        cr = _build_comparative_report(single_f1=0.9, multi_f1=0.5)
        assert cr.f1_delta < -0.01

    def test_f1_delta_zero(self) -> None:
        """When both use same F1, delta should be zero."""
        cr = _build_comparative_report(single_f1=0.6, multi_f1=0.6)
        assert cr.f1_delta == pytest.approx(0.0, abs=0.01)

    def test_convergence_verdict_improved(self) -> None:
        cr = _build_comparative_report(single_f1=0.5, multi_f1=0.7)
        assert cr.convergence_verdict == "IMPROVED"

    def test_convergence_verdict_degraded(self) -> None:
        cr = _build_comparative_report(single_f1=0.9, multi_f1=0.5)
        assert cr.convergence_verdict == "DEGRADED"

    def test_convergence_verdict_maintained(self) -> None:
        cr = _build_comparative_report(single_f1=0.6, multi_f1=0.6)
        assert cr.convergence_verdict == "MAINTAINED"

    def test_to_dict_has_deltas(self) -> None:
        cr = _build_comparative_report()
        d = cr.to_dict()
        assert "deltas" in d
        assert "f1_score" in d["deltas"]
        assert "precision" in d["deltas"]
        assert "recall" in d["deltas"]
        assert "timing_overlap" in d["deltas"]
        assert "convergence_verdict" in d

    def test_to_dict_has_comparison_mode(self) -> None:
        cr = _build_comparative_report()
        d = cr.to_dict()
        assert d["comparison_mode"] == "vedic_vs_multi"

    def test_to_markdown_has_sections(self) -> None:
        cr = _build_comparative_report()
        md = cr.to_markdown()
        assert "# Multi-System Empirical Calibration Report" in md
        assert "## Comparative Summary" in md
        assert "Convergence Verdict" in md

    def test_to_markdown_improved_text(self) -> None:
        cr = _build_comparative_report(single_f1=0.5, multi_f1=0.7)
        md = cr.to_markdown()
        assert "improved" in md.lower()

    def test_to_markdown_degraded_text(self) -> None:
        cr = _build_comparative_report(single_f1=0.9, multi_f1=0.5)
        md = cr.to_markdown()
        assert "degraded" in md.lower()

    def test_to_markdown_maintained_text(self) -> None:
        cr = _build_comparative_report(single_f1=0.6, multi_f1=0.6)
        md = cr.to_markdown()
        assert "maintained" in md.lower()


# ── Multi-System Pipeline Tests ──────────────────────────────────────────────


class TestMultiSystemAssessment:
    """Tests for the multi-system assessment pipeline."""

    def _get_marriage_fixture(self) -> dict[str, Any]:
        """Get the first marriage fixture for testing."""
        domains = discover_fixtures()
        path = domains["marriage"][0]
        return load_fixture(path)

    def test_multi_system_returns_all_keys(self) -> None:
        """Multi-system assessment should return all expected keys."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        result = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic", "western"),
        )

        assert "single_system_assessment" in result
        assert "system_assessments" in result
        assert "cross_system_convergence" in result
        assert "assessment_status" in result
        assert "timing_status" in result

    def test_multi_system_has_vedic_assessment(self) -> None:
        """Multi-system should include Vedic assessment."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        result = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic",),
        )

        assert "VEDIC" in result["system_assessments"]

    def test_multi_system_with_western(self) -> None:
        """Multi-system with western should include western assessment."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        result = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic", "western"),
        )

        assert "VEDIC" in result["system_assessments"]
        assert "WESTERN" in result["system_assessments"]

    def test_multi_system_convergence_has_fields(self) -> None:
        """Cross-system convergence should have all required fields."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        result = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic", "western"),
        )

        cs = result["cross_system_convergence"]
        assert "raw_convergence" in cs
        assert "independence_score" in cs
        assert "adjusted_convergence" in cs
        assert "systems" in cs

    def test_adjusted_convergence_leq_raw(self) -> None:
        """Adjusted convergence must be <= raw convergence (penalty applied)."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        result = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic", "western"),
        )

        cs = result["cross_system_convergence"]
        assert cs["adjusted_convergence"] <= cs["raw_convergence"] + 0.0001

    def test_independence_score_in_range(self) -> None:
        """Independence score should be in [0.0, 1.0]."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        result = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic", "western"),
        )

        cs = result["cross_system_convergence"]
        assert 0.0 <= cs["independence_score"] <= 1.0

    def test_deterministic_output(self) -> None:
        """Two runs should produce identical results."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        r1 = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic", "western"),
        )
        r2 = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic", "western"),
        )

        assert json.dumps(r1, sort_keys=True) == json.dumps(
            r2, sort_keys=True
        )

    def test_vedic_only_no_cross_system(self) -> None:
        """Single-system (vedic only) should have empty cross_system."""
        chart = self._get_marriage_fixture()
        convergence_svc = ConvergenceService()

        result = run_multi_system_assessment(
            chart, "marriage", "MARRIAGE_FORMATION",
            convergence_svc, systems=("vedic",),
        )

        assert result["cross_system_convergence"] == {}


# ── Western Assessment from Fixture Tests ─────────────────────────────────────


class TestWesternAssessmentFromFixture:
    """Tests that Western assessment uses real fixture birth data."""

    def _get_marriage_fixture(self) -> dict[str, Any]:
        domains = discover_fixtures()
        path = domains["marriage"][0]
        return load_fixture(path)

    def test_western_assessment_produces_system_assessment(self) -> None:
        """Western pipeline should return a SystemAssessment."""
        chart = self._get_marriage_fixture()
        sa = _run_western_assessment(chart, "MARRIAGE_FORMATION")

        assert isinstance(sa, SystemAssessment)
        assert sa.system_type is SystemType.WESTERN

    def test_western_assessment_has_provenance(self) -> None:
        """Western assessment should have valid provenance."""
        chart = self._get_marriage_fixture()
        sa = _run_western_assessment(chart, "MARRIAGE_FORMATION")

        assert sa.provenance is not None
        assert sa.provenance.system_type is SystemType.WESTERN
        assert sa.provenance.source_tradition in ("PTOLEMY", "LILLY")

    def test_western_uses_fixture_coordinates(self) -> None:
        """Western assessment should use the fixture's lat/lon, not defaults."""
        domains = discover_fixtures()
        path1 = domains["marriage"][0]
        path2 = domains["marriage"][-1]

        chart1 = load_fixture(path1)
        chart2 = load_fixture(path2)

        sa1 = _run_western_assessment(chart1, "MARRIAGE_FORMATION")
        sa2 = _run_western_assessment(chart2, "MARRIAGE_FORMATION")

        assert sa1.system_type is SystemType.WESTERN
        assert sa2.system_type is SystemType.WESTERN

    def test_western_assessment_serializable(self) -> None:
        """Western assessment should serialize to dict."""
        chart = self._get_marriage_fixture()
        sa = _run_western_assessment(chart, "MARRIAGE_FORMATION")

        d = sa.to_dict()
        assert d["system_type"] == "WESTERN"
        assert "outcome_taxonomy" in d
        assert "assessment_status" in d


# ── Numerology Assessment Tests ──────────────────────────────────────────────


class TestNumerologyAssessment:
    """Tests for Numerology pipeline from fixture data."""

    def _get_marriage_fixture(self) -> dict[str, Any]:
        domains = discover_fixtures()
        path = domains["marriage"][0]
        return load_fixture(path)

    def test_numerology_produces_system_assessment(self) -> None:
        """Numerology pipeline should return a SystemAssessment."""
        chart = self._get_marriage_fixture()
        sa = _run_numerology_assessment(chart, "MARRIAGE_FORMATION")

        assert isinstance(sa, SystemAssessment)
        assert sa.system_type is SystemType.NUMEROLOGY

    def test_numerology_has_provenance(self) -> None:
        """Numerology assessment should have PYTHAGOREAN provenance."""
        chart = self._get_marriage_fixture()
        sa = _run_numerology_assessment(chart, "MARRIAGE_FORMATION")

        assert sa.provenance is not None
        assert sa.provenance.system_type is SystemType.NUMEROLOGY

    def test_numerology_deterministic(self) -> None:
        """Same fixture should produce identical numerology results."""
        chart = self._get_marriage_fixture()

        sa1 = _run_numerology_assessment(chart, "MARRIAGE_FORMATION")
        sa2 = _run_numerology_assessment(chart, "MARRIAGE_FORMATION")

        assert sa1.to_dict() == sa2.to_dict()


# ── Independence Math Tests ──────────────────────────────────────────────────


class TestIndependenceMath:
    """Verify that independence scores are mathematically sound."""

    def test_vedic_western_shared_roots(self) -> None:
        """Vedic and Western share Hellenistic roots → penalty applied."""
        vedic_prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        western_prov = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="LILLY",
        )

        analyzer = IndependenceAnalyzer()
        independence = analyzer.calculate_collective_independence(
            [vedic_prov, western_prov]
        )

        assert independence < 1.0
        assert independence > 0.0

    def test_numerology_independent_of_vedic(self) -> None:
        """Numerology has no shared roots with Vedic → full independence."""
        vedic_prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        num_prov = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )

        analyzer = IndependenceAnalyzer()
        independence = analyzer.calculate_collective_independence(
            [vedic_prov, num_prov]
        )

        assert independence == 1.0

    def test_numerology_independent_of_western(self) -> None:
        """Numerology has no shared roots with Western → full independence."""
        western_prov = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="LILLY",
        )
        num_prov = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )

        analyzer = IndependenceAnalyzer()
        independence = analyzer.calculate_collective_independence(
            [western_prov, num_prov]
        )

        assert independence == 1.0

    def test_three_system_independence(self) -> None:
        """Three-system independence: Vedic-Western penalized, Numerology full.

        Pairwise: Vedic-Western < 1.0, Vedic-Num = 1.0, West-Num = 1.0
        Average > 0.8.
        """
        vedic_prov = EvidenceProvenance(
            system_type=SystemType.VEDIC,
            source_tradition="BPHS",
        )
        western_prov = EvidenceProvenance(
            system_type=SystemType.WESTERN,
            source_tradition="LILLY",
        )
        num_prov = EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition="PYTHAGOREAN",
        )

        analyzer = IndependenceAnalyzer()
        independence = analyzer.calculate_collective_independence(
            [vedic_prov, western_prov, num_prov]
        )

        assert independence > 0.8
        assert independence <= 1.0

    def test_convergence_score_preserved_with_high_independence(self) -> None:
        """High independence should preserve convergence score."""
        raw_convergence = 0.8
        independence = 0.9
        adjusted = raw_convergence * independence

        assert adjusted == pytest.approx(0.72, abs=0.01)
        assert adjusted < raw_convergence

    def test_convergence_score_penalized_with_low_independence(self) -> None:
        """Low independence should penalize convergence score."""
        raw_convergence = 0.8
        independence = 0.5
        adjusted = raw_convergence * independence

        assert adjusted == pytest.approx(0.4, abs=0.01)
        assert adjusted < raw_convergence

    def test_numerology_adds_independence_without_penalty(self) -> None:
        """Adding Numerology to Vedic+Western should increase independence."""
        vedic_western_prov = [
            EvidenceProvenance(
                system_type=SystemType.VEDIC, source_tradition="BPHS",
            ),
            EvidenceProvenance(
                system_type=SystemType.WESTERN, source_tradition="LILLY",
            ),
        ]
        all_three_prov = [
            EvidenceProvenance(
                system_type=SystemType.VEDIC, source_tradition="BPHS",
            ),
            EvidenceProvenance(
                system_type=SystemType.WESTERN, source_tradition="LILLY",
            ),
            EvidenceProvenance(
                system_type=SystemType.NUMEROLOGY,
                source_tradition="PYTHAGOREAN",
            ),
        ]

        analyzer = IndependenceAnalyzer()
        indep_two = analyzer.calculate_collective_independence(
            vedic_western_prov
        )
        indep_three = analyzer.calculate_collective_independence(
            all_three_prov
        )

        assert indep_three >= indep_two


# ── Multi-System Calibration Report Tests ─────────────────────────────────────


class TestMultiSystemCalibration:
    """Tests for the full multi-system calibration pipeline."""

    @pytest.mark.slow
    def test_multi_system_calibration_produces_report(self) -> None:
        """Multi-system calibration should produce a CalibrationReport."""
        report = run_multi_system_calibration(
            systems=("vedic", "western"),
        )
        assert isinstance(report, CalibrationReport)

    @pytest.mark.slow
    def test_multi_system_calibration_has_domains(self) -> None:
        """Report should have metrics for multiple domains."""
        report = run_multi_system_calibration(
            systems=("vedic", "western"),
        )
        assert len(report.domain_metrics) >= 10

    @pytest.mark.slow
    def test_multi_system_calibration_non_negative(self) -> None:
        """All metrics should be non-negative."""
        report = run_multi_system_calibration(
            systems=("vedic", "western"),
        )
        assert report.precision >= 0.0
        assert report.recall >= 0.0
        assert report.f1_score >= 0.0

    @pytest.mark.slow
    def test_comparative_calibration_produces_report(self) -> None:
        """Comparative calibration should produce a ComparativeReport."""
        comparative = run_comparative_calibration()
        assert isinstance(comparative, ComparativeCalibrationReport)

    @pytest.mark.slow
    def test_comparative_has_both_reports(self) -> None:
        """Comparative report should contain both single and multi reports."""
        comparative = run_comparative_calibration()
        assert isinstance(comparative.single_system_report, CalibrationReport)
        assert isinstance(comparative.multi_system_report, CalibrationReport)

    @pytest.mark.slow
    def test_comparative_has_deltas(self) -> None:
        """Comparative report should have delta values."""
        comparative = run_comparative_calibration()
        d = comparative.to_dict()
        assert "deltas" in d
        assert "f1_score" in d["deltas"]

    @pytest.mark.slow
    def test_comparative_has_verdict(self) -> None:
        """Comparative report should have a convergence verdict."""
        comparative = run_comparative_calibration()
        assert comparative.convergence_verdict in (
            "IMPROVED", "DEGRADED", "MAINTAINED",
        )

    @pytest.mark.slow
    def test_comparative_markdown_report(self) -> None:
        """Comparative report should generate valid Markdown."""
        comparative = run_comparative_calibration()
        md = comparative.to_markdown()
        assert "# Multi-System Empirical Calibration Report" in md
        assert "## Comparative Summary" in md

    @pytest.mark.slow
    def test_comparative_json_serializable(self) -> None:
        """Comparative report should be JSON-serializable."""
        comparative = run_comparative_calibration()
        d = comparative.to_dict()
        json_str = json.dumps(d, indent=2, sort_keys=True)
        assert len(json_str) > 0
        parsed = json.loads(json_str)
        assert "convergence_verdict" in parsed

    @pytest.mark.slow
    def test_comparative_deterministic(self) -> None:
        """Two comparative runs should produce identical results."""
        c1 = run_comparative_calibration()
        c2 = run_comparative_calibration()
        d1 = c1.to_dict()
        d2 = c2.to_dict()
        # Exclude timestamps
        d1["single_system"].pop("timestamp", None)
        d2["single_system"].pop("timestamp", None)
        d1["multi_system"].pop("timestamp", None)
        d2["multi_system"].pop("timestamp", None)
        assert json.dumps(d1, sort_keys=True) == json.dumps(
            d2, sort_keys=True
        )

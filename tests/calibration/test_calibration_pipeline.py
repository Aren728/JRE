"""Tests for calibration pipeline — fixture discovery, execution, and reporting."""

from __future__ import annotations

import json

from tests.calibration.metrics import CalibrationReport
from tests.calibration.pipeline import (
    discover_fixtures,
    load_fixture,
    run_calibration,
    run_single_assessment,
)

from jrs.convergence.service import ConvergenceService

# ── Fixture Discovery ────────────────────────────────────────────────────────


class TestFixtureDiscovery:
    """Tests for validation fixture discovery."""

    def test_discovers_all_domains(self) -> None:
        """Should discover at least 10 domain directories."""
        domains = discover_fixtures()
        assert len(domains) >= 10

    def test_marriage_domain_has_fixtures(self) -> None:
        domains = discover_fixtures()
        assert "marriage" in domains
        assert len(domains["marriage"]) >= 5

    def test_career_domain_has_fixtures(self) -> None:
        domains = discover_fixtures()
        assert "career" in domains
        assert len(domains["career"]) >= 5

    def test_wealth_domain_has_fixtures(self) -> None:
        domains = discover_fixtures()
        assert "wealth" in domains
        assert len(domains["wealth"]) >= 4

    def test_all_fixtures_are_json(self) -> None:
        """All discovered fixtures should be .json files."""
        domains = discover_fixtures()
        for domain, paths in domains.items():
            for path in paths:
                assert path.suffix == ".json", (
                    f"{domain}: {path.name} is not JSON"
                )

    def test_total_fixture_count(self) -> None:
        """Should discover at least 50 fixtures across all domains."""
        domains = discover_fixtures()
        total = sum(len(paths) for paths in domains.values())
        assert total >= 50


# ── Fixture Loading ──────────────────────────────────────────────────────────


class TestFixtureLoading:
    """Tests for fixture loading and validation."""

    def test_load_marriage_fixture(self) -> None:
        """Should load a marriage fixture with required fields."""
        domains = discover_fixtures()
        path = domains["marriage"][0]
        chart = load_fixture(path)
        assert "chart_id" in chart
        assert "natal_facts" in chart
        assert "expected_assessments" in chart

    def test_all_fixtures_have_required_fields(self) -> None:
        """Every fixture should have chart_id, natal_facts, expected_assessments."""
        domains = discover_fixtures()
        for _domain, paths in domains.items():
            for path in paths:
                chart = load_fixture(path)
                assert "chart_id" in chart, f"{path.name}: missing chart_id"
                assert "natal_facts" in chart, f"{path.name}: missing natal_facts"
                assert "expected_assessments" in chart, (
                    f"{path.name}: missing expected_assessments"
                )

    def test_all_fixtures_have_assessment_fields(self) -> None:
        """Each expected_assessment should have assessment_status."""
        domains = discover_fixtures()
        for _domain, paths in domains.items():
            for path in paths:
                chart = load_fixture(path)
                for outcome, assessment in chart["expected_assessments"].items():
                    assert "assessment_status" in assessment, (
                        f"{path.name}/{outcome}: missing assessment_status"
                    )

    def test_fixture_json_roundtrip(self) -> None:
        """Loaded fixtures should survive JSON serialization roundtrip."""
        domains = discover_fixtures()
        path = domains["marriage"][0]
        chart = load_fixture(path)
        serialized = json.dumps(chart, sort_keys=True)
        deserialized = json.loads(serialized)
        assert deserialized["chart_id"] == chart["chart_id"]


# ── Single Assessment ────────────────────────────────────────────────────────


class TestSingleAssessment:
    """Tests for running a single assessment through the pipeline."""

    def test_marriage_formation_assessment(self) -> None:
        """Should produce a valid DomainAssessment for marriage."""
        domains = discover_fixtures()
        path = domains["marriage"][0]
        chart = load_fixture(path)
        convergence_svc = ConvergenceService()

        result = run_single_assessment(
            chart, "marriage", "MARRIAGE_FORMATION", convergence_svc,
        )
        assert "assessment_status" in result
        assert "timing_status" in result
        assert "overall_evidence_strength" in result

    def test_assessment_has_valid_status(self) -> None:
        """Generated status should be a valid AssessmentStatus value."""
        from jrs.convergence.models import AssessmentStatus

        valid_statuses = {s.value for s in AssessmentStatus}
        domains = discover_fixtures()
        path = domains["marriage"][0]
        chart = load_fixture(path)
        convergence_svc = ConvergenceService()

        result = run_single_assessment(
            chart, "marriage", "MARRIAGE_FORMATION", convergence_svc,
        )
        assert result["assessment_status"] in valid_statuses

    def test_deterministic_assessment(self) -> None:
        """Same inputs should produce identical assessments."""
        domains = discover_fixtures()
        path = domains["marriage"][0]
        chart = load_fixture(path)
        convergence_svc = ConvergenceService()

        r1 = run_single_assessment(
            chart, "marriage", "MARRIAGE_FORMATION", convergence_svc,
        )
        r2 = run_single_assessment(
            chart, "marriage", "MARRIAGE_FORMATION", convergence_svc,
        )
        assert json.dumps(r1, sort_keys=True) == json.dumps(r2, sort_keys=True)


# ── Full Calibration Run ─────────────────────────────────────────────────────


class TestFullCalibration:
    """Tests for the full calibration run across all domains."""

    def test_calibration_produces_report(self) -> None:
        """Full calibration should produce a CalibrationReport."""
        report = run_calibration()
        assert isinstance(report, CalibrationReport)

    def test_calibration_covers_domains(self) -> None:
        """Report should have metrics for at least 10 domains."""
        report = run_calibration()
        assert len(report.domain_metrics) >= 10

    def test_calibration_has_positive_metrics(self) -> None:
        """Report should have non-negative metrics."""
        report = run_calibration()
        assert report.precision >= 0.0
        assert report.recall >= 0.0
        assert report.f1_score >= 0.0

    def test_calibration_to_dict(self) -> None:
        """Report should serialize to a valid dict."""
        report = run_calibration()
        d = report.to_dict()
        assert "precision" in d
        assert "recall" in d
        assert "f1_score" in d
        assert "domains" in d
        assert len(d["domains"]) >= 10

    def test_calibration_to_markdown(self) -> None:
        """Report should generate valid Markdown."""
        report = run_calibration()
        md = report.to_markdown()
        assert "# Calibration Report" in md
        assert "## marriage" in md
        assert "## career" in md

    def test_calibration_json_serializable(self) -> None:
        """Report dict should be JSON-serializable."""
        report = run_calibration()
        d = report.to_dict()
        json_str = json.dumps(d, indent=2, sort_keys=True)
        assert len(json_str) > 0
        # Should be parseable back
        parsed = json.loads(json_str)
        assert parsed["domain_count"] >= 10

    def test_per_domain_outcome_metrics(self) -> None:
        """Each domain should have per-outcome metrics."""
        report = run_calibration()
        for dm in report.domain_metrics:
            assert len(dm.outcome_metrics) > 0, (
                f"Domain {dm.domain} has no outcome metrics"
            )

    def test_calibration_report_deterministic(self) -> None:
        """Two calibration runs should produce identical results."""
        r1 = run_calibration()
        r2 = run_calibration()
        d1 = r1.to_dict()
        d2 = r2.to_dict()
        # Exclude timestamp for comparison
        d1.pop("timestamp", None)
        d2.pop("timestamp", None)
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

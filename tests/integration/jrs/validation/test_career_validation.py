"""Integration tests for Career domain validation against reference charts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jrs.convergence.models import AssessmentStatus, TimingStatus, OverallEvidenceStrength
from jrs.convergence.service import ConvergenceService
from jrs.domains.career.models import CareerOutcomeTaxonomy
from jrs.domains.career.service import CareerDomainService
from jrs.evidence.models import EvidenceRecord
from jrs.temporal.models import ActivationType, EventWindow, TemporalTrigger

_FIXTURES_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "fixtures" / "validation_charts" / "career_domain"
)


@pytest.fixture
def career_svc() -> CareerDomainService:
    """Create a CareerDomainService."""
    return CareerDomainService()


@pytest.fixture
def convergence_svc() -> ConvergenceService:
    """Create a ConvergenceService."""
    return ConvergenceService()


def load_chart(chart_file: str) -> dict:
    """Load a reference chart from the fixtures directory."""
    path = _FIXTURES_DIR / chart_file
    with path.open() as f:
        return json.load(f)


def extract_evidence_records(
    chart: dict,
    career_svc: CareerDomainService,
) -> tuple[EvidenceRecord, ...]:
    """Extract evidence records from chart natal facts using career rules."""
    facts = chart.get("natal_facts", {})
    return career_svc.evaluate_career_facts(facts)


def extract_event_windows(
    chart: dict,
) -> tuple[EventWindow, ...]:
    """Extract event windows from chart dasha and transit periods."""
    windows: list[EventWindow] = []

    dasha_raw = chart.get("dasha_periods", [])
    for d in dasha_raw:
        trigger = TemporalTrigger(
            activation_type=ActivationType(d["activation_type"]),
            triggering_planet=d.get("triggering_planet", ""),
            activation_start_utc=d.get("activation_start_utc", ""),
            activation_end_utc=d.get("activation_end_utc", ""),
            strength=float(d.get("strength", 1.0)),
        )
        windows.append(EventWindow(
            candidate_event_taxonomy="CAREER_ASCENT",
            triggers=(trigger,),
        ))

    transit_raw = chart.get("transits", [])
    for t in transit_raw:
        trigger = TemporalTrigger(
            activation_type=ActivationType(t["activation_type"]),
            triggering_planet=t.get("triggering_planet", ""),
            activation_start_utc=t.get("activation_start_utc", ""),
            activation_end_utc=t.get("activation_end_utc", ""),
            strength=float(t.get("strength", 1.0)),
        )
        windows.append(EventWindow(
            candidate_event_taxonomy="CAREER_ASCENT",
            triggers=(trigger,),
        ))

    return tuple(windows)


def run_pipeline(
    chart: dict,
    career_svc: CareerDomainService,
    convergence_svc: ConvergenceService,
    outcome_taxonomy: str,
) -> dict:
    """Run the full JRS Career pipeline for a single outcome.

    Steps:
        1. Extract Facts (natal_facts from chart)
        2. Generate Evidence Records (JRS-031 career rules)
        3. Calculate Temporal Windows (JRS-028 dasha/transits)
        4. Assess Convergence (JRS-029)
    """
    # Step 1 & 2: Extract facts and generate evidence records
    evidence_records = extract_evidence_records(chart, career_svc)

    # Step 3: Calculate temporal windows
    event_windows = extract_event_windows(chart)

    # Step 4: Assess convergence
    assessment = convergence_svc.assess_domain(
        outcome_taxonomy,
        evidence_records=evidence_records,
        event_windows=event_windows,
    )

    return assessment.to_dict()


# ── Chart 1: Government Service ──────────────────────────────────────────────


class TestChart01GovernmentService:
    """Validation tests for Chart 1 - government service."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_01_government_service.json")

    def test_government_service(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "GOVERNMENT_SERVICE",
        )
        expected = chart["expected_assessments"]["GOVERNMENT_SERVICE"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_authority_status(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "AUTHORITY_STATUS",
        )
        expected = chart["expected_assessments"]["AUTHORITY_STATUS"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_career_ascent(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "CAREER_ASCENT",
        )
        expected = chart["expected_assessments"]["CAREER_ASCENT"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Chart 2: Successful Business ─────────────────────────────────────────────


class TestChart02SuccessfulBusiness:
    """Validation tests for Chart 2 - successful business."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_02_successful_business.json")

    def test_successful_business(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "SUCCESSFUL_BUSINESS",
        )
        expected = chart["expected_assessments"]["SUCCESSFUL_BUSINESS"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_entrepreneurship(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "ENTREPRENEURSHIP",
        )
        expected = chart["expected_assessments"]["ENTREPRENEURSHIP"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_career_ascent(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "CAREER_ASCENT",
        )
        expected = chart["expected_assessments"]["CAREER_ASCENT"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Chart 3: Foreign Career ──────────────────────────────────────────────────


class TestChart03ForeignCareer:
    """Validation tests for Chart 3 - foreign career."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_03_foreign_career.json")

    def test_foreign_career(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "FOREIGN_CAREER",
        )
        expected = chart["expected_assessments"]["FOREIGN_CAREER"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_change_of_profession(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "CHANGE_OF_PROFESSION",
        )
        expected = chart["expected_assessments"]["CHANGE_OF_PROFESSION"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_government_not_supported(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "GOVERNMENT_SERVICE",
        )
        expected = chart["expected_assessments"]["GOVERNMENT_SERVICE"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Chart 4: Career Obstacles ────────────────────────────────────────────────


class TestChart04CareerObstacles:
    """Validation tests for Chart 4 - career obstacles."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_04_career_obstacles.json")

    def test_career_obstacles(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "CAREER_OBSTACLES",
        )
        expected = chart["expected_assessments"]["CAREER_OBSTACLES"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["overall_evidence_strength"] == expected["overall_evidence_strength"]

    def test_professional_stagnation(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "PROFESSIONAL_STAGNATION",
        )
        expected = chart["expected_assessments"]["PROFESSIONAL_STAGNATION"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_loss_of_employment(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "LOSS_OF_EMPLOYMENT",
        )
        expected = chart["expected_assessments"]["LOSS_OF_EMPLOYMENT"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Chart 5: Creative Career ─────────────────────────────────────────────────


class TestChart05CreativeCareer:
    """Validation tests for Chart 5 - creative career."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_05_creative_career.json")

    def test_creative_career(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "CREATIVE_CAREER",
        )
        expected = chart["expected_assessments"]["CREATIVE_CAREER"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_financial_prosperity(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "FINANCIAL_PROSPERITY",
        )
        expected = chart["expected_assessments"]["FINANCIAL_PROSPERITY"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_career_ascent(
        self,
        chart: dict,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, career_svc, convergence_svc, "CAREER_ASCENT",
        )
        expected = chart["expected_assessments"]["CAREER_ASCENT"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Cross-Chart Determinism ──────────────────────────────────────────────────


class TestCrossChartDeterminism:
    """Test that the pipeline produces deterministic results."""

    def test_all_charts_deterministic(
        self,
        career_svc: CareerDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        """Verify byte-identical output for identical inputs across all charts."""
        chart_files = [
            "chart_01_government_service.json",
            "chart_02_successful_business.json",
            "chart_03_foreign_career.json",
            "chart_04_career_obstacles.json",
            "chart_05_creative_career.json",
        ]

        for chart_file in chart_files:
            chart = load_chart(chart_file)
            for outcome in chart["expected_assessments"]:
                r1 = run_pipeline(
                    chart, career_svc, convergence_svc, outcome,
                )
                r2 = run_pipeline(
                    chart, career_svc, convergence_svc, outcome,
                )
                assert json.dumps(r1, sort_keys=True) == json.dumps(
                    r2, sort_keys=True,
                ), f"Non-deterministic output for {chart_file}/{outcome}"


# ── Fixture Validation ───────────────────────────────────────────────────────


class TestFixturesValid:
    """Validate that all fixture files are well-formed."""

    def test_all_fixtures_exist(self) -> None:
        expected_files = [
            "chart_01_government_service.json",
            "chart_02_successful_business.json",
            "chart_03_foreign_career.json",
            "chart_04_career_obstacles.json",
            "chart_05_creative_career.json",
        ]
        for f in expected_files:
            assert (_FIXTURES_DIR / f).exists(), f"Missing fixture: {f}"

    def test_all_fixtures_have_required_fields(self) -> None:
        chart_files = [
            "chart_01_government_service.json",
            "chart_02_successful_business.json",
            "chart_03_foreign_career.json",
            "chart_04_career_obstacles.json",
            "chart_05_creative_career.json",
        ]
        for chart_file in chart_files:
            chart = load_chart(chart_file)
            assert "chart_id" in chart, f"{chart_file} missing chart_id"
            assert "natal_facts" in chart, f"{chart_file} missing natal_facts"
            assert "expected_assessments" in chart, f"{chart_file} missing expected_assessments"
            assert len(chart["expected_assessments"]) >= 3, (
                f"{chart_file} should have at least 3 expected assessments"
            )

    def test_distinct_outcomes_across_charts(self) -> None:
        """Verify at least 3 distinct outcome types are tested."""
        all_outcomes: set[str] = set()
        chart_files = [
            "chart_01_government_service.json",
            "chart_02_successful_business.json",
            "chart_03_foreign_career.json",
            "chart_04_career_obstacles.json",
            "chart_05_creative_career.json",
        ]
        for chart_file in chart_files:
            chart = load_chart(chart_file)
            all_outcomes.update(chart["expected_assessments"].keys())
        assert len(all_outcomes) >= 3, (
            f"Expected at least 3 distinct outcomes, got {len(all_outcomes)}: {all_outcomes}"
        )

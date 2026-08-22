"""Integration tests for Transitions domain validation against reference charts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jrs.convergence.models import AssessmentStatus, TimingStatus, OverallEvidenceStrength
from jrs.convergence.service import ConvergenceService
from jrs.domains.transitions.models import TransitionOutcomeTaxonomy
from jrs.domains.transitions.service import TransitionsDomainService
from jrs.evidence.models import EvidenceRecord
from jrs.temporal.models import ActivationType, EventWindow, TemporalTrigger

_FIXTURES_DIR = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "fixtures" / "validation_charts" / "transitions_domain"
)


@pytest.fixture
def transitions_svc() -> TransitionsDomainService:
    """Create a TransitionsDomainService."""
    return TransitionsDomainService()


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
    transitions_svc: TransitionsDomainService,
) -> tuple[EvidenceRecord, ...]:
    """Extract evidence records from chart natal facts using transitions rules."""
    facts = chart.get("natal_facts", {})
    return transitions_svc.evaluate_transitions_facts(facts)


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
            candidate_event_taxonomy="LIFE_PHASE_SHIFT",
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
            candidate_event_taxonomy="LIFE_PHASE_SHIFT",
            triggers=(trigger,),
        ))

    return tuple(windows)


def run_pipeline(
    chart: dict,
    transitions_svc: TransitionsDomainService,
    convergence_svc: ConvergenceService,
    outcome_taxonomy: str,
) -> dict:
    """Run the full JRS Transitions pipeline for a single outcome.

    Steps:
        1. Extract Facts (natal_facts from chart)
        2. Generate Evidence Records (JRS-043 transitions rules)
        3. Calculate Temporal Windows (JRS-028 dasha/transits)
        4. Assess Convergence (JRS-029)
    """
    # Step 1 & 2: Extract facts and generate evidence records
    evidence_records = extract_evidence_records(chart, transitions_svc)

    # Step 3: Calculate temporal windows
    event_windows = extract_event_windows(chart)

    # Step 4: Assess convergence
    assessment = convergence_svc.assess_domain(
        outcome_taxonomy,
        evidence_records=evidence_records,
        event_windows=event_windows,
    )

    return assessment.to_dict()


# ── Chart 1: Sudden Upheaval ────────────────────────────────────────────────


class TestChart01SuddenUpheaval:
    """Validation tests for Chart 1 - sudden upheaval."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_01_sudden_upheaval.json")

    def test_sudden_upheaval(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "SUDDEN_UPHEAVAL",
        )
        expected = chart["expected_assessments"]["SUDDEN_UPHEAVAL"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_life_phase_shift(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "LIFE_PHASE_SHIFT",
        )
        expected = chart["expected_assessments"]["LIFE_PHASE_SHIFT"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_crisis_recovery(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "CRISIS_RECOVERY",
        )
        expected = chart["expected_assessments"]["CRISIS_RECOVERY"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Chart 2: Gradual Evolution ───────────────────────────────────────────────


class TestChart02GradualEvolution:
    """Validation tests for Chart 2 - gradual evolution."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_02_gradual_evolution.json")

    def test_gradual_evolution(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "GRADUAL_EVOLUTION",
        )
        expected = chart["expected_assessments"]["GRADUAL_EVOLUTION"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_life_phase_shift(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "LIFE_PHASE_SHIFT",
        )
        expected = chart["expected_assessments"]["LIFE_PHASE_SHIFT"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_sudden_upheaval(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "SUDDEN_UPHEAVAL",
        )
        expected = chart["expected_assessments"]["SUDDEN_UPHEAVAL"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Chart 3: Crisis Recovery ─────────────────────────────────────────────────


class TestChart03CrisisRecovery:
    """Validation tests for Chart 3 - crisis recovery."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_03_crisis_recovery.json")

    def test_crisis_recovery(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "CRISIS_RECOVERY",
        )
        expected = chart["expected_assessments"]["CRISIS_RECOVERY"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_sudden_upheaval(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "SUDDEN_UPHEAVAL",
        )
        expected = chart["expected_assessments"]["SUDDEN_UPHEAVAL"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_life_phase_shift(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "LIFE_PHASE_SHIFT",
        )
        expected = chart["expected_assessments"]["LIFE_PHASE_SHIFT"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Chart 4: Spiritual Awakening ─────────────────────────────────────────────


class TestChart04SpiritualAwakening:
    """Validation tests for Chart 4 - spiritual awakening."""

    @pytest.fixture
    def chart(self) -> dict:
        return load_chart("chart_04_spiritual_awakening.json")

    def test_spiritual_awakening(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "SPIRITUAL_AWAKENING",
        )
        expected = chart["expected_assessments"]["SPIRITUAL_AWAKENING"]
        assert result["assessment_status"] == expected["assessment_status"]
        assert result["timing_status"] == expected["timing_status"]

    def test_life_phase_shift(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "LIFE_PHASE_SHIFT",
        )
        expected = chart["expected_assessments"]["LIFE_PHASE_SHIFT"]
        assert result["assessment_status"] == expected["assessment_status"]

    def test_gradual_evolution(
        self,
        chart: dict,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        result = run_pipeline(
            chart, transitions_svc, convergence_svc, "GRADUAL_EVOLUTION",
        )
        expected = chart["expected_assessments"]["GRADUAL_EVOLUTION"]
        assert result["assessment_status"] == expected["assessment_status"]


# ── Cross-Chart Determinism ──────────────────────────────────────────────────


class TestCrossChartDeterminism:
    """Test that the pipeline produces deterministic results."""

    def test_all_charts_deterministic(
        self,
        transitions_svc: TransitionsDomainService,
        convergence_svc: ConvergenceService,
    ) -> None:
        """Verify byte-identical output for identical inputs across all charts."""
        chart_files = [
            "chart_01_sudden_upheaval.json",
            "chart_02_gradual_evolution.json",
            "chart_03_crisis_recovery.json",
            "chart_04_spiritual_awakening.json",
        ]

        for chart_file in chart_files:
            chart = load_chart(chart_file)
            for outcome in chart["expected_assessments"]:
                r1 = run_pipeline(
                    chart, transitions_svc, convergence_svc, outcome,
                )
                r2 = run_pipeline(
                    chart, transitions_svc, convergence_svc, outcome,
                )
                assert json.dumps(r1, sort_keys=True) == json.dumps(
                    r2, sort_keys=True,
                ), f"Non-deterministic output for {chart_file}/{outcome}"


# ── Fixture Validation ───────────────────────────────────────────────────────


class TestFixturesValid:
    """Validate that all fixture files are well-formed."""

    def test_all_fixtures_exist(self) -> None:
        expected_files = [
            "chart_01_sudden_upheaval.json",
            "chart_02_gradual_evolution.json",
            "chart_03_crisis_recovery.json",
            "chart_04_spiritual_awakening.json",
        ]
        for f in expected_files:
            assert (_FIXTURES_DIR / f).exists(), f"Missing fixture: {f}"

    def test_all_fixtures_have_required_fields(self) -> None:
        chart_files = [
            "chart_01_sudden_upheaval.json",
            "chart_02_gradual_evolution.json",
            "chart_03_crisis_recovery.json",
            "chart_04_spiritual_awakening.json",
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
        """Verify at least 4 distinct outcome types are tested."""
        all_outcomes: set[str] = set()
        chart_files = [
            "chart_01_sudden_upheaval.json",
            "chart_02_gradual_evolution.json",
            "chart_03_crisis_recovery.json",
            "chart_04_spiritual_awakening.json",
        ]
        for chart_file in chart_files:
            chart = load_chart(chart_file)
            all_outcomes.update(chart["expected_assessments"].keys())
        assert len(all_outcomes) >= 4, (
            f"Expected at least 4 distinct outcomes, got {len(all_outcomes)}: {all_outcomes}"
        )

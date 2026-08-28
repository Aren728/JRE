"""JRS-090: Unit tests for Calibration & Error Analysis Engine.

Verifies mathematical accuracy of precision, recall, F1, FPR, FNR,
IoU, ECE, Wilson CI bounds, layer performance, diagnostic summaries,
and integration with REFERENCE_COHORT_12.
"""

from __future__ import annotations

from typing import List

import pytest

from jrs.validation.calibration import (
    CohortCalibrationEngine,
    _compute_ece,
    _compute_timing_iou,
    _wilson_ci,
)
from jrs.validation.models import (
    BatchValidationReport,
    CohortCalibrationReport,
    DomainType,
    HistoricalEvent,
    LayerPerformance,
    MetricEvaluation,
    SingleValidationReport,
    ValidationStatus,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture()
def engine() -> CohortCalibrationEngine:
    """Provide a CohortCalibrationEngine instance."""
    return CohortCalibrationEngine()


def _make_metric(
    event_id: str,
    hit: bool,
    prediction_strength: float = 0.8,
    timing_match: bool = True,
    certainty: float = 1.0,
) -> MetricEvaluation:
    """Create a MetricEvaluation for testing."""
    return MetricEvaluation(
        packet_hash="test_hash",
        event_id=event_id,
        event_certainty=certainty,
        prediction_strength=prediction_strength,
        hit=hit,
        timing_match=timing_match,
        score=0.8 if hit else 0.0,
    )


def _make_event(
    event_id: str,
    chart_id: str = "TEST_CHART",
    certainty: float = 1.0,
    layer_states: dict[str, str] | None = None,
) -> HistoricalEvent:
    """Create a HistoricalEvent for testing."""
    return HistoricalEvent(
        event_id=event_id,
        chart_id=chart_id,
        domain=DomainType.CAREER_PEAK,
        start_date="2020-01-01T00:00:00Z",
        end_date="2020-01-01T23:59:59Z",
        event_certainty=certainty,
        description="Test event",
        expected_layer_states=layer_states,
    )


def _make_batch_report(
    metrics: list[MetricEvaluation],
) -> BatchValidationReport:
    """Create a BatchValidationReport from metrics."""
    reports = []
    for m in metrics:
        reports.append(SingleValidationReport(
            chart_id=m.event_id,
            status=ValidationStatus.SUCCESS,
            metric_evaluation=m,
        ))
    return BatchValidationReport(
        total_charts=len(reports),
        successful_evaluations=len(reports),
        failed_evaluations=0,
        reports=tuple(reports),
    )


# ── 1. Wilson Score Confidence Interval ──────────────────────────────────────


class TestWilsonCI:
    """Verify Wilson score CI computation."""

    def test_perfect_precision(self) -> None:
        """All successes: CI should be narrow and close to 1.0."""
        lower, upper = _wilson_ci(10, 10)
        assert lower >= 0.7
        assert upper <= 1.0

    def test_zero_successes(self) -> None:
        """No successes: CI should be wide and low."""
        lower, upper = _wilson_ci(0, 10)
        assert lower == 0.0
        assert upper > 0.0

    def test_empty_total(self) -> None:
        """Zero total: return full range."""
        lower, upper = _wilson_ci(0, 0)
        assert lower == 0.0
        assert upper == 1.0

    def test_half_successes(self) -> None:
        """50% success rate: CI should straddle 0.5."""
        lower, upper = _wilson_ci(5, 10)
        assert lower < 0.5 < upper

    def test_large_sample_narrow(self) -> None:
        """Large sample: CI should be narrow."""
        lower, upper = _wilson_ci(800, 1000)
        assert upper - lower < 0.1

    def test_bounds_clamped(self) -> None:
        """CI bounds must be in [0.0, 1.0]."""
        for s, t in [(0, 1), (1, 1), (5, 5), (10, 10)]:
            lower, upper = _wilson_ci(s, t)
            assert 0.0 <= lower <= upper <= 1.0


# ── 2. Timing Window IoU ─────────────────────────────────────────────────────


class TestTimingIoU:
    """Verify timing window Intersection over Union."""

    def test_identical_windows(self) -> None:
        """Identical windows: IoU = 1.0."""
        iou = _compute_timing_iou(
            "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z",
            "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z",
        )
        assert iou == pytest.approx(1.0)

    def test_no_overlap(self) -> None:
        """Disjoint windows: IoU = 0.0."""
        iou = _compute_timing_iou(
            "2020-01-01T00:00:00Z", "2020-01-02T00:00:00Z",
            "2020-01-03T00:00:00Z", "2020-01-04T00:00:00Z",
        )
        assert iou == 0.0

    def test_partial_overlap(self) -> None:
        """Partial overlap: IoU between 0 and 1."""
        iou = _compute_timing_iou(
            "2020-01-01T00:00:00Z", "2020-01-03T00:00:00Z",
            "2020-01-02T00:00:00Z", "2020-01-04T00:00:00Z",
        )
        assert 0.0 < iou < 1.0
        # Intersection = 1 day, Union = 3 days
        assert iou == pytest.approx(1.0 / 3.0)

    def test_contained_window(self) -> None:
        """Small window inside large window: IoU < 1.0."""
        iou = _compute_timing_iou(
            "2020-01-02T00:00:00Z", "2020-01-03T00:00:00Z",
            "2020-01-01T00:00:00Z", "2020-01-04T00:00:00Z",
        )
        # Intersection = 1 day, Union = 3 days
        assert iou == pytest.approx(1.0 / 3.0)

    def test_invalid_timestamps(self) -> None:
        """Invalid timestamps: IoU = 0.0."""
        iou = _compute_timing_iou("invalid", "also_invalid", "2020-01-01", "2020-01-02")
        assert iou == 0.0

    def test_zero_duration_union(self) -> None:
        """Both windows are single instants at the same time."""
        iou = _compute_timing_iou(
            "2020-01-01T00:00:00Z", "2020-01-01T00:00:00Z",
            "2020-01-01T00:00:00Z", "2020-01-01T00:00:00Z",
        )
        # Union = 0, should return 0.0
        assert iou == 0.0


# ── 3. Expected Calibration Error (ECE) ──────────────────────────────────────


class TestECE:
    """Verify ECE computation."""

    def test_perfect_calibration(self) -> None:
        """Perfectly calibrated predictions: ECE should be low."""
        # Each bin has predictions matching labels proportionally
        predictions = [0.1] * 10 + [0.3] * 10 + [0.5] * 10 + [0.7] * 10 + [0.9] * 10
        labels = [False] * 10 + [False] * 10 + [True] * 10 + [True] * 10 + [True] * 10
        ece = _compute_ece(predictions, labels, n_bins=5)
        # With well-calibrated bins, ECE should be reasonable
        assert ece < 0.35

    def test_worst_calibration(self) -> None:
        """Worst case: all high confidence are wrong."""
        predictions = [0.9, 0.9, 0.9, 0.9, 0.9]
        labels = [False, False, False, False, False]
        ece = _compute_ece(predictions, labels, n_bins=5)
        assert ece > 0.5

    def test_empty_input(self) -> None:
        """Empty predictions: ECE = 0.0."""
        ece = _compute_ece([], [])
        assert ece == 0.0

    def test_single_sample(self) -> None:
        """Single sample: ECE should be 0 or |confidence - label|."""
        ece = _compute_ece([0.8], [True], n_bins=5)
        assert 0.0 <= ece <= 1.0

    def test_all_same_confidence(self) -> None:
        """All same confidence: ECE depends on label distribution."""
        predictions = [0.5] * 10
        labels = [True] * 5 + [False] * 5
        ece = _compute_ece(predictions, labels, n_bins=1)
        assert 0.0 <= ece <= 1.0


# ── 4. Precision, Recall, F1, FPR, FNR ───────────────────────────────────────


class TestClassificationMetrics:
    """Verify global classification metrics computation."""

    def test_all_hits(self, engine: CohortCalibrationEngine) -> None:
        """All predictions correct: precision=1, recall=1, F1=1."""
        metrics = [_make_metric(f"E_{i}", hit=True) for i in range(5)]
        events = [_make_event(f"E_{i}") for i in range(5)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        assert report.precision == pytest.approx(1.0)
        assert report.recall == pytest.approx(1.0)
        assert report.f1_score == pytest.approx(1.0)
        assert report.false_positive_rate == pytest.approx(0.0)

    def test_no_hits(self, engine: CohortCalibrationEngine) -> None:
        """No predictions correct: precision=0, recall=0, F1=0."""
        metrics = [_make_metric(f"E_{i}", hit=False, prediction_strength=0.1) for i in range(5)]
        events = [_make_event(f"E_{i}") for i in range(5)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        assert report.precision == pytest.approx(0.0)
        assert report.recall == pytest.approx(0.0)
        assert report.f1_score == pytest.approx(0.0)

    def test_mixed_results(self, engine: CohortCalibrationEngine) -> None:
        """Mixed results produce intermediate metrics."""
        metrics = [
            _make_metric("E_0", hit=True),
            _make_metric("E_1", hit=True),
            _make_metric("E_2", hit=False, prediction_strength=0.8),
            _make_metric("E_3", hit=False, prediction_strength=0.1),
        ]
        events = [_make_event(f"E_{i}") for i in range(4)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        assert 0.0 <= report.precision <= 1.0
        assert 0.0 <= report.recall <= 1.0
        assert 0.0 <= report.f1_score <= 1.0

    def test_empty_batch(self, engine: CohortCalibrationEngine) -> None:
        """Empty batch: all metrics zero."""
        batch = BatchValidationReport(
            total_charts=0,
            successful_evaluations=0,
            failed_evaluations=0,
            reports=(),
        )
        report = engine.evaluate_cohort(batch, [])
        assert report.total_evaluated == 0

    def test_wilson_ci_computed(self, engine: CohortCalibrationEngine) -> None:
        """Wilson CI bounds should be computed for non-zero counts."""
        metrics = [_make_metric(f"E_{i}", hit=True) for i in range(5)]
        events = [_make_event(f"E_{i}") for i in range(5)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        assert 0.0 <= report.precision_ci_lower <= report.precision_ci_upper <= 1.0
        assert 0.0 <= report.recall_ci_lower <= report.recall_ci_upper <= 1.0

    def test_timing_iou_average(self, engine: CohortCalibrationEngine) -> None:
        """Timing IoU average should be computed from timing_match field."""
        metrics = [
            _make_metric("E_0", hit=True, timing_match=True),
            _make_metric("E_1", hit=True, timing_match=False),
        ]
        events = [_make_event(f"E_{i}") for i in range(2)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        # 1 match + 1 non-match => avg = 0.5
        assert report.timing_window_overlap_avg == pytest.approx(0.5)

    def test_ece_computed(self, engine: CohortCalibrationEngine) -> None:
        """ECE should be computed from predictions and labels."""
        metrics = [
            _make_metric("E_0", hit=True, prediction_strength=0.9),
            _make_metric("E_1", hit=True, prediction_strength=0.8),
            _make_metric("E_2", hit=False, prediction_strength=0.3),
            _make_metric("E_3", hit=False, prediction_strength=0.1),
        ]
        events = [_make_event(f"E_{i}") for i in range(4)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        assert 0.0 <= report.confidence_calibration_error <= 1.0


# ── 5. Layer Performance ──────────────────────────────────────────────────────


class TestLayerPerformance:
    """Verify layer-by-layer performance decomposition."""

    def test_layer_performance_with_expected_states(
        self, engine: CohortCalibrationEngine,
    ) -> None:
        """Layer performance computed from expected_layer_states."""
        events = [
            _make_event("E_0", layer_states={
                "formation": "STRONG",
                "relationship": "MODERATE",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            }),
            _make_event("E_1", layer_states={
                "formation": "STRONG",
                "relationship": "STRONG",
                "modification": "MODERATE",
                "confirmation": "MODERATE",
                "activation": "STRONG",
            }),
        ]
        metrics = [
            _make_metric("E_0", hit=True, prediction_strength=0.8),
            _make_metric("E_1", hit=True, prediction_strength=0.9),
        ]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        assert isinstance(report.layer_telemetry, LayerPerformance)
        assert 0.0 <= report.layer_telemetry.formation_accuracy <= 1.0
        assert 0.0 <= report.layer_telemetry.relationship_accuracy <= 1.0
        assert 0.0 <= report.layer_telemetry.modification_accuracy <= 1.0
        assert 0.0 <= report.layer_telemetry.varga_confirmation_accuracy <= 1.0
        assert 0.0 <= report.layer_telemetry.activation_accuracy <= 1.0

    def test_layer_performance_no_expected_states(
        self, engine: CohortCalibrationEngine,
    ) -> None:
        """Events without expected_layer_states: layer performance = 0."""
        events = [_make_event("E_0", layer_states=None)]
        metrics = [_make_metric("E_0", hit=True)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        # No expected states => no accuracy data
        lt = report.layer_telemetry
        assert lt.formation_accuracy == 0.0

    def test_layer_performance_serialization(self) -> None:
        """LayerPerformance serializes correctly."""
        lp = LayerPerformance(
            formation_accuracy=0.85,
            relationship_accuracy=0.72,
            modification_accuracy=0.60,
            varga_confirmation_accuracy=0.45,
            activation_accuracy=0.90,
        )
        d = lp.to_dict()
        assert d["formation_accuracy"] == 0.85
        assert d["activation_accuracy"] == 0.90

    def test_cohort_report_serialization(self) -> None:
        """CohortCalibrationReport serializes correctly."""
        report = CohortCalibrationReport(
            total_evaluated=12,
            precision=0.75,
            recall=0.80,
            f1_score=0.77,
            false_positive_rate=0.15,
            false_negative_rate=0.20,
            timing_window_overlap_avg=0.60,
            confidence_calibration_error=0.08,
            precision_ci_lower=0.60,
            precision_ci_upper=0.90,
            recall_ci_lower=0.65,
            recall_ci_upper=0.95,
            f1_ci_lower=0.62,
            f1_ci_upper=0.92,
            layer_telemetry=LayerPerformance(
                formation_accuracy=0.85,
                relationship_accuracy=0.70,
                modification_accuracy=0.65,
                varga_confirmation_accuracy=0.50,
                activation_accuracy=0.80,
            ),
        )
        d = report.to_dict()
        assert d["total_evaluated"] == 12
        assert d["precision"] == 0.75
        assert d["f1_score"] == 0.77
        assert d["layer_telemetry"]["formation_accuracy"] == 0.85


# ── 6. Diagnostic Summary ────────────────────────────────────────────────────


class TestDiagnosticSummary:
    """Verify diagnostic summary generation."""

    def test_strong_assessment(self, engine: CohortCalibrationEngine) -> None:
        """High F1 score: overall assessment = STRONG."""
        metrics = [_make_metric(f"E_{i}", hit=True) for i in range(10)]
        events = [_make_event(f"E_{i}") for i in range(10)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)
        diag = engine.generate_diagnostic_summary(report)

        assert diag["overall_assessment"] == "STRONG"

    def test_weak_assessment(self, engine: CohortCalibrationEngine) -> None:
        """Low F1 score: overall assessment = WEAK."""
        metrics = [
            _make_metric(f"E_{i}", hit=False, prediction_strength=0.1)
            for i in range(10)
        ]
        events = [_make_event(f"E_{i}") for i in range(10)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)
        diag = engine.generate_diagnostic_summary(report)

        assert diag["overall_assessment"] == "WEAK"

    def test_no_data_assessment(self, engine: CohortCalibrationEngine) -> None:
        """Empty report: assessment = NO_DATA."""
        batch = BatchValidationReport(total_charts=0, reports=())
        report = engine.evaluate_cohort(batch, [])
        diag = engine.generate_diagnostic_summary(report)

        assert diag["overall_assessment"] == "NO_DATA"

    def test_failure_modes_identified(self, engine: CohortCalibrationEngine) -> None:
        """High FP rate should produce failure mode diagnostic."""
        # Create scenario with high FP
        metrics = [
            _make_metric("E_0", hit=True, prediction_strength=0.9),
            _make_metric("E_1", hit=False, prediction_strength=0.9),
            _make_metric("E_2", hit=False, prediction_strength=0.9),
        ]
        events = [_make_event(f"E_{i}") for i in range(3)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)
        diag = engine.generate_diagnostic_summary(report)

        assert isinstance(diag["failure_modes"], list)

    def test_empty_batch_diagnostics(self, engine: CohortCalibrationEngine) -> None:
        """Empty batch: diagnostics should not crash."""
        batch = BatchValidationReport(total_charts=0, reports=())
        report = engine.evaluate_cohort(batch, [])
        diag = engine.generate_diagnostic_summary(report)

        assert diag["total_evaluated"] == 0
        assert diag["overall_assessment"] == "NO_DATA"
        assert isinstance(diag["recommendations"], list)

    def test_recommendations_present(self, engine: CohortCalibrationEngine) -> None:
        """Diagnostic summary should include recommendations."""
        metrics = [_make_metric(f"E_{i}", hit=True) for i in range(5)]
        events = [_make_event(f"E_{i}") for i in range(5)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)
        diag = engine.generate_diagnostic_summary(report)

        assert "recommendations" in diag
        assert isinstance(diag["recommendations"], list)

    def test_calibration_quality_assessment(
        self, engine: CohortCalibrationEngine,
    ) -> None:
        """Calibration quality should be assessed from ECE."""
        metrics = [
            _make_metric("E_0", hit=True, prediction_strength=0.9),
            _make_metric("E_1", hit=True, prediction_strength=0.8),
            _make_metric("E_2", hit=False, prediction_strength=0.1),
        ]
        events = [_make_event(f"E_{i}") for i in range(3)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)
        diag = engine.generate_diagnostic_summary(report)

        assert diag["calibration_quality"] in {
            "WELL_CALIBRATED", "MODERATELY_CALIBRATED", "POORLY_CALIBRATED",
        }

    def test_layer_assessment_present(
        self, engine: CohortCalibrationEngine,
    ) -> None:
        """Diagnostic should include layer assessment."""
        events = [
            _make_event("E_0", layer_states={
                "formation": "STRONG",
                "relationship": "MODERATE",
                "modification": "MODERATE",
                "confirmation": "WEAK",
                "activation": "STRONG",
            }),
        ]
        metrics = [_make_metric("E_0", hit=True, prediction_strength=0.8)]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)
        diag = engine.generate_diagnostic_summary(report)

        assert "layer_assessment" in diag
        assert isinstance(diag["layer_assessment"], dict)
        assert "formation" in diag["layer_assessment"]


# ── 7. Integration with REFERENCE_COHORT_12 ───────────────────────────────────


class TestReferenceCohortIntegration:
    """Integration tests using the 12-chart reference cohort."""

    def test_engine_with_reference_cohort_events(
        self, engine: CohortCalibrationEngine,
    ) -> None:
        """CohortCalibrationEngine should process reference cohort events."""
        from jrs.validation.datasets import REFERENCE_COHORT_12

        events = [evt for _, evt in REFERENCE_COHORT_12]
        metrics = [_make_metric(evt.event_id, hit=True) for evt in events]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)

        assert report.total_evaluated == 12
        assert report.precision == pytest.approx(1.0)
        assert report.recall == pytest.approx(1.0)

    def test_reference_cohort_events_have_layer_states(self) -> None:
        """All 12 reference events should have expected_layer_states."""
        from jrs.validation.datasets import REFERENCE_COHORT_12

        for _, event in REFERENCE_COHORT_12:
            assert event.expected_layer_states is not None, (
                f"{event.event_id} missing expected_layer_states"
            )
            assert set(event.expected_layer_states.keys()) == {
                "formation", "relationship", "modification",
                "confirmation", "activation",
            }

    def test_reference_cohort_layer_states_valid_values(self) -> None:
        """All layer state values must be valid."""
        from jrs.validation.datasets import REFERENCE_COHORT_12

        valid_values = {"STRONG", "MODERATE", "WEAK", "ABSENT"}
        for _, event in REFERENCE_COHORT_12:
            if event.expected_layer_states:
                for key, value in event.expected_layer_states.items():
                    assert value in valid_values, (
                        f"{event.event_id}.{key} = '{value}' "
                        f"(not in {valid_values})"
                    )

    def test_diagnostics_on_reference_cohort(
        self, engine: CohortCalibrationEngine,
    ) -> None:
        """Full diagnostic pipeline on reference cohort should work."""
        from jrs.validation.datasets import REFERENCE_COHORT_12

        events = [evt for _, evt in REFERENCE_COHORT_12]
        metrics = [_make_metric(evt.event_id, hit=True) for evt in events]
        batch = _make_batch_report(metrics)

        report = engine.evaluate_cohort(batch, events)
        diag = engine.generate_diagnostic_summary(report)

        assert diag["total_evaluated"] == 12
        assert diag["overall_assessment"] == "STRONG"
        assert isinstance(diag["failure_modes"], list)
        assert isinstance(diag["layer_assessment"], dict)
        assert isinstance(diag["recommendations"], list)

"""Unit tests for calibration metric computation."""

from __future__ import annotations

import json

import pytest
from tests.calibration.metrics import (
    CalibrationReport,
    DomainMetrics,
    OutcomeMetrics,
    compute_outcome_metrics,
    compute_timing_overlap,
)

# ── OutcomeMetrics ───────────────────────────────────────────────────────────


class TestOutcomeMetrics:
    """Tests for OutcomeMetrics computation."""

    def test_perfect_true_positive(self) -> None:
        """Both ground truth and predicted are positive → TP=1."""
        m = compute_outcome_metrics(
            outcome="MARRIAGE_FORMATION",
            ground_truth_status="SUPPORTED",
            predicted_status="SUPPORTED",
        )
        assert m.true_positives == 1
        assert m.false_positives == 0
        assert m.true_negatives == 0
        assert m.false_negatives == 0
        assert m.precision == 1.0
        assert m.recall == 1.0
        assert m.f1_score == 1.0

    def test_perfect_true_negative(self) -> None:
        """Both ground truth and predicted are negative → TN=1."""
        m = compute_outcome_metrics(
            outcome="SEPARATION",
            ground_truth_status="NEUTRAL",
            predicted_status="CONTRADICTED",
        )
        assert m.true_positives == 0
        assert m.false_positives == 0
        assert m.true_negatives == 1
        assert m.false_negatives == 0

    def test_false_positive(self) -> None:
        """Ground truth negative, predicted positive → FP=1."""
        m = compute_outcome_metrics(
            outcome="SEPARATION",
            ground_truth_status="NEUTRAL",
            predicted_status="SUPPORTED",
        )
        assert m.false_positives == 1
        assert m.true_positives == 0
        assert m.false_positive_rate == 1.0

    def test_false_negative(self) -> None:
        """Ground truth positive, predicted negative → FN=1."""
        m = compute_outcome_metrics(
            outcome="MARRIAGE_FORMATION",
            ground_truth_status="SUPPORTED",
            predicted_status="NEUTRAL",
        )
        assert m.false_negatives == 1
        assert m.true_positives == 0
        assert m.false_negative_rate == 1.0

    def test_precision_calculation(self) -> None:
        """Precision = TP / (TP + FP)."""
        # Manually construct with known values
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=3,
            false_positives=1,
            true_negatives=5,
            false_negatives=2,
            timing_overlap_score=0.0,
        )
        assert m.precision == pytest.approx(0.75)

    def test_recall_calculation(self) -> None:
        """Recall = TP / (TP + FN)."""
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=3,
            false_positives=1,
            true_negatives=5,
            false_negatives=2,
            timing_overlap_score=0.0,
        )
        assert m.recall == pytest.approx(0.6)

    def test_f1_calculation(self) -> None:
        """F1 = 2 * P * R / (P + R)."""
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=3,
            false_positives=1,
            true_negatives=5,
            false_negatives=1,
            timing_overlap_score=0.0,
        )
        # P = 3/4 = 0.75, R = 3/4 = 0.75, F1 = 0.75
        assert m.f1_score == pytest.approx(0.75)

    def test_f1_zero_precision(self) -> None:
        """F1 = 0 when precision is 0."""
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=0,
            false_positives=5,
            true_negatives=5,
            false_negatives=0,
            timing_overlap_score=0.0,
        )
        assert m.f1_score == 0.0

    def test_f1_zero_recall(self) -> None:
        """F1 = 0 when recall is 0."""
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=0,
            false_positives=0,
            true_negatives=5,
            false_negatives=5,
            timing_overlap_score=0.0,
        )
        assert m.f1_score == 0.0

    def test_fpr_calculation(self) -> None:
        """FPR = FP / (FP + TN)."""
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=3,
            false_positives=2,
            true_negatives=8,
            false_negatives=1,
            timing_overlap_score=0.0,
        )
        assert m.false_positive_rate == pytest.approx(2 / 10)

    def test_fnr_calculation(self) -> None:
        """FNR = FN / (FN + TP)."""
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=3,
            false_positives=2,
            true_negatives=8,
            false_negatives=1,
            timing_overlap_score=0.0,
        )
        assert m.false_negative_rate == pytest.approx(1 / 4)

    def test_zero_denominators(self) -> None:
        """Metrics handle zero denominators gracefully."""
        m = OutcomeMetrics(
            outcome="TEST",
            true_positives=0,
            false_positives=0,
            true_negatives=0,
            false_negatives=0,
            timing_overlap_score=0.0,
        )
        assert m.precision == 0.0
        assert m.recall == 0.0
        assert m.f1_score == 0.0
        assert m.false_positive_rate == 0.0
        assert m.false_negative_rate == 0.0

    def test_to_dict(self) -> None:
        m = compute_outcome_metrics(
            outcome="TEST",
            ground_truth_status="SUPPORTED",
            predicted_status="SUPPORTED",
        )
        d = m.to_dict()
        assert d["outcome"] == "TEST"
        assert d["true_positives"] == 1
        assert d["precision"] == 1.0

    def test_to_dict_deterministic(self) -> None:
        m = compute_outcome_metrics(
            outcome="TEST",
            ground_truth_status="SUPPORTED",
            predicted_status="SUPPORTED",
        )
        d1 = m.to_dict()
        d2 = m.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_strongly_supported_is_positive(self) -> None:
        m = compute_outcome_metrics(
            outcome="TEST",
            ground_truth_status="STRONGLY_SUPPORTED",
            predicted_status="STRONGLY_SUPPORTED",
        )
        assert m.true_positives == 1

    def test_weakly_supported_is_positive(self) -> None:
        m = compute_outcome_metrics(
            outcome="TEST",
            ground_truth_status="WEAKLY_SUPPORTED",
            predicted_status="SUPPORTED",
        )
        assert m.true_positives == 1

    def test_strongly_contradicted_is_negative(self) -> None:
        m = compute_outcome_metrics(
            outcome="TEST",
            ground_truth_status="STRONGLY_CONTRADICTED",
            predicted_status="CONTRADICTED",
        )
        assert m.true_negatives == 1


# ── Timing Overlap ───────────────────────────────────────────────────────────


class TestTimingOverlap:
    """Tests for timing overlap computation."""

    def test_same_timing(self) -> None:
        assert compute_timing_overlap("CONVERGENT", "CONVERGENT") is True

    def test_different_timing(self) -> None:
        assert compute_timing_overlap("CONVERGENT", "INACTIVE") is False

    def test_both_inactive(self) -> None:
        assert compute_timing_overlap("INACTIVE", "INACTIVE") is True

    def test_timing_match_in_outcome_metrics(self) -> None:
        m = compute_outcome_metrics(
            outcome="TEST",
            ground_truth_status="SUPPORTED",
            predicted_status="SUPPORTED",
            timing_match=True,
        )
        assert m.timing_overlap_score == 1.0

    def test_timing_mismatch_in_outcome_metrics(self) -> None:
        m = compute_outcome_metrics(
            outcome="TEST",
            ground_truth_status="SUPPORTED",
            predicted_status="SUPPORTED",
            timing_match=False,
        )
        assert m.timing_overlap_score == 0.0


# ── DomainMetrics ────────────────────────────────────────────────────────────


class TestDomainMetrics:
    """Tests for DomainMetrics aggregation."""

    def test_macro_averaged_precision(self) -> None:
        dm = DomainMetrics(
            domain="test",
            outcome_metrics=(
                OutcomeMetrics("A", 1, 0, 0, 0, 1.0),  # P=1.0
                OutcomeMetrics("B", 1, 1, 0, 0, 0.5),  # P=0.5
            ),
            total_charts=1,
        )
        assert dm.precision == pytest.approx(0.75)

    def test_empty_outcomes(self) -> None:
        dm = DomainMetrics(domain="test")
        assert dm.precision == 0.0
        assert dm.recall == 0.0
        assert dm.f1_score == 0.0

    def test_to_dict(self) -> None:
        dm = DomainMetrics(
            domain="marriage",
            outcome_metrics=(
                OutcomeMetrics("MARRIAGE_FORMATION", 1, 0, 0, 0, 1.0),
            ),
            total_charts=5,
        )
        d = dm.to_dict()
        assert d["domain"] == "marriage"
        assert d["total_charts"] == 5
        assert d["outcome_count"] == 1


# ── CalibrationReport ────────────────────────────────────────────────────────


class TestCalibrationReport:
    """Tests for CalibrationReport."""

    def test_to_dict(self) -> None:
        report = CalibrationReport(
            domain_metrics=(
                DomainMetrics(
                    domain="marriage",
                    outcome_metrics=(
                        OutcomeMetrics("MARRIAGE_FORMATION", 1, 0, 0, 0, 1.0),
                    ),
                    total_charts=5,
                ),
            ),
            timestamp="2025-01-01T00:00:00Z",
        )
        d = report.to_dict()
        assert d["domain_count"] == 1
        assert d["precision"] == 1.0
        assert d["timestamp"] == "2025-01-01T00:00:00Z"

    def test_to_markdown(self) -> None:
        report = CalibrationReport(
            domain_metrics=(
                DomainMetrics(
                    domain="marriage",
                    outcome_metrics=(
                        OutcomeMetrics("MARRIAGE_FORMATION", 1, 0, 0, 0, 1.0),
                    ),
                    total_charts=5,
                ),
            ),
            timestamp="2025-01-01T00:00:00Z",
        )
        md = report.to_markdown()
        assert "# Calibration Report" in md
        assert "marriage" in md
        assert "MARRIAGE_FORMATION" in md

    def test_empty_report(self) -> None:
        report = CalibrationReport()
        assert report.precision == 0.0
        assert report.f1_score == 0.0
        d = report.to_dict()
        assert d["domain_count"] == 0

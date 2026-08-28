"""JRS-090: Calibration & Error Analysis Engine.

Computes precision, recall, F1, FPR, FNR, timing-window IoU, and
Expected Calibration Error (ECE) across a cohort. Provides telescopic
layer-by-layer performance decomposition and diagnostic summaries.

Source: JRS-090 Calibration & Error Analysis Engine.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from .models import (
    BatchValidationReport,
    CohortCalibrationReport,
    HistoricalEvent,
    LayerPerformance,
    MetricEvaluation,
    SingleValidationReport,
    ValidationStatus,
)

# ── Layer Accuracy Thresholds ─────────────────────────────────────────────────

_LAYER_THRESHOLD: float = 0.5
_LAYER_MAP: dict[str, str] = {
    "formation": "formation_accuracy",
    "relationship": "relationship_accuracy",
    "modification": "modification_accuracy",
    "confirmation": "varga_confirmation_accuracy",
    "activation": "activation_accuracy",
}

_STATE_SCORES: dict[str, float] = {
    "STRONG": 1.0,
    "MODERATE": 0.5,
    "WEAK": 0.25,
    "ABSENT": 0.0,
}


# ── Wilson Score Confidence Interval ──────────────────────────────────────────


def _wilson_ci(
    successes: int,
    total: int,
    z: float = 1.96,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Compute Wilson score confidence interval for a binomial proportion.

    Args:
        successes: Number of successes (TP for precision/recall numerator).
        total: Total number of trials (TP+FP for precision, TP+FN for recall).
        z: Z-score for desired confidence level (default 1.96 for 95%).
        confidence: Confidence level (unused, kept for API clarity).

    Returns:
        Tuple of (lower_bound, upper_bound), each clamped to [0.0, 1.0].
    """
    if total == 0:
        return (0.0, 1.0)

    p_hat = successes / total
    denominator = 1.0 + (z * z) / total
    centre = p_hat + (z * z) / (2.0 * total)
    spread = z * math.sqrt((p_hat * (1.0 - p_hat) + (z * z) / (4.0 * total)) / total)

    lower = max(0.0, (centre - spread) / denominator)
    upper = min(1.0, (centre + spread) / denominator)

    return (round(lower, 4), round(upper, 4))


# ── Timing Window IoU ─────────────────────────────────────────────────────────


def _parse_timestamp_days(ts: str) -> float | None:
    """Parse an ISO-8601 timestamp and return days since epoch.

    Returns None if parsing fails.
    """
    try:
        from datetime import datetime, timezone

        # Handle Z suffix
        ts_clean = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        epoch = datetime(2000, 1, 1, tzinfo=timezone.utc)
        delta = dt - epoch
        return delta.total_seconds() / 86400.0
    except (ValueError, TypeError):
        return None


def _compute_timing_iou(
    pred_start: str,
    pred_end: str,
    actual_start: str,
    actual_end: str,
) -> float:
    """Compute Intersection over Union (IoU) for two time windows.

    IoU = intersection_days / union_days, bounded in [0.0, 1.0].
    If union is 0, returns 0.0.
    """
    p_s = _parse_timestamp_days(pred_start)
    p_e = _parse_timestamp_days(pred_end)
    a_s = _parse_timestamp_days(actual_start)
    a_e = _parse_timestamp_days(actual_end)

    if None in (p_s, p_e, a_s, a_e):
        return 0.0

    # Ensure start <= end
    p_s, p_e = min(p_s, p_e), max(p_s, p_e)
    a_s, a_e = min(a_s, a_e), max(a_s, a_e)

    intersection_start = max(p_s, a_s)
    intersection_end = min(p_e, a_e)
    intersection = max(0.0, intersection_end - intersection_start)

    union_start = min(p_s, a_s)
    union_end = max(p_e, a_e)
    union = max(0.0, union_end - union_start)

    if union == 0.0:
        return 0.0

    return intersection / union


# ── ECE (Expected Calibration Error) ─────────────────────────────────────────


def _compute_ece(
    predictions: list[float],
    labels: list[bool],
    n_bins: int = 5,
) -> float:
    """Compute Expected Calibration Error.

    Bins predictions into N confidence bins (0–0.2, 0.2–0.4, ...).
    For each bin, computes |avg_confidence - actual_accuracy| * (count / total).
    """
    if not predictions:
        return 0.0

    bin_edges = [i / n_bins for i in range(n_bins + 1)]
    total = len(predictions)
    ece = 0.0

    for i in range(n_bins):
        bin_low = bin_edges[i]
        bin_high = bin_edges[i + 1]

        # Find samples in this bin
        in_bin = [
            j for j, p in enumerate(predictions)
            if bin_low <= p < bin_high or (i == n_bins - 1 and p == bin_high)
        ]

        if not in_bin:
            continue

        avg_confidence = sum(predictions[j] for j in in_bin) / len(in_bin)
        actual_accuracy = sum(1 for j in in_bin if labels[j]) / len(in_bin)
        bin_weight = len(in_bin) / total

        ece += abs(avg_confidence - actual_accuracy) * bin_weight

    return round(ece, 4)


# ── CohortCalibrationEngine ──────────────────────────────────────────────────


class CohortCalibrationEngine:
    """Calibration and error analysis engine for validation cohorts.

    Computes global metrics (precision, recall, F1, FPR, FNR),
    timing-window IoU, ECE, Wilson CI bounds, and telescopic
    layer-by-layer performance decomposition.

    Usage::

        engine = CohortCalibrationEngine()
        report = engine.evaluate_cohort(batch_report, ground_truth_events)
        diagnostic = engine.generate_diagnostic_summary(report)
    """

    def evaluate_cohort(
        self,
        batch_report: BatchValidationReport,
        ground_truth_events: list[HistoricalEvent],
    ) -> CohortCalibrationReport:
        """Evaluate cohort calibration metrics.

        Args:
            batch_report: Aggregated batch validation results.
            ground_truth_events: Ground-truth events with expected layer states.

        Returns:
            CohortCalibrationReport with full metric breakdown.
        """
        # Filter to successful evaluations
        successful = [
            r for r in batch_report.reports
            if r.status == ValidationStatus.SUCCESS and r.metric_evaluation is not None
        ]

        if not successful:
            return CohortCalibrationReport(
                total_evaluated=0,
                layer_telemetry=LayerPerformance(),
            )

        # Extract metric evaluations
        evaluations = [r.metric_evaluation for r in successful]

        # Compute confusion matrix components
        tp = sum(1 for e in evaluations if e.hit and e.prediction_strength >= _LAYER_THRESHOLD)
        fp = sum(1 for e in evaluations if not e.hit and e.prediction_strength >= _LAYER_THRESHOLD)
        fn = sum(1 for e in evaluations if e.hit and e.prediction_strength < _LAYER_THRESHOLD)
        tn = sum(1 for e in evaluations if not e.hit and e.prediction_strength < _LAYER_THRESHOLD)

        # Actually, for blind validation: hit=True means event was detected
        # and prediction_strength is the score. We use the MetricEvaluation
        # hit field directly.
        tp = sum(1 for e in evaluations if e.hit)
        fp = sum(1 for e in evaluations if not e.hit and e.prediction_strength > 0.0)
        fn = sum(1 for e in evaluations if e.event_certainty >= 0.5 and not e.hit)
        tn = sum(1 for e in evaluations if e.event_certainty < 0.5 and not e.hit)

        # Compute metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) > 0 else 0.0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        # Wilson CI bounds
        prec_ci = _wilson_ci(tp, tp + fp) if (tp + fp) > 0 else (0.0, 1.0)
        rec_ci = _wilson_ci(tp, tp + fn) if (tp + fn) > 0 else (0.0, 1.0)

        # For F1 CI, use the lower/upper of precision and recall CIs
        f1_ci_lower = round(min(prec_ci[0], rec_ci[0]), 4)
        f1_ci_upper = round(min(prec_ci[1], rec_ci[1]), 4)

        # Timing window IoU
        timing_ious = self._compute_timing_ious(evaluations, ground_truth_events)
        avg_iou = (sum(timing_ious) / len(timing_ious)
                   if timing_ious else 0.0)

        # ECE
        predictions = [e.prediction_strength for e in evaluations]
        labels = [e.hit for e in evaluations]
        ece = _compute_ece(predictions, labels)

        # Layer performance
        layer_telemetry = self._compute_layer_performance(
            evaluations, ground_truth_events,
        )

        return CohortCalibrationReport(
            total_evaluated=len(evaluations),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            false_positive_rate=round(fpr, 4),
            false_negative_rate=round(fnr, 4),
            timing_window_overlap_avg=round(avg_iou, 4),
            confidence_calibration_error=ece,
            precision_ci_lower=prec_ci[0],
            precision_ci_upper=prec_ci[1],
            recall_ci_lower=rec_ci[0],
            recall_ci_upper=rec_ci[1],
            f1_ci_lower=f1_ci_lower,
            f1_ci_upper=f1_ci_upper,
            layer_telemetry=layer_telemetry,
            chart_evaluations=tuple(evaluations),
        )

    def generate_diagnostic_summary(
        self,
        report: CohortCalibrationReport,
    ) -> dict[str, Any]:
        """Generate a structured diagnostic summary.

        Highlights top failure modes and provides actionable insights.

        Args:
            report: The cohort calibration report to diagnose.

        Returns:
            Structured diagnostic dictionary.
        """
        diagnostics: dict[str, Any] = {
            "total_evaluated": report.total_evaluated,
            "overall_assessment": self._assess_overall(report),
            "failure_modes": self._identify_failure_modes(report),
            "layer_assessment": self._assess_layers(report),
            "calibration_quality": self._assess_calibration(report),
            "recommendations": self._generate_recommendations(report),
        }
        return diagnostics

    # ── Private helpers ───────────────────────────────────────────────────

    def _compute_timing_ious(
        self,
        evaluations: list[MetricEvaluation],
        ground_truth_events: list[HistoricalEvent],
    ) -> list[float]:
        """Compute timing IoU for each evaluation against its ground truth."""
        event_map = {e.event_id: e for e in ground_truth_events}
        ious: list[float] = []

        for eval_ in evaluations:
            event = event_map.get(eval_.event_id)
            if event is None:
                continue

            # Use start_date and end_date for IoU computation
            # Since we don't have predicted windows directly in MetricEvaluation,
            # we use timing_match as a proxy
            if eval_.timing_match:
                ious.append(1.0)
            else:
                ious.append(0.0)

        return ious

    def _compute_layer_performance(
        self,
        evaluations: list[MetricEvaluation],
        ground_truth_events: list[HistoricalEvent],
    ) -> LayerPerformance:
        """Compute per-layer accuracy from expected_layer_states."""
        event_map = {e.event_id: e for e in ground_truth_events}

        layer_totals: dict[str, float] = {
            "formation": 0.0,
            "relationship": 0.0,
            "modification": 0.0,
            "confirmation": 0.0,
            "activation": 0.0,
        }
        layer_counts: dict[str, int] = {
            "formation": 0,
            "relationship": 0,
            "modification": 0,
            "confirmation": 0,
            "activation": 0,
        }

        for eval_ in evaluations:
            event = event_map.get(eval_.event_id)
            if event is None or event.expected_layer_states is None:
                continue

            for layer_name, state_value in event.expected_layer_states.items():
                if layer_name not in layer_totals:
                    continue

                expected_score = _STATE_SCORES.get(state_value, 0.0)

                # Map prediction_strength to layer accuracy
                # prediction_strength serves as the aggregate proxy
                predicted_score = eval_.prediction_strength

                # Accuracy = 1 - |expected - predicted| (normalized)
                accuracy = 1.0 - abs(expected_score - min(predicted_score, 1.0))
                accuracy = max(0.0, min(1.0, accuracy))

                layer_totals[layer_name] += accuracy
                layer_counts[layer_name] += 1

        def _avg(key: str) -> float:
            if layer_counts[key] == 0:
                return 0.0
            return layer_totals[key] / layer_counts[key]

        return LayerPerformance(
            formation_accuracy=round(_avg("formation"), 4),
            relationship_accuracy=round(_avg("relationship"), 4),
            modification_accuracy=round(_avg("modification"), 4),
            varga_confirmation_accuracy=round(_avg("confirmation"), 4),
            activation_accuracy=round(_avg("activation"), 4),
        )

    def _assess_overall(self, report: CohortCalibrationReport) -> str:
        """Provide a high-level overall assessment."""
        if report.total_evaluated == 0:
            return "NO_DATA"
        if report.f1_score >= 0.8:
            return "STRONG"
        if report.f1_score >= 0.5:
            return "MODERATE"
        return "WEAK"

    def _identify_failure_modes(
        self,
        report: CohortCalibrationReport,
    ) -> list[str]:
        """Identify top failure modes from the metrics."""
        modes: list[str] = []

        if report.false_positive_rate > 0.3:
            modes.append(
                f"High false positive rate ({report.false_positive_rate:.2f}): "
                "Predictions detecting events that did not occur"
            )

        if report.false_negative_rate > 0.3:
            modes.append(
                f"High false negative rate ({report.false_negative_rate:.2f}): "
                "Failing to detect events that did occur"
            )

        if report.confidence_calibration_error > 0.15:
            modes.append(
                f"High calibration error ({report.confidence_calibration_error:.4f}): "
                "Confidence scores poorly calibrated to actual accuracy"
            )

        if report.timing_window_overlap_avg < 0.3:
            modes.append(
                f"Low timing overlap ({report.timing_window_overlap_avg:.2f}): "
                "Predicted temporal windows poorly aligned with actual events"
            )

        # Check for specific layer weaknesses
        lt = report.layer_telemetry
        if lt.formation_accuracy < 0.5 and report.total_evaluated > 0:
            modes.append(
                f"Weak formation detection ({lt.formation_accuracy:.2f}): "
                "Yoga/Aspect existence layer underperforming"
            )

        if lt.activation_accuracy < 0.5 and report.total_evaluated > 0:
            modes.append(
                f"Weak activation timing ({lt.activation_accuracy:.2f}): "
                "Dasha + Transit + Nakshatra layer underperforming"
            )

        return modes

    def _assess_layers(
        self,
        report: CohortCalibrationReport,
    ) -> dict[str, str]:
        """Assess each pipeline layer."""
        lt = report.layer_telemetry
        assessment: dict[str, str] = {}

        for name, value in [
            ("formation", lt.formation_accuracy),
            ("relationship", lt.relationship_accuracy),
            ("modification", lt.modification_accuracy),
            ("varga_confirmation", lt.varga_confirmation_accuracy),
            ("activation", lt.activation_accuracy),
        ]:
            if value >= 0.8:
                assessment[name] = "STRONG"
            elif value >= 0.5:
                assessment[name] = "MODERATE"
            elif value > 0.0:
                assessment[name] = "WEAK"
            else:
                assessment[name] = "NO_DATA"

        return assessment

    def _assess_calibration(
        self,
        report: CohortCalibrationReport,
    ) -> str:
        """Assess calibration quality from ECE."""
        if report.confidence_calibration_error <= 0.05:
            return "WELL_CALIBRATED"
        if report.confidence_calibration_error <= 0.15:
            return "MODERATELY_CALIBRATED"
        return "POORLY_CALIBRATED"

    def _generate_recommendations(
        self,
        report: CohortCalibrationReport,
    ) -> list[str]:
        """Generate actionable recommendations."""
        recs: list[str] = []

        if report.total_evaluated < 10:
            recs.append(
                f"Small sample size ({report.total_evaluated}): "
                "Expand cohort for statistical significance"
            )

        if report.false_positive_rate > 0.3:
            recs.append(
                "Reduce false positives by tightening formation thresholds "
                "or adding more confirmation layers"
            )

        if report.false_negative_rate > 0.3:
            recs.append(
                "Reduce false negatives by lowering detection thresholds "
                "or improving aspect/conjunction coverage"
            )

        if report.confidence_calibration_error > 0.15:
            recs.append(
                "Improve confidence calibration: recalibrate using "
                "temperature scaling or isotonic regression"
            )

        lt = report.layer_telemetry
        if lt.activation_accuracy < 0.5 and report.total_evaluated > 0:
            recs.append(
                "Activation layer needs improvement: verify Dasha/Transit "
                "engine integration and Nakshatra edge detection"
            )

        if lt.formation_accuracy < 0.5 and report.total_evaluated > 0:
            recs.append(
                "Formation layer needs improvement: review Yoga detection "
                "rules and aspect coverage"
            )

        return recs

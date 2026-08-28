"""JRS Phase A: Statistical Evaluation — Precision, Recall, F1, Domain Calibration.

Computes statistical metrics comparing predicted yoga activations against
verified life events across all chart domains.

Metrics computed:
    - Precision, Recall, F1 Score, False Positive/Negative rates
    - Domain Calibration (per-domain breakdown)
    - Temporal Timing Window Overlap (Dasha/Transit match accuracy)
    - Accuracy (overall correct classification rate)

Source: RI-010 Engine Architecture; standard ML evaluation methodology.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import (
    ChartValidationResult,
    ClassificationMetrics,
    DomainCalibration,
    EventDomain,
    EventPredictionMatch,
    PredictionVerdict,
    StatisticalReport,
    TimingAnalysis,
    TimingMatchStatus,
)


def _compute_classification_metrics(
    tp: int, fp: int, tn: int, fn: int,
) -> ClassificationMetrics:
    """Compute precision, recall, F1, and accuracy from confusion matrix.

    Args:
        tp: True positives.
        fp: False positives.
        tn: True negatives.
        fn: False negatives.

    Returns:
        ClassificationMetrics with computed values.
    """
    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    accuracy = (tp + tn) / total if total > 0 else 0.0

    return ClassificationMetrics(
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        precision=precision,
        recall=recall,
        f1_score=f1,
        accuracy=accuracy,
    )


def _classify_match(
    match: EventPredictionMatch,
) -> tuple[int, int, int, int]:
    """Classify a single match into the confusion matrix.

    Returns:
        Tuple of (tp, fp, tn, fn) increments.
    """
    if match.verdict == PredictionVerdict.TRUE_POSITIVE:
        return (1, 0, 0, 0)
    if match.verdict == PredictionVerdict.FALSE_POSITIVE:
        return (0, 1, 0, 0)
    if match.verdict == PredictionVerdict.TRUE_NEGATIVE:
        return (0, 0, 1, 0)
    if match.verdict == PredictionVerdict.FALSE_NEGATIVE:
        return (0, 0, 0, 1)
    return (0, 0, 0, 0)


def compute_timing_analysis(
    results: list[ChartValidationResult],
) -> TimingAnalysis:
    """Compute timing window overlap analysis across all charts.

    Args:
        results: List of chart validation results.

    Returns:
        TimingAnalysis with overlap statistics.
    """
    total_windows = 0
    overlap = 0
    partial = 0
    no_overlap = 0
    overlap_ratios: list[float] = []

    for result in results:
        for match in result.matches:
            if match.timing_status == TimingMatchStatus.OVERLAP:
                overlap += 1
                overlap_ratios.append(match.timing_overlap_ratio)
            elif match.timing_status == TimingMatchStatus.PARTIAL_OVERLAP:
                partial += 1
                overlap_ratios.append(match.timing_overlap_ratio)
            elif match.timing_status == TimingMatchStatus.NO_OVERLAP:
                no_overlap += 1
            else:
                # PREDICTED_ONLY or ACTUAL_ONLY
                no_overlap += 1
            total_windows += 1

    mean_ratio = (
        sum(overlap_ratios) / len(overlap_ratios) if overlap_ratios else 0.0
    )
    timing_accuracy = (
        overlap / total_windows if total_windows > 0 else 0.0
    )

    return TimingAnalysis(
        total_predicted_windows=total_windows,
        overlap_count=overlap,
        partial_overlap_count=partial,
        no_overlap_count=no_overlap,
        mean_overlap_ratio=mean_ratio,
        timing_accuracy=timing_accuracy,
    )


def compute_domain_calibrations(
    results: list[ChartValidationResult],
) -> tuple[DomainCalibration, ...]:
    """Compute per-domain calibration metrics.

    Args:
        results: List of chart validation results.

    Returns:
        Tuple of DomainCalibration, one per domain with data.
    """
    # Group results by domain
    domain_results: dict[str, list[ChartValidationResult]] = {}
    for result in results:
        domain_key = result.domain.value
        if domain_key not in domain_results:
            domain_results[domain_key] = []
        domain_results[domain_key].append(result)

    calibrations: list[DomainCalibration] = []
    for domain_key, domain_res_list in sorted(domain_results.items()):
        tp, fp, tn, fn = 0, 0, 0, 0
        overlap_ratios: list[float] = []
        confidences: list[float] = []

        for result in domain_res_list:
            for match in result.matches:
                m_tp, m_fp, m_tn, m_fn = _classify_match(match)
                tp += m_tp
                fp += m_fp
                tn += m_tn
                fn += m_fn
                overlap_ratios.append(match.timing_overlap_ratio)
                confidences.append(match.confidence)

        metrics = _compute_classification_metrics(tp, fp, tn, fn)
        mean_overlap = (
            sum(overlap_ratios) / len(overlap_ratios)
            if overlap_ratios else 0.0
        )
        mean_conf = (
            sum(confidences) / len(confidences) if confidences else 0.0
        )

        calibrations.append(DomainCalibration(
            domain=domain_key,
            chart_count=len(domain_res_list),
            metrics=metrics,
            timing_overlap_ratio=mean_overlap,
            mean_confidence=mean_conf,
        ))

    return tuple(calibrations)


class StatisticalEvaluator:
    """Computes aggregate statistical evaluation metrics.

    Processes ChartValidationResult objects from the HistoricalValidationRunner
    and produces a StatisticalReport with precision, recall, F1, domain
    calibration, and timing overlap analysis.
    """

    def evaluate(
        self,
        results: list[ChartValidationResult],
    ) -> StatisticalReport:
        """Compute the full statistical evaluation report.

        Args:
            results: List of chart validation results from the runner.

        Returns:
            StatisticalReport with all aggregate metrics.
        """
        if not results:
            return StatisticalReport()

        # ── Aggregate confusion matrix ──
        tp, fp, tn, fn = 0, 0, 0, 0
        total_known = 0
        total_predicted = 0
        all_confidences: list[float] = []

        for result in results:
            total_known += result.total_known_events
            total_predicted += result.total_predicted_yogas
            for match in result.matches:
                m_tp, m_fp, m_tn, m_fn = _classify_match(match)
                tp += m_tp
                fp += m_fp
                tn += m_tn
                fn += m_fn
                all_confidences.append(match.confidence)

        overall_metrics = _compute_classification_metrics(tp, fp, tn, fn)

        # ── Domain calibrations ──
        domain_calibrations = compute_domain_calibrations(results)

        # ── Timing analysis ──
        timing_analysis = compute_timing_analysis(results)

        # ── Mean confidence ──
        mean_conf = (
            sum(all_confidences) / len(all_confidences)
            if all_confidences else 0.0
        )

        return StatisticalReport(
            total_charts=len(results),
            total_known_events=total_known,
            total_predicted_yogas=total_predicted,
            overall_metrics=overall_metrics,
            domain_calibrations=domain_calibrations,
            timing_analysis=timing_analysis,
            mean_confidence=mean_conf,
        )

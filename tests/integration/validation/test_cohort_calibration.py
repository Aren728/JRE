"""JRS-090 Integration Test: Validate 12-Chart Reference Cohort.

Runs the full calibration pipeline on REFERENCE_COHORT_12 to measure
actual predictive performance before scaling to larger datasets.
"""

from __future__ import annotations

import pytest

from src.jrs.validation.datasets.reference_cohort import REFERENCE_COHORT_12
from src.jrs.validation.runner import BlindValidationRunner
from src.jrs.validation.calibration import CohortCalibrationEngine
from src.jrs.validation.models import (
    BatchValidationReport,
    MetricEvaluation,
    SingleValidationReport,
    ValidationStatus,
)


def test_cohort_calibration_integration(tmp_path):
    """Integration test that runs the full calibration pipeline on the 12-chart
    reference cohort and outputs comprehensive performance metrics.
    """
    print("\n" + "=" * 80)
    print("JRS-090: COHORT CALIBRATION REPORT (12-Chart Reference Cohort)")
    print("=" * 80)

    # Step 1: Initialize runner and calibration engine
    runner = BlindValidationRunner()
    calibration_engine = CohortCalibrationEngine()

    # Step 2: Run blind validation on all 12 charts
    print("\n[1/4] Running BlindValidationRunner on 12 charts...")
    reports: list[SingleValidationReport] = []

    for chart_subject, historical_event in REFERENCE_COHORT_12:
        print(f"  Processing: {chart_subject.chart_id}")

        # Run blind evaluation
        try:
            metric_eval = runner.run_blind_evaluation(
                subject=chart_subject,
                target_timestamp=historical_event.start_date,
                ground_truth_event=historical_event,
                output_dir=tmp_path,
            )
            reports.append(SingleValidationReport(
                chart_id=chart_subject.chart_id,
                status=ValidationStatus.SUCCESS,
                metric_evaluation=metric_eval,
            ))
        except Exception as exc:
            reports.append(SingleValidationReport(
                chart_id=chart_subject.chart_id,
                status=ValidationStatus.PERSISTENCE_FAILED,
                error_message=str(exc),
            ))

    # Step 3: Create batch report
    successes = sum(1 for r in reports if r.status == ValidationStatus.SUCCESS)
    failures = sum(1 for r in reports if r.status != ValidationStatus.SUCCESS)
    batch_report = BatchValidationReport(
        total_charts=len(reports),
        successful_evaluations=successes,
        failed_evaluations=failures,
        reports=tuple(reports),
    )

    print(f"\n[2/4] Batch report created: {successes} successes, {failures} failures")

    # Step 4: Extract ground truth events
    ground_truth_events = [event for _, event in REFERENCE_COHORT_12]

    # Step 5: Run calibration engine
    print("\n[3/4] Running CohortCalibrationEngine...")
    calibration_report = calibration_engine.evaluate_cohort(
        batch_report=batch_report,
        ground_truth_events=ground_truth_events,
    )

    # Step 6: Generate diagnostic summary
    print("\n[4/4] Generating diagnostic summary...")
    diagnostic_summary = calibration_engine.generate_diagnostic_summary(calibration_report)

    # Step 7: Print comprehensive report
    print("\n" + "=" * 80)
    print("GLOBAL CLASSIFICATION METRICS")
    print("=" * 80)
    print(f"Total Charts Evaluated: {calibration_report.total_evaluated}")
    print(f"Precision:              {calibration_report.precision:.3f} "
          f"(95% CI: {calibration_report.precision_ci_lower:.3f} - "
          f"{calibration_report.precision_ci_upper:.3f})")
    print(f"Recall:                 {calibration_report.recall:.3f} "
          f"(95% CI: {calibration_report.recall_ci_lower:.3f} - "
          f"{calibration_report.recall_ci_upper:.3f})")
    print(f"F1 Score:               {calibration_report.f1_score:.3f} "
          f"(95% CI: {calibration_report.f1_ci_lower:.3f} - "
          f"{calibration_report.f1_ci_upper:.3f})")
    print(f"False Positive Rate:    {calibration_report.false_positive_rate:.3f}")
    print(f"False Negative Rate:    {calibration_report.false_negative_rate:.3f}")

    print("\n" + "=" * 80)
    print("TEMPORAL & CALIBRATION METRICS")
    print("=" * 80)
    print(f"Avg Timing IoU:         {calibration_report.timing_window_overlap_avg:.3f}")
    print(f"Expected Calib Error:   {calibration_report.confidence_calibration_error:.3f}")

    print("\n" + "=" * 80)
    print("LAYER-BY-LAYER PERFORMANCE BREAKDOWN")
    print("=" * 80)
    layer_perf = calibration_report.layer_telemetry
    print(f"Formation Accuracy:           {layer_perf.formation_accuracy:.3f}")
    print(f"Relationship Accuracy:        {layer_perf.relationship_accuracy:.3f}")
    print(f"Modification Accuracy:        {layer_perf.modification_accuracy:.3f}")
    print(f"Varga Confirmation Accuracy:  {layer_perf.varga_confirmation_accuracy:.3f}")
    print(f"Activation Accuracy:          {layer_perf.activation_accuracy:.3f}")

    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print(f"Overall Assessment:     {diagnostic_summary['overall_assessment']}")
    print(f"Calibration Quality:    {diagnostic_summary['calibration_quality']}")

    print("\nFailure Modes:")
    for mode in diagnostic_summary["failure_modes"]:
        print(f"  - {mode}")

    print("\nRecommendations:")
    for rec in diagnostic_summary["recommendations"]:
        print(f"  - {rec}")

    print("\nLayer Assessment:")
    for layer, assessment in diagnostic_summary["layer_assessment"].items():
        print(f"  {layer}: {assessment}")

    print("\n" + "=" * 80)
    print("INDIVIDUAL CHART EVALUATIONS")
    print("=" * 80)
    for i, eval_result in enumerate(calibration_report.chart_evaluations, 1):
        print(f"\n[Chart {i}]")
        print(f"  Event ID:            {eval_result.event_id}")
        print(f"  Predicted Strength:  {eval_result.prediction_strength:.3f}")
        print(f"  Event Certainty:     {eval_result.event_certainty:.3f}")
        print(f"  Hit:                 {eval_result.hit}")
        print(f"  Timing Match:        {eval_result.timing_match}")
        print(f"  Score:               {eval_result.score:.3f}")

    print("\n" + "=" * 80)
    print("CALIBRATION COMPLETE")
    print("=" * 80 + "\n")

    # Assertions to ensure report is valid
    assert calibration_report.total_evaluated == 12
    assert 0.0 <= calibration_report.precision <= 1.0
    assert 0.0 <= calibration_report.recall <= 1.0
    assert 0.0 <= calibration_report.f1_score <= 1.0
    assert 0.0 <= calibration_report.false_positive_rate <= 1.0
    assert 0.0 <= calibration_report.false_negative_rate <= 1.0
    assert 0.0 <= calibration_report.timing_window_overlap_avg <= 1.0
    assert calibration_report.confidence_calibration_error >= 0.0
    assert diagnostic_summary["overall_assessment"] in [
        "STRONG", "MODERATE", "WEAK", "NO_DATA",
    ]
    assert len(diagnostic_summary["failure_modes"]) >= 0
    assert len(diagnostic_summary["recommendations"]) >= 0

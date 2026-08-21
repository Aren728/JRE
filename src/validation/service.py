"""Validation system service — runs validation against reference charts."""

from __future__ import annotations

from typing import Any

from .config import load_validation_config
from .errors import InvalidReferenceChartError, TriggerExtractionError
from .models import (
    ExtractedTrigger,
    ReferenceChart,
    TriggerSource,
    ValidationConfig,
    ValidationReport,
    ValidationResult,
    compute_match_score,
    extract_triggers_from_engines,
    find_missing_and_false_positives,
)


class ValidationService:
    """Validation service: runs reference chart validation against JRS outputs.

    Usage::

        svc = ValidationService()
        report = svc.run_validation(chart, evidence_packet)
    """

    def __init__(self, config: ValidationConfig | None = None) -> None:
        """Initialize the validation service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from
                    ``config/validation.toml``.
        """
        self._config = config or load_validation_config()

    def run_validation(
        self,
        chart: ReferenceChart,
        jrs_output: Any = None,
    ) -> ValidationReport:
        """Run validation for a single reference chart.

        Args:
            chart: The reference chart with known events.
            jrs_output: Optional EvidencePacket from JRE-024. If ``None``,
                       uses the chart's ground truth for trigger matching.

        Returns:
            A ValidationReport with the validation results.

        Raises:
            InvalidReferenceChartError: If the chart is malformed.
        """
        if not chart.chart_id:
            raise InvalidReferenceChartError("chart_id must not be empty")

        if not chart.known_events:
            raise InvalidReferenceChartError(
                f"Chart {chart.chart_id} has no known events",
            )

        # Collect all expected triggers from all events
        all_expected: list[str] = []
        for event in chart.known_events:
            all_expected.extend(event.expected_triggers)

        # Extract actual triggers
        if jrs_output is not None:
            actual = self._extract_from_jrs_output(jrs_output)
        else:
            actual = self._extract_from_ground_truth(chart)

        # Compute match score
        match_score = compute_match_score(
            tuple(all_expected),
            actual,
            self._config.trigger_weights,
        )

        # Find missing and false positives
        missing, false_pos = find_missing_and_false_positives(
            tuple(all_expected),
            actual,
        )

        result = ValidationResult(
            chart_id=chart.chart_id,
            expected_triggers=tuple(all_expected),
            actual_triggers=actual,
            match_score=match_score,
            missing_triggers=missing,
            false_positives=false_pos,
            total_events=len(chart.known_events),
        )

        return ValidationReport(
            results=(result,),
            overall_score=match_score,
            total_charts=1,
        )

    def run_batch_validation(
        self,
        charts: tuple[ReferenceChart, ...],
        jrs_outputs: tuple[Any, ...] | None = None,
    ) -> ValidationReport:
        """Run validation for multiple reference charts.

        Args:
            charts: Tuple of reference charts.
            jrs_outputs: Optional tuple of EvidencePackets, one per chart.

        Returns:
            A ValidationReport with aggregated results.
        """
        results: list[ValidationResult] = []

        for i, chart in enumerate(charts):
            output = jrs_outputs[i] if jrs_outputs and i < len(jrs_outputs) else None
            report = self.run_validation(chart, output)
            results.extend(report.results)

        overall_score = (
            sum(r.match_score for r in results) / len(results)
            if results
            else 0.0
        )

        return ValidationReport(
            results=tuple(results),
            overall_score=overall_score,
            total_charts=len(charts),
        )

    def _extract_from_jrs_output(
        self,
        jrs_output: Any,
    ) -> tuple[ExtractedTrigger, ...]:
        """Extract triggers from a JRS EvidencePacket.

        Args:
            jrs_output: The EvidencePacket from JRE-024.

        Returns:
            A tuple of extracted triggers.

        Raises:
            TriggerExtractionError: If extraction fails.
        """
        try:
            engine_names = tuple(
                eo.engine_name for eo in jrs_output.engine_outputs
            )
            research = jrs_output.research_evidence
            return extract_triggers_from_engines(
                engine_names,
                research,
                self._config.source_reliability,
            )
        except (AttributeError, TypeError) as exc:
            raise TriggerExtractionError(
                f"Failed to extract triggers from JRS output: {exc}",
            ) from exc

    def _extract_from_ground_truth(
        self,
        chart: ReferenceChart,
    ) -> tuple[ExtractedTrigger, ...]:
        """Extract triggers from a chart's ground truth data.

        When no JRS output is available, we use the chart's ground truth
        to create a baseline set of triggers for comparison.

        Args:
            chart: The reference chart.

        Returns:
            A tuple of triggers derived from ground truth.
        """
        triggers: list[ExtractedTrigger] = []

        # Use ground truth keys as evidence of engine presence
        gt = chart.ground_truth
        for key in sorted(gt.keys()):
            triggers.append(ExtractedTrigger(
                trigger_id=f"gt_{key}",
                source=TriggerSource.SYNTHESIS,
                confidence=1.0,
                metadata=f"Ground truth: {key}={gt[key]}",
            ))

        return tuple(triggers)

    @property
    def config(self) -> ValidationConfig:
        """Return the loaded configuration."""
        return self._config

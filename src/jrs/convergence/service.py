"""Convergence engine service — domain assessment from evidence and temporal data."""

from __future__ import annotations

from jrs.evidence.models import EvidenceDirection, EvidenceRecord
from jrs.temporal.models import EventWindow

from .config import load_convergence_config
from .errors import InvalidAssessmentInputError
from .models import (
    ConvergenceConfig,
    DomainAssessment,
    EvidenceDimensions,
    SourceConfidence,
    classify_assessment_status,
    classify_overall_strength,
    classify_timing_status,
    count_independent_channels,
)


class ConvergenceService:
    """Convergence engine: produces DomainAssessment from evidence and temporal data.

    Usage::

        svc = ConvergenceService()
        assessment = svc.assess_domain(
            "MARRIAGE_FORMATION", evidence_records, event_windows,
        )
    """

    def __init__(self, config: ConvergenceConfig | None = None) -> None:
        """Initialize the convergence service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from
                    ``config/convergence.toml``.
        """
        self._config = config or load_convergence_config()

    def assess_domain(
        self,
        outcome_taxonomy: str,
        evidence_records: tuple[EvidenceRecord, ...] = (),
        event_windows: tuple[EventWindow, ...] = (),
    ) -> DomainAssessment:
        """Assess evidence for a specific outcome taxonomy.

        Ingests EvidenceRecords and EventWindows to produce a structured,
        multi-dimensional DomainAssessment.

        Args:
            outcome_taxonomy: The outcome being assessed (e.g., "MARRIAGE_FORMATION").
            evidence_records: Tuple of EvidenceRecord objects.
            event_windows: Tuple of EventWindow objects.

        Returns:
            A DomainAssessment with dimensions and status classifications.

        Raises:
            InvalidAssessmentInputError: If outcome_taxonomy is empty.
        """
        if not outcome_taxonomy:
            raise InvalidAssessmentInputError("outcome_taxonomy must not be empty")

        # Separate records by direction
        support_records = tuple(
            r for r in evidence_records
            if r.direction is EvidenceDirection.SUPPORT
        )
        contradict_records = tuple(
            r for r in evidence_records
            if r.direction is EvidenceDirection.CONTRADICT
        )
        mitigate_records = tuple(
            r for r in evidence_records
            if r.direction is EvidenceDirection.MITIGATE
        )

        # Calculate dimensions
        independent = count_independent_channels(
            support_records, self._config.source_weights,
        )
        source_confidence = self._classify_source_confidence(support_records)
        timing_count = self._count_timing_convergence(event_windows)

        dimensions = EvidenceDimensions(
            supporting_count=len(support_records),
            independent_channels=independent,
            contradicting_count=len(contradict_records),
            mitigations=len(mitigate_records),
            timing_convergence_count=timing_count,
            source_confidence=source_confidence,
        )

        # Classify statuses
        assessment_status = classify_assessment_status(
            dimensions, self._config,
        )
        timing_status = classify_timing_status(
            timing_count, self._config,
        )
        overall_strength = classify_overall_strength(
            dimensions, self._config,
        )

        return DomainAssessment(
            outcome_taxonomy=outcome_taxonomy,
            dimensions=dimensions,
            assessment_status=assessment_status,
            timing_status=timing_status,
            overall_evidence_strength=overall_strength,
        )

    def _classify_source_confidence(
        self,
        records: tuple[EvidenceRecord, ...],
    ) -> SourceConfidence:
        """Classify source confidence based on average source weight."""
        if not records:
            return SourceConfidence.MODERATE

        weights = self._config.source_weights
        total_weight = 0.0
        count = 0

        for record in records:
            src_weight = weights.get(record.source_id, 0.8)
            total_weight += src_weight
            count += 1

        if count == 0:
            return SourceConfidence.MODERATE

        avg_weight = total_weight / count

        if avg_weight >= self._config.high_confidence_min_weight:
            return SourceConfidence.HIGH
        if avg_weight <= self._config.low_confidence_max_weight:
            return SourceConfidence.LOW

        return SourceConfidence.MODERATE

    def _count_timing_convergence(
        self,
        event_windows: tuple[EventWindow, ...],
    ) -> int:
        """Count event windows with convergent timing."""
        from jrs.temporal.models import ConvergenceLevel

        count = 0
        for window in event_windows:
            if window.convergence_level in (
                ConvergenceLevel.MODERATE,
                ConvergenceLevel.HIGH,
                ConvergenceLevel.VERY_HIGH,
            ):
                count += 1
        return count

    @property
    def config(self) -> ConvergenceConfig:
        """Return the loaded configuration."""
        return self._config

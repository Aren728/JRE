"""JRS-064 Rectification Integration — service.

Ingests candidate birth times, runs them through the JRS pipeline,
and evaluates how well the resulting assessments match known ground
truth events.  Proposes time adjustments using JRE-021 without
circular self-validation.

Strict Boundaries:
- Candidate generation is separated from candidate evaluation.
- No modification of existing domain services or JRE engines.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from jrs.convergence.models import (
    DomainAssessment,
)
from rectification import (
    EventType,
    LifeEvent,
    RectificationMethod,
    RectificationService,
)
from rectification.models import apply_offset_to_birth_time

from .errors import (
    InvalidCandidateError,
    InvalidKnownEventsError,
    NoAdjustmentError,
    PipelineEvaluationError,
)
from .models import (
    AdjustmentDirection,
    AdjustmentProposal,
    EventMatch,
    KnownEvent,
    MatchQuality,
    RectificationResult,
    classify_match_quality,
    compute_assessment_mismatch,
    compute_timing_mismatch,
)


class RectificationIntegrationService:
    """JRS-064 integration layer between JRE-021 rectification and JRS pipeline.

    Usage::

        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            birth_data={"birth_time_utc": "2000-01-01T12:00:00Z"},
            known_events=[KnownEvent(...)],
        )
    """

    def __init__(
        self,
        assessment_weight: float = 0.7,
        timing_weight: float = 0.3,
        max_adjustment_minutes: float = 120.0,
        adjustment_step_minutes: float = 5.0,
    ) -> None:
        """Initialize the rectification integration service.

        Args:
            assessment_weight: Weight for assessment status mismatch in
                the overall mismatch score.
            timing_weight: Weight for timing status mismatch in the
                overall mismatch score.
            max_adjustment_minutes: Maximum adjustment to consider in
                minutes.
            adjustment_step_minutes: Step size in minutes for scanning
                candidate offsets.
        """
        if not 0.0 <= assessment_weight <= 1.0:
            raise ValueError(
                f"assessment_weight must be in [0, 1], got {assessment_weight}"
            )
        if not 0.0 <= timing_weight <= 1.0:
            raise ValueError(
                f"timing_weight must be in [0, 1], got {timing_weight}"
            )
        if max_adjustment_minutes <= 0:
            raise ValueError(
                f"max_adjustment_minutes must be positive, got {max_adjustment_minutes}"
            )
        if adjustment_step_minutes <= 0:
            raise ValueError(
                f"adjustment_step_minutes must be positive, got {adjustment_step_minutes}"
            )
        self._assessment_weight = assessment_weight
        self._timing_weight = timing_weight
        self._max_adjustment_minutes = max_adjustment_minutes
        self._adjustment_step_minutes = adjustment_step_minutes

    # ── Public API ───────────────────────────────────────────────────────

    def evaluate_candidate(
        self,
        birth_data: dict[str, Any],
        known_events: list[KnownEvent],
        pipeline_output: dict[str, DomainAssessment] | None = None,
    ) -> RectificationResult:
        """Evaluate a candidate birth time against known ground truth events.

        This method is the EVALUATION half of the no-circularity boundary.
        It takes a fixed candidate and known events, and produces a mismatch
        score.  It does NOT generate new candidates.

        Args:
            birth_data: Dictionary containing at least ``birth_time_utc``.
            known_events: List of KnownEvent ground truth anchors.
            pipeline_output: Optional pre-computed mapping of
                ``domain_label -> DomainAssessment``.  If ``None``, an
                empty result is returned (the caller is expected to
                provide the pipeline output from the actual JRS pipeline).

        Returns:
            A RectificationResult with the mismatch score and per-event
            match details.

        Raises:
            InvalidCandidateError: If birth_data is missing birth_time_utc.
            InvalidKnownEventsError: If known_events is empty.
            PipelineEvaluationError: If pipeline_output is None.
        """
        candidate_time = birth_data.get("birth_time_utc", "")
        if not candidate_time:
            raise InvalidCandidateError(
                "birth_data must contain a non-empty birth_time_utc"
            )
        if not known_events:
            raise InvalidKnownEventsError(
                "known_events must be a non-empty list"
            )
        if pipeline_output is None:
            raise PipelineEvaluationError(
                "pipeline_output is required for evaluation"
            )

        # Evaluate each known event against the pipeline output
        event_matches: list[EventMatch] = []
        total_mismatch = 0.0
        supporting_ids: list[str] = []
        contradicting_ids: list[str] = []

        for known_event in known_events:
            match = self._match_event(known_event, pipeline_output)
            event_matches.append(match)
            total_mismatch += match.mismatch_score

            if match.match_quality in (
                MatchQuality.EXACT_MATCH,
                MatchQuality.STRONG_MATCH,
            ):
                supporting_ids.append(
                    f"{known_event.domain_label}:{known_event.expected_outcome}"
                )
            elif match.match_quality in (
                MatchQuality.WEAK_MATCH,
                MatchQuality.NO_MATCH,
            ):
                contradicting_ids.append(
                    f"{known_event.domain_label}:{known_event.expected_outcome}"
                )

        # Average mismatch across all known events
        avg_mismatch = total_mismatch / len(known_events) if known_events else 1.0

        # Suggest adjustment (separate from evaluation — no circularity)
        adjustment = self._compute_adjustment(avg_mismatch)

        return RectificationResult(
            candidate_time=candidate_time,
            mismatch_score=avg_mismatch,
            suggested_adjustment_minutes=adjustment,
            event_matches=tuple(event_matches),
            supporting_evidence_ids=tuple(supporting_ids),
            contradicting_evidence_ids=tuple(contradicting_ids),
        )

    def suggest_adjustments(
        self,
        birth_data: dict[str, Any],
        known_events: list[KnownEvent],
        pipeline_runner: Any = None,
    ) -> list[AdjustmentProposal]:
        """Suggest time adjustments using JRE-021 logic.

        This method is the GENERATION half of the no-circularity boundary.
        It proposes candidate offsets using classical rectification methods
        (via JRE-021), then evaluates them through evaluate_candidate.

        The key anti-circularity guarantee: the JRE-021 methods propose
        offsets based on transit/dasha timing, NOT based on whether the
        resulting assessments match known events.  The evaluation of those
        proposals is done separately by evaluate_candidate.

        Args:
            birth_data: Dictionary containing at least ``birth_time_utc``
                and optionally ``life_events`` and ``transit_times``.
            known_events: List of KnownEvent ground truth anchors.
            pipeline_runner: Optional callable that takes a birth_data
                dict and returns a dict of domain_label -> DomainAssessment.
                If None, only JRE-021-based proposals are returned
                without evaluation.

        Returns:
            A list of AdjustmentProposal objects, sorted by confidence
            descending.

        Raises:
            InvalidCandidateError: If birth_data is missing birth_time_utc.
            InvalidKnownEventsError: If known_events is empty.
        """
        candidate_time = birth_data.get("birth_time_utc", "")
        if not candidate_time:
            raise InvalidCandidateError(
                "birth_data must contain a non-empty birth_time_utc"
            )
        if not known_events:
            raise InvalidKnownEventsError(
                "known_events must be a non-empty list"
            )

        proposals: list[AdjustmentProposal] = []

        # Strategy 1: Classical rectification via JRE-021
        jre_proposals = self._jre021_proposals(birth_data)
        proposals.extend(jre_proposals)

        # Strategy 2: Brute-force scan (evaluate_candidate for each offset)
        scan_proposals = self._scan_proposals(
            birth_data, known_events, pipeline_runner,
        )
        proposals.extend(scan_proposals)

        # Deduplicate by offset (rounded to nearest step)
        seen_offsets: set[float] = set()
        unique_proposals: list[AdjustmentProposal] = []
        for p in proposals:
            rounded = round(p.offset_minutes / self._adjustment_step_minutes) * \
                self._adjustment_step_minutes
            if rounded not in seen_offsets:
                seen_offsets.add(rounded)
                unique_proposals.append(p)

        # Sort by confidence descending
        unique_proposals.sort(key=lambda p: p.confidence, reverse=True)

        if not unique_proposals:
            raise NoAdjustmentError(
                "No valid adjustment proposals could be generated"
            )

        return unique_proposals

    # ── Private Helpers ──────────────────────────────────────────────────

    def _match_event(
        self,
        known_event: KnownEvent,
        pipeline_output: dict[str, DomainAssessment],
    ) -> EventMatch:
        """Match a single known event against pipeline output."""
        # Find the assessment for this domain
        assessment = pipeline_output.get(known_event.domain_label)

        if assessment is None:
            # No assessment produced — total mismatch
            return EventMatch(
                known_event=known_event,
                candidate_outcome="",
                candidate_assessment_status="NEUTRAL",
                candidate_timing_status="INACTIVE",
                match_quality=MatchQuality.NO_MATCH,
                mismatch_score=1.0,
            )

        # Check if the expected outcome matches the assessed outcome
        outcome_match = (
            assessment.outcome_taxonomy == known_event.expected_outcome
        )

        # Compute assessment status mismatch
        assess_mismatch = compute_assessment_mismatch(
            known_event.expected_assessment_status,
            assessment.assessment_status.value,
        )

        # Compute timing status mismatch
        timing_mismatch = compute_timing_mismatch(
            known_event.expected_timing_status,
            assessment.timing_status.value,
        )

        # Combine mismatches with weights
        mismatch = (
            self._assessment_weight * assess_mismatch
            + self._timing_weight * timing_mismatch
        )

        # Penalize outcome mismatch
        if not outcome_match:
            mismatch = min(1.0, mismatch + 0.3)

        mismatch = max(0.0, min(1.0, mismatch))
        match_quality = classify_match_quality(mismatch)

        return EventMatch(
            known_event=known_event,
            candidate_outcome=assessment.outcome_taxonomy,
            candidate_assessment_status=assessment.assessment_status.value,
            candidate_timing_status=assessment.timing_status.value,
            match_quality=match_quality,
            mismatch_score=mismatch,
        )

    def _compute_adjustment(self, mismatch_score: float) -> float:
        """Compute a suggested adjustment in minutes from the mismatch score.

        Higher mismatch → larger adjustment suggested.
        Returns the magnitude (always positive); direction is implicit.
        """
        if mismatch_score <= 0.1:
            return 0.0
        # Linear scaling: mismatch 1.0 → max_adjustment
        return round(
            mismatch_score * self._max_adjustment_minutes
            / self._adjustment_step_minutes
        ) * self._adjustment_step_minutes

    def _jre021_proposals(
        self,
        birth_data: dict[str, Any],
    ) -> list[AdjustmentProposal]:
        """Generate proposals using JRE-021 classical rectification methods.

        This calls JRE-021's RectificationService to get transit-based
        offset suggestions.  The key: JRE-021 proposes based on transit
        timing alignment, NOT based on assessment quality.  This
        guarantees no circularity.
        """
        proposals: list[AdjustmentProposal] = []

        candidate_time = birth_data.get("birth_time_utc", "")
        life_events_raw = birth_data.get("life_events", ())
        transit_times = birth_data.get("transit_times", {})

        if not life_events_raw:
            return proposals

        # Convert raw events to LifeEvent objects
        life_events: list[LifeEvent] = []
        for ev in life_events_raw:
            if isinstance(ev, dict):
                try:
                    life_events.append(LifeEvent(
                        event_date_utc=ev.get("event_date_utc", ""),
                        event_type=EventType(ev.get("event_type", "OTHER")),
                        description=ev.get("description", ""),
                    ))
                except (ValueError, TypeError):
                    continue
            elif isinstance(ev, LifeEvent):
                life_events.append(ev)

        if not life_events:
            return proposals

        # Try each rectification method
        jre_service = RectificationService()
        for method in RectificationMethod:
            try:
                report = jre_service.calculate_offset(
                    candidate_time,
                    tuple(life_events),
                    method,
                    transit_times if transit_times else None,
                )
                # Extract the suggested offset
                if report.offsets:
                    suggested_dt = datetime.fromisoformat(
                        report.suggested_birth_time.replace("Z", "+00:00")
                    )
                    candidate_dt = datetime.fromisoformat(
                        candidate_time.replace("Z", "+00:00")
                    )
                    diff = (suggested_dt - candidate_dt).total_seconds() / 60.0

                    if abs(diff) > 0.5:
                        direction = (
                            AdjustmentDirection.LATER if diff > 0
                            else AdjustmentDirection.EARLIER
                        )
                        avg_confidence = sum(
                            r.confidence_score for r in report.offsets
                        ) / len(report.offsets)

                        proposals.append(AdjustmentProposal(
                            offset_minutes=abs(diff),
                            direction=direction,
                            confidence=avg_confidence,
                            reason=f"JRE-021 {method.value} method",
                            method=method.value,
                        ))
            except Exception:  # noqa: BLE001
                # JRE-021 may fail for some inputs — skip silently
                continue

        return proposals

    def _scan_proposals(
        self,
        birth_data: dict[str, Any],
        known_events: list[KnownEvent],
        pipeline_runner: Any,
    ) -> list[AdjustmentProposal]:
        """Generate proposals by scanning offset candidates.

        This is the brute-force approach: try offsets from
        -max_adjustment to +max_adjustment in step increments,
        evaluate each, and return the best-scoring ones.
        """
        if pipeline_runner is None:
            return []

        proposals: list[AdjustmentProposal] = []
        candidate_time = birth_data.get("birth_time_utc", "")
        step = self._adjustment_step_minutes
        max_adj = self._max_adjustment_minutes

        # Scan from -max to +max
        offset = -max_adj
        while offset <= max_adj:
            if abs(offset) < 0.5:
                offset += step
                continue

            adjusted_time = apply_offset_to_birth_time(
                candidate_time, offset * 60.0,
            )
            adjusted_data = {**birth_data, "birth_time_utc": adjusted_time}

            try:
                pipeline_output = pipeline_runner(adjusted_data)
                result = self.evaluate_candidate(
                    adjusted_data, known_events, pipeline_output,
                )
            except Exception:  # noqa: BLE001
                offset += step
                continue

            # Better mismatch → higher confidence
            confidence = 1.0 - result.mismatch_score
            if confidence > 0.0:
                direction = (
                    AdjustmentDirection.LATER if offset > 0
                    else AdjustmentDirection.EARLIER
                )
                proposals.append(AdjustmentProposal(
                    offset_minutes=abs(offset),
                    direction=direction,
                    confidence=confidence,
                    reason=f"Brute-force scan (mismatch={result.mismatch_score:.3f})",
                    method="SCAN",
                ))

            offset += step

        return proposals

    @property
    def assessment_weight(self) -> float:
        """Return the assessment mismatch weight."""
        return self._assessment_weight

    @property
    def timing_weight(self) -> float:
        """Return the timing mismatch weight."""
        return self._timing_weight

    @property
    def max_adjustment_minutes(self) -> float:
        """Return the maximum adjustment in minutes."""
        return self._max_adjustment_minutes

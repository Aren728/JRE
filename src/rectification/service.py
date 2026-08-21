"""JRE-021 RectificationService facade.

``RectificationService.calculate_offset`` is the canonical entry point:
it computes time offsets based on known life events using classical
rectification methods.

It produces NO qualitative output.
"""

from __future__ import annotations

from .config import load_config
from .errors import InvalidRectificationRequestError
from .models import (
    LifeEvent,
    RectificationConfig,
    RectificationMethod,
    RectificationReport,
    RectificationResult,
    aggregate_offsets,
    apply_offset_to_birth_time,
    compute_confidence_score,
    compute_offset_seconds,
    event_type_relevant_to_method,
)


class RectificationService:
    """Deterministic Rectification (Birth Time) computation facade."""

    def __init__(self, config: RectificationConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> RectificationConfig:
        return self._config

    def calculate_offset(
        self,
        birth_time_utc: str,
        events: tuple[LifeEvent, ...],
        method: RectificationMethod,
        transit_times: dict[str, str] | None = None,
    ) -> RectificationReport:
        """Calculate birth time offset using a single rectification method.

        Parameters
        ----------
        birth_time_utc : str
            Original birth time in ISO-UTC format.
        events : tuple of LifeEvent
            Known life events used as anchors.
        method : RectificationMethod
            The rectification method to apply.
        transit_times : dict, optional
            Mapping of event descriptions to transit/progression/dasha times
            in ISO-UTC format.  Required for all methods.

        Returns
        -------
        RectificationReport
            Suggested birth time and individual method results.
        """
        self._validate_request(birth_time_utc, events, method, transit_times)

        if transit_times is None:
            transit_times = {}

        results: list[RectificationResult] = []
        for event in events:
            transit_time = transit_times.get(event.description)
            if transit_time is None:
                continue

            offset = compute_offset_seconds(event.event_date_utc, transit_time)
            abs_offset = abs(offset)

            # Check max offset
            if abs_offset > self._config.max_offset_seconds:
                continue

            # Get method-specific parameters
            method_weight = self._config.method_weights.get(method.value, 0.33)
            method_tolerance = self._config.method_tolerances.get(method.value, 3600.0)

            # Check event type relevance
            relevant = event_type_relevant_to_method(event.event_type, method)

            # Check corroboration: do other events with same type produce similar offsets?
            corroborated = self._check_corroboration(
                event, offset, events, transit_times, method,
            )

            # Compute confidence
            confidence = compute_confidence_score(
                offset_seconds=abs_offset,
                tolerance_seconds=method_tolerance,
                method_weight=method_weight,
                event_type_relevant=relevant,
                corroborated=corroborated,
                evidence_weights=self._config.evidence_weights,
            )

            # Build evidence list
            evidence: list[str] = []
            evidence.append(f"Method: {method.value}")
            evidence.append(f"Event: {event.event_type.value} at {event.event_date_utc}")
            evidence.append(f"Transit time: {transit_time}")
            evidence.append(f"Offset: {offset:.1f} seconds")
            if relevant:
                evidence.append("Event type is relevant to this method")
            if corroborated:
                evidence.append("Multiple events corroborate this offset")

            results.append(RectificationResult(
                method=method,
                calculated_offset_seconds=offset,
                confidence_score=confidence,
                evidence=tuple(evidence),
            ))

        # Aggregate into a single suggested birth time
        aggregate = aggregate_offsets(tuple(results), self._config.max_offset_seconds)
        suggested = apply_offset_to_birth_time(birth_time_utc, aggregate)

        return RectificationReport(
            input_birth_time=birth_time_utc,
            suggested_birth_time=suggested,
            offsets=tuple(results),
        )

    def _check_corroboration(
        self,
        target_event: LifeEvent,
        target_offset: float,
        all_events: tuple[LifeEvent, ...],
        transit_times: dict[str, str],
        method: RectificationMethod,
    ) -> bool:
        """Check if other events of the same type corroborate the offset.

        Corroboration means another event of the same type produces an
        offset within 20% of the target offset.
        """
        tolerance_ratio = 0.20
        for event in all_events:
            if event is target_event:
                continue
            if event.event_type != target_event.event_type:
                continue
            transit_time = transit_times.get(event.description)
            if transit_time is None:
                continue
            other_offset = compute_offset_seconds(event.event_date_utc, transit_time)
            if abs(target_offset) < 1e-9:
                if abs(other_offset) < 1e-9:
                    return True
            else:
                if abs(other_offset - target_offset) / abs(target_offset) <= tolerance_ratio:
                    return True
        return False

    def _validate_request(
        self,
        birth_time_utc: str,
        events: tuple[LifeEvent, ...],
        method: RectificationMethod,
        transit_times: dict[str, str] | None,
    ) -> None:
        """Validate the rectification request."""
        if not isinstance(birth_time_utc, str) or birth_time_utc == "":
            raise InvalidRectificationRequestError(
                "birth_time_utc must be a non-empty string"
            )
        if not isinstance(events, tuple) or not events:
            raise InvalidRectificationRequestError(
                "events must be a non-empty tuple of LifeEvent values"
            )
        for event in events:
            if not isinstance(event, LifeEvent):
                raise InvalidRectificationRequestError(
                    f"events must contain LifeEvent values, "
                    f"got {type(event).__name__}"
                )
        if not isinstance(method, RectificationMethod):
            raise InvalidRectificationRequestError(
                f"method must be a RectificationMethod, "
                f"got {type(method).__name__}"
            )

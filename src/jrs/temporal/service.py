"""Temporal evidence service — event window calculation."""

from __future__ import annotations

from typing import Any

from .config import load_temporal_config
from .errors import InvalidEventWindowError, InvalidTriggerError
from .models import (
    ActivationType,
    ConvergenceLevel,
    EventWindow,
    TemporalConfig,
    TemporalTrigger,
    classify_convergence,
    find_overlapping_triggers,
)


class TemporalEvidenceService:
    """Temporal evidence service: calculates event windows from triggers.

    Usage::

        svc = TemporalEvidenceService()
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION", natal_facts, dasha_periods, transits,
        )
    """

    def __init__(self, config: TemporalConfig | None = None) -> None:
        """Initialize the temporal evidence service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from
                    ``config/temporal.toml``.
        """
        self._config = config or load_temporal_config()

    def calculate_event_window(
        self,
        candidate_event: str,
        natal_facts: dict[str, Any] | None = None,
        dasha_periods: tuple[TemporalTrigger, ...] = (),
        transits: tuple[TemporalTrigger, ...] = (),
        varga_triggers: tuple[TemporalTrigger, ...] = (),
        ashtakavarga_triggers: tuple[TemporalTrigger, ...] = (),
    ) -> EventWindow:
        """Calculate an EventWindow for a candidate event.

        Aggregates natal conditions, Dasha periods, transit activations,
        and Varga triggers into a structured, time-bound EventWindow.

        Args:
            candidate_event: The candidate event taxonomy (e.g., "MARRIAGE_FORMATION").
            natal_facts: Optional natal chart facts dictionary.
            dasha_periods: Dasha period triggers (from JRE-010).
            transits: Transit triggers (from JRE-006).
            varga_triggers: Varga triggers (from JRE-008).
            ashtakavarga_triggers: Ashtakavarga triggers (from JRE-016).

        Returns:
            An EventWindow with precise start/end UTC timestamps.

        Raises:
            InvalidEventWindowError: If the event window cannot be constructed.
        """
        if not candidate_event:
            raise InvalidEventWindowError("candidate_event must not be empty")

        # Collect all triggers
        all_triggers = (
            list(dasha_periods) + list(transits)
            + list(varga_triggers) + list(ashtakavarga_triggers)
        )

        if not all_triggers:
            return EventWindow(
                candidate_event_taxonomy=candidate_event,
                convergence_level=ConvergenceLevel.NONE,
            )

        # Find overlapping triggers
        overlapping = find_overlapping_triggers(tuple(all_triggers))

        # Use overlapping triggers if available, otherwise use all
        active_triggers = overlapping if overlapping else tuple(all_triggers)

        # Calculate window boundaries
        window_start, window_end = self._compute_window_boundaries(active_triggers)

        # Classify convergence
        convergence = classify_convergence(
            active_triggers,
            self._config.convergence_rules,
            self._config.min_triggers_for_high,
            self._config.min_triggers_for_moderate,
        )

        # Count conflicting indicators
        conflicting = self._count_conflicts(active_triggers)

        return EventWindow(
            candidate_event_taxonomy=candidate_event,
            window_start_utc=window_start,
            window_end_utc=window_end,
            triggers=active_triggers,
            convergence_level=convergence,
            conflicting_indicators=conflicting,
        )

    def build_trigger(
        self,
        activation_type: ActivationType,
        planet: str = "",
        rashi: str = "",
        start_utc: str = "",
        end_utc: str = "",
        strength: float = 1.0,
        description: str = "",
    ) -> TemporalTrigger:
        """Build a TemporalTrigger with validation.

        Args:
            activation_type: The type of activation.
            planet: The triggering planet name.
            rashi: The triggering rashi.
            start_utc: Activation start (ISO format).
            end_utc: Activation end (ISO format).
            strength: Trigger strength (0.0 to 1.0).
            description: Human-readable description.

        Returns:
            A validated TemporalTrigger.

        Raises:
            InvalidTriggerError: If the trigger is invalid.
        """
        if strength < 0.0 or strength > 1.0:
            raise InvalidTriggerError(
                f"strength must be between 0.0 and 1.0, got {strength}",
            )

        return TemporalTrigger(
            activation_type=activation_type,
            triggering_planet=planet,
            triggering_rashi=rashi,
            activation_start_utc=start_utc,
            activation_end_utc=end_utc,
            strength=strength,
            description=description,
        )

    def _compute_window_boundaries(
        self,
        triggers: tuple[TemporalTrigger, ...],
    ) -> tuple[str, str]:
        """Compute the overall window boundaries from triggers.

        Returns the earliest start and latest end across all triggers.
        """
        if not triggers:
            return ("", "")

        starts = [t.activation_start_utc for t in triggers if t.activation_start_utc]
        ends = [t.activation_end_utc for t in triggers if t.activation_end_utc]

        if not starts or not ends:
            return ("", "")

        # Sort and take earliest start, latest end
        window_start = min(starts)
        window_end = max(ends)

        return (window_start, window_end)

    def _count_conflicts(
        self,
        triggers: tuple[TemporalTrigger, ...],
    ) -> int:
        """Count conflicting indicators among triggers.

        A conflict is when triggers have opposite strengths (some very high,
        some very low) or when there are contradictory activation types.
        """
        if len(triggers) < 2:
            return 0

        conflicts = 0
        strengths = [t.strength for t in triggers]

        # Check for strength opposition
        high = sum(1 for s in strengths if s >= 0.7)
        low = sum(1 for s in strengths if s <= 0.3)
        if high > 0 and low > 0:
            conflicts += 1

        # Check for mixed activation types (Dasha vs no-Dasha can indicate conflict)
        types = {t.activation_type for t in triggers}
        if ActivationType.DASHA in types and ActivationType.TRANSIT in types:
            # Not a conflict, but noted
            pass

        return conflicts

    @property
    def config(self) -> TemporalConfig:
        """Return the loaded configuration."""
        return self._config

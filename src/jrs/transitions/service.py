"""Transitions engine service — deterministic temporal state-change calculation.

Ingests Dasha periods, transit events, and eclipse events.  Calculates
the exact timestamps where state changes occur (Dasha boundaries, Nakshatra
ingresses, Rashi ingresses, retrograde stations, eclipse windows, etc.).

Output is deterministic facts (TransitionEvent objects), NOT interpretations.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from jyotish.models import (
    EclipseEvent,
    TransitEvent,
    TransitEventKind,
)

from .errors import InvalidTransitionInputError
from .models import (
    StateChange,
    TransitionEvent,
    TransitionType,
)


class TransitionService:
    """Deterministic transition calculation engine.

    Ingests Dasha periods, transit events, and eclipse events from
    existing JRE engines and produces TransitionEvent facts.

    Usage::

        svc = TransitionService()
        events = svc.calculate_transitions(
            ephemeris_data=transit_events,
            dasha_data=dasha_periods,
            eclipse_data=eclipse_events,
        )
    """

    def __init__(
        self,
        sandhi_buffer_days: float = 3.0,
    ) -> None:
        """Initialize the transition service.

        Args:
            sandhi_buffer_days: Number of days before/after a Dasha
                boundary to define the Dasha Sandhi window.
        """
        if sandhi_buffer_days < 0:
            raise InvalidTransitionInputError(
                f"sandhi_buffer_days must be >= 0, got {sandhi_buffer_days}"
            )
        self._sandhi_buffer = timedelta(days=sandhi_buffer_days)

    def calculate_transitions(
        self,
        ephemeris_data: tuple[TransitEvent, ...] | None = None,
        dasha_data: tuple[Any, ...] | None = None,
        eclipse_data: tuple[EclipseEvent, ...] | None = None,
    ) -> tuple[TransitionEvent, ...]:
        """Calculate all transition events from input data.

        Args:
            ephemeris_data: Tuple of TransitEvent objects from JRE-003.
            dasha_data: Tuple of DashaPeriod objects from JRE-010.
            eclipse_data: Tuple of EclipseEvent objects from JRE-003.

        Returns:
            A tuple of TransitionEvent objects, sorted by timestamp.

        Raises:
            InvalidTransitionInputError: If inputs are invalid types.
        """
        events: list[TransitionEvent] = []

        # Process Dasha periods → DASHA_BOUNDARY + DASHA_SANDHI
        if dasha_data:
            if not isinstance(dasha_data, tuple):
                raise InvalidTransitionInputError("dasha_data must be a tuple")
            events.extend(self._process_dasha_periods(dasha_data))

        # Process Transit events → NAKSHATRA_INGRESS, RASHI_INGRESS, etc.
        if ephemeris_data:
            if not isinstance(ephemeris_data, tuple):
                raise InvalidTransitionInputError("ephemeris_data must be a tuple")
            events.extend(self._process_transit_events(ephemeris_data))

        # Process Eclipse events → ECLIPSE_WINDOW
        if eclipse_data:
            if not isinstance(eclipse_data, tuple):
                raise InvalidTransitionInputError("eclipse_data must be a tuple")
            events.extend(self._process_eclipse_events(eclipse_data))

        # Sort by timestamp for deterministic output
        events.sort(key=lambda e: e.exact_timestamp)

        return tuple(events)

    # ── Dasha Processing ─────────────────────────────────────────────────

    def _process_dasha_periods(
        self,
        periods: tuple[Any, ...],
    ) -> list[TransitionEvent]:
        """Process DashaPeriod objects into DASHA_BOUNDARY and DASHA_SANDHI events."""
        events: list[TransitionEvent] = []

        for i, period in enumerate(periods):
            # DASHA_BOUNDARY: the start of each period
            before_lord = ""
            after_lord = _period_lord_label(period)

            if i > 0:
                before_lord = _period_lord_label(periods[i - 1])

            timestamp = _datetime_to_iso(period.start_utc)

            state_change = StateChange(
                before=before_lord,
                after=after_lord,
            )

            duration = (period.end_utc - period.start_utc).total_seconds()

            affected: tuple[str, ...] = ("dasha_lord",)
            if period.antardasha_lord is not None:
                affected = ("dasha_lord", "antardasha_lord")
            if period.pratyantardasha_lord is not None:
                affected = ("dasha_lord", "antardasha_lord", "pratyantardasha_lord")

            events.append(TransitionEvent(
                transition_type=TransitionType.DASHA_BOUNDARY,
                exact_timestamp=timestamp,
                state_change=state_change,
                affected_facts=affected,
                provenance="JRE-010",
                duration_seconds=duration,
                metadata={"depth": str(period.depth)},
            ))

            # DASHA_SANDHI: junction window before the boundary
            sandhi_start = period.start_utc - self._sandhi_buffer
            sandhi_end = period.start_utc + self._sandhi_buffer
            sandhi_ts = _datetime_to_iso(sandhi_start)

            events.append(TransitionEvent(
                transition_type=TransitionType.DASHA_SANDHI,
                exact_timestamp=sandhi_ts,
                state_change=StateChange(
                    before=before_lord,
                    after=after_lord,
                ),
                affected_facts=("dasha_lord",),
                provenance="JRE-010",
                duration_seconds=self._sandhi_buffer.total_seconds() * 2,
                metadata={
                    "sandhi_window_end": _datetime_to_iso(sandhi_end),
                },
            ))

        return events

    # ── Transit Event Processing ─────────────────────────────────────────

    def _process_transit_events(
        self,
        transit_events: tuple[TransitEvent, ...],
    ) -> list[TransitionEvent]:
        """Process TransitEvent objects into transition events."""
        events: list[TransitionEvent] = []

        for te in transit_events:
            transition_type = _transit_kind_to_transition_type(te.kind)
            if transition_type is None:
                continue

            before_state = _format_transit_state_before(te)
            after_state = _format_transit_state_after(te)

            metadata: dict[str, str] = {
                "body": te.body.value,
                "direction": te.direction.value,
            }
            if te.boundary_deg is not None:
                metadata["boundary_deg"] = str(te.boundary_deg)

            affected = _transit_affected_facts(te.kind)

            events.append(TransitionEvent(
                transition_type=transition_type,
                exact_timestamp=te.event_utc_iso,
                state_change=StateChange(
                    before=before_state,
                    after=after_state,
                ),
                affected_facts=affected,
                provenance="JRE-003",
                metadata=metadata,
            ))

        return events

    # ── Eclipse Processing ───────────────────────────────────────────────

    def _process_eclipse_events(
        self,
        eclipse_events: tuple[EclipseEvent, ...],
    ) -> list[TransitionEvent]:
        """Process EclipseEvent objects into ECLIPSE_WINDOW transition events."""
        events: list[TransitionEvent] = []

        for ee in eclipse_events:
            duration = (
                ee.post_event_interval_days + ee.pre_event_interval_days
            ) * 86400.0

            metadata: dict[str, str] = {
                "eclipse_kind": ee.kind.value,
                "classification": ee.classification.value,
                "magnitude": str(ee.magnitude),
            }

            events.append(TransitionEvent(
                transition_type=TransitionType.ECLIPSE_WINDOW,
                exact_timestamp=ee.maximum_utc_iso,
                state_change=StateChange(
                    before=f"{ee.kind.value}_PRE_ECLIPSE",
                    after=f"{ee.kind.value}_POST_ECLIPSE",
                ),
                affected_facts=("eclipse_kind", "eclipse_classification"),
                provenance="JRE-003-eclipse",
                duration_seconds=duration,
                metadata=metadata,
            ))

        return events


# ── Helper Functions ─────────────────────────────────────────────────────────


def _transit_kind_to_transition_type(kind: TransitEventKind) -> TransitionType | None:
    """Map a TransitEventKind to a TransitionType."""
    mapping: dict[TransitEventKind, TransitionType] = {
        TransitEventKind.NAKSHATRA_INGRESS: TransitionType.NAKSHATRA_INGRESS,
        TransitEventKind.RASHI_INGRESS: TransitionType.RASHI_INGRESS,
        TransitEventKind.STATION_RETROGRADE: TransitionType.RETROGRADE_STATION,
        TransitEventKind.STATION_DIRECT: TransitionType.DIRECT_STATION,
    }
    return mapping.get(kind)


def _period_lord_label(period: Any) -> str:
    """Extract a human-readable label for a Dasha period's lord."""
    lords: list[str] = []
    if hasattr(period, "mahadasha_lord"):
        lords.append(period.mahadasha_lord.value)
    if hasattr(period, "antardasha_lord") and period.antardasha_lord is not None:
        lords.append(period.antardasha_lord.value)
    if hasattr(period, "pratyantardasha_lord") and period.pratyantardasha_lord is not None:
        lords.append(period.pratyantardasha_lord.value)
    return "-".join(lords)


def _datetime_to_iso(dt: Any) -> str:
    """Convert a datetime to ISO-8601 UTC string."""
    if hasattr(dt, "isoformat"):
        result = dt.isoformat()
        if isinstance(result, str):
            return result
    return str(dt)


def _format_transit_state_before(te: TransitEvent) -> str:
    """Format the 'before' state description for a transit event."""
    if te.kind in (TransitEventKind.RASHI_INGRESS, TransitEventKind.NAKSHATRA_INGRESS):
        # For ingress events, the 'before' is the previous state
        if te.boundary_deg is not None:
            return f"approaching_{te.boundary_deg:.1f}deg"
        return f"pre_{te.kind.value}"
    if te.kind in (TransitEventKind.STATION_RETROGRADE, TransitEventKind.STATION_DIRECT):
        return f"pre_{te.kind.value}"
    return f"pre_{te.kind.value}"


def _format_transit_state_after(te: TransitEvent) -> str:
    """Format the 'after' state description for a transit event."""
    if te.reached is not None:
        return str(te.reached.value) if hasattr(te.reached, "value") else str(te.reached)
    return f"post_{te.kind.value}"


def _transit_affected_facts(kind: TransitEventKind) -> tuple[str, ...]:
    """Determine which facts are affected by a transit event kind."""
    if kind in (TransitEventKind.RASHI_INGRESS, TransitEventKind.RASHI_EGRESS):
        return ("rashi", "degree_in_rashi")
    if kind in (TransitEventKind.NAKSHATRA_INGRESS, TransitEventKind.NAKSHATRA_EGRESS):
        return ("nakshatra", "pada", "degree_in_nakshatra")
    if kind in (TransitEventKind.PADA_INGRESS, TransitEventKind.PADA_EGRESS):
        return ("pada",)
    if kind in (TransitEventKind.STATION_RETROGRADE, TransitEventKind.STATION_DIRECT):
        return ("retrograde", "speed_longitude")
    return ("longitude_used",)

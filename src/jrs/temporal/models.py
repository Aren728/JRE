"""Temporal evidence data models — activation types, triggers, event windows."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────

class ActivationType(Enum):
    """Types of temporal activation."""

    DASHA = "DASHA"
    ANTARDASHA = "ANTARDASHA"
    TRANSIT = "TRANSIT"
    VARGA = "VARGA"
    ASHTAKAVARGA = "ASHTAKAVARGA"
    CLASSICAL_AGE = "CLASSICAL_AGE"


class ConvergenceLevel(Enum):
    """Level of convergence when multiple triggers align."""

    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


# Convergence numeric mapping
CONVERGENCE_VALUES: dict[ConvergenceLevel, float] = {
    ConvergenceLevel.NONE: 0.0,
    ConvergenceLevel.LOW: 0.25,
    ConvergenceLevel.MODERATE: 0.5,
    ConvergenceLevel.HIGH: 0.75,
    ConvergenceLevel.VERY_HIGH: 1.0,
}


# ── Core Models ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TemporalTrigger:
    """A single temporal activation trigger."""

    activation_type: ActivationType
    triggering_planet: str = ""
    triggering_rashi: str = ""
    activation_start_utc: str = ""  # ISO format
    activation_end_utc: str = ""  # ISO format
    strength: float = 1.0
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "activation_type": self.activation_type.value,
            "triggering_planet": self.triggering_planet,
            "triggering_rashi": self.triggering_rashi,
            "activation_start_utc": self.activation_start_utc,
            "activation_end_utc": self.activation_end_utc,
            "strength": self.strength,
            "description": self.description,
        }


@dataclass(frozen=True)
class EventWindow:
    """A time-bound window where conditions converge for a candidate event."""

    candidate_event_taxonomy: str
    window_start_utc: str = ""  # ISO format
    window_end_utc: str = ""  # ISO format
    triggers: tuple[TemporalTrigger, ...] = ()
    convergence_level: ConvergenceLevel = ConvergenceLevel.NONE
    conflicting_indicators: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "candidate_event_taxonomy": self.candidate_event_taxonomy,
            "window_start_utc": self.window_start_utc,
            "window_end_utc": self.window_end_utc,
            "triggers": [t.to_dict() for t in self.triggers],
            "convergence_level": self.convergence_level.value,
            "conflicting_indicators": self.conflicting_indicators,
        }


# ── Temporal Config (embedded) ───────────────────────────────────────────────

@dataclass(frozen=True)
class TemporalConfig:
    """Configuration for the temporal evidence layer."""

    version: str = "1.0"
    convergence_rules: dict[str, float] = field(default_factory=dict)
    min_triggers_for_high: int = 3
    min_triggers_for_moderate: int = 2
    activation_type_weights: dict[str, float] = field(default_factory=dict)


# ── Overlap Calculation Helpers ──────────────────────────────────────────────

def parse_iso_timestamp(ts: str) -> datetime | None:
    """Parse an ISO format timestamp string.

    Args:
        ts: ISO format timestamp string.

    Returns:
        A datetime object, or None if parsing fails.
    """
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, TypeError):
        return None


def windows_overlap(
    start1: str, end1: str,
    start2: str, end2: str,
) -> bool:
    """Check if two time windows overlap.

    Args:
        start1, end1: First window boundaries (ISO format).
        start2, end2: Second window boundaries (ISO format).

    Returns:
        True if the windows overlap.
    """
    dt_start1 = parse_iso_timestamp(start1)
    dt_end1 = parse_iso_timestamp(end1)
    dt_start2 = parse_iso_timestamp(start2)
    dt_end2 = parse_iso_timestamp(end2)

    if dt_start1 is None or dt_end1 is None or dt_start2 is None or dt_end2 is None:
        return False

    return dt_start1 <= dt_end2 and dt_start2 <= dt_end1


def compute_overlap_window(
    start1: str, end1: str,
    start2: str, end2: str,
) -> tuple[str, str]:
    """Compute the overlapping time window of two periods.

    Args:
        start1, end1: First window boundaries (ISO format).
        start2, end2: Second window boundaries (ISO format).

    Returns:
        A tuple of (overlap_start, overlap_end) in ISO format.
        Returns empty strings if no overlap.
    """
    dt_start1 = parse_iso_timestamp(start1)
    dt_end1 = parse_iso_timestamp(end1)
    dt_start2 = parse_iso_timestamp(start2)
    dt_end2 = parse_iso_timestamp(end2)

    if dt_start1 is None or dt_end1 is None or dt_start2 is None or dt_end2 is None:
        return ("", "")

    overlap_start = max(dt_start1, dt_start2)
    overlap_end = min(dt_end1, dt_end2)

    if overlap_start > overlap_end:
        return ("", "")

    return (overlap_start.isoformat(), overlap_end.isoformat())


def classify_convergence(
    triggers: tuple[TemporalTrigger, ...],
    convergence_rules: dict[str, float] | None = None,
    min_high: int = 3,
    min_moderate: int = 2,
) -> ConvergenceLevel:
    """Classify the convergence level based on overlapping triggers.

    Uses weighted scoring based on activation types and the number of
    distinct triggers that overlap in time.

    Args:
        triggers: The tuple of temporal triggers.
        convergence_rules: Optional mapping of trigger type pairs to scores.
        min_high: Minimum triggers for HIGH convergence.
        min_moderate: Minimum triggers for MODERATE convergence.

    Returns:
        The classified ConvergenceLevel.
    """
    if not triggers:
        return ConvergenceLevel.NONE

    # Count distinct activation types
    distinct_types = {t.activation_type for t in triggers}
    num_distinct = len(distinct_types)

    # Compute weighted score
    score = sum(t.strength for t in triggers)
    avg_strength = score / len(triggers) if triggers else 0.0

    # Combine type diversity and strength
    # More distinct types = higher convergence
    if num_distinct >= 4 and avg_strength >= 0.8:
        return ConvergenceLevel.VERY_HIGH
    if num_distinct >= 3 or (num_distinct >= 2 and len(triggers) >= min_high):
        return ConvergenceLevel.HIGH
    if num_distinct >= 2 or len(triggers) >= min_moderate:
        return ConvergenceLevel.MODERATE
    if len(triggers) >= 1:
        return ConvergenceLevel.LOW

    return ConvergenceLevel.NONE


def find_overlapping_triggers(
    triggers: tuple[TemporalTrigger, ...],
) -> tuple[TemporalTrigger, ...]:
    """Find triggers that overlap with at least one other trigger.

    Args:
        triggers: The tuple of temporal triggers.

    Returns:
        A tuple of triggers that have temporal overlap with another trigger.
    """
    if len(triggers) < 2:
        return ()

    overlapping: list[TemporalTrigger] = []
    for i, t1 in enumerate(triggers):
        for j, t2 in enumerate(triggers):
            if i >= j:
                continue
            if windows_overlap(
                t1.activation_start_utc, t1.activation_end_utc,
                t2.activation_start_utc, t2.activation_end_utc,
            ):
                if t1 not in overlapping:
                    overlapping.append(t1)
                if t2 not in overlapping:
                    overlapping.append(t2)

    return tuple(overlapping)

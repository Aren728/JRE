"""Transitions engine data models — deterministic temporal state-change facts.

This module calculates exact transition EVENTS as deterministic facts.
It does NOT interpret what these transitions mean for the user.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────


class TransitionType(Enum):
    """Classification of temporal state-change transitions."""

    DASHA_BOUNDARY = "DASHA_BOUNDARY"
    DASHA_SANDHI = "DASHA_SANDHI"
    NAKSHATRA_INGRESS = "NAKSHATRA_INGRESS"
    RASHI_INGRESS = "RASHI_INGRESS"
    RETROGRADE_STATION = "RETROGRADE_STATION"
    DIRECT_STATION = "DIRECT_STATION"
    ECLIPSE_WINDOW = "ECLIPSE_WINDOW"
    DIGNITY_TRANSITION = "DIGNITY_TRANSITION"


# ── Core Models ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class StateChange:
    """A before/after state description for a transition.

    ``before`` and ``after`` are free-form string descriptions of the
    state that was active before and after the transition.
    """

    before: str = ""
    after: str = ""

    def to_dict(self) -> dict[str, str]:
        """Deterministic serialization."""
        return {"before": self.before, "after": self.after}


@dataclass(frozen=True)
class TransitionEvent:
    """A single deterministic temporal state-change fact.

    This is a FACT container — it records what changed and when,
    without interpreting the significance of the change.
    """

    transition_type: TransitionType
    exact_timestamp: str  # ISO-8601 UTC
    state_change: StateChange
    affected_facts: tuple[str, ...] = ()
    provenance: str = ""
    duration_seconds: float | None = None
    deterministic_id: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Compute deterministic_id if not provided."""
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_transition_hash(self)
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "transition_type": self.transition_type.value,
            "exact_timestamp": self.exact_timestamp,
            "state_change": self.state_change.to_dict(),
            "affected_facts": list(self.affected_facts),
            "provenance": self.provenance,
            "duration_seconds": self.duration_seconds,
            "deterministic_id": self.deterministic_id,
            "metadata": dict(self.metadata),
        }


# ── Deterministic Hashing ────────────────────────────────────────────────────


def _compute_transition_hash(event: TransitionEvent) -> str:
    """Compute a deterministic SHA-256 hash for a TransitionEvent."""
    data = {
        "transition_type": event.transition_type.value,
        "exact_timestamp": event.exact_timestamp,
        "state_change": event.state_change.to_dict(),
        "affected_facts": list(event.affected_facts),
        "provenance": event.provenance,
        "duration_seconds": event.duration_seconds,
        "metadata": event.metadata,
    }
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update(b"transition_event:")
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


def compute_deterministic_id(event: TransitionEvent) -> str:
    """Public wrapper: compute the deterministic ID for a TransitionEvent."""
    return _compute_transition_hash(event)

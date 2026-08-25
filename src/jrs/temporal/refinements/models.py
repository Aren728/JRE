"""JRS-073 Temporal Refinements — data models.

Defines ``TemporalModifier`` objects that represent time-bound weight
adjustments to EvidenceRecords.  Two primary modifier types:

- **DASHA_SANDHI**: Tapers evidence weight near Dasha period boundaries,
  reflecting the classical teaching that transitional periods carry
  uncertainty (BPHS Dasha Vigyana Ch. 8).
- **ECLIPSE_WINDOW**: Amplifies malefic evidence and dampens benefic
  evidence during eclipse visibility windows (BPHS Graha Pravesh
  Ch. 18, Phaladeepika Ch. 14).

All dataclasses are frozen with SHA-256 deterministic IDs.  No
interpretation is performed here — only modifier definitions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ModifierType(StrEnum):
    """Types of temporal modifiers."""

    DASHA_SANDHI = "DASHA_SANDHI"
    ECLIPSE_WINDOW = "ECLIPSE_WINDOW"


@dataclass(frozen=True)
class TemporalModifier:
    """A time-bound weight adjustment to EvidenceRecords.

    TemporalModifier represents a deterministic scaling factor that
    applies to evidence falling within a specific time window.  The
    ``weight_scalar`` multiplies the evidence strength, allowing the
    temporal refinement layer to taper or amplify evidence near
    Dasha boundaries or during eclipse windows.

    Attributes:
        modifier_type: The type of modifier (DASHA_SANDHI or ECLIPSE_WINDOW).
        start_time: ISO 8601 UTC timestamp — start of the modifier window.
        end_time: ISO 8601 UTC timestamp — end of the modifier window.
        weight_scalar: Multiplier applied to evidence strength (0.0–2.0).
            1.0 means no change; <1.0 dampens; >1.0 amplifies.
        event_window_start_utc: ISO 8601 UTC timestamp — the Dasha period
            start (for DASHA_SANDHI) or eclipse event start.
        event_window_end_utc: ISO 8601 UTC timestamp — the Dasha period
            end (for DASHA_SANDHI) or eclipse event end.
        description: Human-readable description of the modifier.
        deterministic_id: SHA-256 hash computed from fields on construction.
    """

    modifier_type: ModifierType
    start_time: str  # ISO 8601 UTC
    end_time: str  # ISO 8601 UTC
    weight_scalar: float = 1.0
    event_window_start_utc: str = ""
    event_window_end_utc: str = ""
    description: str = ""
    deterministic_id: str = field(default="")

    def __post_init__(self) -> None:
        """Validate fields and compute deterministic_id."""
        if not 0.0 <= self.weight_scalar <= 2.0:
            raise ValueError(
                f"weight_scalar must be in [0.0, 2.0], "
                f"got {self.weight_scalar}"
            )
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_modifier_hash(self),
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "modifier_type": self.modifier_type.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "weight_scalar": self.weight_scalar,
            "event_window_start_utc": self.event_window_start_utc,
            "event_window_end_utc": self.event_window_end_utc,
            "description": self.description,
            "deterministic_id": self.deterministic_id,
        }

    def applies_at(self, timestamp: str) -> bool:
        """Check if this modifier applies at a given timestamp.

        Args:
            timestamp: ISO 8601 UTC timestamp to check.

        Returns:
            True if the timestamp falls within [start_time, end_time].
        """
        from datetime import datetime

        try:
            dt = datetime.fromisoformat(timestamp)
            start = datetime.fromisoformat(self.start_time)
            end = datetime.fromisoformat(self.end_time)
        except (ValueError, TypeError):
            return False
        return start <= dt <= end


def _compute_modifier_hash(modifier: TemporalModifier) -> str:
    """Compute deterministic SHA-256 hash for a TemporalModifier."""
    data = {
        "modifier_type": modifier.modifier_type.value,
        "start_time": modifier.start_time,
        "end_time": modifier.end_time,
        "weight_scalar": modifier.weight_scalar,
        "event_window_start_utc": modifier.event_window_start_utc,
        "event_window_end_utc": modifier.event_window_end_utc,
        "description": modifier.description,
    }
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update(b"temporal_modifier:")
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()[:16]

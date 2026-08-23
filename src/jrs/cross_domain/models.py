"""Cross-Domain Event Reasoning Engine — data models.

Outputs deterministic facts (EventClusters), NOT final predictions or
interpretations.  Ingests DomainAssessment objects (from the convergence
engine) paired with temporal windows, and identifies intersections where
multiple domains show HIGH timing convergence in overlapping windows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from jrs.convergence.models import DomainAssessment

# ── Enums ────────────────────────────────────────────────────────────────────


class CrossDomainEventType(Enum):
    """High-level event types that emerge from cross-domain clustering."""

    CAREER_RELOCATION = "CAREER_RELOCATION"
    FINANCIAL_UPHEAVAL = "FINANCIAL_UPHEAVAL"
    MAJOR_LIFE_TRANSITION = "MAJOR_LIFE_TRANSITION"
    STAGNATION = "STAGNATION"
    HEALTH_CRISIS = "HEALTH_CRISIS"
    RELATIONSHIP_SHIFT = "RELATIONSHIP_SHIFT"
    SPIRITUAL_AWAKENING = "SPIRITUAL_AWAKENING"
    PROPERTY_ACQUISITION = "PROPERTY_ACQUISITION"
    LEGAL_PROCEEDINGS = "LEGAL_PROCEEDINGS"
    EDUCATIONAL_MILESTONE = "EDUCATIONAL_MILESTONE"


# ── Core Models ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TemporalWindow:
    """A bounded time interval for cross-domain overlap detection.

    Uses ISO-8601 date strings for deterministic comparison.
    """

    start_utc: str = ""
    end_utc: str = ""

    def overlaps(self, other: TemporalWindow) -> bool:
        """Check if this window overlaps with another.

        Two windows overlap when neither ends before the other starts.
        Empty windows never overlap.
        """
        if not self.start_utc or not self.end_utc:
            return False
        if not other.start_utc or not other.end_utc:
            return False
        # Overlap exists when start1 <= end2 AND start2 <= end1
        return self.start_utc <= other.end_utc and other.start_utc <= self.end_utc

    def overlap_score(self, other: TemporalWindow) -> float:
        """Compute overlap ratio in [0.0, 1.0].

        Returns the fraction of the shorter window that is covered by the
        overlap.  Returns 0.0 if there is no overlap.
        """
        if not self.overlaps(other):
            return 0.0

        overlap_start = max(self.start_utc, other.start_utc)
        overlap_end = min(self.end_utc, other.end_utc)

        # Both are ISO strings, so lexicographic comparison works for dates
        overlap_len = _days_between(overlap_start, overlap_end)
        self_len = _days_between(self.start_utc, self.end_utc)
        other_len = _days_between(other.start_utc, other.end_utc)

        shorter = min(self_len, other_len)
        if shorter <= 0:
            return 0.0

        return min(overlap_len / shorter, 1.0)

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "start_utc": self.start_utc,
            "end_utc": self.end_utc,
        }


def _days_between(start: str, end: str) -> float:
    """Approximate days between two ISO date strings (YYYY-MM-DD).

    Falls back to character-distance ratio for non-standard formats.
    """
    try:
        from datetime import date

        d1 = date.fromisoformat(start)
        d2 = date.fromisoformat(end)
        return float(abs((d2 - d1).days))
    except (ValueError, TypeError):
        # Approximate: character distance / 10 as rough heuristic
        return float(abs(ord(end[-1]) - ord(start[-1])) + 1)


@dataclass(frozen=True)
class CrossDomainAssessment:
    """A DomainAssessment paired with its temporal window.

    This is the input unit for cross-domain clustering.  It does NOT
    modify or extend DomainAssessment; it wraps it.
    """

    assessment: DomainAssessment
    temporal_window: TemporalWindow = field(default_factory=TemporalWindow)
    domain_label: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "assessment": self.assessment.to_dict(),
            "temporal_window": self.temporal_window.to_dict(),
            "domain_label": self.domain_label,
        }


@dataclass(frozen=True)
class EventCluster:
    """A deterministic cluster of cross-domain assessments sharing
    temporal overlap.

    This is a FACT container — it records what domains converge and
    when, without interpreting the meaning of the convergence.
    """

    temporal_window: TemporalWindow
    involved_domains: tuple[str, ...]
    supporting_evidence_count: int
    independent_channels_count: int
    contradictions_count: int
    temporal_overlap_score: float
    deterministic_id: str = ""
    event_type: CrossDomainEventType = CrossDomainEventType.MAJOR_LIFE_TRANSITION

    def __post_init__(self) -> None:
        """Compute deterministic_id if not provided."""
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_cluster_hash(self)
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "temporal_window": self.temporal_window.to_dict(),
            "involved_domains": list(self.involved_domains),
            "supporting_evidence_count": self.supporting_evidence_count,
            "independent_channels_count": self.independent_channels_count,
            "contradictions_count": self.contradictions_count,
            "temporal_overlap_score": self.temporal_overlap_score,
            "deterministic_id": self.deterministic_id,
            "event_type": self.event_type.value,
        }


# ── Deterministic Hashing ────────────────────────────────────────────────────


def _compute_cluster_hash(cluster: EventCluster) -> str:
    """Compute a deterministic SHA-256 hash for an EventCluster."""
    data = {
        "temporal_window": cluster.temporal_window.to_dict(),
        "involved_domains": list(cluster.involved_domains),
        "supporting_evidence_count": cluster.supporting_evidence_count,
        "independent_channels_count": cluster.independent_channels_count,
        "contradictions_count": cluster.contradictions_count,
        "temporal_overlap_score": cluster.temporal_overlap_score,
        "event_type": cluster.event_type.value,
    }
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update(b"event_cluster:")
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


# ── Cluster Classification Helpers ───────────────────────────────────────────

# Domain label → CrossDomainEventType mapping for automatic classification.
_DOMAIN_EVENT_MAP: dict[str, CrossDomainEventType] = {
    "CAREER": CrossDomainEventType.CAREER_RELOCATION,
    "MIGRATION": CrossDomainEventType.CAREER_RELOCATION,
    "WEALTH": CrossDomainEventType.FINANCIAL_UPHEAVAL,
    "ASSETS": CrossDomainEventType.PROPERTY_ACQUISITION,
    "PROPERTY": CrossDomainEventType.PROPERTY_ACQUISITION,
    "MARRIAGE": CrossDomainEventType.RELATIONSHIP_SHIFT,
    "HEALTH": CrossDomainEventType.HEALTH_CRISIS,
    "SPIRITUALITY": CrossDomainEventType.SPIRITUAL_AWAKENING,
    "LITIGATION": CrossDomainEventType.LEGAL_PROCEEDINGS,
    "EDUCATION": CrossDomainEventType.EDUCATIONAL_MILESTONE,
    "TRANSITIONS": CrossDomainEventType.MAJOR_LIFE_TRANSITION,
    "BUSINESS": CrossDomainEventType.FINANCIAL_UPHEAVAL,
}


def classify_event_type(
    domain_labels: tuple[str, ...],
) -> CrossDomainEventType:
    """Classify an event cluster type from its involved domain labels.

    Uses the majority mapping.  Falls back to MAJOR_LIFE_TRANSITION
    when labels don't map to any known type.
    """
    if not domain_labels:
        return CrossDomainEventType.MAJOR_LIFE_TRANSITION

    type_counts: dict[CrossDomainEventType, int] = {}
    for label in domain_labels:
        upper = label.upper()
        # Try direct match, then prefix match
        event_type = _DOMAIN_EVENT_MAP.get(upper)
        if event_type is None:
            for key, etype in _DOMAIN_EVENT_MAP.items():
                if upper.startswith(key):
                    event_type = etype
                    break
        if event_type is not None:
            type_counts[event_type] = type_counts.get(event_type, 0) + 1

    if not type_counts:
        return CrossDomainEventType.MAJOR_LIFE_TRANSITION

    # Return the type with the most domain matches
    return max(type_counts, key=lambda k: type_counts[k])

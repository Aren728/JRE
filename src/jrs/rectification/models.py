"""JRS-064 Rectification Integration — data models.

This module defines the data structures for integrating JRE-021
rectification capabilities with the JRS evidence/convergence pipeline.

Strict Boundaries:
- This module outputs deterministic facts (RectificationResult objects),
  NOT final predictions or interpretations.
- Candidate generation is strictly separated from candidate evaluation.
- No existing domain logic or JRE engines are modified.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────


class MatchQuality(Enum):
    """Quality of match between a candidate assessment and ground truth."""

    EXACT_MATCH = "EXACT_MATCH"
    STRONG_MATCH = "STRONG_MATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    WEAK_MATCH = "WEAK_MATCH"
    NO_MATCH = "NO_MATCH"


class AdjustmentDirection(Enum):
    """Direction of suggested time adjustment."""

    EARLIER = "EARLIER"
    LATER = "LATER"
    NO_CHANGE = "NO_CHANGE"


# ── Core Models ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class KnownEvent:
    """A known life event used as ground truth for rectification evaluation.

    Maps a life event to the domain outcome it should trigger and
    the expected assessment status from the JRS pipeline.
    """

    event_description: str
    domain_label: str
    expected_outcome: str
    expected_assessment_status: str
    expected_timing_status: str = "CONVERGENT"

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "event_description": self.event_description,
            "domain_label": self.domain_label,
            "expected_outcome": self.expected_outcome,
            "expected_assessment_status": self.expected_assessment_status,
            "expected_timing_status": self.expected_timing_status,
        }


@dataclass(frozen=True)
class EventMatch:
    """Detailed match result for a single known event against a candidate."""

    known_event: KnownEvent
    candidate_outcome: str
    candidate_assessment_status: str
    candidate_timing_status: str
    match_quality: MatchQuality
    mismatch_score: float  # 0.0 = perfect match, 1.0 = total mismatch

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "known_event": self.known_event.to_dict(),
            "candidate_outcome": self.candidate_outcome,
            "candidate_assessment_status": self.candidate_assessment_status,
            "candidate_timing_status": self.candidate_timing_status,
            "match_quality": self.match_quality.value,
            "mismatch_score": self.mismatch_score,
        }


@dataclass(frozen=True)
class RectificationResult:
    """Result of evaluating a candidate birth time against known events.

    This is a FACT container — it records how well a candidate time
    aligns with known ground truth, without interpreting the meaning.
    """

    candidate_time: str  # ISO-UTC string
    mismatch_score: float  # 0.0 = perfect match, 1.0 = total mismatch
    suggested_adjustment_minutes: float
    event_matches: tuple[EventMatch, ...] = ()
    supporting_evidence_ids: tuple[str, ...] = ()
    contradicting_evidence_ids: tuple[str, ...] = ()
    deterministic_id: str = ""

    def __post_init__(self) -> None:
        """Compute deterministic_id if not provided."""
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_result_hash(self)
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "candidate_time": self.candidate_time,
            "mismatch_score": self.mismatch_score,
            "suggested_adjustment_minutes": self.suggested_adjustment_minutes,
            "event_matches": [m.to_dict() for m in self.event_matches],
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "contradicting_evidence_ids": list(self.contradicting_evidence_ids),
            "deterministic_id": self.deterministic_id,
        }


@dataclass(frozen=True)
class AdjustmentProposal:
    """A proposed time adjustment from the suggestion engine.

    This is a GENERATION output — the proposal itself is not validated
    by the same engine that produced it (no circular validation).
    """

    offset_minutes: float
    direction: AdjustmentDirection
    confidence: float  # 0.0 to 1.0
    reason: str
    method: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "offset_minutes": self.offset_minutes,
            "direction": self.direction.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "method": self.method,
        }


# ── Deterministic Hashing ────────────────────────────────────────────────────


def _compute_result_hash(result: RectificationResult) -> str:
    """Compute a deterministic SHA-256 hash for a RectificationResult."""
    data = {
        "candidate_time": result.candidate_time,
        "mismatch_score": result.mismatch_score,
        "suggested_adjustment_minutes": result.suggested_adjustment_minutes,
        "event_match_count": len(result.event_matches),
        "supporting_evidence_count": len(result.supporting_evidence_ids),
        "contradicting_evidence_count": len(result.contradicting_evidence_ids),
    }
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update(b"rectification_result:")
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


# ── Scoring Helpers ──────────────────────────────────────────────────────────


# Assessment status scoring (closer = lower mismatch)
_ASSESSMENT_STATUS_SCORES: dict[str, float] = {
    "STRONGLY_SUPPORTED": 1.0,
    "SUPPORTED": 0.8,
    "WEAKLY_SUPPORTED": 0.5,
    "NEUTRAL": 0.3,
    "CONTRADICTED": 0.1,
    "STRONGLY_CONTRADICTED": 0.0,
}


def compute_assessment_mismatch(
    expected_status: str,
    candidate_status: str,
) -> float:
    """Compute mismatch between expected and candidate assessment statuses.

    Returns a value in [0.0, 1.0] where 0.0 means perfect match.
    """
    exp_score = _ASSESSMENT_STATUS_SCORES.get(expected_status, 0.3)
    cand_score = _ASSESSMENT_STATUS_SCORES.get(candidate_status, 0.3)
    return abs(exp_score - cand_score)


def compute_timing_mismatch(
    expected_timing: str,
    candidate_timing: str,
) -> float:
    """Compute mismatch between expected and candidate timing statuses.

    Returns a value in [0.0, 1.0] where 0.0 means perfect match.
    """
    if expected_timing == candidate_timing:
        return 0.0
    # CONVERGENT vs INACTIVE is a stronger mismatch than CONVERGENT vs DIVERGENT
    timing_map = {"CONVERGENT": 1.0, "DIVERGENT": 0.5, "INACTIVE": 0.0}
    exp_val = timing_map.get(expected_timing, 0.5)
    cand_val = timing_map.get(candidate_timing, 0.5)
    return abs(exp_val - cand_val)


def classify_match_quality(mismatch_score: float) -> MatchQuality:
    """Classify match quality from a mismatch score.

    Args:
        mismatch_score: Value in [0.0, 1.0] where 0.0 = perfect match.

    Returns:
        The classified MatchQuality.
    """
    if mismatch_score <= 0.0:
        return MatchQuality.EXACT_MATCH
    if mismatch_score <= 0.15:
        return MatchQuality.STRONG_MATCH
    if mismatch_score <= 0.40:
        return MatchQuality.PARTIAL_MATCH
    if mismatch_score <= 0.70:
        return MatchQuality.WEAK_MATCH
    return MatchQuality.NO_MATCH

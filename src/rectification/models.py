"""JRE-021 Rectification (Birth Time) models — core data structures.

JRE-021 computes precise time offsets based on known life events
using classical rectification methods, strictly as structural data
points without predictive interpretation.

Core Models:
- ``LifeEvent``: event_date_utc, event_type, description
- ``RectificationResult``: method, calculated_offset_seconds, confidence_score, evidence
- ``RectificationReport``: input_birth_time, suggested_birth_time, offsets
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

#: Pinned package version.
RECTIFICATION_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class EventType(StrEnum):
    """Standard life event types used in rectification."""

    MARRIAGE = "MARRIAGE"
    BIRTH_OF_CHILD = "BIRTH_OF_CHILD"
    DIVORCE = "DIVORCE"
    DEATH = "DEATH"
    ACCIDENT = "ACCIDENT"
    ILLNESS = "ILLNESS"
    RECOVERY = "RECOVERY"
    PROMOTION = "PROMOTION"
    JOB_CHANGE = "JOB_CHANGE"
    BUSINESS_START = "BUSINESS_START"
    BUSINESS_END = "BUSINESS_END"
    EDUCATION_COMPLETE = "EDUCATION_COMPLETE"
    IMMIGRATION = "IMMIGRATION"
    LEGAL_ISSUE = "LEGAL_ISSUE"
    FINANCIAL_GAIN = "FINANCIAL_GAIN"
    FINANCIAL_LOSS = "FINANCIAL_LOSS"
    SPIRITUAL_EVENT = "SPIRITUAL_EVENT"
    OTHER = "OTHER"


class RectificationMethod(StrEnum):
    """Classical rectification methods."""

    TRANSIT_TO_ASCENDANT = "TRANSIT_TO_ASCENDANT"
    DASHA_TO_EVENT = "DASHA_TO_EVENT"
    PROGRESSION_TO_ASCENDANT = "PROGRESSION_TO_ASCENDANT"


# --------------------------------------------------------------------------- #
# Default method weights and tolerances
# --------------------------------------------------------------------------- #

DEFAULT_METHOD_WEIGHTS: dict[str, float] = {
    "TRANSIT_TO_ASCENDANT": 0.40,
    "DASHA_TO_EVENT": 0.35,
    "PROGRESSION_TO_ASCENDANT": 0.25,
}

DEFAULT_METHOD_TOLERANCES: dict[str, float] = {
    "TRANSIT_TO_ASCENDANT": 3600.0,       # 1 hour
    "DASHA_TO_EVENT": 86400.0,            # 24 hours
    "PROGRESSION_TO_ASCENDANT": 7200.0,   # 2 hours
}

DEFAULT_EVIDENCE_WEIGHTS: dict[str, float] = {
    "event_type_match": 0.30,
    "offset_within_tolerance": 0.40,
    "multiple_events_corroborate": 0.30,
}


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class LifeEvent:
    """A known life event used as a rectification anchor."""

    event_date_utc: str  # ISO-UTC string
    event_type: EventType
    description: str

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class RectificationResult:
    """Result of a single rectification method applied to one event."""

    method: RectificationMethod
    calculated_offset_seconds: float
    confidence_score: float  # 0.0 to 1.0
    evidence: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class RectificationReport:
    """Complete rectification report aggregating multiple method results."""

    input_birth_time: str  # ISO-UTC string
    suggested_birth_time: str  # ISO-UTC string
    offsets: tuple[RectificationResult, ...]
    version: str = RECTIFICATION_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class RectificationConfig:
    """Immutable JRE-021 configuration."""

    version: str = RECTIFICATION_VERSION
    max_offset_seconds: float = 86400.0
    method_weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_METHOD_WEIGHTS)
    )
    method_tolerances: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_METHOD_TOLERANCES)
    )
    evidence_weights: dict[str, float] = field(
        default_factory=lambda: dict(DEFAULT_EVIDENCE_WEIGHTS)
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #

_SECS_PER_HOUR = 3600.0
_SECS_PER_DAY = 86400.0


def compute_offset_seconds(event_utc: str, transit_utc: str) -> float:
    """Compute the signed time offset between an event and a transit.

    Positive offset means the transit occurred *after* the event
    (i.e., the natal birth time should be shifted later).

    Parameters
    ----------
    event_utc : str
        ISO-UTC timestamp of the life event.
    transit_utc : str
        ISO-UTC timestamp of the transit/progression/dasha.

    Returns
    -------
    float
        Offset in seconds (transit - event).
    """
    from datetime import datetime

    event_dt = datetime.fromisoformat(event_utc.replace("Z", "+00:00"))
    transit_dt = datetime.fromisoformat(transit_utc.replace("Z", "+00:00"))
    delta = transit_dt - event_dt
    return delta.total_seconds()


def compute_confidence_score(
    offset_seconds: float,
    tolerance_seconds: float,
    method_weight: float,
    event_type_relevant: bool,
    corroborated: bool,
    evidence_weights: dict[str, float],
) -> float:
    """Compute a deterministic confidence score (0.0 to 1.0) for a rectification result.

    Parameters
    ----------
    offset_seconds : float
        Absolute offset in seconds.
    tolerance_seconds : float
        Method-specific tolerance threshold.
    method_weight : float
        Weight of this method (from config).
    event_type_relevant : bool
        Whether the event type is relevant to this method.
    corroborated : bool
        Whether multiple events corroborate this offset.
    evidence_weights : dict
        Weights for evidence factors.

    Returns
    -------
    float
        Confidence score in [0.0, 1.0].
    """
    score = 0.0

    # Factor 1: event type match
    if event_type_relevant:
        score += evidence_weights.get("event_type_match", 0.30)

    # Factor 2: offset within tolerance
    if abs(offset_seconds) <= tolerance_seconds:
        score += evidence_weights.get("offset_within_tolerance", 0.40)
    else:
        # Partial credit: decay linearly up to 2x tolerance
        ratio = abs(offset_seconds) / tolerance_seconds
        if ratio <= 2.0:
            partial = evidence_weights.get("offset_within_tolerance", 0.40) * (2.0 - ratio) / 2.0
            score += partial

    # Factor 3: corroboration
    if corroborated:
        score += evidence_weights.get("multiple_events_corroborate", 0.30)

    # Apply method weight as a multiplier
    score *= method_weight

    return max(0.0, min(1.0, score))


def aggregate_offsets(
    results: tuple[RectificationResult, ...],
    max_offset: float,
) -> float:
    """Aggregate multiple rectification results into a single weighted offset.

    Uses weighted average of offsets, weighted by confidence scores.
    If no results, returns 0.0.

    Parameters
    ----------
    results : tuple of RectificationResult
        Individual method results.
    max_offset : float
        Maximum allowed offset in seconds.

    Returns
    -------
    float
        Weighted average offset in seconds, clamped to [-max_offset, max_offset].
    """
    if not results:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0
    for r in results:
        weighted_sum += r.calculated_offset_seconds * r.confidence_score
        total_weight += r.confidence_score

    if total_weight == 0.0:
        return 0.0

    avg = weighted_sum / total_weight
    return max(-max_offset, min(max_offset, avg))


def apply_offset_to_birth_time(
    birth_time_utc: str,
    offset_seconds: float,
) -> str:
    """Apply a time offset to a birth time and return the adjusted ISO-UTC string.

    Parameters
    ----------
    birth_time_utc : str
        Original birth time in ISO-UTC format.
    offset_seconds : float
        Offset in seconds to apply.

    Returns
    -------
    str
        Adjusted birth time in ISO-UTC format.
    """
    if abs(offset_seconds) < 1e-9:
        return birth_time_utc
    from datetime import datetime, timedelta

    dt = datetime.fromisoformat(birth_time_utc.replace("Z", "+00:00"))
    adjusted = dt + timedelta(seconds=offset_seconds)
    return adjusted.isoformat()


def event_type_relevant_to_method(
    event_type: EventType,
    method: RectificationMethod,
) -> bool:
    """Check if an event type is classically relevant to a rectification method.

    Parameters
    ----------
    event_type : EventType
        The life event type.
    method : RectificationMethod
        The rectification method.

    Returns
    -------
    bool
        True if the event type is relevant to the method.
    """
    # Transit to Ascendant: major life events with clear timing
    transit_relevant = frozenset({
        EventType.MARRIAGE,
        EventType.BIRTH_OF_CHILD,
        EventType.DIVORCE,
        EventType.DEATH,
        EventType.ACCIDENT,
        EventType.ILLNESS,
        EventType.RECOVERY,
        EventType.IMMIGRATION,
    })

    # Dasha to Event: career, relationship, and health events
    dasha_relevant = frozenset({
        EventType.MARRIAGE,
        EventType.BIRTH_OF_CHILD,
        EventType.DIVORCE,
        EventType.PROMOTION,
        EventType.JOB_CHANGE,
        EventType.BUSINESS_START,
        EventType.BUSINESS_END,
        EventType.ILLNESS,
        EventType.ACCIDENT,
        EventType.FINANCIAL_GAIN,
        EventType.FINANCIAL_LOSS,
    })

    # Progression to Ascendant: slower-developing events
    progression_relevant = frozenset({
        EventType.MARRIAGE,
        EventType.BIRTH_OF_CHILD,
        EventType.EDUCATION_COMPLETE,
        EventType.PROMOTION,
        EventType.IMMIGRATION,
        EventType.SPIRITUAL_EVENT,
    })

    if method == RectificationMethod.TRANSIT_TO_ASCENDANT:
        return event_type in transit_relevant
    if method == RectificationMethod.DASHA_TO_EVENT:
        return event_type in dasha_relevant
    if method == RectificationMethod.PROGRESSION_TO_ASCENDANT:
        return event_type in progression_relevant
    return False


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> .value; tuples -> lists; -0.0 -> 0.0)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {_model_to_dict(key): _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)

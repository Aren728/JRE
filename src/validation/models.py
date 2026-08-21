"""Validation system data models and trigger extraction logic."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────

class EventType(Enum):
    """Known life event types for validation."""

    MARRIAGE = "MARRIAGE"
    CAREER_START = "CAREER_START"
    PROMOTION = "PROMOTION"
    CHILD_BIRTH = "CHILD_BIRTH"
    ACCIDENT = "ACCIDENT"
    BUSINESS_START = "BUSINESS_START"
    EDUCATION_COMPLETE = "EDUCATION_COMPLETE"
    PROPERTY_PURCHASE = "PROPERTY_PURCHASE"
    LITIGATION = "LITIGATION"
    TRAVEL = "TRAVEL"
    FINANCIAL_GAIN = "FINANCIAL_GAIN"
    FINANCIAL_LOSS = "FINANCIAL_LOSS"
    HEALTH_CRISIS = "HEALTH_CRISIS"
    RELOCATION = "RELOCATION"
    PARTNERSHIP = "PARTNERSHIP"
    OTHER = "OTHER"


class TriggerSource(Enum):
    """Source engine from which a structural trigger was extracted."""

    YOGA = "YOGA"
    DASHA = "DASHA"
    BALA = "BALA"
    ASHTAKAVARGA = "ASHTAKAVARGA"
    AVASTHA = "AVASTHA"
    KARAKA = "KARAKA"
    DRIK = "DRIK"
    SYNTHESIS = "SYNTHESIS"
    BHAVA = "BHAVA"
    JAIMINI = "JAIMINI"
    TAJIKA = "TAJIKA"


# ── Core Models ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KnownEvent:
    """A known life event with expected structural triggers for validation."""

    event_date_utc: str  # ISO format
    event_type: EventType
    expected_triggers: tuple[str, ...] = ()
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "event_date_utc": self.event_date_utc,
            "event_type": self.event_type.value,
            "expected_triggers": list(self.expected_triggers),
            "description": self.description,
        }


@dataclass(frozen=True)
class ReferenceChart:
    """A chart with known life events used for validation against ground truth."""

    chart_id: str
    birth_data: dict[str, str] = field(default_factory=dict)
    known_events: tuple[KnownEvent, ...] = ()
    ground_truth: dict[str, str] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "chart_id": self.chart_id,
            "birth_data": dict(sorted(self.birth_data.items())),
            "known_events": [e.to_dict() for e in self.known_events],
            "ground_truth": dict(sorted(self.ground_truth.items())),
            "description": self.description,
        }


@dataclass(frozen=True)
class ExtractedTrigger:
    """A structural trigger extracted from an engine output."""

    trigger_id: str
    source: TriggerSource
    confidence: float = 1.0
    metadata: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "trigger_id": self.trigger_id,
            "source": self.source.value,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class ValidationResult:
    """Validation result for a single reference chart."""

    chart_id: str
    expected_triggers: tuple[str, ...] = ()
    actual_triggers: tuple[ExtractedTrigger, ...] = ()
    match_score: float = 0.0
    missing_triggers: tuple[str, ...] = ()
    false_positives: tuple[str, ...] = ()
    total_events: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "chart_id": self.chart_id,
            "expected_triggers": list(self.expected_triggers),
            "actual_triggers": [t.to_dict() for t in self.actual_triggers],
            "match_score": round(self.match_score, 4),
            "missing_triggers": list(self.missing_triggers),
            "false_positives": list(self.false_positives),
            "total_events": self.total_events,
        }


@dataclass(frozen=True)
class ValidationReport:
    """Complete validation report containing results for all charts."""

    results: tuple[ValidationResult, ...] = ()
    overall_score: float = 0.0
    total_charts: int = 0
    timestamp: str = field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
    )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "results": [r.to_dict() for r in self.results],
            "overall_score": round(self.overall_score, 4),
            "total_charts": self.total_charts,
            "timestamp": self.timestamp,
        }


# ── Validation Config (embedded for convenience) ─────────────────────────────

@dataclass(frozen=True)
class ValidationConfig:
    """Configuration for the validation system."""

    version: str = "1.0"
    match_threshold: float = 0.5
    trigger_weights: dict[str, float] = field(default_factory=dict)
    source_reliability: dict[str, float] = field(default_factory=dict)


# ── Trigger Extraction Logic ─────────────────────────────────────────────────

def extract_triggers_from_engines(
    engine_names: tuple[str, ...],
    research_evidence: tuple[str, ...] = (),
    source_reliability: dict[str, float] | None = None,
) -> tuple[ExtractedTrigger, ...]:
    """Extract structural triggers from an EvidencePacket's engine list.

    This function generates deterministic trigger IDs based on which engines
    were invoked and what research topics were requested. In a production
    system, this would parse the actual engine output objects; here we use
    a deterministic mapping from engine names to trigger categories.

    Args:
        engine_names: Names of engines that were invoked.
        research_evidence: Research topics that were requested.
        source_reliability: Optional mapping of source names to reliability scores.

    Returns:
        A tuple of extracted triggers, one per engine that was invoked.
    """
    triggers: list[ExtractedTrigger] = []
    reliability = source_reliability or {}

    for engine_name in engine_names:
        # Map engine names to trigger sources
        source = _engine_to_source(engine_name)
        if source is None:
            continue

        confidence = reliability.get(engine_name, 1.0)
        trigger_id = f"{engine_name}_present"

        triggers.append(ExtractedTrigger(
            trigger_id=trigger_id,
            source=source,
            confidence=confidence,
        ))

    # Add research evidence as triggers
    for topic in research_evidence:
        triggers.append(ExtractedTrigger(
            trigger_id=f"research_{topic}",
            source=TriggerSource.SYNTHESIS,
            confidence=0.8,
            metadata=f"Research topic: {topic}",
        ))

    return tuple(triggers)


def _engine_to_source(engine_name: str) -> TriggerSource | None:
    """Map an engine name to its corresponding TriggerSource."""
    mapping: dict[str, TriggerSource] = {
        "yoga": TriggerSource.YOGA,
        "dasha": TriggerSource.DASHA,
        "bala": TriggerSource.BALA,
        "ashtakavarga": TriggerSource.ASHTAKAVARGA,
        "avastha": TriggerSource.AVASTHA,
        "karaka": TriggerSource.KARAKA,
        "drik": TriggerSource.DRIK,
        "synthesis": TriggerSource.SYNTHESIS,
        "bhava": TriggerSource.BHAVA,
        "jaimini": TriggerSource.JAIMINI,
        "tajika": TriggerSource.TAJIKA,
    }
    return mapping.get(engine_name)


def compute_match_score(
    expected: tuple[str, ...],
    actual: tuple[ExtractedTrigger, ...],
    trigger_weights: dict[str, float] | None = None,
) -> float:
    """Compute a deterministic match score between expected and actual triggers.

    Uses weighted precision-recall F1 score:
    - precision = |matched| / |actual|
    - recall = |matched| / |expected|
    - f1 = 2 * precision * recall / (precision + recall)

    If both expected and actual are empty, returns 1.0 (perfect match).
    If one is empty and the other is not, returns 0.0.

    Args:
        expected: Expected trigger IDs.
        actual: Actual extracted triggers.
        trigger_weights: Optional weights per trigger ID (default 1.0 each).

    Returns:
        A float between 0.0 and 1.0 representing the match quality.
    """
    if not expected and not actual:
        return 1.0
    if not expected or not actual:
        return 0.0

    weights = trigger_weights or {}
    actual_ids = {t.trigger_id for t in actual}

    # Weighted intersection
    matched_weight = 0.0
    for exp in expected:
        w = weights.get(exp, 1.0)
        if exp in actual_ids:
            matched_weight += w

    # Weighted totals
    expected_weight = sum(weights.get(exp, 1.0) for exp in expected)
    actual_weight = sum(
        weights.get(t.trigger_id, 1.0) for t in actual
    )

    if expected_weight == 0 or actual_weight == 0:
        return 0.0

    precision = matched_weight / actual_weight
    recall = matched_weight / expected_weight

    if precision + recall == 0:
        return 0.0

    return 2 * precision * recall / (precision + recall)


def find_missing_and_false_positives(
    expected: tuple[str, ...],
    actual: tuple[ExtractedTrigger, ...],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Identify missing triggers and false positives.

    Args:
        expected: Expected trigger IDs.
        actual: Actual extracted triggers.

    Returns:
        A tuple of (missing_triggers, false_positives).
    """
    actual_ids = {t.trigger_id for t in actual}
    missing = tuple(t for t in expected if t not in actual_ids)
    false_pos = tuple(
        t.trigger_id for t in actual if t.trigger_id not in set(expected)
    )
    return missing, false_pos

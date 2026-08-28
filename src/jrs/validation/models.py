"""JRS Phase A: Empirical Validation Harness — Data Models.

Ingests historical birth charts with verified life events, executes the
5-Layer Yoga Pipeline (frozen weights), and compares predicted activations
against real outcomes.

Source: RI-010 Engine Architecture; BPHS Ch 7, 33, 35, 43, 45.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── Enums ────────────────────────────────────────────────────────────────────


class EventDomain(Enum):
    """Domain categories for life events and yoga predictions."""

    CAREER = "CAREER"
    WEALTH = "WEALTH"
    MARRIAGE = "MARRIAGE"
    HEALTH = "HEALTH"
    EDUCATION = "EDUCATION"
    PROPERTY = "PROPERTY"
    PROGENY = "PROGENY"
    LITIGATION = "LITIGATION"
    MIGRATION = "MIGRATION"
    SPIRITUALITY = "SPIRITUALITY"
    GENERAL = "GENERAL"


class PredictionVerdict(Enum):
    """Binary classification of a prediction against ground truth."""

    TRUE_POSITIVE = "TRUE_POSITIVE"
    FALSE_POSITIVE = "FALSE_POSITIVE"
    TRUE_NEGATIVE = "TRUE_NEGATIVE"
    FALSE_NEGATIVE = "FALSE_NEGATIVE"


class TimingMatchStatus(Enum):
    """Status of temporal timing window comparison."""

    OVERLAP = "OVERLAP"
    PARTIAL_OVERLAP = "PARTIAL_OVERLAP"
    NO_OVERLAP = "NO_OVERLAP"
    PREDICTED_ONLY = "PREDICTED_ONLY"
    ACTUAL_ONLY = "ACTUAL_ONLY"


# ── Core Input Models ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BirthData:
    """Birth data for a historical chart."""

    date: str  # YYYY-MM-DD
    time: str  # HH:MM:SS
    timezone: str = "Asia/Kolkata"
    latitude: float = 0.0
    longitude: float = 0.0


@dataclass(frozen=True)
class KnownEvent:
    """A verified life event with its temporal window.

    Attributes:
        event_id: Unique identifier for the event.
        event_date_utc: ISO format date when the event occurred.
        event_window_start_utc: Start of the event's temporal influence window.
        event_window_end_utc: End of the event's temporal influence window.
        domain: Life domain category.
        description: Human-readable event description.
        yoga_types: Yoga names expected to activate for this event.
        expected_planets: Planets expected to be active during the event.
    """

    event_id: str
    event_date_utc: str
    event_window_start_utc: str = ""
    event_window_end_utc: str = ""
    domain: EventDomain = EventDomain.GENERAL
    description: str = ""
    yoga_types: tuple[str, ...] = ()
    expected_planets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "event_id": self.event_id,
            "event_date_utc": self.event_date_utc,
            "event_window_start_utc": self.event_window_start_utc,
            "event_window_end_utc": self.event_window_end_utc,
            "domain": self.domain.value,
            "description": self.description,
            "yoga_types": list(self.yoga_types),
            "expected_planets": list(self.expected_planets),
        }


@dataclass(frozen=True)
class BirthChart:
    """A historical birth chart with natal facts and verified events.

    This is the primary input to the validation harness: a synthetic or
    real chart with pre-computed JRE facts and known life outcomes.
    """

    chart_id: str
    birth_data: BirthData
    jre_facts: dict[str, Any]
    known_events: tuple[KnownEvent, ...] = ()
    domain: EventDomain = EventDomain.GENERAL
    description: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "chart_id": self.chart_id,
            "birth_data": {
                "date": self.birth_data.date,
                "time": self.birth_data.time,
                "timezone": self.birth_data.timezone,
                "latitude": self.birth_data.latitude,
                "longitude": self.birth_data.longitude,
            },
            "known_events": [e.to_dict() for e in self.known_events],
            "domain": self.domain.value,
            "description": self.description,
        }


# ── Prediction Models ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TimingWindow:
    """A predicted temporal window for a yoga activation.

    Attributes:
        yoga_name: Name of the predicted yoga.
        window_start_utc: Predicted activation start (ISO format).
        window_end_utc: Predicted activation end (ISO format).
        dasha_lord: Dasha lord during the window.
        transit_planet: Transit planet triggering the activation.
        confidence: Confidence score [0.0, 1.0].
    """

    yoga_name: str
    window_start_utc: str
    window_end_utc: str
    dasha_lord: str = ""
    transit_planet: str = ""
    confidence: float = 1.0


@dataclass(frozen=True)
class PredictedYoga:
    """A yoga activation predicted by the 5-Layer Pipeline.

    Attributes:
        yoga_name: Name of the yoga.
        predicted_status: Predicted status (FORMED, WEAKENED, CANCELLED).
        domain: Life domain the yoga maps to.
        overall_multiplier: Net strength multiplier from pipeline.
        timing_windows: Temporal windows for predicted activation.
        cancellation_reason: If cancelled, the reason.
        involved_planets: Planets forming the yoga.
        confidence: Overall prediction confidence [0.0, 1.0].
    """

    yoga_name: str
    predicted_status: str  # FORMED, WEAKENED, CANCELLED
    domain: EventDomain = EventDomain.GENERAL
    overall_multiplier: float = 1.0
    timing_windows: tuple[TimingWindow, ...] = ()
    cancellation_reason: str | None = None
    involved_planets: tuple[str, ...] = ()
    confidence: float = 1.0


# ── Validation Result Models ─────────────────────────────────────────────────


@dataclass(frozen=True)
class EventPredictionMatch:
    """Match result between a single predicted yoga and a known event.

    Attributes:
        event_id: The known event being matched against.
        yoga_name: The predicted yoga being evaluated.
        verdict: Classification verdict (TP, FP, TN, FN).
        timing_status: Temporal overlap status.
        timing_overlap_ratio: Fraction of event window covered by prediction.
        confidence: Prediction confidence.
    """

    event_id: str
    yoga_name: str
    verdict: PredictionVerdict
    timing_status: TimingMatchStatus = TimingMatchStatus.NO_OVERLAP
    timing_overlap_ratio: float = 0.0
    confidence: float = 1.0


@dataclass(frozen=True)
class ChartValidationResult:
    """Validation result for a single chart processed through the pipeline.

    Attributes:
        chart_id: The chart being validated.
        predicted_yogas: All yoga predictions from the pipeline.
        matches: Per-event, per-yoga match results.
        total_known_events: Number of known events.
        total_predicted_yogas: Number of predicted yogas.
        domain: Primary domain of the chart.
    """

    chart_id: str
    predicted_yogas: tuple[PredictedYoga, ...] = ()
    matches: tuple[EventPredictionMatch, ...] = ()
    total_known_events: int = 0
    total_predicted_yogas: int = 0
    domain: EventDomain = EventDomain.GENERAL

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "chart_id": self.chart_id,
            "predicted_yogas": [
                {
                    "yoga_name": y.yoga_name,
                    "predicted_status": y.predicted_status,
                    "domain": y.domain.value,
                    "overall_multiplier": y.overall_multiplier,
                    "involved_planets": list(y.involved_planets),
                    "confidence": y.confidence,
                }
                for y in self.predicted_yogas
            ],
            "matches": [
                {
                    "event_id": m.event_id,
                    "yoga_name": m.yoga_name,
                    "verdict": m.verdict.value,
                    "timing_status": m.timing_status.value,
                    "timing_overlap_ratio": m.timing_overlap_ratio,
                    "confidence": m.confidence,
                }
                for m in self.matches
            ],
            "total_known_events": self.total_known_events,
            "total_predicted_yogas": self.total_predicted_yogas,
            "domain": self.domain.value,
        }


# ── Statistical Report Models ────────────────────────────────────────────────


@dataclass(frozen=True)
class ClassificationMetrics:
    """Classification metrics for a single category.

    Attributes:
        true_positives: Correctly predicted positive cases.
        false_positives: Incorrectly predicted positive cases.
        true_negatives: Correctly predicted negative cases.
        false_negatives: Missed positive cases.
        precision: TP / (TP + FP).
        recall: TP / (TP + FN).
        f1_score: Harmonic mean of precision and recall.
        accuracy: (TP + TN) / total.
    """

    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    accuracy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "accuracy": round(self.accuracy, 4),
        }


@dataclass(frozen=True)
class DomainCalibration:
    """Calibration metrics for a specific domain.

    Attributes:
        domain: The domain being evaluated.
        chart_count: Number of charts in this domain.
        metrics: Classification metrics.
        timing_overlap_ratio: Average timing overlap ratio.
        mean_confidence: Average prediction confidence.
    """

    domain: str
    chart_count: int = 0
    metrics: ClassificationMetrics = field(default_factory=ClassificationMetrics)
    timing_overlap_ratio: float = 0.0
    mean_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "domain": self.domain,
            "chart_count": self.chart_count,
            "metrics": self.metrics.to_dict(),
            "timing_overlap_ratio": round(self.timing_overlap_ratio, 4),
            "mean_confidence": round(self.mean_confidence, 4),
        }


@dataclass(frozen=True)
class TimingAnalysis:
    """Timing window overlap analysis.

    Attributes:
        total_predicted_windows: Total timing windows predicted.
        overlap_count: Windows that overlap with actual events.
        partial_overlap_count: Windows with partial overlap.
        no_overlap_count: Windows with no overlap.
        mean_overlap_ratio: Average overlap ratio across all matches.
        timing_accuracy: overlap_count / total_predicted_windows.
    """

    total_predicted_windows: int = 0
    overlap_count: int = 0
    partial_overlap_count: int = 0
    no_overlap_count: int = 0
    mean_overlap_ratio: float = 0.0
    timing_accuracy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "total_predicted_windows": self.total_predicted_windows,
            "overlap_count": self.overlap_count,
            "partial_overlap_count": self.partial_overlap_count,
            "no_overlap_count": self.no_overlap_count,
            "mean_overlap_ratio": round(self.mean_overlap_ratio, 4),
            "timing_accuracy": round(self.timing_accuracy, 4),
        }


@dataclass(frozen=True)
class StatisticalReport:
    """Full statistical evaluation report across all charts.

    Attributes:
        total_charts: Number of charts evaluated.
        total_known_events: Total known events across all charts.
        total_predicted_yogas: Total yoga predictions across all charts.
        overall_metrics: Aggregate classification metrics.
        domain_calibrations: Per-domain calibration breakdown.
        timing_analysis: Timing window overlap analysis.
        mean_confidence: Average prediction confidence.
    """

    total_charts: int = 0
    total_known_events: int = 0
    total_predicted_yogas: int = 0
    overall_metrics: ClassificationMetrics = field(
        default_factory=ClassificationMetrics,
    )
    domain_calibrations: tuple[DomainCalibration, ...] = ()
    timing_analysis: TimingAnalysis = field(default_factory=TimingAnalysis)
    mean_confidence: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "total_charts": self.total_charts,
            "total_known_events": self.total_known_events,
            "total_predicted_yogas": self.total_predicted_yogas,
            "overall_metrics": self.overall_metrics.to_dict(),
            "domain_calibrations": [dc.to_dict() for dc in self.domain_calibrations],
            "timing_analysis": self.timing_analysis.to_dict(),
            "mean_confidence": round(self.mean_confidence, 4),
        }

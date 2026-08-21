"""Convergence engine data models — assessment status, evidence dimensions, domain assessment."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────

class AssessmentStatus(Enum):
    """Categorical assessment of evidence for an outcome."""

    STRONGLY_SUPPORTED = "STRONGLY_SUPPORTED"
    SUPPORTED = "SUPPORTED"
    WEAKLY_SUPPORTED = "WEAKLY_SUPPORTED"
    NEUTRAL = "NEUTRAL"
    CONTRADICTED = "CONTRADICTED"
    STRONGLY_CONTRADICTED = "STRONGLY_CONTRADICTED"


class TimingStatus(Enum):
    """Status of timing convergence."""

    CONVERGENT = "CONVERGENT"
    DIVERGENT = "DIVERGENT"
    INACTIVE = "INACTIVE"


class OverallEvidenceStrength(Enum):
    """Overall strength of evidence across all dimensions."""

    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


class SourceConfidence(Enum):
    """Confidence level based on source reliability."""

    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


# Confidence numeric mapping
SOURCE_CONFIDENCE_VALUES: dict[SourceConfidence, float] = {
    SourceConfidence.HIGH: 1.0,
    SourceConfidence.MODERATE: 0.6,
    SourceConfidence.LOW: 0.3,
}


# ── Core Models ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class EvidenceDimensions:
    """Multi-dimensional breakdown of evidence for an outcome."""

    supporting_count: int = 0
    independent_channels: int = 0
    contradicting_count: int = 0
    mitigations: int = 0
    timing_convergence_count: int = 0
    source_confidence: SourceConfidence = SourceConfidence.MODERATE

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "supporting_count": self.supporting_count,
            "independent_channels": self.independent_channels,
            "contradicting_count": self.contradicting_count,
            "mitigations": self.mitigations,
            "timing_convergence_count": self.timing_convergence_count,
            "source_confidence": self.source_confidence.value,
        }


@dataclass(frozen=True)
class DomainAssessment:
    """A structured, multi-dimensional assessment of evidence for a domain outcome."""

    outcome_taxonomy: str
    dimensions: EvidenceDimensions = field(default_factory=EvidenceDimensions)
    assessment_status: AssessmentStatus = AssessmentStatus.NEUTRAL
    timing_status: TimingStatus = TimingStatus.INACTIVE
    overall_evidence_strength: OverallEvidenceStrength = OverallEvidenceStrength.WEAK

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "outcome_taxonomy": self.outcome_taxonomy,
            "dimensions": self.dimensions.to_dict(),
            "assessment_status": self.assessment_status.value,
            "timing_status": self.timing_status.value,
            "overall_evidence_strength": self.overall_evidence_strength.value,
        }


# ── Convergence Config (embedded) ────────────────────────────────────────────

@dataclass(frozen=True)
class ConvergenceConfig:
    """Configuration for the convergence engine."""

    version: str = "1.0"
    source_weights: dict[str, float] = field(default_factory=dict)
    strength_weights: dict[str, float] = field(default_factory=dict)
    independence_penalty: float = 0.5
    # Thresholds for assessment status classification
    strongly_supported_min_independent: int = 3
    strongly_supported_min_supporting: int = 4
    supported_min_independent: int = 2
    supported_min_supporting: int = 2
    weakly_supported_min_supporting: int = 1
    strongly_contradicted_min_contradicting: int = 3
    contradicted_min_contradicting: int = 2
    # Timing thresholds
    convergent_min_windows: int = 1
    # Source confidence thresholds
    high_confidence_min_weight: float = 0.8
    low_confidence_max_weight: float = 0.4


# ── Dimension Calculation Helpers ────────────────────────────────────────────

def count_independent_channels(
    support_records: tuple[Any, ...],
    source_weights: dict[str, float] | None = None,
) -> int:
    """Count independent evidence channels, preventing double-counting.

    Two records from the same source_id AND same independence_group count
    as a single independent channel. Records from different sources or
    different independence groups count separately.

    Args:
        support_records: Tuple of EvidenceRecord-like objects with
            source_id and independence_group attributes.
        source_weights: Optional source weight mapping.

    Returns:
        The count of independent channels.
    """
    if not support_records:
        return 0

    # Group by (source_id, independence_group)
    seen: set[tuple[str, str]] = set()
    for record in support_records:
        source_id = getattr(record, "source_id", "")
        independence_group = getattr(record, "independence_group", "")
        key = (source_id, independence_group)
        if key not in seen:
            seen.add(key)

    return len(seen)


def compute_weighted_support_score(
    records: tuple[Any, ...],
    strength_weights: dict[str, float] | None = None,
    source_weights: dict[str, float] | None = None,
) -> float:
    """Compute a weighted support score from evidence records.

    Each record's contribution is: strength_weight * source_weight.

    Args:
        records: Tuple of EvidenceRecord-like objects.
        strength_weights: Mapping of strength level names to weights.
        source_weights: Mapping of source IDs to weights.

    Returns:
        The total weighted support score.
    """
    if not records:
        return 0.0

    sw = strength_weights or {}
    src_w = source_weights or {}
    total = 0.0

    for record in records:
        strength_val = getattr(record, "strength", None)
        strength_name = strength_val.value if strength_val is not None else "MODERATE"
        s_weight = sw.get(strength_name, 0.6)

        source_id = getattr(record, "source_id", "")
        src_weight = src_w.get(source_id, 0.8)

        total += s_weight * src_weight

    return total


def classify_assessment_status(
    dimensions: EvidenceDimensions,
    config: ConvergenceConfig | None = None,
) -> AssessmentStatus:
    """Classify assessment status based on evidence dimensions.

    Uses strict threshold rules from the config to map dimensions
    to a categorical AssessmentStatus.

    Args:
        dimensions: The computed evidence dimensions.
        config: Optional convergence config with thresholds.

    Returns:
        The classified AssessmentStatus.
    """
    cfg = config or ConvergenceConfig()

    # Strongly contradicted: many contradictions, few supports
    if (dimensions.contradicting_count >= cfg.strongly_contradicted_min_contradicting
            and dimensions.supporting_count <= dimensions.contradicting_count):
        return AssessmentStatus.STRONGLY_CONTRADICTED

    # Contradicted: moderate contradictions
    if (dimensions.contradicting_count >= cfg.contradicted_min_contradicting
            and dimensions.supporting_count <= dimensions.contradicting_count):
        return AssessmentStatus.CONTRADICTED

    # Strongly supported: many independent channels and supporting records
    if (dimensions.independent_channels >= cfg.strongly_supported_min_independent
            and dimensions.supporting_count >= cfg.strongly_supported_min_supporting):
        return AssessmentStatus.STRONGLY_SUPPORTED

    # Supported: moderate independent channels
    if (dimensions.independent_channels >= cfg.supported_min_independent
            and dimensions.supporting_count >= cfg.supported_min_supporting):
        return AssessmentStatus.SUPPORTED

    # Weakly supported: at least one supporting record
    if dimensions.supporting_count >= cfg.weakly_supported_min_supporting:
        return AssessmentStatus.WEAKLY_SUPPORTED

    return AssessmentStatus.NEUTRAL


def classify_timing_status(
    timing_convergence_count: int,
    config: ConvergenceConfig | None = None,
) -> TimingStatus:
    """Classify timing status based on convergence count.

    Args:
        timing_convergence_count: Number of converging event windows.
        config: Optional convergence config with thresholds.

    Returns:
        The classified TimingStatus.
    """
    cfg = config or ConvergenceConfig()

    if timing_convergence_count >= cfg.convergent_min_windows:
        return TimingStatus.CONVERGENT

    return TimingStatus.INACTIVE


def classify_overall_strength(
    dimensions: EvidenceDimensions,
    config: ConvergenceConfig | None = None,
) -> OverallEvidenceStrength:
    """Classify overall evidence strength.

    Combines supporting count, independent channels, and source confidence.

    Args:
        dimensions: The computed evidence dimensions.
        config: Optional convergence config.

    Returns:
        The classified OverallEvidenceStrength.
    """
    cfg = config or ConvergenceConfig()

    # Compute composite score
    support_score = dimensions.supporting_count * 1.0
    channel_score = dimensions.independent_channels * 1.5
    confidence_multiplier = SOURCE_CONFIDENCE_VALUES.get(
        dimensions.source_confidence, 0.6,
    )

    composite = (support_score + channel_score) * confidence_multiplier

    # Apply contradiction penalty
    contra_penalty = dimensions.contradicting_count * cfg.independence_penalty
    composite -= contra_penalty

    if composite >= 5.0:
        return OverallEvidenceStrength.STRONG
    if composite >= 2.5:
        return OverallEvidenceStrength.MODERATE

    return OverallEvidenceStrength.WEAK

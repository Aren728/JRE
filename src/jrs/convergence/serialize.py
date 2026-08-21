"""Convergence engine deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from .models import (
    AssessmentStatus,
    ConvergenceConfig,
    DomainAssessment,
    EvidenceDimensions,
    OverallEvidenceStrength,
    SourceConfidence,
    TimingStatus,
)


def evidence_dimensions_from_dict(data: dict[str, Any]) -> EvidenceDimensions:
    """Deserialize an EvidenceDimensions from a dict."""
    return EvidenceDimensions(
        supporting_count=int(data.get("supporting_count", 0)),
        independent_channels=int(data.get("independent_channels", 0)),
        contradicting_count=int(data.get("contradicting_count", 0)),
        mitigations=int(data.get("mitigations", 0)),
        timing_convergence_count=int(data.get("timing_convergence_count", 0)),
        source_confidence=SourceConfidence(
            data.get("source_confidence", "MODERATE"),
        ),
    )


def domain_assessment_from_dict(data: dict[str, Any]) -> DomainAssessment:
    """Deserialize a DomainAssessment from a dict."""
    return DomainAssessment(
        outcome_taxonomy=data["outcome_taxonomy"],
        dimensions=evidence_dimensions_from_dict(data.get("dimensions", {})),
        assessment_status=AssessmentStatus(
            data.get("assessment_status", "NEUTRAL"),
        ),
        timing_status=TimingStatus(
            data.get("timing_status", "INACTIVE"),
        ),
        overall_evidence_strength=OverallEvidenceStrength(
            data.get("overall_evidence_strength", "WEAK"),
        ),
    )


def convergence_config_from_dict(data: dict[str, Any]) -> ConvergenceConfig:
    """Deserialize a ConvergenceConfig from a dict."""
    return ConvergenceConfig(
        version=data.get("version", "1.0"),
        source_weights=dict(data.get("source_weights", {})),
        strength_weights=dict(data.get("strength_weights", {})),
        independence_penalty=float(data.get("independence_penalty", 0.5)),
        strongly_supported_min_independent=int(
            data.get("strongly_supported_min_independent", 3),
        ),
        strongly_supported_min_supporting=int(
            data.get("strongly_supported_min_supporting", 4),
        ),
        supported_min_independent=int(
            data.get("supported_min_independent", 2),
        ),
        supported_min_supporting=int(
            data.get("supported_min_supporting", 2),
        ),
        weakly_supported_min_supporting=int(
            data.get("weakly_supported_min_supporting", 1),
        ),
        strongly_contradicted_min_contradicting=int(
            data.get("strongly_contradicted_min_contradicting", 3),
        ),
        contradicted_min_contradicting=int(
            data.get("contradicted_min_contradicting", 2),
        ),
        convergent_min_windows=int(data.get("convergent_min_windows", 1)),
        high_confidence_min_weight=float(
            data.get("high_confidence_min_weight", 0.8),
        ),
        low_confidence_max_weight=float(
            data.get("low_confidence_max_weight", 0.4),
        ),
    )


def result_to_dict(assessment: DomainAssessment) -> dict[str, Any]:
    """Deterministic dict serialization of a DomainAssessment."""
    return assessment.to_dict()


def result_to_json(
    assessment: DomainAssessment,
    *,
    indent: int | None = None,
) -> str:
    """Deterministic JSON serialization of a DomainAssessment."""
    d = result_to_dict(assessment)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)

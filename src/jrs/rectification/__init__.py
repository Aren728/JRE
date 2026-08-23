"""JRS-064 Rectification Integration — integration layer.

Bridges JRE-021 (Rectification) capabilities with the JRS
evidence/convergence pipeline.  Outputs deterministic facts
(RectificationResult objects), NOT final predictions or interpretations.

Strict Boundaries:
- No modification of existing JRE/JRS engines or domain logic.
- Candidate generation is strictly separated from evaluation.
- No circular self-validation.
"""

from .errors import (
    InvalidCandidateError,
    InvalidKnownEventsError,
    NoAdjustmentError,
    PipelineEvaluationError,
    RectificationIntegrationError,
)
from .models import (
    AdjustmentDirection,
    AdjustmentProposal,
    EventMatch,
    KnownEvent,
    MatchQuality,
    RectificationResult,
    classify_match_quality,
    compute_assessment_mismatch,
    compute_timing_mismatch,
)
from .service import RectificationIntegrationService

__all__ = [
    # service
    "RectificationIntegrationService",
    # models
    "KnownEvent",
    "EventMatch",
    "RectificationResult",
    "AdjustmentProposal",
    "MatchQuality",
    "AdjustmentDirection",
    # helpers
    "classify_match_quality",
    "compute_assessment_mismatch",
    "compute_timing_mismatch",
    # errors
    "RectificationIntegrationError",
    "InvalidCandidateError",
    "InvalidKnownEventsError",
    "PipelineEvaluationError",
    "NoAdjustmentError",
]

"""JRS Convergence Engine — Evidence Convergence & Contradiction.

Public API
----------
- ``ConvergenceService``          – domain assessment from evidence + temporal
- ``AssessmentStatus``            – categorical assessment
- ``TimingStatus``                – timing convergence status
- ``OverallEvidenceStrength``     – overall strength classification
- ``SourceConfidence``            – source reliability confidence
- ``EvidenceDimensions``          – multi-dimensional evidence breakdown
- ``DomainAssessment``            – the final assessment output
- ``ConvergenceConfig``           – convergence configuration
- ``load_convergence_config``     – TOML config loader
"""

from __future__ import annotations

from .config import load_convergence_config
from .errors import (
    ConvergenceError,
    DimensionCalculationError,
    InvalidAssessmentInputError,
    InvalidConvergenceConfigError,
)
from .models import (
    SOURCE_CONFIDENCE_VALUES,
    AssessmentStatus,
    ConvergenceConfig,
    DomainAssessment,
    EvidenceDimensions,
    OverallEvidenceStrength,
    SourceConfidence,
    TimingStatus,
    classify_assessment_status,
    classify_overall_strength,
    classify_timing_status,
    compute_weighted_support_score,
    count_independent_channels,
)
from .serialize import (
    convergence_config_from_dict,
    domain_assessment_from_dict,
    evidence_dimensions_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import ConvergenceService

__all__: tuple[str, ...] = (
    # Errors
    "ConvergenceError",
    "InvalidConvergenceConfigError",
    "InvalidAssessmentInputError",
    "DimensionCalculationError",
    # Enums
    "AssessmentStatus",
    "TimingStatus",
    "OverallEvidenceStrength",
    "SourceConfidence",
    "SOURCE_CONFIDENCE_VALUES",
    # Models
    "EvidenceDimensions",
    "DomainAssessment",
    "ConvergenceConfig",
    "count_independent_channels",
    "compute_weighted_support_score",
    "classify_assessment_status",
    "classify_timing_status",
    "classify_overall_strength",
    # Config
    "load_convergence_config",
    # Serialize
    "evidence_dimensions_from_dict",
    "domain_assessment_from_dict",
    "convergence_config_from_dict",
    "result_to_dict",
    "result_to_json",
    # Service
    "ConvergenceService",
)

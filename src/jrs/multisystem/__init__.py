"""JRS-065 Multi-System Evidence Graph Foundation.

Provides structural interfaces, provenance tracking, and independence
analysis for cross-system evidence convergence prevention.
"""

from jrs.multisystem.errors import (
    ConvergenceError,
    IndependenceCalculationError,
    InvalidSystemTypeError,
    MissingEvidenceError,
    MultiSystemError,
    ProvenanceError,
)
from jrs.multisystem.models import (
    CrossSystemEvidence,
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
    compute_independence_score,
    compute_pairwise_independence,
    shared_derivative_roots,
)
from jrs.multisystem.service import IndependenceAnalyzer

__all__ = [
    "ConvergenceError",
    "CrossSystemEvidence",
    "EvidenceProvenance",
    "IndependenceAnalyzer",
    "IndependenceCalculationError",
    "InvalidSystemTypeError",
    "MissingEvidenceError",
    "MultiSystemError",
    "ProvenanceError",
    "SystemAssessment",
    "SystemType",
    "compute_convergence_score",
    "compute_independence_score",
    "compute_pairwise_independence",
    "shared_derivative_roots",
]

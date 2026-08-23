"""Error types for the Multi-System Evidence Graph module."""

from __future__ import annotations


class MultiSystemError(Exception):
    """Base error for multi-system evidence graph operations."""


class InvalidSystemTypeError(MultiSystemError):
    """Raised when an invalid SystemType is encountered."""


class IndependenceCalculationError(MultiSystemError):
    """Raised when independence score calculation fails."""


class ConvergenceError(MultiSystemError):
    """Raised when cross-system convergence computation fails."""


class ProvenanceError(MultiSystemError):
    """Raised when evidence provenance is invalid or incomplete."""


class MissingEvidenceError(MultiSystemError):
    """Raised when required system assessments are missing."""

"""Evidence framework error taxonomy."""

from __future__ import annotations


class EvidenceError(Exception):
    """Base exception for Evidence framework."""


class InvalidEvidenceConfigError(EvidenceError):
    """Raised when evidence configuration is invalid or missing required fields."""


class InvalidEvidenceRecordError(EvidenceError):
    """Raised when an EvidenceRecord is malformed or has invalid references."""


class CircularReferenceError(EvidenceError):
    """Raised when circular references are detected in evidence chains."""


class EvidenceNotFoundError(EvidenceError):
    """Raised when a referenced evidence_id does not exist in the registry."""


class DuplicateEvidenceError(EvidenceError):
    """Raised when attempting to register an evidence_id that already exists."""

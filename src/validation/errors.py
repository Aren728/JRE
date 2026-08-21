"""Validation system error taxonomy."""

from __future__ import annotations


class ValidationError(Exception):
    """Base exception for Validation system."""


class InvalidValidationConfigError(ValidationError):
    """Raised when validation configuration is invalid or missing required fields."""


class InvalidReferenceChartError(ValidationError):
    """Raised when a reference chart is malformed or missing required fields."""


class TriggerExtractionError(ValidationError):
    """Raised when structural triggers cannot be extracted from an EvidencePacket."""


class ValidationComputationError(ValidationError):
    """Raised when validation score computation fails."""

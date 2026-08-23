"""JRS-064 Rectification Integration — error taxonomy.

All errors in this module are non-retryable and indicate deterministic
programming or configuration failures.
"""

from __future__ import annotations


class RectificationIntegrationError(Exception):
    """Base class for all JRS-064 rectification integration errors."""


class InvalidCandidateError(RectificationIntegrationError):
    """Raised when a candidate birth time is invalid or empty."""


class InvalidKnownEventsError(RectificationIntegrationError):
    """Raised when the known events list is empty or malformed."""


class PipelineEvaluationError(RectificationIntegrationError):
    """Raised when the JRS pipeline fails to evaluate a candidate."""


class NoAdjustmentError(RectificationIntegrationError):
    """Raised when no valid adjustment can be suggested."""

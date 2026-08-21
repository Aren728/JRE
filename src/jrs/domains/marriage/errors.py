"""Marriage domain error taxonomy."""

from __future__ import annotations


class MarriageDomainError(Exception):
    """Base exception for Marriage domain."""


class InvalidMarriageConfigError(MarriageDomainError):
    """Raised when marriage domain configuration is invalid."""


class InvalidFactError(MarriageDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(MarriageDomainError):
    """Raised when rule evaluation fails."""

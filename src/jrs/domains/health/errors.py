"""Health/Vitality domain error taxonomy."""

from __future__ import annotations


class HealthDomainError(Exception):
    """Base exception for Health domain."""


class InvalidHealthConfigError(HealthDomainError):
    """Raised when health domain configuration is invalid."""


class InvalidFactError(HealthDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(HealthDomainError):
    """Raised when rule evaluation fails."""

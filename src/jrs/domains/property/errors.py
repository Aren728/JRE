"""Property domain error taxonomy."""

from __future__ import annotations


class PropertyDomainError(Exception):
    """Base exception for Property domain."""


class InvalidPropertyConfigError(PropertyDomainError):
    """Raised when property domain configuration is invalid."""


class InvalidFactError(PropertyDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(PropertyDomainError):
    """Raised when rule evaluation fails."""

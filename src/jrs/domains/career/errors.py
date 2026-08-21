"""Career domain error taxonomy."""

from __future__ import annotations


class CareerDomainError(Exception):
    """Base exception for Career domain."""


class InvalidCareerConfigError(CareerDomainError):
    """Raised when career domain configuration is invalid."""


class InvalidFactError(CareerDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(CareerDomainError):
    """Raised when rule evaluation fails."""

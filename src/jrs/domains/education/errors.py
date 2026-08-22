"""Education domain error taxonomy."""

from __future__ import annotations


class EducationDomainError(Exception):
    """Base exception for Education domain."""


class InvalidEducationConfigError(EducationDomainError):
    """Raised when education domain configuration is invalid."""


class InvalidFactError(EducationDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(EducationDomainError):
    """Raised when rule evaluation fails."""

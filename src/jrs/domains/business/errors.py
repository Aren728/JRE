"""Business domain error taxonomy."""

from __future__ import annotations


class BusinessDomainError(Exception):
    """Base exception for Business domain."""


class InvalidBusinessConfigError(BusinessDomainError):
    """Raised when business domain configuration is invalid."""


class InvalidFactError(BusinessDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(BusinessDomainError):
    """Raised when rule evaluation fails."""

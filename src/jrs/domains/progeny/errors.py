"""Progeny domain error taxonomy."""

from __future__ import annotations


class ProgenyDomainError(Exception):
    """Base exception for Progeny domain."""


class InvalidProgenyConfigError(ProgenyDomainError):
    """Raised when progeny domain configuration is invalid."""


class InvalidFactError(ProgenyDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(ProgenyDomainError):
    """Raised when rule evaluation fails."""

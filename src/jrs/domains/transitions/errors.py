"""Transitions domain error taxonomy."""

from __future__ import annotations


class TransitionsDomainError(Exception):
    """Base exception for Transitions domain."""


class InvalidTransitionsConfigError(TransitionsDomainError):
    """Raised when transitions domain configuration is invalid."""


class InvalidFactError(TransitionsDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(TransitionsDomainError):
    """Raised when rule evaluation fails."""

"""Wealth domain error taxonomy."""

from __future__ import annotations


class WealthDomainError(Exception):
    """Base exception for Wealth domain."""


class InvalidWealthConfigError(WealthDomainError):
    """Raised when wealth domain configuration is invalid."""


class InvalidFactError(WealthDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(WealthDomainError):
    """Raised when rule evaluation fails."""

"""Traits domain error taxonomy."""

from __future__ import annotations


class TraitsDomainError(Exception):
    """Base exception for Traits domain."""


class InvalidTraitsConfigError(TraitsDomainError):
    """Raised when traits domain configuration is invalid."""


class InvalidFactError(TraitsDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(TraitsDomainError):
    """Raised when rule evaluation fails."""

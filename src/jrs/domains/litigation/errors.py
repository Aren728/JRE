"""Litigation/Conflict domain error taxonomy."""

from __future__ import annotations


class LitigationDomainError(Exception):
    """Base exception for Litigation domain."""


class InvalidLitigationConfigError(LitigationDomainError):
    """Raised when litigation domain configuration is invalid."""


class InvalidFactError(LitigationDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(LitigationDomainError):
    """Raised when rule evaluation fails."""

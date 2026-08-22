"""Migration domain error taxonomy."""

from __future__ import annotations


class MigrationDomainError(Exception):
    """Base exception for Migration domain."""


class InvalidMigrationConfigError(MigrationDomainError):
    """Raised when migration domain configuration is invalid."""


class InvalidFactError(MigrationDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(MigrationDomainError):
    """Raised when rule evaluation fails."""

"""Assets/Vehicles domain error taxonomy."""

from __future__ import annotations


class AssetsDomainError(Exception):
    """Base exception for Assets domain."""


class InvalidAssetsConfigError(AssetsDomainError):
    """Raised when assets domain configuration is invalid."""


class InvalidFactError(AssetsDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(AssetsDomainError):
    """Raised when rule evaluation fails."""

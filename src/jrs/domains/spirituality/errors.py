"""Spirituality domain error taxonomy."""

from __future__ import annotations


class SpiritualityDomainError(Exception):
    """Base exception for Spirituality domain."""


class InvalidSpiritualityConfigError(SpiritualityDomainError):
    """Raised when spirituality domain configuration is invalid."""


class InvalidFactError(SpiritualityDomainError):
    """Raised when input facts are malformed or missing required fields."""


class RuleEvaluationError(SpiritualityDomainError):
    """Raised when rule evaluation fails."""

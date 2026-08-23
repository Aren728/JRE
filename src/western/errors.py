"""Error types for the Western astrology calculation module."""

from __future__ import annotations


class WesternCalculationError(Exception):
    """Raised when a deterministic calculation fails."""


class WesternInputError(ValueError):
    """Raised when input data is invalid or out of range."""

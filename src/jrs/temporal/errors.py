"""Temporal evidence error taxonomy."""

from __future__ import annotations


class TemporalError(Exception):
    """Base exception for Temporal evidence layer."""


class InvalidTemporalConfigError(TemporalError):
    """Raised when temporal configuration is invalid."""


class InvalidTriggerError(TemporalError):
    """Raised when a TemporalTrigger is malformed."""


class InvalidEventWindowError(TemporalError):
    """Raised when an EventWindow cannot be constructed."""


class OverlapCalculationError(TemporalError):
    """Raised when overlap calculation fails."""

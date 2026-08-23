"""Transitions engine error taxonomy."""

from __future__ import annotations


class TransitionsError(Exception):
    """Base exception for Transitions engine."""


class InvalidTransitionInputError(TransitionsError):
    """Raised when transition input is malformed or insufficient."""


class TransitionComputationError(TransitionsError):
    """Raised when transition computation fails internally."""

"""Convergence engine error taxonomy."""

from __future__ import annotations


class ConvergenceError(Exception):
    """Base exception for Convergence engine."""


class InvalidConvergenceConfigError(ConvergenceError):
    """Raised when convergence configuration is invalid."""


class InvalidAssessmentInputError(ConvergenceError):
    """Raised when assessment input is malformed or empty."""


class DimensionCalculationError(ConvergenceError):
    """Raised when evidence dimension calculation fails."""

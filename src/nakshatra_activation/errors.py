"""Nakshatra Activation error taxonomy."""

from __future__ import annotations


class NakshatraActivationError(Exception):
    """Base exception for Nakshatra Activation module."""


class InvalidActivationRequestError(NakshatraActivationError):
    """Raised when activation computation request is invalid."""


class InvalidActivationConfigError(NakshatraActivationError):
    """Raised when activation configuration is invalid."""


class ActivationComputationError(NakshatraActivationError):
    """Raised when activation computation fails."""

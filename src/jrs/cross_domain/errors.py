"""Cross-domain event reasoning engine error taxonomy."""

from __future__ import annotations


class CrossDomainError(Exception):
    """Base exception for Cross-Domain engine."""


class InvalidClusterInputError(CrossDomainError):
    """Raised when cluster input is malformed or insufficient."""


class ClusterComputationError(CrossDomainError):
    """Raised when cluster computation fails internally."""

"""Research module error taxonomy."""

from __future__ import annotations


class ResearchDomainError(Exception):
    """Base exception for Research module."""


class InvalidResearchConfigError(ResearchDomainError):
    """Raised when research configuration is invalid."""


class CitationNotFoundError(ResearchDomainError):
    """Raised when a rule_id has no matching citation."""

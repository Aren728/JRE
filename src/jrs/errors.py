"""JRS Orchestrator error taxonomy."""

from __future__ import annotations


class JRSerror(Exception):
    """Base exception for JRS Orchestrator."""


class InvalidJRSConfigError(JRSerror):
    """Raised when JRS configuration is invalid or missing required fields."""


class InvalidQueryError(JRSerror):
    """Raised when a query intent is malformed or references unknown categories."""


class EngineExecutionError(JRSerror):
    """Raised when a downstream JRE engine fails during routing execution."""


class OrchestrationError(JRSerror):
    """Raised when orchestration or evidence aggregation fails."""

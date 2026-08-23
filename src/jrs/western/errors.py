"""Error types for the Western JRS interpretation module."""

from __future__ import annotations


class InvalidWesternConfigError(Exception):
    """Raised when the Western TOML configuration is invalid."""

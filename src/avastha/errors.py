"""JRE-015 Avastha (Planetary States) error taxonomy.

``AvasthaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class AvasthaError(Exception):
    """Base class for all JRE-015 Avastha layer errors."""


class InvalidAvasthaConfigError(AvasthaError):
    """Raised when a ``AvasthaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidAvasthaRequestError(AvasthaError):
    """Raised when an Avastha computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class AvasthaComputationError(AvasthaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

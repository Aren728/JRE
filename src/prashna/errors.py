"""JRE-019 Prashna (Horary) error taxonomy.

``PrashnaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class PrashnaError(Exception):
    """Base class for all JRE-019 Prashna layer errors."""


class InvalidPrashnaConfigError(PrashnaError):
    """Raised when a ``PrashnaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidPrashnaRequestError(PrashnaError):
    """Raised when a Prashna computation request is malformed: missing
    data, invalid inputs, or empty data."""


class PrashnaComputationError(PrashnaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

"""JRE-012 Drik (Aspect) error taxonomy.

``DrikError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class DrikError(Exception):
    """Base class for all JRE-012 Drik layer errors."""


class InvalidDrikConfigError(DrikError):
    """Raised when a ``DrikConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidDrikRequestError(DrikError):
    """Raised when a Drik computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class DrikComputationError(DrikError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

"""JRE-011 Bala (Shadbala) error taxonomy.

``BalaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses; a failed delegated lower-layer
computation is wrapped in ``BalaComputationError``.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class BalaError(Exception):
    """Base class for all JRE-011 Bala layer errors."""


class InvalidBalaConfigError(BalaError):
    """Raised when a ``BalaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidBalaRequestError(BalaError):
    """Raised when a Bala computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class BalaComputationError(BalaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

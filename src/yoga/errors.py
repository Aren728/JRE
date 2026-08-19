"""JRE-013 Yoga error taxonomy.

``YogaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class YogaError(Exception):
    """Base class for all JRE-013 Yoga layer errors."""


class InvalidYogaConfigError(YogaError):
    """Raised when a ``YogaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidYogaRequestError(YogaError):
    """Raised when a Yoga computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class YogaComputationError(YogaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

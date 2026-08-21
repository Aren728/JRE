"""JRE-021 Rectification (Birth Time) error taxonomy.

``RectificationError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class RectificationError(Exception):
    """Base class for all JRE-021 Rectification layer errors."""


class InvalidRectificationConfigError(RectificationError):
    """Raised when a ``RectificationConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidRectificationRequestError(RectificationError):
    """Raised when a Rectification computation request is malformed: missing
    data, invalid inputs, or empty data."""


class RectificationComputationError(RectificationError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

"""JRE-016 Ashtakavarga (eight-fold strength) error taxonomy.

``AshtakavargaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class AshtakavargaError(Exception):
    """Base class for all JRE-016 Ashtakavarga layer errors."""


class InvalidAshtakavargaConfigError(AshtakavargaError):
    """Raised when a ``AshtakavargaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidAshtakavargaRequestError(AshtakavargaError):
    """Raised when an Ashtakavarga computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class AshtakavargaComputationError(AshtakavargaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

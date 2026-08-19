"""JRE-017 Tajika (Varshaphala / annual chart) error taxonomy.

``TajikaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class TajikaError(Exception):
    """Base class for all JRE-017 Tajika layer errors."""


class InvalidTajikaConfigError(TajikaError):
    """Raised when a ``TajikaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidTajikaRequestError(TajikaError):
    """Raised when a Tajika computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class TajikaComputationError(TajikaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

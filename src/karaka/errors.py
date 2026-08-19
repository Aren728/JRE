"""JRE-014 Karaka (Significator) error taxonomy.

``KarakaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class KarakaError(Exception):
    """Base class for all JRE-014 Karaka layer errors."""


class InvalidKarakaConfigError(KarakaError):
    """Raised when a ``KarakaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidKarakaRequestError(KarakaError):
    """Raised when a Karaka computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class KarakaComputationError(KarakaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

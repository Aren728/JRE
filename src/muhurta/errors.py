"""JRE-020 Muhurta (Electional) error taxonomy.

``MuhurtaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class MuhurtaError(Exception):
    """Base class for all JRE-020 Muhurta layer errors."""


class InvalidMuhurtaConfigError(MuhurtaError):
    """Raised when a ``MuhurtaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidMuhurtaRequestError(MuhurtaError):
    """Raised when a Muhurta computation request is malformed: missing
    data, invalid inputs, or empty data."""


class MuhurtaComputationError(MuhurtaError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

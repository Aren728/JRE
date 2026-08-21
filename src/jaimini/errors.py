"""JRE-018 Jaimini (Chara Dasha / Argala) error taxonomy.

``JaiminiError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class JaiminiError(Exception):
    """Base class for all JRE-018 Jaimini layer errors."""


class InvalidJaiminiConfigError(JaiminiError):
    """Raised when a ``JaiminiConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidJaiminiRequestError(JaiminiError):
    """Raised when a Jaimini computation request is malformed: missing
    planet states, invalid inputs, or empty data."""


class JaiminiComputationError(JaiminiError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

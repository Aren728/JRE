"""JRE-022 Synthesis (Verdict) error taxonomy.

``SynthesisError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class SynthesisError(Exception):
    """Base class for all JRE-022 Synthesis layer errors."""


class InvalidSynthesisConfigError(SynthesisError):
    """Raised when a ``SynthesisConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidSynthesisRequestError(SynthesisError):
    """Raised when a Synthesis computation request is malformed: missing
    data, invalid inputs, or empty data."""


class SynthesisComputationError(SynthesisError):
    """Raised when a delegated lower-layer computation fails.  The
    message includes the wrapped error class name."""

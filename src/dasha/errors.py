"""JRE-010 Dasha error taxonomy.

``DashaError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses; a failed delegated lower-layer
fact lookup is wrapped in ``DashaComputationError`` whose message
includes the wrapped error class name.  No raw
``ValueError``/``KeyError``/``AttributeError`` escapes the public
surface.
"""


class DashaError(Exception):
    """Base class for all JRE-010 Dasha layer errors."""


class InvalidDashaConfigError(DashaError):
    """Raised when a ``DashaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidDashaRequestError(DashaError):
    """Raised when a Dasha computation request is malformed: missing birth
    state, unknown dasha system, invalid duration, or an invalid date/time
    value."""


class DashaComputationError(DashaError):
    """Raised when a delegated lower-layer fact cannot be echoed.  The
    message includes the wrapped error class name."""

"""JRE-008 Varga error taxonomy.

``VargaError`` is the base; config and request/definition validation raise
the two ``Invalid*`` subclasses; a failed delegated JRE-003 fact echo is
wrapped in ``VargaComputationError`` whose message includes the wrapped
error class name. No raw ``ValueError``/``KeyError``/``AttributeError``
escapes the public surface.
"""


class VargaError(Exception):
    """Base class for all JRE-008 Varga layer errors."""


class InvalidVargaConfigError(VargaError):
    """Raised when a ``VargaConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidVargaRequestError(VargaError):
    """Raised when a varga computation request is malformed: unknown varga
    id, unknown method id, empty bodies, out-of-range ``degree_in_rashi``,
    or an invalid definition/method value."""


class VargaComputationError(VargaError):
    """Raised when a delegated lower-layer fact cannot be echoed. The
    message includes the wrapped error class name."""

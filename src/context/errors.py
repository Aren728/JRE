"""JRE-007 Canonical Context error taxonomy (SPEC §7, DC §3).

``ContextError`` is the base; config and request/snapshot validation raise
the two ``Invalid*`` subclasses; a failed delegated JRE-002/003/005/006
computation is wrapped in ``ContextComputationError`` whose message
includes the wrapped error class name. No raw ``ValueError``/``KeyError``/
``AttributeError`` escapes the public surface.
"""


class ContextError(Exception):
    """Base class for all JRE-007 canonical-context layer errors."""


class InvalidContextConfigError(ContextError):
    """Raised when a ``ContextConfig`` value or TOML file is invalid."""


class InvalidContextRequestError(ContextError):
    """Raised when a snapshot request is malformed (bad instant/interval,
    empty bodies, unknown time-precision, or a generic snapshot
    carrying natal sections)."""


class ContextComputationError(ContextError):
    """Raised when a delegated lower-layer computation fails and cannot be
    echoed. The message includes the wrapped error class name."""

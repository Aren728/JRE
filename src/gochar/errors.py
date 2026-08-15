"""JRE-006 Gochar error taxonomy (SPEC §7, DATA-CONTRACT §3).

``GocharError`` is the base; config and request validation raise the two
``Invalid*`` subclasses; a failed delegated JRE-003/JRE-005 computation is
wrapped in ``GocharComputationError`` whose message includes the wrapped
error class name. No raw ``ValueError``/``KeyError``/``AttributeError``
escapes the public surface.
"""


class GocharError(Exception):
    """Base class for all JRE-006 gochar layer errors."""


class InvalidGocharConfigError(GocharError):
    """Raised when a ``GocharConfig`` value or TOML file is invalid."""


class InvalidGocharRequestError(GocharError):
    """Raised when a request is malformed (bad instant/interval, start >
    end, empty bodies, unknown reference/house system, ``natal_house_series``
    without an anchor)."""


class GocharComputationError(GocharError):
    """Raised when a delegated JRE-003/JRE-005 computation fails and cannot
    be echoed. The message includes the wrapped error class name."""

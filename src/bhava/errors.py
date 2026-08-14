"""Structured errors for the JRE-005 Bhava / House engine (SPEC §29).

Every error includes the offending value(s) in its message. JRE-003 errors
from delegated calls propagate unchanged (never wrapped into a fact).
"""


class BhavaError(Exception):
    """Base class for all Bhava layer errors."""


class InvalidAnalysisRequestError(BhavaError):
    """Raised when a service request is malformed (bad birth, empty
    references, unknown fields)."""


class InvalidBhavaConfigError(BhavaError):
    """Raised when a ``BhavaConfig`` value is invalid (unknown enum, orb
    out of range, empty/duplicate/unknown system set, bad profile string)."""


class InconsistentChartError(BhavaError):
    """Raised when an input ``NatalChart`` violates the JRE-005 invariants
    (SPEC §8)."""


class UnplacedBodyError(BhavaError):
    """Raised when a body cannot be assigned to any house and
    ``unplaced_body_behavior == RAISE`` (ADR-018)."""


class UnsupportedReferenceError(BhavaError):
    """Raised when a reference is not in {LAGNA, MOON, SUN, ASC}."""

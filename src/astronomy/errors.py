"""Structured errors for the JRE astronomical core (JRE-002).

Every error includes the offending value(s) in its message. The service never
swallows provider errors into a ``BodyPosition`` — errors propagate with their
original type.
"""


class EphemerisError(Exception):
    """Base class for all astronomical core errors."""


class InvalidTimestampError(EphemerisError):
    """Raised when a date/time/timezone input is malformed or unsupported."""


class InvalidCoordinatesError(EphemerisError):
    """Raised when latitude/longitude are out of range or non-finite."""


class UnsupportedProviderError(EphemerisError):
    """Raised when a requested ``provider_id`` is not registered."""


class EphemerisDataError(EphemerisError):
    """Raised when ephemeris data is unavailable or fails its integrity check."""

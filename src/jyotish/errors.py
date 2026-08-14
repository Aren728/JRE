"""Structured errors for the Jyotish coordinate/state layer (JRE-003).

Every error includes the offending value(s) in its message. The service never
swallows a provider error into a fact — errors propagate with their original
type (astronomy errors are passed through unchanged).
"""


class JyotishError(Exception):
    """Base class for all Jyotish layer errors."""


class InvalidBirthDataError(JyotishError):
    """Raised when birth data is malformed or out of range."""


class InvalidConfigError(JyotishError):
    """Raised when a configuration field is invalid (precision range, unknown enum)."""


class InvalidOrbError(JyotishError):
    """Raised when orb values are non-positive, inconsistent, or a kind is unknown."""


class UnsupportedHouseSystemError(JyotishError):
    """Raised when ``house_system`` is not registered with any provider."""


class UnsupportedReferencePointError(JyotishError):
    """Raised when a ``TransitReferencePoint`` value is unknown."""


class TransitSearchError(JyotishError):
    """Raised when the transit event search fails to converge within its cap."""


class EclipseError(JyotishError):
    """Raised when the eclipse provider fails (binding/data)."""


class ProviderCompatibilityError(JyotishError):
    """Raised when provider metadata mismatches the ``ephemeris_version`` pin."""

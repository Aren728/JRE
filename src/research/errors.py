"""JRE-009 Research Worker error taxonomy.

``ResearchError`` is the base; config and request validation raise
the two ``Invalid*`` subclasses; a failed file read is wrapped in
``ResearchComputationError`` whose message includes the wrapped error
class name. No raw ``ValueError``/``KeyError``/``AttributeError``/``OSError``
escapes the public surface.
"""


class ResearchError(Exception):
    """Base class for all JRE-009 Research Worker layer errors."""


class InvalidResearchConfigError(ResearchError):
    """Raised when a ``ResearchConfig`` value or the authoritative TOML file
    is invalid or missing."""


class InvalidResearchRequestError(ResearchError):
    """Raised when a research task is malformed: empty query, empty source
    directories, empty target concepts, or an unknown status value."""


class ResearchComputationError(ResearchError):
    """Raised when a delegated lower-layer operation (file I/O) fails and
    cannot be echoed. The message includes the wrapped error class name."""

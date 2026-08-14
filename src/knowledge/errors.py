"""Structured errors for the Classical Knowledge & Rule Engine (JRE-004).

Every error includes the offending value(s) in its message (SPEC §17). The
service never swallows a catalog/provenance error into a result — errors
propagate with their original type.
"""


class KnowledgeError(Exception):
    """Base class for all knowledge-layer errors."""


class InvalidConfigError(KnowledgeError):
    """Raised when a knowledge configuration field is invalid (SPEC §13/§14)."""


class UnknownSourceError(KnowledgeError):
    """Raised when a ``source_id`` is not present in the source registry."""


class UnknownEditionError(KnowledgeError):
    """Raised when an ``edition_id`` does not resolve for a source."""


class UnknownProfileError(KnowledgeError):
    """Raised when a ``profile_id`` is not registered."""


class RuleSchemaError(KnowledgeError):
    """Raised when a rule fails schema / fact-vocabulary validation."""


class ProvenanceError(KnowledgeError):
    """Raised when a rule lacks mandatory provenance (when enforced)."""


class CatalogIntegrityError(KnowledgeError):
    """Raised on checksum mismatch or catalog version-pin mismatch."""


class ConflictResolutionError(KnowledgeError):
    """Raised on asymmetric ``conflicts_with``, ``exception_for`` cycles, or malformed declarations."""  # noqa: E501


class SynthesisError(KnowledgeError):
    """Raised when the snapshot misses a domain-required section or normalization fails."""

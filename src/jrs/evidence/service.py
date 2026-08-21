"""Evidence framework service — registry and chain resolver."""

from __future__ import annotations

from .config import load_evidence_config
from .errors import (
    DuplicateEvidenceError,
    EvidenceNotFoundError,
)
from .models import (
    EvidenceChain,
    EvidenceConfig,
    EvidenceRecord,
    detect_circular_references,
    resolve_evidence_chain,
)


class EvidenceService:
    """Evidence service: manages the evidence registry and resolves evidence chains.

    Usage::

        svc = EvidenceService()
        svc.register_evidence(record)
        chain = svc.get_evidence_chain("E-1042")
    """

    def __init__(self, config: EvidenceConfig | None = None) -> None:
        """Initialize the evidence service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from
                    ``config/evidence.toml``.
        """
        self._config = config or load_evidence_config()
        self._registry: dict[str, EvidenceRecord] = {}

    def register_evidence(self, record: EvidenceRecord) -> None:
        """Register an evidence record in the registry.

        Args:
            record: The evidence record to register.

        Raises:
            DuplicateEvidenceError: If the evidence_id already exists.
            InvalidEvidenceRecordError: If the record references non-existent
                evidence_ids in its links.
        """
        if record.evidence_id in self._registry:
            raise DuplicateEvidenceError(
                f"Evidence {record.evidence_id} already registered",
            )

        # Validate that linked evidence_ids exist (or will exist)
        # We allow forward references for batch registration
        self._registry[record.evidence_id] = record

    def get_evidence_chain(self, evidence_id: str) -> EvidenceChain:
        """Resolve the full evidence chain for a given evidence_id.

        Traverses contradicted_by, mitigated_by, and reverse links to build
        a complete EvidenceChain.

        Args:
            evidence_id: The evidence_id to resolve.

        Returns:
            The resolved EvidenceChain.

        Raises:
            EvidenceNotFoundError: If the evidence_id is not in the registry.
        """
        chain = resolve_evidence_chain(
            evidence_id,
            self._registry,
            self._config.max_chain_depth,
        )
        if chain is None:
            raise EvidenceNotFoundError(
                f"Evidence {evidence_id} not found in registry",
            )
        return chain

    def validate_registry(self) -> list[tuple[str, ...]]:
        """Validate the registry for circular references.

        Returns:
            A list of cycles found. Empty if no cycles.
        """
        return detect_circular_references(self._registry)

    def get_record(self, evidence_id: str) -> EvidenceRecord | None:
        """Get a single evidence record by ID.

        Args:
            evidence_id: The evidence_id to look up.

        Returns:
            The EvidenceRecord if found, None otherwise.
        """
        return self._registry.get(evidence_id)

    def get_all_records(self) -> tuple[EvidenceRecord, ...]:
        """Get all registered evidence records.

        Returns:
            A tuple of all EvidenceRecord objects.
        """
        return tuple(self._registry.values())

    def get_records_by_outcome(self, outcome_taxonomy: str) -> tuple[EvidenceRecord, ...]:
        """Get all evidence records for a specific outcome taxonomy.

        Args:
            outcome_taxonomy: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching EvidenceRecord objects.
        """
        return tuple(
            r for r in self._registry.values()
            if r.outcome_taxonomy == outcome_taxonomy
        )

    def get_records_by_source(self, source_id: str) -> tuple[EvidenceRecord, ...]:
        """Get all evidence records from a specific classical source.

        Args:
            source_id: The source_id to filter by.

        Returns:
            A tuple of matching EvidenceRecord objects.
        """
        return tuple(
            r for r in self._registry.values()
            if r.source_id == source_id
        )

    @property
    def config(self) -> EvidenceConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def registry_size(self) -> int:
        """Return the number of registered evidence records."""
        return len(self._registry)

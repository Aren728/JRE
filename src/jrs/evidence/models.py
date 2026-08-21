"""Evidence framework data models — classical sources, evidence records, rule catalog."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────

class EvidenceDirection(Enum):
    """Direction of evidence relative to an outcome."""

    SUPPORT = "SUPPORT"
    CONTRADICT = "CONTRADICT"
    MITIGATE = "MITIGATE"
    NEUTRAL = "NEUTRAL"


class EvidenceStrength(Enum):
    """Strength of a piece of evidence."""

    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    VERY_LOW = "VERY_LOW"


# Strength to numeric mapping for scoring
STRENGTH_VALUES: dict[EvidenceStrength, float] = {
    EvidenceStrength.VERY_HIGH: 1.0,
    EvidenceStrength.HIGH: 0.8,
    EvidenceStrength.MODERATE: 0.6,
    EvidenceStrength.LOW: 0.4,
    EvidenceStrength.VERY_LOW: 0.2,
}


# ── Core Models ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ClassicalSource:
    """A classical astrological text or authority."""

    source_id: str
    name: str
    author: str = ""
    era: str = ""
    reliability_weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "source_id": self.source_id,
            "name": self.name,
            "author": self.author,
            "era": self.era,
            "reliability_weight": self.reliability_weight,
        }


@dataclass(frozen=True)
class EvidenceRecord:
    """A single piece of evidence linking a classical rule to an outcome."""

    evidence_id: str
    outcome_taxonomy: str
    supporting_fact_type: str
    rule_id: str
    source_id: str
    location: str = ""
    direction: EvidenceDirection = EvidenceDirection.SUPPORT
    strength: EvidenceStrength = EvidenceStrength.MODERATE
    timing_relevance: str = ""
    independence_group: str = ""
    contradicted_by: tuple[str, ...] = ()
    mitigated_by: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "evidence_id": self.evidence_id,
            "outcome_taxonomy": self.outcome_taxonomy,
            "supporting_fact_type": self.supporting_fact_type,
            "rule_id": self.rule_id,
            "source_id": self.source_id,
            "location": self.location,
            "direction": self.direction.value,
            "strength": self.strength.value,
            "timing_relevance": self.timing_relevance,
            "independence_group": self.independence_group,
            "contradicted_by": list(self.contradicted_by),
            "mitigated_by": list(self.mitigated_by),
        }


@dataclass(frozen=True)
class RuleCatalogEntry:
    """A rule in the classical rule catalog."""

    rule_id: str
    description: str
    required_conditions: tuple[str, ...] = ()
    outcome_taxonomy: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "required_conditions": list(self.required_conditions),
            "outcome_taxonomy": self.outcome_taxonomy,
        }


@dataclass(frozen=True)
class EvidenceChain:
    """A resolved evidence chain: the record plus its linked contradictions/mitigations."""

    record: EvidenceRecord
    contradictions: tuple[EvidenceRecord, ...] = ()
    mitigations: tuple[EvidenceRecord, ...] = ()
    supporting: tuple[EvidenceRecord, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "record": self.record.to_dict(),
            "contradictions": [r.to_dict() for r in self.contradictions],
            "mitigations": [r.to_dict() for r in self.mitigations],
            "supporting": [r.to_dict() for r in self.supporting],
        }


# ── Validation Config (embedded) ─────────────────────────────────────────────

@dataclass(frozen=True)
class EvidenceConfig:
    """Configuration for the evidence framework."""

    version: str = "1.0"
    source_weights: dict[str, float] = field(default_factory=dict)
    strength_multipliers: dict[str, float] = field(default_factory=dict)
    max_chain_depth: int = 10


# ── Graph Traversal Helpers ──────────────────────────────────────────────────

def detect_circular_references(
    records: dict[str, EvidenceRecord],
) -> list[tuple[str, ...]]:
    """Detect circular references in evidence chains.

    Checks both contradicted_by and mitigated_by links for cycles.

    Args:
        records: Mapping of evidence_id to EvidenceRecord.

    Returns:
        A list of cycles found, each represented as a tuple of evidence_ids.
        Empty list if no cycles detected.
    """
    cycles: list[tuple[str, ...]] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def _dfs(eid: str, path: list[str]) -> None:
        if eid in rec_stack:
            # Found a cycle — extract it
            cycle_start = path.index(eid)
            cycle = tuple(path[cycle_start:]) + (eid,)
            if cycle not in cycles:
                cycles.append(cycle)
            return
        if eid in visited:
            return

        visited.add(eid)
        rec_stack.add(eid)
        path.append(eid)

        record = records.get(eid)
        if record is not None:
            for linked_id in record.contradicted_by:
                if linked_id in records:
                    _dfs(linked_id, path)
            for linked_id in record.mitigated_by:
                if linked_id in records:
                    _dfs(linked_id, path)

        path.pop()
        rec_stack.discard(eid)

    for eid in records:
        if eid not in visited:
            _dfs(eid, [])

    return cycles


def resolve_evidence_chain(
    evidence_id: str,
    records: dict[str, EvidenceRecord],
    max_depth: int = 10,
) -> EvidenceChain | None:
    """Resolve the full evidence chain for a given evidence_id.

    Traverses contradicted_by, mitigated_by, and reverse links (supporting)
    to build a complete EvidenceChain.

    Args:
        evidence_id: The evidence_id to resolve.
        records: Mapping of evidence_id to EvidenceRecord.
        max_depth: Maximum traversal depth to prevent infinite loops.

    Returns:
        An EvidenceChain if the evidence_id exists, None otherwise.
    """
    record = records.get(evidence_id)
    if record is None:
        return None

    contradictions = _resolve_links(
        record.contradicted_by, records, max_depth,
    )
    mitigations = _resolve_links(
        record.mitigated_by, records, max_depth,
    )
    supporting = _find_supporting(evidence_id, records)

    return EvidenceChain(
        record=record,
        contradictions=contradictions,
        mitigations=mitigations,
        supporting=supporting,
    )


def _resolve_links(
    link_ids: tuple[str, ...],
    records: dict[str, EvidenceRecord],
    max_depth: int,
    _depth: int = 0,
) -> tuple[EvidenceRecord, ...]:
    """Resolve a list of linked evidence_ids to EvidenceRecords."""
    if _depth >= max_depth:
        return ()

    result: list[EvidenceRecord] = []
    for lid in link_ids:
        rec = records.get(lid)
        if rec is not None:
            result.append(rec)
    return tuple(result)


def _find_supporting(
    evidence_id: str,
    records: dict[str, EvidenceRecord],
) -> tuple[EvidenceRecord, ...]:
    """Find all records that reference this evidence_id in their links."""
    supporting: list[EvidenceRecord] = []
    for rec in records.values():
        if evidence_id in rec.contradicted_by or evidence_id in rec.mitigated_by:
            supporting.append(rec)
    return tuple(supporting)

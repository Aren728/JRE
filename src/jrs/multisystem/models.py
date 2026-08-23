"""JRS-065 Multi-System Evidence Graph Foundation — data models.

Defines the structural interfaces, provenance tracking, and independence
analysis required to prevent false convergence when multiple astrological
systems are added later.

Strict Boundaries:
- This module is purely structural: it defines interfaces, provenance
  tracking, and independence analysis.
- Vedic JRS remains the primary, fully implemented system.
- No actual Western, Nadi, Numerology, Vastu, or Palmistry calculation
  logic is implemented here.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────


class SystemType(Enum):
    """Astrological/divinatory system types.

    Each system type represents a distinct tradition of knowledge.
    Systems sharing ``derivative_roots`` are treated as partially
    non-independent to prevent false convergence.
    """

    VEDIC = "VEDIC"
    WESTERN = "WESTERN"
    NADI = "NADI"
    NUMEROLOGY = "NUMEROLOGY"
    VASTU = "VASTU"
    PALMISTRY = "PALMISTRY"


# ── Derivative Root Configuration ────────────────────────────────────────────
#
# Classical genealogy of astrological systems.  Two systems sharing a
# common ancestor root are *not fully independent* — their evidence
# channels may overlap even when expressed in different symbolic
# vocabularies.
#
# Vedic and Western share roots in Hellenistic astrology.
# Nadi is a distinct Tamil tradition with some Vedic overlap.
# Numerology, Vastu, and Palmistry are structurally independent of
# the astrological systems.

# Each system lists the *other* SystemTypes it shares historical roots with.
# VEDIC and Western share roots in Hellenistic astrology.
# NADI has partial Vedic overlap.
# NUMEROLOGY, VASTU, PALMISTRY are structurally independent.
_SYSTEM_DERIVATIVE_ROOTS: dict[SystemType, frozenset[SystemType]] = {
    SystemType.VEDIC: frozenset({SystemType.WESTERN}),
    SystemType.WESTERN: frozenset({SystemType.VEDIC}),
    SystemType.NADI: frozenset({SystemType.VEDIC}),
    SystemType.NUMEROLOGY: frozenset(),
    SystemType.VASTU: frozenset(),
    SystemType.PALMISTRY: frozenset(),
}


def shared_derivative_roots(
    system_a: SystemType,
    system_b: SystemType,
) -> frozenset[SystemType]:
    """Return shared derivative lineage between two systems.

    Two systems share roots if either lists the other in its derivative
    roots (bidirectional lineage check).  Returns a frozenset containing
    both systems if related, empty frozenset otherwise.

    Args:
        system_a: First system type.
        system_b: Second system type.

    Returns:
        A frozenset with both system types if they share lineage,
        empty frozenset if no lineage is shared.
    """
    roots_a = _SYSTEM_DERIVATIVE_ROOTS.get(system_a, frozenset())
    roots_b = _SYSTEM_DERIVATIVE_ROOTS.get(system_b, frozenset())
    # Bidirectional: A lists B in roots, or B lists A in roots
    if system_b in roots_a or system_a in roots_b:
        return frozenset({system_a, system_b})
    return frozenset()


# ── Core Models ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EvidenceProvenance:
    """Provenance metadata for a piece of evidence from a specific system.

    Tracks which system produced the evidence, its tradition, which
    other systems it shares roots with, and its confidence weight.
    """

    system_type: SystemType
    source_tradition: str
    derivative_roots: tuple[SystemType, ...] = ()
    confidence_weight: float = 1.0

    def __post_init__(self) -> None:
        """Validate fields after construction."""
        if not 0.0 <= self.confidence_weight <= 1.0:
            raise ValueError(
                f"confidence_weight must be in [0, 1], "
                f"got {self.confidence_weight}"
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "system_type": self.system_type.value,
            "source_tradition": self.source_tradition,
            "derivative_roots": [r.value for r in self.derivative_roots],
            "confidence_weight": self.confidence_weight,
        }


@dataclass(frozen=True)
class CrossSystemEvidence:
    """An evidence cluster spanning multiple astrological systems.

    This is a FACT container — it records what systems converge on
    a conclusion, when they converge, and how independent the
    convergence truly is.  It does NOT interpret the meaning.

    The ``deterministic_id`` is a SHA-256 hash of the serializable
    content, computed automatically on construction if not provided.
    """

    event_cluster_id: str
    system_assessments: dict[str, SystemAssessment] = field(
        default_factory=dict,
    )
    independence_score: float = 0.0
    convergence_score: float = 0.0
    deterministic_id: str = ""

    def __post_init__(self) -> None:
        """Compute deterministic_id if not provided."""
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_evidence_hash(self),
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "event_cluster_id": self.event_cluster_id,
            "system_assessments": {
                k: v.to_dict() for k, v in self.system_assessments.items()
            },
            "independence_score": self.independence_score,
            "convergence_score": self.convergence_score,
            "deterministic_id": self.deterministic_id,
        }


@dataclass(frozen=True)
class SystemAssessment:
    """Assessment output from a single astrological system.

    Wraps an outcome taxonomy string and assessment status, paired
    with the system's provenance.  This is the per-system unit that
    feeds into ``CrossSystemEvidence``.
    """

    system_type: SystemType
    outcome_taxonomy: str
    assessment_status: str  # e.g. "SUPPORTED", "NEUTRAL", etc.
    timing_status: str = "INACTIVE"
    provenance: EvidenceProvenance | None = None

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "system_type": self.system_type.value,
            "outcome_taxonomy": self.outcome_taxonomy,
            "assessment_status": self.assessment_status,
            "timing_status": self.timing_status,
            "provenance": self.provenance.to_dict()
            if self.provenance is not None
            else None,
        }


# ── Deterministic Hashing ────────────────────────────────────────────────────


def _compute_evidence_hash(evidence: CrossSystemEvidence) -> str:
    """Compute a deterministic SHA-256 hash for CrossSystemEvidence."""
    data = {
        "event_cluster_id": evidence.event_cluster_id,
        "system_keys": sorted(evidence.system_assessments.keys()),
        "independence_score": evidence.independence_score,
        "convergence_score": evidence.convergence_score,
    }
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update(b"cross_system_evidence:")
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


# ── Independence Calculation Helpers ─────────────────────────────────────────

# Penalty factor applied when two systems share derivative roots.
# Each shared root reduces the pairwise independence by this amount.
_SHARED_ROOT_PENALTY: float = 0.3

# Maximum penalty cap — independence can never drop below this floor
# for a pair, preventing total erasure of independence.
_MIN_PAIR_INDEPENDENCE: float = 0.1


def compute_pairwise_independence(
    provenance_a: EvidenceProvenance,
    provenance_b: EvidenceProvenance,
) -> float:
    """Compute independence between two evidence provenances.

    Systems sharing derivative roots receive a penalty to their
    pairwise independence score.  Systems with no shared roots
    achieve full independence (1.0).

    The penalty is:
        1.0 - (penalty_per_root * shared_root_count)
    clamped to [_MIN_PAIR_INDEPENDENCE, 1.0].

    Args:
        provenance_a: Provenance of the first system's evidence.
        provenance_b: Provenance of the second system's evidence.

    Returns:
        A float in [_MIN_PAIR_INDEPENDENCE, 1.0] representing how
        independent the two evidence sources are.
    """
    if provenance_a.system_type is provenance_b.system_type:
        return _MIN_PAIR_INDEPENDENCE

    shared = shared_derivative_roots(
        provenance_a.system_type,
        provenance_b.system_type,
    )
    num_shared_roots = len(shared)

    if num_shared_roots == 0:
        return 1.0

    penalty = _SHARED_ROOT_PENALTY * num_shared_roots
    score = max(_MIN_PAIR_INDEPENDENCE, 1.0 - penalty)
    return score


def compute_independence_score(
    provenances: tuple[EvidenceProvenance, ...],
) -> float:
    """Compute an aggregate independence score for a set of evidence provenances.

    The independence score measures how truly independent the evidence
    sources are from each other.  High scores indicate genuinely
    independent systems; low scores indicate systems with shared roots
    that may produce false convergence.

    Algorithm:
        1. For each unique pair (i < j), compute pairwise independence.
        2. Average all pairwise scores.
        3. If only one provenance exists, return its confidence_weight
           (a single system has no cross-system independence concern).

    Args:
        provenances: Tuple of EvidenceProvenance objects.

    Returns:
        A float in [0.0, 1.0] representing aggregate independence.
    """
    if not provenances:
        return 0.0

    if len(provenances) == 1:
        return provenances[0].confidence_weight

    pairwise_scores: list[float] = []
    for i in range(len(provenances)):
        for j in range(i + 1, len(provenances)):
            score = compute_pairwise_independence(
                provenances[i],
                provenances[j],
            )
            pairwise_scores.append(score)

    if not pairwise_scores:
        return 1.0

    return sum(pairwise_scores) / len(pairwise_scores)


def compute_convergence_score(
    assessments: dict[str, SystemAssessment],
) -> float:
    """Compute a convergence score across system assessments.

    Convergence measures the agreement between systems on the same
    outcome.  Systems that agree on outcome and timing contribute to
    higher convergence; disagreement reduces it.

    Args:
        assessments: Mapping of system_type value strings to
            SystemAssessment objects.

    Returns:
        A float in [0.0, 1.0] representing cross-system convergence.
    """
    if not assessments:
        return 0.0

    if len(assessments) == 1:
        # Single system: convergence is based on assessment status only
        assessment = next(iter(assessments.values()))
        return _status_to_score(assessment.assessment_status)

    # Compute pairwise agreement across all unique pairs
    items = list(assessments.values())
    agreement_scores: list[float] = []

    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            pair_score = _pairwise_agreement(items[i], items[j])
            agreement_scores.append(pair_score)

    if not agreement_scores:
        return 0.0

    return sum(agreement_scores) / len(agreement_scores)


def _pairwise_agreement(
    a: SystemAssessment,
    b: SystemAssessment,
) -> float:
    """Compute agreement between two system assessments.

    Returns a score in [0.0, 1.0]:
    - 1.0 if both agree on outcome and timing
    - Lower if they disagree
    """
    outcome_match = a.outcome_taxonomy == b.outcome_taxonomy
    status_match = a.assessment_status == b.assessment_status
    timing_match = a.timing_status == b.timing_status

    # Weighted combination
    score = 0.0
    if outcome_match:
        score += 0.5
    if status_match:
        score += 0.3
    if timing_match:
        score += 0.2

    return score


_STATUS_SCORES: dict[str, float] = {
    "STRONGLY_SUPPORTED": 1.0,
    "SUPPORTED": 0.8,
    "WEAKLY_SUPPORTED": 0.5,
    "NEUTRAL": 0.3,
    "CONTRADICTED": 0.1,
    "STRONGLY_CONTRADICTED": 0.0,
}


def _status_to_score(status: str) -> float:
    """Convert an assessment status string to a numeric score."""
    return _STATUS_SCORES.get(status, 0.3)

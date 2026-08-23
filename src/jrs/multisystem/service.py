"""Multi-System Evidence Graph service.

Provides the IndependenceAnalyzer which calculates independence scores
for cross-system evidence to prevent false convergence.
"""

from __future__ import annotations

import hashlib
import json

from jrs.multisystem.errors import (
    ProvenanceError,
)
from jrs.multisystem.models import (
    CrossSystemEvidence,
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
    compute_convergence_score,
    shared_derivative_roots,
)


class IndependenceAnalyzer:
    """Analyzes independence between different astrological systems.

    Calculates independence scores (0.0 to 1.0) for evidence from
    multiple systems. Systems sharing derivative roots receive lower
    independence scores to prevent false convergence.
    """

    def __init__(
        self,
        *,
        self_reference_penalty: float = 0.5,
        shared_root_penalty_per_shared: float = 0.15,
        base_score: float = 1.0,
    ) -> None:
        self._self_reference_penalty = self_reference_penalty
        self._shared_root_penalty_per_shared = shared_root_penalty_per_shared
        self._base_score = base_score

    def calculate_pairwise_independence(
        self,
        provenance_a: EvidenceProvenance,
        provenance_b: EvidenceProvenance,
    ) -> float:
        """Calculate independence score between two system evidences.

        A self-reference (same SystemType) receives a heavy penalty.
        Shared derivative roots each reduce the score by the configured penalty.
        Score is clamped to [0.0, 1.0].
        """
        if provenance_a.system_type == provenance_b.system_type:
            return max(0.0, self._base_score - self._self_reference_penalty)

        # Use the module-level helper for shared roots
        shared = shared_derivative_roots(
            provenance_a.system_type,
            provenance_b.system_type,
        )
        num_shared = len(shared)

        # Each shared root reduces independence
        penalty = num_shared * self._shared_root_penalty_per_shared

        score = self._base_score - penalty
        return max(0.0, min(1.0, score))

    def calculate_collective_independence(
        self,
        provenances: list[EvidenceProvenance],
    ) -> float:
        """Calculate collective independence across multiple system evidences.

        The collective score is the average of all pairwise independence scores.
        If fewer than 2 provenances, returns the base score.
        """
        if len(provenances) < 2:
            if provenances:
                return provenances[0].confidence_weight
            return self._base_score

        pairwise_scores: list[float] = []
        for i in range(len(provenances)):
            for j in range(i + 1, len(provenances)):
                score = self.calculate_pairwise_independence(
                    provenances[i], provenances[j]
                )
                pairwise_scores.append(score)

        if not pairwise_scores:
            return self._base_score

        return sum(pairwise_scores) / len(pairwise_scores)

    def analyze_convergence(
        self,
        provenances: list[EvidenceProvenance],
        raw_convergence_score: float,
    ) -> tuple[float, float]:
        """Adjust a raw convergence score by system independence.

        Returns (adjusted_convergence, independence_score).
        High independence -> convergence is preserved.
        Low independence -> convergence is dampened.

        Args:
            provenances: Provenance of each contributing system.
            raw_convergence_score: The unadjusted convergence score [0.0, 1.0].

        Returns:
            Tuple of (adjusted_convergence_score, independence_score).
        """
        if not provenances:
            return (0.0, 0.0)

        independence = self.calculate_collective_independence(provenances)

        # Adjusted convergence = raw * independence
        adjusted = raw_convergence_score * independence

        return (adjusted, independence)

    def build_cross_system_evidence(
        self,
        event_cluster_id: str,
        provenances: dict[SystemType, EvidenceProvenance],
        assessments: dict[str, SystemAssessment],
    ) -> CrossSystemEvidence:
        """Build a CrossSystemEvidence from provenances and assessments.

        Args:
            event_cluster_id: ID of the event cluster being assessed.
            provenances: Provenance for each system.
            assessments: Assessment per system (keyed by system_type.value).

        Returns:
            CrossSystemEvidence with computed independence and convergence.
        """
        if not provenances:
            raise ProvenanceError("At least one provenance is required")

        prov_list = list(provenances.values())
        independence = self.calculate_collective_independence(prov_list)

        # Compute raw convergence from assessments
        raw_convergence = compute_convergence_score(assessments)
        adjusted_convergence = raw_convergence * independence

        # Build deterministic ID
        id_input = json.dumps(
            {
                "event_cluster_id": event_cluster_id,
                "systems": sorted(s.value for s in provenances),
                "independence": round(independence, 6),
                "convergence": round(adjusted_convergence, 6),
            },
            sort_keys=True,
        )
        deterministic_id = hashlib.sha256(id_input.encode()).hexdigest()

        return CrossSystemEvidence(
            event_cluster_id=event_cluster_id,
            system_assessments=assessments,
            independence_score=independence,
            convergence_score=adjusted_convergence,
            deterministic_id=deterministic_id,
        )

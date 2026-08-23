"""Cross-Domain Event Reasoning Engine — service.

Ingests CrossDomainAssessment objects (DomainAssessment + temporal window)
and identifies EventClusters where multiple domains show timing convergence
in overlapping temporal windows.

Output is deterministic facts (EventClusters), NOT final predictions.
"""

from __future__ import annotations

from jrs.convergence.models import (
    OverallEvidenceStrength,
    TimingStatus,
)

from .errors import InvalidClusterInputError
from .models import (
    CrossDomainAssessment,
    EventCluster,
    TemporalWindow,
    classify_event_type,
)


class CrossDomainService:
    """Cross-domain event reasoning engine.

    Identifies intersections where multiple domains show timing
    convergence in overlapping temporal windows.

    Usage::

        svc = CrossDomainService()
        clusters = svc.identify_clusters([
            CrossDomainAssessment(assessment=..., temporal_window=...),
            CrossDomainAssessment(assessment=..., temporal_window=...),
        ])
    """

    def __init__(
        self,
        min_overlap_score: float = 0.1,
        min_domains: int = 2,
    ) -> None:
        """Initialize the cross-domain service.

        Args:
            min_overlap_score: Minimum temporal overlap score for two
                windows to be considered overlapping.  Must be in [0, 1].
            min_domains: Minimum number of distinct domains required to
                form a cluster.
        """
        if not 0.0 <= min_overlap_score <= 1.0:
            raise InvalidClusterInputError(
                f"min_overlap_score must be in [0, 1], got {min_overlap_score}"
            )
        if min_domains < 1:
            raise InvalidClusterInputError(
                f"min_domains must be >= 1, got {min_domains}"
            )
        self._min_overlap_score = min_overlap_score
        self._min_domains = min_domains

    def identify_clusters(
        self,
        assessments: list[CrossDomainAssessment],
    ) -> list[EventCluster]:
        """Identify cross-domain event clusters from assessments.

        Groups assessments by temporal overlap.  Within each overlapping
        group, checks that the assessments are from different domains and
        have ACTIVE timing (CONVERGENT) with non-WEAK evidence.

        Args:
            assessments: List of CrossDomainAssessment objects.

        Returns:
            A list of EventCluster objects, one per overlapping group.
            Empty list if no qualifying clusters are found.

        Raises:
            InvalidClusterInputError: If assessments is not a list.
        """
        if not isinstance(assessments, list):
            raise InvalidClusterInputError("assessments must be a list")

        if len(assessments) < self._min_domains:
            return []

        # Filter to assessments with active timing and sufficient evidence
        active = [a for a in assessments if _is_active(a)]

        if len(active) < self._min_domains:
            return []

        # Find overlapping groups using union-find
        groups = _find_overlapping_groups(active, self._min_overlap_score)

        # Build EventClusters from qualifying groups
        clusters: list[EventCluster] = []
        for group in groups:
            if len(group) < self._min_domains:
                continue
            cluster = _build_cluster(group)
            if cluster is not None:
                clusters.append(cluster)

        return clusters

    @property
    def min_overlap_score(self) -> float:
        """Return the minimum overlap score threshold."""
        return self._min_overlap_score

    @property
    def min_domains(self) -> int:
        """Return the minimum domains threshold."""
        return self._min_domains


# ── Internal Helpers ─────────────────────────────────────────────────────────


def _is_active(assessment: CrossDomainAssessment) -> bool:
    """Check if an assessment is active (convergent timing, non-weak evidence)."""
    a = assessment.assessment
    return (
        a.timing_status is TimingStatus.CONVERGENT
        and a.overall_evidence_strength is not OverallEvidenceStrength.WEAK
    )


def _find_overlapping_groups(
    assessments: list[CrossDomainAssessment],
    min_overlap: float,
) -> list[list[CrossDomainAssessment]]:
    """Find groups of assessments with overlapping temporal windows.

    Uses union-find to transitively connect assessments whose windows
    overlap above the minimum threshold.
    """
    n = len(assessments)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[rx] = ry

    # Connect assessments with overlapping windows
    for i in range(n):
        for j in range(i + 1, n):
            w_i = assessments[i].temporal_window
            w_j = assessments[j].temporal_window
            if w_i.overlaps(w_j):
                score = w_i.overlap_score(w_j)
                if score >= min_overlap:
                    union(i, j)

    # Collect groups
    groups_map: dict[int, list[CrossDomainAssessment]] = {}
    for i in range(n):
        root = find(i)
        groups_map.setdefault(root, []).append(assessments[i])

    return list(groups_map.values())


def _build_cluster(
    group: list[CrossDomainAssessment],
) -> EventCluster | None:
    """Build an EventCluster from a group of overlapping assessments."""
    if not group:
        return None

    # Compute temporal window as the union of all assessment windows
    starts = [a.temporal_window.start_utc for a in group if a.temporal_window.start_utc]
    ends = [a.temporal_window.end_utc for a in group if a.temporal_window.end_utc]
    if not starts or not ends:
        return None

    cluster_window = TemporalWindow(
        start_utc=min(starts),
        end_utc=max(ends),
    )

    # Collect domain labels (only those with non-empty labels)
    domain_labels = tuple(
        a.domain_label for a in group if a.domain_label
    )

    # Need at least 2 distinct domain labels to form a cross-domain cluster
    unique_labels = frozenset(domain_labels)
    if len(unique_labels) < 2:
        return None

    # Aggregate evidence dimensions
    total_supporting = sum(
        a.assessment.dimensions.supporting_count for a in group
    )
    total_channels = sum(
        a.assessment.dimensions.independent_channels for a in group
    )
    total_contradictions = sum(
        a.assessment.dimensions.contradicting_count for a in group
    )

    # Compute temporal overlap score as the average pairwise overlap
    overlap_scores: list[float] = []
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            score = group[i].temporal_window.overlap_score(
                group[j].temporal_window
            )
            overlap_scores.append(score)

    avg_overlap = (
        sum(overlap_scores) / len(overlap_scores) if overlap_scores else 1.0
    )

    # Classify event type
    event_type = classify_event_type(domain_labels)

    return EventCluster(
        temporal_window=cluster_window,
        involved_domains=domain_labels,
        supporting_evidence_count=total_supporting,
        independent_channels_count=total_channels,
        contradictions_count=total_contradictions,
        temporal_overlap_score=avg_overlap,
        event_type=event_type,
    )

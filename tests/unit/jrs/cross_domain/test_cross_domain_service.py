"""Unit tests for CrossDomainService — cluster identification logic."""

from __future__ import annotations

import json

import pytest

from jrs.convergence.models import (
    AssessmentStatus,
    DomainAssessment,
    EvidenceDimensions,
    OverallEvidenceStrength,
    TimingStatus,
)
from jrs.cross_domain.errors import InvalidClusterInputError
from jrs.cross_domain.models import (
    CrossDomainAssessment,
    CrossDomainEventType,
    TemporalWindow,
)
from jrs.cross_domain.service import CrossDomainService

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_assessment(
    outcome: str = "MARRIAGE_FORMATION",
    timing: TimingStatus = TimingStatus.CONVERGENT,
    strength: OverallEvidenceStrength = OverallEvidenceStrength.STRONG,
    supporting: int = 3,
    independent: int = 2,
    contradicting: int = 0,
) -> DomainAssessment:
    """Build a DomainAssessment for testing."""
    return DomainAssessment(
        outcome_taxonomy=outcome,
        dimensions=EvidenceDimensions(
            supporting_count=supporting,
            independent_channels=independent,
            contradicting_count=contradicting,
        ),
        assessment_status=AssessmentStatus.SUPPORTED,
        timing_status=timing,
        overall_evidence_strength=strength,
    )


def _make_cross_assessment(
    outcome: str = "MARRIAGE_FORMATION",
    domain_label: str = "MARRIAGE",
    window_start: str = "2025-01-01",
    window_end: str = "2025-06-01",
    timing: TimingStatus = TimingStatus.CONVERGENT,
    strength: OverallEvidenceStrength = OverallEvidenceStrength.STRONG,
    supporting: int = 3,
    independent: int = 2,
    contradicting: int = 0,
) -> CrossDomainAssessment:
    """Build a CrossDomainAssessment for testing."""
    return CrossDomainAssessment(
        assessment=_make_assessment(
            outcome=outcome,
            timing=timing,
            strength=strength,
            supporting=supporting,
            independent=independent,
            contradicting=contradicting,
        ),
        temporal_window=TemporalWindow(start_utc=window_start, end_utc=window_end),
        domain_label=domain_label,
    )


# ── Initialization ───────────────────────────────────────────────────────────


class TestCrossDomainServiceInit:
    """Tests for CrossDomainService initialization."""

    def test_default_init(self) -> None:
        svc = CrossDomainService()
        assert svc.min_overlap_score == 0.1
        assert svc.min_domains == 2

    def test_custom_init(self) -> None:
        svc = CrossDomainService(min_overlap_score=0.3, min_domains=3)
        assert svc.min_overlap_score == 0.3
        assert svc.min_domains == 3

    def test_invalid_overlap_score_negative(self) -> None:
        with pytest.raises(InvalidClusterInputError, match="min_overlap_score"):
            CrossDomainService(min_overlap_score=-0.1)

    def test_invalid_overlap_score_above_one(self) -> None:
        with pytest.raises(InvalidClusterInputError, match="min_overlap_score"):
            CrossDomainService(min_overlap_score=1.5)

    def test_invalid_min_domains(self) -> None:
        with pytest.raises(InvalidClusterInputError, match="min_domains"):
            CrossDomainService(min_domains=0)


# ── Isolated Assessments ─────────────────────────────────────────────────────


class TestIsolatedAssessments:
    """Verify that isolated domain assessments remain isolated."""

    def test_single_assessment_no_cluster(self) -> None:
        """A single active assessment cannot form a cluster (min_domains=2)."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_empty_list(self) -> None:
        svc = CrossDomainService()
        assert svc.identify_clusters([]) == []

    def test_invalid_input_not_list(self) -> None:
        svc = CrossDomainService()
        with pytest.raises(InvalidClusterInputError, match="must be a list"):
            svc.identify_clusters("not a list")  # type: ignore[arg-type]

    def test_two_assessments_different_windows_no_overlap(self) -> None:
        """Two assessments from different domains but non-overlapping windows."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                window_start="2025-01-01",
                window_end="2025-03-01",
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                window_start="2025-06-01",
                window_end="2025-09-01",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_two_assessments_inactive_timing_no_cluster(self) -> None:
        """Two assessments with non-overlapping timing status remain isolated."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                timing=TimingStatus.INACTIVE,
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                timing=TimingStatus.INACTIVE,
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_two_assessments_weak_evidence_no_cluster(self) -> None:
        """Two assessments with weak evidence don't cluster."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                strength=OverallEvidenceStrength.WEAK,
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                strength=OverallEvidenceStrength.WEAK,
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_two_assessments_same_domain_no_cluster(self) -> None:
        """Two assessments from the same domain don't form a cluster."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                outcome="CAREER_ASCENT",
                window_start="2025-01-01",
                window_end="2025-06-01",
            ),
            _make_cross_assessment(
                domain_label="CAREER",
                outcome="CAREER_ASCENT",
                window_start="2025-01-01",
                window_end="2025-06-01",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        # Same domain labels → not enough distinct domains
        assert clusters == []


# ── Overlapping Assessments ──────────────────────────────────────────────────


class TestOverlappingAssessments:
    """Assessments with overlapping temporal windows correctly combine."""

    def test_two_domains_overlapping_windows(self) -> None:
        """Two active assessments from different domains with overlapping windows."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                window_start="2025-01-01",
                window_end="2025-06-01",
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                window_start="2025-03-01",
                window_end="2025-09-01",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        cluster = clusters[0]
        assert "CAREER" in cluster.involved_domains
        assert "WEALTH" in cluster.involved_domains
        assert cluster.temporal_overlap_score > 0.0
        assert cluster.supporting_evidence_count == 6  # 3 + 3
        assert cluster.independent_channels_count == 4  # 2 + 2

    def test_three_domains_overlapping(self) -> None:
        """Three active assessments from different domains, all overlapping."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                window_start="2025-01-01",
                window_end="2025-06-01",
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                window_start="2025-02-01",
                window_end="2025-07-01",
            ),
            _make_cross_assessment(
                domain_label="MARRIAGE",
                outcome="MARRIAGE_FORMATION",
                window_start="2025-03-01",
                window_end="2025-08-01",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        cluster = clusters[0]
        assert len(cluster.involved_domains) == 3
        assert set(cluster.involved_domains) == {"CAREER", "WEALTH", "MARRIAGE"}

    def test_cluster_temporal_window_union(self) -> None:
        """Cluster temporal window is the union of all assessment windows."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                window_start="2025-01-01",
                window_end="2025-06-01",
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                window_start="2025-03-01",
                window_end="2025-09-01",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        tw = clusters[0].temporal_window
        assert tw.start_utc == "2025-01-01"  # min of starts
        assert tw.end_utc == "2025-09-01"  # max of ends

    def test_cluster_has_deterministic_id(self) -> None:
        """Cluster gets a deterministic SHA-256 id."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        assert len(clusters[0].deterministic_id) == 64

    def test_cluster_contradictions_aggregated(self) -> None:
        """Contradictions from all assessments are summed."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                contradicting=2,
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                contradicting=1,
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        assert clusters[0].contradictions_count == 3

    def test_cluster_event_type_classified(self) -> None:
        """Cluster event type is classified from domain labels."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
            _make_cross_assessment(
                domain_label="MIGRATION",
                outcome="FOREIGN_SETTLEMENT",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        assert clusters[0].event_type == CrossDomainEventType.CAREER_RELOCATION


# ── Partial Overlap / Split Clusters ─────────────────────────────────────────


class TestSplitClusters:
    """Tests for multiple distinct clusters from the same assessment set."""

    def test_two_separate_clusters(self) -> None:
        """Four assessments forming two separate overlapping groups."""
        svc = CrossDomainService()
        assessments = [
            # Cluster 1: CAREER + WEALTH (overlap in Jan-Jun)
            _make_cross_assessment(
                domain_label="CAREER",
                window_start="2025-01-01",
                window_end="2025-06-01",
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                window_start="2025-03-01",
                window_end="2025-06-01",
            ),
            # Cluster 2: HEALTH + MARRIAGE (overlap in Jul-Dec)
            _make_cross_assessment(
                domain_label="HEALTH",
                outcome="HIGH_VITALITY",
                window_start="2025-07-01",
                window_end="2025-12-01",
            ),
            _make_cross_assessment(
                domain_label="MARRIAGE",
                outcome="MARRIAGE_FORMATION",
                window_start="2025-09-01",
                window_end="2025-12-01",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 2

        # Check that each cluster has 2 domains
        domain_sets = [set(c.involved_domains) for c in clusters]
        assert {"CAREER", "WEALTH"} in domain_sets
        assert {"HEALTH", "MARRIAGE"} in domain_sets

    def test_transitive_overlap(self) -> None:
        """Three assessments where A overlaps B, B overlaps C, but A doesn't overlap C.
        Union-find should transitively group all three."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                window_start="2025-01-01",
                window_end="2025-03-01",
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                window_start="2025-02-01",
                window_end="2025-05-01",
            ),
            _make_cross_assessment(
                domain_label="MARRIAGE",
                outcome="MARRIAGE_FORMATION",
                window_start="2025-04-01",
                window_end="2025-06-01",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        # All three should be in one cluster via transitive overlap
        assert len(clusters) == 1
        assert len(clusters[0].involved_domains) == 3


# ── Edge Cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge case tests for the cross-domain service."""

    def test_all_inactive_assessments(self) -> None:
        """All assessments inactive → no clusters."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                timing=TimingStatus.INACTIVE,
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                timing=TimingStatus.INACTIVE,
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_one_active_one_inactive(self) -> None:
        """One active, one inactive → no cluster (only 1 active)."""
        svc = CrossDomainService(min_domains=2)
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                timing=TimingStatus.INACTIVE,
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_empty_domain_labels(self) -> None:
        """Assessments with empty domain labels don't form clusters."""
        svc = CrossDomainService()
        assessments = [
            CrossDomainAssessment(
                assessment=_make_assessment(),
                temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
                domain_label="",
            ),
            CrossDomainAssessment(
                assessment=_make_assessment(outcome="WEALTH_ACCUMULATION"),
                temporal_window=TemporalWindow(start_utc="2025-03-01", end_utc="2025-09-01"),
                domain_label="",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_deterministic_output(self) -> None:
        """Same inputs produce identical clusters."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
            ),
        ]
        c1 = svc.identify_clusters(assessments)
        c2 = svc.identify_clusters(assessments)
        assert len(c1) == len(c2)
        assert c1[0].deterministic_id == c2[0].deterministic_id

    def test_cluster_to_dict_roundtrip(self) -> None:
        """Cluster serialization is valid JSON."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        d = clusters[0].to_dict()
        json_str = json.dumps(d, sort_keys=True)
        assert len(json_str) > 0

    def test_min_domains_three(self) -> None:
        """With min_domains=3, pairs don't form clusters."""
        svc = CrossDomainService(min_domains=3)
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

    def test_min_domains_three_with_three_assessments(self) -> None:
        """With min_domains=3, three overlapping assessments form a cluster."""
        svc = CrossDomainService(min_domains=3)
        assessments = [
            _make_cross_assessment(domain_label="CAREER"),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
            ),
            _make_cross_assessment(
                domain_label="HEALTH",
                outcome="HIGH_VITALITY",
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1
        assert len(clusters[0].involved_domains) == 3

    def test_moderate_evidence_included(self) -> None:
        """Assessments with MODERATE evidence are included."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                strength=OverallEvidenceStrength.MODERATE,
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                strength=OverallEvidenceStrength.MODERATE,
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert len(clusters) == 1

    def test_divergent_timing_excluded(self) -> None:
        """Assessments with DIVERGENT timing are excluded."""
        svc = CrossDomainService()
        assessments = [
            _make_cross_assessment(
                domain_label="CAREER",
                timing=TimingStatus.DIVERGENT,
            ),
            _make_cross_assessment(
                domain_label="WEALTH",
                outcome="WEALTH_ACCUMULATION",
                timing=TimingStatus.DIVERGENT,
            ),
        ]
        clusters = svc.identify_clusters(assessments)
        assert clusters == []

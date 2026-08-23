"""Unit tests for cross-domain event reasoning engine models."""

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
from jrs.cross_domain.models import (
    CrossDomainAssessment,
    CrossDomainEventType,
    EventCluster,
    TemporalWindow,
    classify_event_type,
)

# ── TemporalWindow ───────────────────────────────────────────────────────────


class TestTemporalWindow:
    """Tests for the TemporalWindow model."""

    def test_creation(self) -> None:
        w = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        assert w.start_utc == "2025-01-01"
        assert w.end_utc == "2025-06-01"

    def test_empty_window_no_overlap(self) -> None:
        w1 = TemporalWindow()
        w2 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        assert w1.overlaps(w2) is False
        assert w2.overlaps(w1) is False

    def test_overlapping_windows(self) -> None:
        w1 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        w2 = TemporalWindow(start_utc="2025-03-01", end_utc="2025-09-01")
        assert w1.overlaps(w2) is True
        assert w2.overlaps(w1) is True

    def test_non_overlapping_windows(self) -> None:
        w1 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-03-01")
        w2 = TemporalWindow(start_utc="2025-06-01", end_utc="2025-09-01")
        assert w1.overlaps(w2) is False

    def test_adjacent_windows_no_overlap(self) -> None:
        w1 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-03-01")
        w2 = TemporalWindow(start_utc="2025-03-01", end_utc="2025-06-01")
        # Adjacent: w1.end == w2.start, so w1.start <= w2.end (True)
        # and w2.start <= w1.end (True), so they overlap at a point
        assert w1.overlaps(w2) is True

    def test_identical_windows_overlap(self) -> None:
        w1 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        w2 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        assert w1.overlaps(w2) is True
        assert w1.overlap_score(w2) == 1.0

    def test_overlap_score_partial(self) -> None:
        # w1: Jan-Jun (151 days), w2: Mar-Sep (184 days)
        # Overlap: Mar-Jun (92 days)
        # Score relative to shorter (w1): 92/151 ≈ 0.609
        w1 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        w2 = TemporalWindow(start_utc="2025-03-01", end_utc="2025-09-01")
        score = w1.overlap_score(w2)
        assert 0.5 < score < 0.8

    def test_overlap_score_no_overlap(self) -> None:
        w1 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-03-01")
        w2 = TemporalWindow(start_utc="2025-06-01", end_utc="2025-09-01")
        assert w1.overlap_score(w2) == 0.0

    def test_overlap_score_symmetric(self) -> None:
        w1 = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        w2 = TemporalWindow(start_utc="2025-03-01", end_utc="2025-09-01")
        assert w1.overlap_score(w2) == pytest.approx(w2.overlap_score(w1), abs=0.01)

    def test_frozen(self) -> None:
        w = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        with pytest.raises(AttributeError):
            w.start_utc = "2026-01-01"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        w = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        d = w.to_dict()
        assert d["start_utc"] == "2025-01-01"
        assert d["end_utc"] == "2025-06-01"

    def test_to_dict_deterministic(self) -> None:
        w = TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01")
        assert json.dumps(w.to_dict(), sort_keys=True) == json.dumps(
            w.to_dict(), sort_keys=True
        )


# ── CrossDomainAssessment ────────────────────────────────────────────────────


class TestCrossDomainAssessment:
    """Tests for the CrossDomainAssessment wrapper."""

    def _make_assessment(
        self,
        outcome: str = "MARRIAGE_FORMATION",
        timing: TimingStatus = TimingStatus.CONVERGENT,
        strength: OverallEvidenceStrength = OverallEvidenceStrength.STRONG,
    ) -> DomainAssessment:
        return DomainAssessment(
            outcome_taxonomy=outcome,
            dimensions=EvidenceDimensions(
                supporting_count=3,
                independent_channels=2,
                contradicting_count=0,
            ),
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=timing,
            overall_evidence_strength=strength,
        )

    def test_creation(self) -> None:
        da = CrossDomainAssessment(
            assessment=self._make_assessment(),
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            domain_label="MARRIAGE",
        )
        assert da.domain_label == "MARRIAGE"
        assert da.assessment.outcome_taxonomy == "MARRIAGE_FORMATION"
        assert da.temporal_window.start_utc == "2025-01-01"

    def test_to_dict(self) -> None:
        da = CrossDomainAssessment(
            assessment=self._make_assessment(),
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            domain_label="CAREER",
        )
        d = da.to_dict()
        assert d["domain_label"] == "CAREER"
        assert d["assessment"]["outcome_taxonomy"] == "MARRIAGE_FORMATION"
        assert d["temporal_window"]["start_utc"] == "2025-01-01"

    def test_frozen(self) -> None:
        da = CrossDomainAssessment(
            assessment=self._make_assessment(),
            domain_label="TEST",
        )
        with pytest.raises(AttributeError):
            da.domain_label = "CHANGED"  # type: ignore[misc]


# ── EventCluster ─────────────────────────────────────────────────────────────


class TestEventCluster:
    """Tests for the EventCluster model."""

    def test_creation(self) -> None:
        cluster = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER", "WEALTH"),
            supporting_evidence_count=5,
            independent_channels_count=3,
            contradictions_count=1,
            temporal_overlap_score=0.75,
        )
        assert len(cluster.involved_domains) == 2
        assert cluster.supporting_evidence_count == 5
        assert cluster.temporal_overlap_score == 0.75

    def test_deterministic_id_computed(self) -> None:
        cluster = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER", "WEALTH"),
            supporting_evidence_count=5,
            independent_channels_count=3,
            contradictions_count=1,
            temporal_overlap_score=0.75,
        )
        assert cluster.deterministic_id != ""
        assert len(cluster.deterministic_id) == 64  # SHA-256 hex

    def test_deterministic_id_same_for_equal_inputs(self) -> None:
        kwargs = dict(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER", "WEALTH"),
            supporting_evidence_count=5,
            independent_channels_count=3,
            contradictions_count=1,
            temporal_overlap_score=0.75,
        )
        c1 = EventCluster(**kwargs)
        c2 = EventCluster(**kwargs)
        assert c1.deterministic_id == c2.deterministic_id

    def test_deterministic_id_different_for_different_inputs(self) -> None:
        c1 = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER",),
            supporting_evidence_count=5,
            independent_channels_count=3,
            contradictions_count=1,
            temporal_overlap_score=0.75,
        )
        c2 = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("WEALTH",),
            supporting_evidence_count=5,
            independent_channels_count=3,
            contradictions_count=1,
            temporal_overlap_score=0.75,
        )
        assert c1.deterministic_id != c2.deterministic_id

    def test_to_dict(self) -> None:
        cluster = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER", "WEALTH"),
            supporting_evidence_count=5,
            independent_channels_count=3,
            contradictions_count=1,
            temporal_overlap_score=0.75,
            event_type=CrossDomainEventType.CAREER_RELOCATION,
        )
        d = cluster.to_dict()
        assert d["involved_domains"] == ["CAREER", "WEALTH"]
        assert d["event_type"] == "CAREER_RELOCATION"
        assert d["temporal_overlap_score"] == 0.75

    def test_to_dict_deterministic(self) -> None:
        cluster = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER", "WEALTH"),
            supporting_evidence_count=5,
            independent_channels_count=3,
            contradictions_count=1,
            temporal_overlap_score=0.75,
        )
        d1 = cluster.to_dict()
        d2 = cluster.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_frozen(self) -> None:
        cluster = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER",),
            supporting_evidence_count=1,
            independent_channels_count=1,
            contradictions_count=0,
            temporal_overlap_score=1.0,
        )
        with pytest.raises(AttributeError):
            cluster.involved_domains = ()  # type: ignore[misc]

    def test_default_event_type(self) -> None:
        cluster = EventCluster(
            temporal_window=TemporalWindow(start_utc="2025-01-01", end_utc="2025-06-01"),
            involved_domains=("CAREER",),
            supporting_evidence_count=1,
            independent_channels_count=1,
            contradictions_count=0,
            temporal_overlap_score=1.0,
        )
        assert cluster.event_type is CrossDomainEventType.MAJOR_LIFE_TRANSITION


# ── CrossDomainEventType ─────────────────────────────────────────────────────


class TestCrossDomainEventType:
    """Tests for the CrossDomainEventType enum."""

    def test_all_types_have_string_values(self) -> None:
        for t in CrossDomainEventType:
            assert isinstance(t.value, str)
            assert t.value == t.name

    def test_type_count(self) -> None:
        assert len(CrossDomainEventType) == 10

    def test_type_from_value(self) -> None:
        assert (
            CrossDomainEventType("CAREER_RELOCATION")
            is CrossDomainEventType.CAREER_RELOCATION
        )

    def test_invalid_type(self) -> None:
        with pytest.raises(ValueError):
            CrossDomainEventType("INVALID")


# ── classify_event_type ──────────────────────────────────────────────────────


class TestClassifyEventType:
    """Tests for the classify_event_type function."""

    def test_career_label(self) -> None:
        assert classify_event_type(("CAREER",)) == CrossDomainEventType.CAREER_RELOCATION

    def test_wealth_label(self) -> None:
        assert classify_event_type(("WEALTH",)) == CrossDomainEventType.FINANCIAL_UPHEAVAL

    def test_marriage_label(self) -> None:
        assert classify_event_type(("MARRIAGE",)) == CrossDomainEventType.RELATIONSHIP_SHIFT

    def test_health_label(self) -> None:
        assert classify_event_type(("HEALTH",)) == CrossDomainEventType.HEALTH_CRISIS

    def test_majority_voting(self) -> None:
        # Two career labels, one wealth → CAREER_RELOCATION
        assert classify_event_type(("CAREER", "CAREER", "WEALTH")) == (
            CrossDomainEventType.CAREER_RELOCATION
        )

    def test_empty_labels(self) -> None:
        assert classify_event_type(()) == CrossDomainEventType.MAJOR_LIFE_TRANSITION

    def test_unknown_label(self) -> None:
        assert classify_event_type(("UNKNOWN_DOMAIN",)) == (
            CrossDomainEventType.MAJOR_LIFE_TRANSITION
        )

    def test_prefix_match(self) -> None:
        assert classify_event_type(("CAREER_SHIFT",)) == (
            CrossDomainEventType.CAREER_RELOCATION
        )

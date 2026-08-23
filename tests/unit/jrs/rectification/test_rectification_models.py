"""Unit tests for JRS-064 Rectification Integration models."""

from __future__ import annotations

import pytest

from jrs.rectification.models import (
    AdjustmentDirection,
    AdjustmentProposal,
    EventMatch,
    KnownEvent,
    MatchQuality,
    RectificationResult,
    classify_match_quality,
    compute_assessment_mismatch,
    compute_timing_mismatch,
)

# ── KnownEvent Tests ─────────────────────────────────────────────────────────


class TestKnownEvent:
    def test_creation(self) -> None:
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        assert ke.event_description == "Marriage"
        assert ke.domain_label == "MARRIAGE"
        assert ke.expected_outcome == "MARRIAGE_FORMATION"
        assert ke.expected_assessment_status == "SUPPORTED"
        assert ke.expected_timing_status == "CONVERGENT"

    def test_to_dict(self) -> None:
        ke = KnownEvent(
            event_description="Promotion",
            domain_label="CAREER",
            expected_outcome="CAREER_ADVANCEMENT",
            expected_assessment_status="STRONGLY_SUPPORTED",
            expected_timing_status="CONVERGENT",
        )
        d = ke.to_dict()
        assert d["event_description"] == "Promotion"
        assert d["domain_label"] == "CAREER"
        assert d["expected_outcome"] == "CAREER_ADVANCEMENT"
        assert d["expected_assessment_status"] == "STRONGLY_SUPPORTED"
        assert d["expected_timing_status"] == "CONVERGENT"

    def test_frozen(self) -> None:
        ke = KnownEvent(
            event_description="X",
            domain_label="Y",
            expected_outcome="Z",
            expected_assessment_status="W",
        )
        with pytest.raises(AttributeError):
            ke.event_description = "Changed"  # type: ignore[misc]


# ── EventMatch Tests ─────────────────────────────────────────────────────────


class TestEventMatch:
    def test_creation(self) -> None:
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        em = EventMatch(
            known_event=ke,
            candidate_outcome="MARRIAGE_FORMATION",
            candidate_assessment_status="SUPPORTED",
            candidate_timing_status="CONVERGENT",
            match_quality=MatchQuality.EXACT_MATCH,
            mismatch_score=0.0,
        )
        assert em.known_event is ke
        assert em.match_quality is MatchQuality.EXACT_MATCH
        assert em.mismatch_score == 0.0

    def test_to_dict(self) -> None:
        ke = KnownEvent(
            event_description="X",
            domain_label="Y",
            expected_outcome="Z",
            expected_assessment_status="W",
        )
        em = EventMatch(
            known_event=ke,
            candidate_outcome="Z",
            candidate_assessment_status="W",
            candidate_timing_status="CONVERGENT",
            match_quality=MatchQuality.STRONG_MATCH,
            mismatch_score=0.1,
        )
        d = em.to_dict()
        assert d["match_quality"] == "STRONG_MATCH"
        assert d["mismatch_score"] == 0.1
        assert d["known_event"]["domain_label"] == "Y"


# ── MatchQuality Enum Tests ─────────────────────────────────────────────────


class TestMatchQuality:
    def test_has_5_values(self) -> None:
        assert len(MatchQuality) == 5

    def test_all_values(self) -> None:
        expected = {
            "EXACT_MATCH",
            "STRONG_MATCH",
            "PARTIAL_MATCH",
            "WEAK_MATCH",
            "NO_MATCH",
        }
        assert {m.value for m in MatchQuality} == expected


# ── AdjustmentDirection Enum Tests ───────────────────────────────────────────


class TestAdjustmentDirection:
    def test_has_3_values(self) -> None:
        assert len(AdjustmentDirection) == 3

    def test_all_values(self) -> None:
        expected = {"EARLIER", "LATER", "NO_CHANGE"}
        assert {d.value for d in AdjustmentDirection} == expected


# ── RectificationResult Tests ────────────────────────────────────────────────


class TestRectificationResult:
    def test_creation(self) -> None:
        rr = RectificationResult(
            candidate_time="2000-01-01T12:00:00Z",
            mismatch_score=0.2,
            suggested_adjustment_minutes=10.0,
        )
        assert rr.candidate_time == "2000-01-01T12:00:00Z"
        assert rr.mismatch_score == 0.2
        assert rr.suggested_adjustment_minutes == 10.0
        assert rr.event_matches == ()
        assert rr.supporting_evidence_ids == ()
        assert rr.contradicting_evidence_ids == ()

    def test_deterministic_id_computed(self) -> None:
        rr1 = RectificationResult(
            candidate_time="2000-01-01T12:00:00Z",
            mismatch_score=0.2,
            suggested_adjustment_minutes=10.0,
        )
        rr2 = RectificationResult(
            candidate_time="2000-01-01T12:00:00Z",
            mismatch_score=0.2,
            suggested_adjustment_minutes=10.0,
        )
        assert rr1.deterministic_id != ""
        assert rr1.deterministic_id == rr2.deterministic_id

    def test_different_inputs_different_hash(self) -> None:
        rr1 = RectificationResult(
            candidate_time="2000-01-01T12:00:00Z",
            mismatch_score=0.2,
            suggested_adjustment_minutes=10.0,
        )
        rr2 = RectificationResult(
            candidate_time="2000-01-01T13:00:00Z",
            mismatch_score=0.2,
            suggested_adjustment_minutes=10.0,
        )
        assert rr1.deterministic_id != rr2.deterministic_id

    def test_to_dict(self) -> None:
        rr = RectificationResult(
            candidate_time="2000-01-01T12:00:00Z",
            mismatch_score=0.5,
            suggested_adjustment_minutes=15.0,
            supporting_evidence_ids=("MARRIAGE:MARRIAGE_FORMATION",),
            contradicting_evidence_ids=("CAREER:CAREER_ADVANCEMENT",),
        )
        d = rr.to_dict()
        assert d["candidate_time"] == "2000-01-01T12:00:00Z"
        assert d["mismatch_score"] == 0.5
        assert d["suggested_adjustment_minutes"] == 15.0
        assert d["supporting_evidence_ids"] == ["MARRIAGE:MARRIAGE_FORMATION"]
        assert d["contradicting_evidence_ids"] == ["CAREER:CAREER_ADVANCEMENT"]
        assert "deterministic_id" in d

    def test_with_event_matches(self) -> None:
        ke = KnownEvent(
            event_description="X",
            domain_label="Y",
            expected_outcome="Z",
            expected_assessment_status="W",
        )
        em = EventMatch(
            known_event=ke,
            candidate_outcome="Z",
            candidate_assessment_status="W",
            candidate_timing_status="CONVERGENT",
            match_quality=MatchQuality.EXACT_MATCH,
            mismatch_score=0.0,
        )
        rr = RectificationResult(
            candidate_time="2000-01-01T12:00:00Z",
            mismatch_score=0.0,
            suggested_adjustment_minutes=0.0,
            event_matches=(em,),
        )
        d = rr.to_dict()
        assert len(d["event_matches"]) == 1
        assert d["event_matches"][0]["match_quality"] == "EXACT_MATCH"

    def test_frozen(self) -> None:
        rr = RectificationResult(
            candidate_time="2000-01-01T12:00:00Z",
            mismatch_score=0.0,
            suggested_adjustment_minutes=0.0,
        )
        with pytest.raises(AttributeError):
            rr.mismatch_score = 0.5  # type: ignore[misc]


# ── AdjustmentProposal Tests ─────────────────────────────────────────────────


class TestAdjustmentProposal:
    def test_creation(self) -> None:
        ap = AdjustmentProposal(
            offset_minutes=15.0,
            direction=AdjustmentDirection.LATER,
            confidence=0.8,
            reason="JRE-021 TRANSIT_TO_ASCENDANT method",
            method="TRANSIT_TO_ASCENDANT",
        )
        assert ap.offset_minutes == 15.0
        assert ap.direction is AdjustmentDirection.LATER
        assert ap.confidence == 0.8
        assert ap.method == "TRANSIT_TO_ASCENDANT"

    def test_to_dict(self) -> None:
        ap = AdjustmentProposal(
            offset_minutes=30.0,
            direction=AdjustmentDirection.EARLIER,
            confidence=0.6,
            reason="Scan result",
            method="SCAN",
        )
        d = ap.to_dict()
        assert d["offset_minutes"] == 30.0
        assert d["direction"] == "EARLIER"
        assert d["confidence"] == 0.6
        assert d["method"] == "SCAN"


# ── Scoring Helper Tests ─────────────────────────────────────────────────────


class TestComputeAssessmentMismatch:
    def test_same_status(self) -> None:
        assert compute_assessment_mismatch("SUPPORTED", "SUPPORTED") == 0.0

    def test_opposite_statuses(self) -> None:
        score = compute_assessment_mismatch(
            "STRONGLY_SUPPORTED", "STRONGLY_CONTRADICTED"
        )
        assert score == pytest.approx(1.0)

    def test_partial_mismatch(self) -> None:
        score = compute_assessment_mismatch("SUPPORTED", "NEUTRAL")
        assert 0.0 < score < 1.0

    def test_unknown_status(self) -> None:
        score = compute_assessment_mismatch("UNKNOWN", "SUPPORTED")
        assert 0.0 <= score <= 1.0


class TestComputeTimingMismatch:
    def test_same_timing(self) -> None:
        assert compute_timing_mismatch("CONVERGENT", "CONVERGENT") == 0.0

    def test_opposite_timing(self) -> None:
        score = compute_timing_mismatch("CONVERGENT", "INACTIVE")
        assert score == pytest.approx(1.0)

    def test_partial_timing(self) -> None:
        score = compute_timing_mismatch("CONVERGENT", "DIVERGENT")
        assert 0.0 < score < 1.0

    def test_unknown_timing(self) -> None:
        score = compute_timing_mismatch("UNKNOWN", "CONVERGENT")
        assert score >= 0.0


class TestClassifyMatchQuality:
    def test_exact_match(self) -> None:
        assert classify_match_quality(0.0) is MatchQuality.EXACT_MATCH

    def test_strong_match(self) -> None:
        assert classify_match_quality(0.1) is MatchQuality.STRONG_MATCH

    def test_partial_match(self) -> None:
        assert classify_match_quality(0.3) is MatchQuality.PARTIAL_MATCH

    def test_weak_match(self) -> None:
        assert classify_match_quality(0.5) is MatchQuality.WEAK_MATCH

    def test_no_match(self) -> None:
        assert classify_match_quality(0.9) is MatchQuality.NO_MATCH

    def test_boundary_strong(self) -> None:
        assert classify_match_quality(0.15) is MatchQuality.STRONG_MATCH

    def test_boundary_partial(self) -> None:
        assert classify_match_quality(0.40) is MatchQuality.PARTIAL_MATCH

    def test_boundary_weak(self) -> None:
        assert classify_match_quality(0.70) is MatchQuality.WEAK_MATCH

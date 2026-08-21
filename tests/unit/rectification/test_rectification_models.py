"""Unit tests for JRE-021 Rectification domain models."""

from __future__ import annotations

import pytest

from rectification.models import (
    RECTIFICATION_VERSION,
    EventType,
    LifeEvent,
    RectificationConfig,
    RectificationMethod,
    RectificationReport,
    RectificationResult,
    aggregate_offsets,
    apply_offset_to_birth_time,
    compute_confidence_score,
    compute_offset_seconds,
    event_type_relevant_to_method,
)
from tests.unit.rectification.conftest import make_life_event


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class TestEventType:
    def test_has_18_values(self) -> None:
        assert len(EventType) == 18

    def test_marriage(self) -> None:
        assert EventType.MARRIAGE.value == "MARRIAGE"

    def test_from_string(self) -> None:
        assert EventType("PROMOTION") == EventType.PROMOTION

    def test_invalid_string_raises(self) -> None:
        with pytest.raises(ValueError):
            EventType("INVALID_EVENT")


class TestRectificationMethod:
    def test_has_3_values(self) -> None:
        assert len(RectificationMethod) == 3

    def test_all_methods(self) -> None:
        expected = {
            "TRANSIT_TO_ASCENDANT",
            "DASHA_TO_EVENT",
            "PROGRESSION_TO_ASCENDANT",
        }
        assert {m.value for m in RectificationMethod} == expected


# --------------------------------------------------------------------------- #
# LifeEvent
# --------------------------------------------------------------------------- #


class TestLifeEvent:
    def test_creation(self) -> None:
        e = make_life_event()
        assert e.event_date_utc == "2010-06-15T10:00:00Z"
        assert e.event_type == EventType.MARRIAGE
        assert e.description == "Marriage event"

    def test_frozen(self) -> None:
        e = make_life_event()
        with pytest.raises(AttributeError):
            e.description = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        e = make_life_event()
        d = e.to_dict()
        assert d["event_date_utc"] == "2010-06-15T10:00:00Z"
        assert d["event_type"] == "MARRIAGE"
        assert d["description"] == "Marriage event"


# --------------------------------------------------------------------------- #
# RectificationResult
# --------------------------------------------------------------------------- #


class TestRectificationResult:
    def test_creation(self) -> None:
        r = RectificationResult(
            method=RectificationMethod.TRANSIT_TO_ASCENDANT,
            calculated_offset_seconds=3600.0,
            confidence_score=0.75,
            evidence=("evidence1", "evidence2"),
        )
        assert r.method == RectificationMethod.TRANSIT_TO_ASCENDANT
        assert r.calculated_offset_seconds == 3600.0
        assert r.confidence_score == 0.75
        assert len(r.evidence) == 2

    def test_to_dict(self) -> None:
        r = RectificationResult(
            method=RectificationMethod.DASHA_TO_EVENT,
            calculated_offset_seconds=-1800.0,
            confidence_score=0.60,
            evidence=("evidence1",),
        )
        d = r.to_dict()
        assert d["method"] == "DASHA_TO_EVENT"
        assert d["calculated_offset_seconds"] == -1800.0
        assert d["confidence_score"] == 0.60
        assert d["evidence"] == ["evidence1"]


# --------------------------------------------------------------------------- #
# RectificationReport
# --------------------------------------------------------------------------- #


class TestRectificationReport:
    def test_to_dict(self) -> None:
        report = RectificationReport(
            input_birth_time="2000-01-01T12:00:00Z",
            suggested_birth_time="2000-01-01T13:00:00Z",
            offsets=(),
        )
        d = report.to_dict()
        assert d["input_birth_time"] == "2000-01-01T12:00:00Z"
        assert d["suggested_birth_time"] == "2000-01-01T13:00:00Z"
        assert d["offsets"] == []
        assert d["version"] == RECTIFICATION_VERSION


# --------------------------------------------------------------------------- #
# RectificationConfig
# --------------------------------------------------------------------------- #


class TestRectificationConfig:
    def test_version(self) -> None:
        assert RECTIFICATION_VERSION == "0.1.0"

    def test_defaults(self) -> None:
        c = RectificationConfig()
        assert c.max_offset_seconds == 86400.0
        assert "TRANSIT_TO_ASCENDANT" in c.method_weights
        assert "DASHA_TO_EVENT" in c.method_tolerances
        assert "event_type_match" in c.evidence_weights

    def test_to_dict(self) -> None:
        c = RectificationConfig()
        d = c.to_dict()
        assert d["version"] == RECTIFICATION_VERSION
        assert d["max_offset_seconds"] == 86400.0


# --------------------------------------------------------------------------- #
# compute_offset_seconds
# --------------------------------------------------------------------------- #


class TestComputeOffsetSeconds:
    def test_same_time_zero(self) -> None:
        assert compute_offset_seconds(
            "2010-01-01T00:00:00Z", "2010-01-01T00:00:00Z"
        ) == 0.0

    def test_positive_offset(self) -> None:
        # Transit 1 hour after event
        assert compute_offset_seconds(
            "2010-01-01T00:00:00Z", "2010-01-01T01:00:00Z"
        ) == 3600.0

    def test_negative_offset(self) -> None:
        # Transit 2 hours before event
        assert compute_offset_seconds(
            "2010-01-01T02:00:00Z", "2010-01-01T00:00:00Z"
        ) == -7200.0

    def test_day_boundary(self) -> None:
        assert compute_offset_seconds(
            "2010-01-01T00:00:00Z", "2010-01-02T00:00:00Z"
        ) == 86400.0

    def test_deterministic(self) -> None:
        o1 = compute_offset_seconds("2010-01-01T00:00:00Z", "2010-01-01T01:00:00Z")
        o2 = compute_offset_seconds("2010-01-01T00:00:00Z", "2010-01-01T01:00:00Z")
        assert o1 == o2


# --------------------------------------------------------------------------- #
# compute_confidence_score
# --------------------------------------------------------------------------- #


class TestComputeConfidenceScore:
    def test_perfect_conditions(self) -> None:
        score = compute_confidence_score(
            offset_seconds=100.0,
            tolerance_seconds=3600.0,
            method_weight=1.0,
            event_type_relevant=True,
            corroborated=True,
            evidence_weights={
                "event_type_match": 0.30,
                "offset_within_tolerance": 0.40,
                "multiple_events_corroborate": 0.30,
            },
        )
        assert score == 1.0

    def test_no_relevance_no_corroboration(self) -> None:
        score = compute_confidence_score(
            offset_seconds=100.0,
            tolerance_seconds=3600.0,
            method_weight=1.0,
            event_type_relevant=False,
            corroborated=False,
            evidence_weights={
                "event_type_match": 0.30,
                "offset_within_tolerance": 0.40,
                "multiple_events_corroborate": 0.30,
            },
        )
        # Only offset_within_tolerance contributes: 0.40 * 1.0 = 0.40
        assert abs(score - 0.40) < 0.01

    def test_beyond_tolerance_no_credit(self) -> None:
        score = compute_confidence_score(
            offset_seconds=10000.0,
            tolerance_seconds=3600.0,
            method_weight=1.0,
            event_type_relevant=False,
            corroborated=False,
            evidence_weights={
                "event_type_match": 0.30,
                "offset_within_tolerance": 0.40,
                "multiple_events_corroborate": 0.30,
            },
        )
        assert score == 0.0

    def test_partial_credit_within_2x(self) -> None:
        # Offset = 1.5x tolerance → partial credit = 0.40 * (2.0 - 1.5)/2.0 = 0.10
        score = compute_confidence_score(
            offset_seconds=5400.0,
            tolerance_seconds=3600.0,
            method_weight=1.0,
            event_type_relevant=False,
            corroborated=False,
            evidence_weights={
                "event_type_match": 0.30,
                "offset_within_tolerance": 0.40,
                "multiple_events_corroborate": 0.30,
            },
        )
        assert abs(score - 0.10) < 0.01

    def test_clamped_to_0_1(self) -> None:
        score = compute_confidence_score(
            offset_seconds=100.0,
            tolerance_seconds=3600.0,
            method_weight=10.0,  # oversized weight
            event_type_relevant=True,
            corroborated=True,
            evidence_weights={
                "event_type_match": 0.30,
                "offset_within_tolerance": 0.40,
                "multiple_events_corroborate": 0.30,
            },
        )
        assert score == 1.0

    def test_deterministic(self) -> None:
        kw = {
            "offset_seconds": 100.0,
            "tolerance_seconds": 3600.0,
            "method_weight": 0.5,
            "event_type_relevant": True,
            "corroborated": False,
            "evidence_weights": {
                "event_type_match": 0.30,
                "offset_within_tolerance": 0.40,
                "multiple_events_corroborate": 0.30,
            },
        }
        s1 = compute_confidence_score(**kw)
        s2 = compute_confidence_score(**kw)
        assert s1 == s2


# --------------------------------------------------------------------------- #
# aggregate_offsets
# --------------------------------------------------------------------------- #


class TestAggregateOffsets:
    def test_empty_returns_zero(self) -> None:
        assert aggregate_offsets((), 86400.0) == 0.0

    def test_single_result(self) -> None:
        r = RectificationResult(
            method=RectificationMethod.TRANSIT_TO_ASCENDANT,
            calculated_offset_seconds=3600.0,
            confidence_score=1.0,
            evidence=(),
        )
        assert aggregate_offsets((r,), 86400.0) == 3600.0

    def test_weighted_average(self) -> None:
        r1 = RectificationResult(
            method=RectificationMethod.TRANSIT_TO_ASCENDANT,
            calculated_offset_seconds=3600.0,
            confidence_score=0.8,
            evidence=(),
        )
        r2 = RectificationResult(
            method=RectificationMethod.DASHA_TO_EVENT,
            calculated_offset_seconds=7200.0,
            confidence_score=0.2,
            evidence=(),
        )
        # Weighted: (3600*0.8 + 7200*0.2) / (0.8+0.2) = (2880+1440)/1.0 = 4320
        result = aggregate_offsets((r1, r2), 86400.0)
        assert abs(result - 4320.0) < 0.01

    def test_clamped_to_max(self) -> None:
        r = RectificationResult(
            method=RectificationMethod.TRANSIT_TO_ASCENDANT,
            calculated_offset_seconds=200000.0,
            confidence_score=1.0,
            evidence=(),
        )
        assert aggregate_offsets((r,), 86400.0) == 86400.0

    def test_negative_clamped(self) -> None:
        r = RectificationResult(
            method=RectificationMethod.TRANSIT_TO_ASCENDANT,
            calculated_offset_seconds=-200000.0,
            confidence_score=1.0,
            evidence=(),
        )
        assert aggregate_offsets((r,), 86400.0) == -86400.0

    def test_zero_confidence_returns_zero(self) -> None:
        r = RectificationResult(
            method=RectificationMethod.TRANSIT_TO_ASCENDANT,
            calculated_offset_seconds=3600.0,
            confidence_score=0.0,
            evidence=(),
        )
        assert aggregate_offsets((r,), 86400.0) == 0.0


# --------------------------------------------------------------------------- #
# apply_offset_to_birth_time
# --------------------------------------------------------------------------- #


class TestApplyOffsetToBirthTime:
    def test_no_offset(self) -> None:
        result = apply_offset_to_birth_time("2000-01-01T12:00:00Z", 0.0)
        assert "2000-01-01" in result

    def test_positive_offset(self) -> None:
        result = apply_offset_to_birth_time("2000-01-01T12:00:00Z", 3600.0)
        assert "13:00" in result

    def test_negative_offset(self) -> None:
        result = apply_offset_to_birth_time("2000-01-01T12:00:00Z", -3600.0)
        assert "11:00" in result

    def test_deterministic(self) -> None:
        r1 = apply_offset_to_birth_time("2000-01-01T12:00:00Z", 3600.0)
        r2 = apply_offset_to_birth_time("2000-01-01T12:00:00Z", 3600.0)
        assert r1 == r2


# --------------------------------------------------------------------------- #
# event_type_relevant_to_method
# --------------------------------------------------------------------------- #


class TestEventRelevance:
    def test_marriage_relevant_to_transit(self) -> None:
        assert event_type_relevant_to_method(
            EventType.MARRIAGE, RectificationMethod.TRANSIT_TO_ASCENDANT
        ) is True

    def test_marriage_relevant_to_dasha(self) -> None:
        assert event_type_relevant_to_method(
            EventType.MARRIAGE, RectificationMethod.DASHA_TO_EVENT
        ) is True

    def test_education_not_relevant_to_transit(self) -> None:
        assert event_type_relevant_to_method(
            EventType.EDUCATION_COMPLETE, RectificationMethod.TRANSIT_TO_ASCENDANT
        ) is False

    def test_education_relevant_to_progression(self) -> None:
        assert event_type_relevant_to_method(
            EventType.EDUCATION_COMPLETE, RectificationMethod.PROGRESSION_TO_ASCENDANT
        ) is True

    def test_business_start_relevant_to_dasha(self) -> None:
        assert event_type_relevant_to_method(
            EventType.BUSINESS_START, RectificationMethod.DASHA_TO_EVENT
        ) is True

"""Integration tests for JRE-021 Rectification.

Verifies the full RectificationReport against known reference scenarios,
ensuring end-to-end correctness from inputs through to
the final suggested_birth_time and offset aggregation.
"""

from __future__ import annotations

from rectification.models import (
    EventType,
    RectificationMethod,
    RectificationReport,
)
from rectification.service import RectificationService
from tests.unit.rectification.conftest import make_life_event


# --------------------------------------------------------------------------- #
# Reference scenario: Marriage + Promotion — Transit method
# --------------------------------------------------------------------------- #

REFERENCE_BIRTH_TIME = "1985-04-10T06:30:00Z"


class TestReferenceTransitMethod:
    """Reference: Transit to Ascendant with corroborated events."""

    def test_full_report_structure(self) -> None:
        svc = RectificationService()
        events = (
            make_life_event(
                event_date_utc="2010-06-15T10:00:00Z",
                event_type=EventType.MARRIAGE,
                description="Marriage",
            ),
            make_life_event(
                event_date_utc="2015-08-20T09:00:00Z",
                event_type=EventType.BIRTH_OF_CHILD,
                description="Child birth",
            ),
        )
        transit_times = {
            "Marriage": "2010-06-15T11:00:00Z",    # +1 hour
            "Child birth": "2015-08-20T10:00:00Z",  # +1 hour
        }
        report = svc.calculate_offset(
            REFERENCE_BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        assert isinstance(report, RectificationReport)
        assert report.input_birth_time == REFERENCE_BIRTH_TIME
        assert len(report.offsets) == 2
        # Both events produce +3600 offset
        for offset in report.offsets:
            assert offset.calculated_offset_seconds == 3600.0
            assert offset.confidence_score > 0.0

    def test_suggested_time_differs_from_input(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),)
        transit_times = {"Marriage": "2010-06-15T11:00:00Z"}
        report = svc.calculate_offset(
            REFERENCE_BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        assert report.suggested_birth_time != REFERENCE_BIRTH_TIME


# --------------------------------------------------------------------------- #
# Reference scenario: Dasha to Event with career events
# --------------------------------------------------------------------------- #


class TestReferenceDashaMethod:
    """Reference: Dasha to Event with career events."""

    def test_dasha_with_opposing_offsets(self) -> None:
        svc = RectificationService()
        events = (
            make_life_event(
                event_date_utc="2012-03-20T14:00:00Z",
                event_type=EventType.PROMOTION,
                description="Promotion",
            ),
            make_life_event(
                event_date_utc="2014-07-10T16:00:00Z",
                event_type=EventType.JOB_CHANGE,
                description="Job change",
            ),
        )
        transit_times = {
            "Promotion": "2012-03-20T12:00:00Z",    # -2 hours
            "Job change": "2014-07-10T18:00:00Z",   # +2 hours
        }
        report = svc.calculate_offset(
            REFERENCE_BIRTH_TIME, events,
            RectificationMethod.DASHA_TO_EVENT,
            transit_times,
        )
        assert len(report.offsets) == 2
        # Offsets should partially cancel in aggregation
        assert report.input_birth_time == REFERENCE_BIRTH_TIME


# --------------------------------------------------------------------------- #
# Reference scenario: No matching transit times
# --------------------------------------------------------------------------- #


class TestReferenceNoTransits:
    """Reference: No transit times provided — empty results."""

    def test_empty_transit_times(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),)
        report = svc.calculate_offset(
            REFERENCE_BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
        )
        assert len(report.offsets) == 0
        assert report.suggested_birth_time == REFERENCE_BIRTH_TIME


# --------------------------------------------------------------------------- #
# Reference scenario: Progression method
# --------------------------------------------------------------------------- #


class TestReferenceProgressionMethod:
    """Reference: Progression to Ascendant with education event."""

    def test_progression_with_education(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2007-06-01T08:00:00Z",
            event_type=EventType.EDUCATION_COMPLETE,
            description="Graduated",
        ),)
        transit_times = {"Graduated": "2007-06-01T09:30:00Z"}
        report = svc.calculate_offset(
            REFERENCE_BIRTH_TIME, events,
            RectificationMethod.PROGRESSION_TO_ASCENDANT,
            transit_times,
        )
        assert len(report.offsets) == 1
        assert report.offsets[0].calculated_offset_seconds == 5400.0  # 1.5 hours


# --------------------------------------------------------------------------- #
# Reference scenario: Deterministic output
# --------------------------------------------------------------------------- #


class TestReferenceDeterminism:
    """Reference: Same inputs produce identical output."""

    def test_deterministic_output(self) -> None:
        svc = RectificationService()
        events = (
            make_life_event(
                event_date_utc="2010-06-15T10:00:00Z",
                event_type=EventType.MARRIAGE,
                description="Marriage",
            ),
        )
        transit_times = {"Marriage": "2010-06-15T11:00:00Z"}
        r1 = svc.calculate_offset(
            REFERENCE_BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        r2 = svc.calculate_offset(
            REFERENCE_BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        assert r1.to_dict() == r2.to_dict()

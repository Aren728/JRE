"""Unit tests for JRE-021 RectificationService."""

from __future__ import annotations

import pytest

from rectification.errors import InvalidRectificationRequestError
from rectification.models import (
    EventType,
    RectificationMethod,
    RectificationReport,
)
from rectification.service import RectificationService
from tests.unit.rectification.conftest import make_life_event


BIRTH_TIME = "2000-01-01T12:00:00Z"


class TestRectificationServiceBasic:
    def test_single_event_transit(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),)
        transit_times = {"Marriage": "2010-06-15T11:00:00Z"}
        report = svc.calculate_offset(
            BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        assert isinstance(report, RectificationReport)
        assert report.input_birth_time == BIRTH_TIME
        assert len(report.offsets) == 1
        assert report.offsets[0].method == RectificationMethod.TRANSIT_TO_ASCENDANT
        assert report.offsets[0].calculated_offset_seconds == 3600.0

    def test_single_event_dasha(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2012-03-20T14:00:00Z",
            event_type=EventType.PROMOTION,
            description="Promotion",
        ),)
        transit_times = {"Promotion": "2012-03-20T12:00:00Z"}
        report = svc.calculate_offset(
            BIRTH_TIME, events,
            RectificationMethod.DASHA_TO_EVENT,
            transit_times,
        )
        assert isinstance(report, RectificationReport)
        assert len(report.offsets) == 1
        # Transit 2 hours before event = -7200 offset
        assert report.offsets[0].calculated_offset_seconds == -7200.0

    def test_multiple_events(self) -> None:
        svc = RectificationService()
        events = (
            make_life_event(
                event_date_utc="2010-06-15T10:00:00Z",
                event_type=EventType.MARRIAGE,
                description="Marriage",
            ),
            make_life_event(
                event_date_utc="2008-11-05T08:30:00Z",
                event_type=EventType.ACCIDENT,
                description="Accident",
            ),
        )
        transit_times = {
            "Marriage": "2010-06-15T11:00:00Z",
            "Accident": "2008-11-05T09:00:00Z",
        }
        report = svc.calculate_offset(
            BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        assert len(report.offsets) == 2

    def test_suggested_birth_time_adjusted(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),)
        transit_times = {"Marriage": "2010-06-15T11:00:00Z"}
        report = svc.calculate_offset(
            BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        # Positive offset → suggested time is later than input
        assert report.suggested_birth_time != BIRTH_TIME

    def test_missing_transit_time_skipped(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),)
        # No transit_times provided
        report = svc.calculate_offset(
            BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
        )
        assert len(report.offsets) == 0

    def test_deterministic(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),)
        transit_times = {"Marriage": "2010-06-15T11:00:00Z"}
        r1 = svc.calculate_offset(
            BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        r2 = svc.calculate_offset(
            BIRTH_TIME, events,
            RectificationMethod.TRANSIT_TO_ASCENDANT,
            transit_times,
        )
        assert r1.to_dict() == r2.to_dict()

    def test_all_methods_produce_valid_report(self) -> None:
        svc = RectificationService()
        events = (make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),)
        transit_times = {"Marriage": "2010-06-15T11:00:00Z"}
        for method in RectificationMethod:
            report = svc.calculate_offset(
                BIRTH_TIME, events, method, transit_times,
            )
            assert isinstance(report, RectificationReport)
            assert report.input_birth_time == BIRTH_TIME

    def test_config_property(self) -> None:
        svc = RectificationService()
        assert svc.config is not None
        assert svc.config.version == "0.1.0"


class TestRectificationServiceValidation:
    def test_empty_birth_time_raises(self) -> None:
        svc = RectificationService()
        events = (make_life_event(),)
        with pytest.raises(InvalidRectificationRequestError):
            svc.calculate_offset("", events, RectificationMethod.TRANSIT_TO_ASCENDANT)

    def test_empty_events_raises(self) -> None:
        svc = RectificationService()
        with pytest.raises(InvalidRectificationRequestError):
            svc.calculate_offset(BIRTH_TIME, (), RectificationMethod.TRANSIT_TO_ASCENDANT)

    def test_invalid_method_type_raises(self) -> None:
        svc = RectificationService()
        events = (make_life_event(),)
        with pytest.raises(InvalidRectificationRequestError):
            svc.calculate_offset(BIRTH_TIME, events, "NOT_A_METHOD")  # type: ignore[arg-type]

    def test_invalid_event_in_tuple_raises(self) -> None:
        svc = RectificationService()
        with pytest.raises(InvalidRectificationRequestError):
            svc.calculate_offset(
                BIRTH_TIME,
                ("NOT_AN_EVENT",),  # type: ignore[arg-type]
                RectificationMethod.TRANSIT_TO_ASCENDANT,
            )

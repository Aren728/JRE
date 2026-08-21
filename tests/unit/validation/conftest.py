"""Shared test fixtures and builders for validation unit tests."""

from __future__ import annotations

from typing import Any

import pytest

from validation.models import (
    EventType,
    ExtractedTrigger,
    KnownEvent,
    ReferenceChart,
    TriggerSource,
    ValidationConfig,
    ValidationResult,
    ValidationReport,
)


@pytest.fixture
def sample_config() -> ValidationConfig:
    """A minimal ValidationConfig for testing."""
    return ValidationConfig(
        version="1.0",
        match_threshold=0.5,
        trigger_weights={"Venus_Yoga": 1.2, "Saturn_Mahadasha": 1.5},
        source_reliability={"yoga": 0.95, "dasha": 0.90},
    )


@pytest.fixture
def sample_known_events() -> tuple[KnownEvent, ...]:
    """A tuple of known events for testing."""
    return (
        KnownEvent(
            event_date_utc="2010-06-15T00:00:00Z",
            event_type=EventType.MARRIAGE,
            expected_triggers=("Venus_Yoga", "7th_Lord_Yoga"),
            description="Marriage event",
        ),
        KnownEvent(
            event_date_utc="2012-09-01T00:00:00Z",
            event_type=EventType.PROMOTION,
            expected_triggers=("10th_Lord_Yoga", "Saturn_in_10th"),
            description="Career promotion",
        ),
    )


@pytest.fixture
def sample_reference_chart(
    sample_known_events: tuple[KnownEvent, ...],
) -> ReferenceChart:
    """A reference chart for testing."""
    return ReferenceChart(
        chart_id="test_chart_001",
        birth_data={"date": "1990-01-01", "time": "12:00:00"},
        known_events=sample_known_events,
        ground_truth={"lagna": "CANCER", "moon": "PISCES"},
    )


def make_known_event(
    event_type: EventType = EventType.MARRIAGE,
    triggers: tuple[str, ...] = ("Venus_Yoga",),
    description: str = "test event",
) -> KnownEvent:
    """Builder for KnownEvent test objects."""
    return KnownEvent(
        event_date_utc="2020-01-01T00:00:00Z",
        event_type=event_type,
        expected_triggers=triggers,
        description=description,
    )


def make_extracted_trigger(
    trigger_id: str = "yoga_present",
    source: TriggerSource = TriggerSource.YOGA,
    confidence: float = 1.0,
) -> ExtractedTrigger:
    """Builder for ExtractedTrigger test objects."""
    return ExtractedTrigger(
        trigger_id=trigger_id,
        source=source,
        confidence=confidence,
    )


def make_validation_result(
    chart_id: str = "test_chart",
    expected: tuple[str, ...] = ("Venus_Yoga",),
    actual_ids: tuple[str, ...] = ("Venus_Yoga",),
    match_score: float = 1.0,
) -> ValidationResult:
    """Builder for ValidationResult test objects."""
    actual = tuple(make_extracted_trigger(tid) for tid in actual_ids)
    missing = tuple(t for t in expected if t not in set(actual_ids))
    false_pos = tuple(tid for tid in actual_ids if tid not in set(expected))
    return ValidationResult(
        chart_id=chart_id,
        expected_triggers=expected,
        actual_triggers=actual,
        match_score=match_score,
        missing_triggers=missing,
        false_positives=false_pos,
    )

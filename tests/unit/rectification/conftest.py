"""Shared builders for JRE-021 Rectification unit tests."""

from __future__ import annotations

import pytest

from rectification.models import (
    EventType,
    LifeEvent,
    RectificationConfig,
    RectificationMethod,
)


def make_life_event(
    event_date_utc: str = "2010-06-15T10:00:00Z",
    event_type: EventType = EventType.MARRIAGE,
    description: str = "Marriage event",
) -> LifeEvent:
    """Build a ``LifeEvent``."""
    return LifeEvent(
        event_date_utc=event_date_utc,
        event_type=event_type,
        description=description,
    )


@pytest.fixture
def marriage_event() -> LifeEvent:
    """A marriage life event."""
    return make_life_event(
        event_date_utc="2010-06-15T10:00:00Z",
        event_type=EventType.MARRIAGE,
        description="Marriage",
    )


@pytest.fixture
def promotion_event() -> LifeEvent:
    """A promotion life event."""
    return make_life_event(
        event_date_utc="2012-03-20T14:00:00Z",
        event_type=EventType.PROMOTION,
        description="Promotion at work",
    )


@pytest.fixture
def accident_event() -> LifeEvent:
    """An accident life event."""
    return make_life_event(
        event_date_utc="2008-11-05T08:30:00Z",
        event_type=EventType.ACCIDENT,
        description="Car accident",
    )


@pytest.fixture
def sample_events() -> tuple[LifeEvent, ...]:
    """Multiple life events for testing."""
    return (
        make_life_event(
            event_date_utc="2010-06-15T10:00:00Z",
            event_type=EventType.MARRIAGE,
            description="Marriage",
        ),
        make_life_event(
            event_date_utc="2012-03-20T14:00:00Z",
            event_type=EventType.PROMOTION,
            description="Promotion",
        ),
        make_life_event(
            event_date_utc="2008-11-05T08:30:00Z",
            event_type=EventType.ACCIDENT,
            description="Accident",
        ),
    )


@pytest.fixture
def sample_config() -> RectificationConfig:
    """A default rectification config."""
    return RectificationConfig()


@pytest.fixture
def sample_transit_times() -> dict[str, str]:
    """Transit times corresponding to sample_events."""
    return {
        "Marriage": "2010-06-15T11:00:00Z",      # 1 hour after event
        "Promotion": "2012-03-20T15:30:00Z",     # 1.5 hours after
        "Accident": "2008-11-05T09:00:00Z",      # 30 min after
    }

"""Shared test fixtures and builders for temporal evidence unit tests."""

from __future__ import annotations

import pytest

from jrs.temporal.models import (
    ActivationType,
    ConvergenceLevel,
    EventWindow,
    TemporalConfig,
    TemporalTrigger,
)


@pytest.fixture
def sample_config() -> TemporalConfig:
    """A minimal TemporalConfig for testing."""
    return TemporalConfig(
        version="1.0",
        convergence_rules={"DASHA+TRANSIT": 0.9},
        min_triggers_for_high=3,
        min_triggers_for_moderate=2,
        activation_type_weights={"DASHA": 1.0, "TRANSIT": 0.8},
    )


@pytest.fixture
def sample_dasha_trigger() -> TemporalTrigger:
    """A sample Dasha trigger for testing."""
    return TemporalTrigger(
        activation_type=ActivationType.DASHA,
        triggering_planet="VENUS",
        triggering_rashi="LIBRA",
        activation_start_utc="2024-01-01T00:00:00Z",
        activation_end_utc="2024-12-31T23:59:59Z",
        strength=0.9,
        description="Venus Mahadasha",
    )


@pytest.fixture
def sample_transit_trigger() -> TemporalTrigger:
    """A sample Transit trigger for testing."""
    return TemporalTrigger(
        activation_type=ActivationType.TRANSIT,
        triggering_planet="JUPITER",
        triggering_rashi="CANCER",
        activation_start_utc="2024-06-01T00:00:00Z",
        activation_end_utc="2024-12-31T23:59:59Z",
        strength=0.8,
        description="Jupiter transiting 7th house",
    )


@pytest.fixture
def sample_varga_trigger() -> TemporalTrigger:
    """A sample Varga trigger for testing."""
    return TemporalTrigger(
        activation_type=ActivationType.VARGA,
        triggering_planet="VENUS",
        triggering_rashi="SCORPIO",
        activation_start_utc="2024-06-15T00:00:00Z",
        activation_end_utc="2024-09-15T23:59:59Z",
        strength=0.7,
        description="Venus strong in D9",
    )


def make_temporal_trigger(
    activation_type: ActivationType = ActivationType.DASHA,
    planet: str = "VENUS",
    start_utc: str = "2024-01-01T00:00:00Z",
    end_utc: str = "2024-12-31T23:59:59Z",
    strength: float = 1.0,
) -> TemporalTrigger:
    """Builder for TemporalTrigger test objects."""
    return TemporalTrigger(
        activation_type=activation_type,
        triggering_planet=planet,
        activation_start_utc=start_utc,
        activation_end_utc=end_utc,
        strength=strength,
    )


def make_event_window(
    candidate_event: str = "MARRIAGE_FORMATION",
    convergence: ConvergenceLevel = ConvergenceLevel.MODERATE,
    triggers: tuple[TemporalTrigger, ...] = (),
) -> EventWindow:
    """Builder for EventWindow test objects."""
    return EventWindow(
        candidate_event_taxonomy=candidate_event,
        triggers=triggers,
        convergence_level=convergence,
    )

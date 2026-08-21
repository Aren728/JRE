"""Unit tests for TemporalEvidenceService."""

from __future__ import annotations

import pytest

from tests.unit.jrs.temporal.conftest import make_temporal_trigger
from jrs.temporal.errors import InvalidEventWindowError, InvalidTriggerError
from jrs.temporal.models import (
    ActivationType,
    ConvergenceLevel,
    EventWindow,
    TemporalConfig,
    TemporalTrigger,
)
from jrs.temporal.service import TemporalEvidenceService


class TestTemporalEvidenceServiceInit:
    """Tests for TemporalEvidenceService initialization."""

    def test_default_config(self) -> None:
        svc = TemporalEvidenceService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = TemporalConfig(min_triggers_for_high=5)
        svc = TemporalEvidenceService(config=config)
        assert svc.config.min_triggers_for_high == 5


class TestTemporalEvidenceServiceBuildTrigger:
    """Tests for the build_trigger method."""

    def test_build_valid_trigger(self) -> None:
        svc = TemporalEvidenceService()
        trigger = svc.build_trigger(
            activation_type=ActivationType.DASHA,
            planet="VENUS",
            rashi="LIBRA",
            start_utc="2024-01-01T00:00:00Z",
            end_utc="2024-12-31T23:59:59Z",
            strength=0.9,
        )
        assert trigger.activation_type is ActivationType.DASHA
        assert trigger.triggering_planet == "VENUS"
        assert trigger.strength == 0.9

    def test_build_trigger_invalid_strength(self) -> None:
        svc = TemporalEvidenceService()
        with pytest.raises(InvalidTriggerError, match="strength must be between"):
            svc.build_trigger(
                activation_type=ActivationType.DASHA,
                strength=1.5,
            )

    def test_build_trigger_negative_strength(self) -> None:
        svc = TemporalEvidenceService()
        with pytest.raises(InvalidTriggerError, match="strength must be between"):
            svc.build_trigger(
                activation_type=ActivationType.DASHA,
                strength=-0.1,
            )


class TestTemporalEvidenceServiceCalculateEventWindow:
    """Tests for the calculate_event_window method."""

    def test_empty_event_raises(self) -> None:
        svc = TemporalEvidenceService()
        with pytest.raises(InvalidEventWindowError, match="must not be empty"):
            svc.calculate_event_window("")

    def test_no_triggers_returns_none_convergence(self) -> None:
        svc = TemporalEvidenceService()
        window = svc.calculate_event_window("MARRIAGE_FORMATION")
        assert window.candidate_event_taxonomy == "MARRIAGE_FORMATION"
        assert window.convergence_level is ConvergenceLevel.NONE

    def test_single_dasha_trigger(self) -> None:
        svc = TemporalEvidenceService()
        dasha = make_temporal_trigger(
            activation_type=ActivationType.DASHA,
            start_utc="2024-01-01T00:00:00Z",
            end_utc="2024-12-31T23:59:59Z",
        )
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION",
            dasha_periods=(dasha,),
        )
        assert window.convergence_level is ConvergenceLevel.LOW
        assert len(window.triggers) == 1

    def test_overlapping_dasha_and_transit(self) -> None:
        svc = TemporalEvidenceService()
        dasha = make_temporal_trigger(
            activation_type=ActivationType.DASHA,
            start_utc="2024-01-01T00:00:00Z",
            end_utc="2024-12-31T23:59:59Z",
        )
        transit = make_temporal_trigger(
            activation_type=ActivationType.TRANSIT,
            start_utc="2024-06-01T00:00:00Z",
            end_utc="2024-12-31T23:59:59Z",
        )
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION",
            dasha_periods=(dasha,),
            transits=(transit,),
        )
        assert window.convergence_level is ConvergenceLevel.MODERATE
        assert len(window.triggers) >= 2

    def test_non_overlapping_triggers(self) -> None:
        svc = TemporalEvidenceService()
        dasha = make_temporal_trigger(
            activation_type=ActivationType.DASHA,
            start_utc="2024-01-01T00:00:00Z",
            end_utc="2024-03-31T23:59:59Z",
        )
        transit = make_temporal_trigger(
            activation_type=ActivationType.TRANSIT,
            start_utc="2024-06-01T00:00:00Z",
            end_utc="2024-12-31T23:59:59Z",
        )
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION",
            dasha_periods=(dasha,),
            transits=(transit,),
        )
        # Non-overlapping: all triggers used, no overlap found
        assert len(window.triggers) == 2

    def test_three_distinct_types_high_convergence(self) -> None:
        svc = TemporalEvidenceService()
        triggers = (
            make_temporal_trigger(
                activation_type=ActivationType.DASHA,
                start_utc="2024-01-01T00:00:00Z",
                end_utc="2024-12-31T23:59:59Z",
            ),
            make_temporal_trigger(
                activation_type=ActivationType.TRANSIT,
                start_utc="2024-01-01T00:00:00Z",
                end_utc="2024-12-31T23:59:59Z",
            ),
            make_temporal_trigger(
                activation_type=ActivationType.VARGA,
                start_utc="2024-01-01T00:00:00Z",
                end_utc="2024-12-31T23:59:59Z",
            ),
        )
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION",
            dasha_periods=(triggers[0],),
            transits=(triggers[1],),
            varga_triggers=(triggers[2],),
        )
        assert window.convergence_level is ConvergenceLevel.HIGH

    def test_window_boundaries_computed(self) -> None:
        svc = TemporalEvidenceService()
        dasha = make_temporal_trigger(
            activation_type=ActivationType.DASHA,
            start_utc="2024-01-01T00:00:00Z",
            end_utc="2024-06-30T23:59:59Z",
        )
        transit = make_temporal_trigger(
            activation_type=ActivationType.TRANSIT,
            start_utc="2024-03-01T00:00:00Z",
            end_utc="2024-12-31T23:59:59Z",
        )
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION",
            dasha_periods=(dasha,),
            transits=(transit,),
        )
        # Window should span earliest start to latest end
        assert window.window_start_utc == "2024-01-01T00:00:00Z"
        assert window.window_end_utc == "2024-12-31T23:59:59Z"

    def test_deterministic_output(self) -> None:
        svc = TemporalEvidenceService()
        dasha = make_temporal_trigger(
            activation_type=ActivationType.DASHA,
            start_utc="2024-01-01T00:00:00Z",
            end_utc="2024-12-31T23:59:59Z",
        )
        w1 = svc.calculate_event_window("TEST", dasha_periods=(dasha,))
        w2 = svc.calculate_event_window("TEST", dasha_periods=(dasha,))
        assert w1.convergence_level is w2.convergence_level
        assert len(w1.triggers) == len(w2.triggers)

    def test_all_trigger_types(self) -> None:
        svc = TemporalEvidenceService()
        window = svc.calculate_event_window(
            "TEST",
            dasha_periods=(make_temporal_trigger(activation_type=ActivationType.DASHA,
                                                 start_utc="2024-01-01T00:00:00Z",
                                                 end_utc="2024-12-31T23:59:59Z"),),
            transits=(make_temporal_trigger(activation_type=ActivationType.TRANSIT,
                                            start_utc="2024-01-01T00:00:00Z",
                                            end_utc="2024-12-31T23:59:59Z"),),
            varga_triggers=(make_temporal_trigger(activation_type=ActivationType.VARGA,
                                                   start_utc="2024-01-01T00:00:00Z",
                                                   end_utc="2024-12-31T23:59:59Z"),),
            ashtakavarga_triggers=(make_temporal_trigger(activation_type=ActivationType.ASHTAKAVARGA,
                                                          start_utc="2024-01-01T00:00:00Z",
                                                          end_utc="2024-12-31T23:59:59Z"),),
        )
        assert len(window.triggers) == 4

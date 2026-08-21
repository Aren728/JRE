"""Integration tests for the Temporal Evidence layer."""

from __future__ import annotations

import json

import pytest

from jrs.temporal.config import load_temporal_config
from jrs.temporal.models import (
    ActivationType,
    ConvergenceLevel,
    EventWindow,
    TemporalTrigger,
    classify_convergence,
)
from jrs.temporal.serialize import (
    event_window_from_dict,
    result_to_json,
    temporal_trigger_from_dict,
)
from jrs.temporal.service import TemporalEvidenceService


@pytest.fixture
def svc() -> TemporalEvidenceService:
    """Create a TemporalEvidenceService with the real config."""
    return TemporalEvidenceService()


class TestConfigLoading:
    """Integration tests for config loading."""

    def test_loads_default_config(self) -> None:
        config = load_temporal_config()
        assert config.version == "1.0"
        assert config.min_triggers_for_high == 3

    def test_convergence_rules_loaded(self) -> None:
        config = load_temporal_config()
        assert "DASHA+TRANSIT" in config.convergence_rules
        assert config.convergence_rules["DASHA+TRANSIT"] == 0.9

    def test_activation_type_weights_loaded(self) -> None:
        config = load_temporal_config()
        assert "DASHA" in config.activation_type_weights
        assert config.activation_type_weights["DASHA"] == 1.0


class TestMarriageEventWindow:
    """Integration tests for generating marriage event windows."""

    def test_marriage_formation_window(
        self,
        svc: TemporalEvidenceService,
    ) -> None:
        """Test generating an event window for marriage formation."""
        dasha = TemporalTrigger(
            activation_type=ActivationType.DASHA,
            triggering_planet="VENUS",
            triggering_rashi="LIBRA",
            activation_start_utc="2024-01-01T00:00:00Z",
            activation_end_utc="2024-12-31T23:59:59Z",
            strength=0.9,
        )
        transit = TemporalTrigger(
            activation_type=ActivationType.TRANSIT,
            triggering_planet="JUPITER",
            triggering_rashi="CANCER",
            activation_start_utc="2024-06-01T00:00:00Z",
            activation_end_utc="2024-12-31T23:59:59Z",
            strength=0.8,
        )
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION",
            dasha_periods=(dasha,),
            transits=(transit,),
        )
        assert window.candidate_event_taxonomy == "MARRIAGE_FORMATION"
        assert window.convergence_level is ConvergenceLevel.MODERATE
        assert len(window.triggers) == 2

    def test_high_convergence_window(
        self,
        svc: TemporalEvidenceService,
    ) -> None:
        """Test a window with 3+ distinct activation types."""
        triggers = [
            TemporalTrigger(
                activation_type=ActivationType.DASHA,
                triggering_planet="VENUS",
                activation_start_utc="2024-01-01T00:00:00Z",
                activation_end_utc="2024-12-31T23:59:59Z",
                strength=0.9,
            ),
            TemporalTrigger(
                activation_type=ActivationType.TRANSIT,
                triggering_planet="JUPITER",
                activation_start_utc="2024-01-01T00:00:00Z",
                activation_end_utc="2024-12-31T23:59:59Z",
                strength=0.8,
            ),
            TemporalTrigger(
                activation_type=ActivationType.VARGA,
                triggering_planet="VENUS",
                activation_start_utc="2024-01-01T00:00:00Z",
                activation_end_utc="2024-12-31T23:59:59Z",
                strength=0.7,
            ),
        ]
        window = svc.calculate_event_window(
            "MARRIAGE_FORMATION",
            dasha_periods=(triggers[0],),
            transits=(triggers[1],),
            varga_triggers=(triggers[2],),
        )
        assert window.convergence_level is ConvergenceLevel.HIGH


class TestSerializationRoundTrip:
    """Integration tests for serialization round-trip."""

    def test_trigger_round_trip(self) -> None:
        trigger = TemporalTrigger(
            activation_type=ActivationType.DASHA,
            triggering_planet="VENUS",
            activation_start_utc="2024-01-01T00:00:00Z",
            activation_end_utc="2024-12-31T23:59:59Z",
        )
        d = trigger.to_dict()
        restored = temporal_trigger_from_dict(d)
        assert restored.activation_type is ActivationType.DASHA
        assert restored.triggering_planet == "VENUS"

    def test_window_round_trip(self) -> None:
        window = EventWindow(
            candidate_event_taxonomy="TEST",
            window_start_utc="2024-01-01T00:00:00Z",
            window_end_utc="2024-12-31T23:59:59Z",
            triggers=(
                TemporalTrigger(
                    activation_type=ActivationType.DASHA,
                    triggering_planet="VENUS",
                    activation_start_utc="2024-01-01T00:00:00Z",
                    activation_end_utc="2024-12-31T23:59:59Z",
                ),
            ),
            convergence_level=ConvergenceLevel.HIGH,
        )
        d = window.to_dict()
        restored = event_window_from_dict(d)
        assert restored.candidate_event_taxonomy == "TEST"
        assert restored.convergence_level is ConvergenceLevel.HIGH
        assert len(restored.triggers) == 1

    def test_window_json_serializable(self) -> None:
        window = EventWindow(
            candidate_event_taxonomy="TEST",
            convergence_level=ConvergenceLevel.MODERATE,
        )
        json_str = result_to_json(window)
        parsed = json.loads(json_str)
        assert parsed["candidate_event_taxonomy"] == "TEST"
        assert parsed["convergence_level"] == "MODERATE"


class TestConvergenceClassification:
    """Integration tests for convergence classification."""

    def test_all_none_triggers(self) -> None:
        assert classify_convergence(()) is ConvergenceLevel.NONE

    def test_single_dasha(self) -> None:
        triggers = (TemporalTrigger(activation_type=ActivationType.DASHA),)
        assert classify_convergence(triggers) is ConvergenceLevel.LOW

    def test_dasha_plus_transit(self) -> None:
        triggers = (
            TemporalTrigger(activation_type=ActivationType.DASHA),
            TemporalTrigger(activation_type=ActivationType.TRANSIT),
        )
        assert classify_convergence(triggers) is ConvergenceLevel.MODERATE

    def test_three_types(self) -> None:
        triggers = (
            TemporalTrigger(activation_type=ActivationType.DASHA),
            TemporalTrigger(activation_type=ActivationType.TRANSIT),
            TemporalTrigger(activation_type=ActivationType.VARGA),
        )
        assert classify_convergence(triggers) is ConvergenceLevel.HIGH

    def test_four_types_high_strength(self) -> None:
        triggers = (
            TemporalTrigger(activation_type=ActivationType.DASHA, strength=0.9),
            TemporalTrigger(activation_type=ActivationType.TRANSIT, strength=0.9),
            TemporalTrigger(activation_type=ActivationType.VARGA, strength=0.9),
            TemporalTrigger(activation_type=ActivationType.ASHTAKAVARGA, strength=0.9),
        )
        assert classify_convergence(triggers) is ConvergenceLevel.VERY_HIGH

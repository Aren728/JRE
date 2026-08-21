"""Unit tests for temporal evidence models and overlap calculation logic."""

from __future__ import annotations

import json

import pytest

from tests.unit.jrs.temporal.conftest import make_temporal_trigger
from jrs.temporal.models import (
    ActivationType,
    CONVERGENCE_VALUES,
    ConvergenceLevel,
    EventWindow,
    TemporalConfig,
    TemporalTrigger,
    classify_convergence,
    compute_overlap_window,
    find_overlapping_triggers,
    parse_iso_timestamp,
    windows_overlap,
)


class TestActivationType:
    """Tests for the ActivationType enum."""

    def test_all_types_have_string_values(self) -> None:
        for at in ActivationType:
            assert isinstance(at.value, str)
            assert at.value == at.name

    def test_type_count(self) -> None:
        assert len(ActivationType) == 6

    def test_type_from_value(self) -> None:
        assert ActivationType("DASHA") is ActivationType.DASHA
        assert ActivationType("TRANSIT") is ActivationType.TRANSIT

    def test_invalid_type(self) -> None:
        with pytest.raises(ValueError):
            ActivationType("INVALID")


class TestConvergenceLevel:
    """Tests for the ConvergenceLevel enum."""

    def test_all_levels_have_string_values(self) -> None:
        for cl in ConvergenceLevel:
            assert isinstance(cl.value, str)

    def test_level_count(self) -> None:
        assert len(ConvergenceLevel) == 5

    def test_level_from_value(self) -> None:
        assert ConvergenceLevel("HIGH") is ConvergenceLevel.HIGH
        assert ConvergenceLevel("NONE") is ConvergenceLevel.NONE


class TestConvergenceValues:
    """Tests for the CONVERGENCE_VALUES mapping."""

    def test_all_levels_mapped(self) -> None:
        for cl in ConvergenceLevel:
            assert cl in CONVERGENCE_VALUES

    def test_values_in_order(self) -> None:
        assert CONVERGENCE_VALUES[ConvergenceLevel.VERY_HIGH] > CONVERGENCE_VALUES[ConvergenceLevel.HIGH]
        assert CONVERGENCE_VALUES[ConvergenceLevel.HIGH] > CONVERGENCE_VALUES[ConvergenceLevel.MODERATE]
        assert CONVERGENCE_VALUES[ConvergenceLevel.MODERATE] > CONVERGENCE_VALUES[ConvergenceLevel.LOW]
        assert CONVERGENCE_VALUES[ConvergenceLevel.LOW] > CONVERGENCE_VALUES[ConvergenceLevel.NONE]

    def test_values_bounded(self) -> None:
        for v in CONVERGENCE_VALUES.values():
            assert 0.0 <= v <= 1.0


class TestParseIsoTimestamp:
    """Tests for the parse_iso_timestamp function."""

    def test_valid_timestamp(self) -> None:
        dt = parse_iso_timestamp("2024-01-15T10:30:00Z")
        assert dt is not None
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_empty_string(self) -> None:
        assert parse_iso_timestamp("") is None

    def test_invalid_format(self) -> None:
        assert parse_iso_timestamp("not-a-date") is None

    def test_none_input(self) -> None:
        assert parse_iso_timestamp(None) is None  # type: ignore[arg-type]


class TestWindowsOverlap:
    """Tests for the windows_overlap function."""

    def test_overlapping(self) -> None:
        assert windows_overlap(
            "2024-01-01T00:00:00Z", "2024-06-30T23:59:59Z",
            "2024-04-01T00:00:00Z", "2024-12-31T23:59:59Z",
        ) is True

    def test_non_overlapping(self) -> None:
        assert windows_overlap(
            "2024-01-01T00:00:00Z", "2024-03-31T23:59:59Z",
            "2024-06-01T00:00:00Z", "2024-12-31T23:59:59Z",
        ) is False

    def test_adjacent(self) -> None:
        assert windows_overlap(
            "2024-01-01T00:00:00Z", "2024-06-30T23:59:59Z",
            "2024-07-01T00:00:00Z", "2024-12-31T23:59:59Z",
        ) is False

    def test_identical(self) -> None:
        assert windows_overlap(
            "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z",
            "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z",
        ) is True

    def test_contained(self) -> None:
        assert windows_overlap(
            "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z",
            "2024-06-01T00:00:00Z", "2024-06-30T23:59:59Z",
        ) is True

    def test_empty_timestamps(self) -> None:
        assert windows_overlap("", "2024-12-31T23:59:59Z",
                              "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z") is False


class TestComputeOverlapWindow:
    """Tests for the compute_overlap_window function."""

    def test_overlapping(self) -> None:
        start, end = compute_overlap_window(
            "2024-01-01T00:00:00Z", "2024-06-30T23:59:59Z",
            "2024-04-01T00:00:00Z", "2024-12-31T23:59:59Z",
        )
        assert "2024-04-01T00:00:00" in start
        assert "2024-06-30T23:59:59" in end

    def test_non_overlapping(self) -> None:
        start, end = compute_overlap_window(
            "2024-01-01T00:00:00Z", "2024-03-31T23:59:59Z",
            "2024-06-01T00:00:00Z", "2024-12-31T23:59:59Z",
        )
        assert start == ""
        assert end == ""

    def test_identical(self) -> None:
        start, end = compute_overlap_window(
            "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z",
            "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z",
        )
        assert "2024-01-01T00:00:00" in start
        assert "2024-12-31T23:59:59" in end

    def test_empty_timestamps(self) -> None:
        start, end = compute_overlap_window(
            "", "2024-12-31T23:59:59Z",
            "2024-01-01T00:00:00Z", "2024-12-31T23:59:59Z",
        )
        assert start == ""
        assert end == ""


class TestFindOverlappingTriggers:
    """Tests for the find_overlapping_triggers function."""

    def test_no_overlap(self) -> None:
        triggers = (
            make_temporal_trigger(start_utc="2024-01-01T00:00:00Z", end_utc="2024-03-31T23:59:59Z"),
            make_temporal_trigger(start_utc="2024-06-01T00:00:00Z", end_utc="2024-12-31T23:59:59Z"),
        )
        result = find_overlapping_triggers(triggers)
        assert result == ()

    def test_overlap(self) -> None:
        triggers = (
            make_temporal_trigger(start_utc="2024-01-01T00:00:00Z", end_utc="2024-06-30T23:59:59Z"),
            make_temporal_trigger(start_utc="2024-04-01T00:00:00Z", end_utc="2024-12-31T23:59:59Z"),
        )
        result = find_overlapping_triggers(triggers)
        assert len(result) == 2

    def test_three_triggers_partial_overlap(self) -> None:
        triggers = (
            make_temporal_trigger(start_utc="2024-01-01T00:00:00Z", end_utc="2024-03-31T23:59:59Z"),
            make_temporal_trigger(start_utc="2024-02-01T00:00:00Z", end_utc="2024-08-31T23:59:59Z"),
            make_temporal_trigger(start_utc="2024-09-01T00:00:00Z", end_utc="2024-12-31T23:59:59Z"),
        )
        result = find_overlapping_triggers(triggers)
        # Trigger 0 overlaps with 1, trigger 1 overlaps with 0
        # Trigger 2 doesn't overlap with either
        assert len(result) == 2

    def test_single_trigger(self) -> None:
        triggers = (make_temporal_trigger(),)
        result = find_overlapping_triggers(triggers)
        assert result == ()

    def test_empty_triggers(self) -> None:
        result = find_overlapping_triggers(())
        assert result == ()


class TestClassifyConvergence:
    """Tests for the classify_convergence function."""

    def test_no_triggers(self) -> None:
        assert classify_convergence(()) is ConvergenceLevel.NONE

    def test_single_trigger(self) -> None:
        triggers = (make_temporal_trigger(),)
        assert classify_convergence(triggers) is ConvergenceLevel.LOW

    def test_two_distinct_types(self) -> None:
        triggers = (
            make_temporal_trigger(activation_type=ActivationType.DASHA),
            make_temporal_trigger(activation_type=ActivationType.TRANSIT),
        )
        assert classify_convergence(triggers) is ConvergenceLevel.MODERATE

    def test_three_distinct_types(self) -> None:
        triggers = (
            make_temporal_trigger(activation_type=ActivationType.DASHA),
            make_temporal_trigger(activation_type=ActivationType.TRANSIT),
            make_temporal_trigger(activation_type=ActivationType.VARGA),
        )
        assert classify_convergence(triggers) is ConvergenceLevel.HIGH

    def test_four_distinct_types_high_strength(self) -> None:
        triggers = (
            make_temporal_trigger(activation_type=ActivationType.DASHA, strength=0.9),
            make_temporal_trigger(activation_type=ActivationType.TRANSIT, strength=0.9),
            make_temporal_trigger(activation_type=ActivationType.VARGA, strength=0.9),
            make_temporal_trigger(activation_type=ActivationType.ASHTAKAVARGA, strength=0.9),
        )
        assert classify_convergence(triggers) is ConvergenceLevel.VERY_HIGH

    def test_custom_thresholds(self) -> None:
        triggers = (
            make_temporal_trigger(activation_type=ActivationType.DASHA),
            make_temporal_trigger(activation_type=ActivationType.TRANSIT),
        )
        # With min_high=2, two distinct types should be HIGH
        assert classify_convergence(triggers, min_high=2) is ConvergenceLevel.HIGH


class TestTemporalTrigger:
    """Tests for the TemporalTrigger model."""

    def test_creation(self) -> None:
        trigger = make_temporal_trigger()
        assert trigger.activation_type is ActivationType.DASHA
        assert trigger.triggering_planet == "VENUS"

    def test_frozen(self) -> None:
        trigger = make_temporal_trigger()
        with pytest.raises(AttributeError):
            trigger.triggering_planet = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        trigger = make_temporal_trigger(planet="JUPITER", strength=0.8)
        d = trigger.to_dict()
        assert d["triggering_planet"] == "JUPITER"
        assert d["strength"] == 0.8

    def test_to_dict_deterministic(self) -> None:
        trigger = make_temporal_trigger()
        d1 = trigger.to_dict()
        d2 = trigger.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_defaults(self) -> None:
        trigger = TemporalTrigger(
            activation_type=ActivationType.TRANSIT,
        )
        assert trigger.triggering_planet == ""
        assert trigger.strength == 1.0


class TestEventWindow:
    """Tests for the EventWindow model."""

    def test_creation(self) -> None:
        window = EventWindow(
            candidate_event_taxonomy="MARRIAGE_FORMATION",
            convergence_level=ConvergenceLevel.HIGH,
        )
        assert window.candidate_event_taxonomy == "MARRIAGE_FORMATION"
        assert window.convergence_level is ConvergenceLevel.HIGH

    def test_frozen(self) -> None:
        window = EventWindow(candidate_event_taxonomy="TEST")
        with pytest.raises(AttributeError):
            window.candidate_event_taxonomy = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        window = EventWindow(
            candidate_event_taxonomy="TEST",
            convergence_level=ConvergenceLevel.MODERATE,
            conflicting_indicators=2,
        )
        d = window.to_dict()
        assert d["candidate_event_taxonomy"] == "TEST"
        assert d["convergence_level"] == "MODERATE"
        assert d["conflicting_indicators"] == 2

    def test_to_dict_deterministic(self) -> None:
        window = EventWindow(candidate_event_taxonomy="TEST")
        d1 = window.to_dict()
        d2 = window.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)


class TestTemporalConfig:
    """Tests for the TemporalConfig model."""

    def test_defaults(self) -> None:
        config = TemporalConfig()
        assert config.version == "1.0"
        assert config.min_triggers_for_high == 3

    def test_frozen(self) -> None:
        config = TemporalConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

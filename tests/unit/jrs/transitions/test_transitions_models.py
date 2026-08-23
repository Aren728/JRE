"""Unit tests for transitions engine models."""

from __future__ import annotations

import json

import pytest

from jrs.transitions.models import (
    StateChange,
    TransitionEvent,
    TransitionType,
    compute_deterministic_id,
)

# ── TransitionType ───────────────────────────────────────────────────────────


class TestTransitionType:
    """Tests for the TransitionType enum."""

    def test_all_types_have_string_values(self) -> None:
        for t in TransitionType:
            assert isinstance(t.value, str)
            assert t.value == t.name

    def test_type_count(self) -> None:
        assert len(TransitionType) == 8

    def test_type_from_value(self) -> None:
        assert (
            TransitionType("DASHA_BOUNDARY")
            is TransitionType.DASHA_BOUNDARY
        )
        assert (
            TransitionType("NAKSHATRA_INGRESS")
            is TransitionType.NAKSHATRA_INGRESS
        )

    def test_invalid_type(self) -> None:
        with pytest.raises(ValueError):
            TransitionType("INVALID")

    def test_all_eight_types(self) -> None:
        expected = {
            "DASHA_BOUNDARY",
            "DASHA_SANDHI",
            "NAKSHATRA_INGRESS",
            "RASHI_INGRESS",
            "RETROGRADE_STATION",
            "DIRECT_STATION",
            "ECLIPSE_WINDOW",
            "DIGNITY_TRANSITION",
        }
        actual = {t.value for t in TransitionType}
        assert actual == expected


# ── StateChange ──────────────────────────────────────────────────────────────


class TestStateChange:
    """Tests for the StateChange model."""

    def test_creation(self) -> None:
        sc = StateChange(before="VENUS", after="SATURN")
        assert sc.before == "VENUS"
        assert sc.after == "SATURN"

    def test_empty_defaults(self) -> None:
        sc = StateChange()
        assert sc.before == ""
        assert sc.after == ""

    def test_to_dict(self) -> None:
        sc = StateChange(before="VENUS", after="SATURN")
        d = sc.to_dict()
        assert d["before"] == "VENUS"
        assert d["after"] == "SATURN"

    def test_to_dict_deterministic(self) -> None:
        sc = StateChange(before="VENUS", after="SATURN")
        assert json.dumps(sc.to_dict(), sort_keys=True) == json.dumps(
            sc.to_dict(), sort_keys=True
        )

    def test_frozen(self) -> None:
        sc = StateChange(before="A", after="B")
        with pytest.raises(AttributeError):
            sc.before = "C"  # type: ignore[misc]


# ── TransitionEvent ──────────────────────────────────────────────────────────


class TestTransitionEvent:
    """Tests for the TransitionEvent model."""

    def test_creation(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="VENUS", after="SUN"),
            affected_facts=("dasha_lord",),
            provenance="JRE-010",
        )
        assert event.transition_type is TransitionType.DASHA_BOUNDARY
        assert event.exact_timestamp == "2025-01-15T12:00:00Z"
        assert event.state_change.before == "VENUS"
        assert event.state_change.after == "SUN"

    def test_deterministic_id_computed(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="VENUS", after="SUN"),
            affected_facts=("dasha_lord",),
            provenance="JRE-010",
        )
        assert event.deterministic_id != ""
        assert len(event.deterministic_id) == 64  # SHA-256 hex

    def test_deterministic_id_same_for_equal_inputs(self) -> None:
        kwargs = dict(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="VENUS", after="SUN"),
            affected_facts=("dasha_lord",),
            provenance="JRE-010",
        )
        e1 = TransitionEvent(**kwargs)
        e2 = TransitionEvent(**kwargs)
        assert e1.deterministic_id == e2.deterministic_id

    def test_deterministic_id_different_for_different_inputs(self) -> None:
        e1 = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="VENUS", after="SUN"),
            affected_facts=("dasha_lord",),
            provenance="JRE-010",
        )
        e2 = TransitionEvent(
            transition_type=TransitionType.RASHI_INGRESS,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="VENUS", after="SUN"),
            affected_facts=("dasha_lord",),
            provenance="JRE-010",
        )
        assert e1.deterministic_id != e2.deterministic_id

    def test_to_dict(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.NAKSHATRA_INGRESS,
            exact_timestamp="2025-03-01T08:30:00Z",
            state_change=StateChange(before="approaching_15.0deg", after="ROHINI"),
            affected_facts=("nakshatra", "pada"),
            provenance="JRE-003",
            duration_seconds=None,
            metadata={"body": "SATURN", "direction": "DIRECT"},
        )
        d = event.to_dict()
        assert d["transition_type"] == "NAKSHATRA_INGRESS"
        assert d["exact_timestamp"] == "2025-03-01T08:30:00Z"
        assert d["state_change"]["before"] == "approaching_15.0deg"
        assert d["state_change"]["after"] == "ROHINI"
        assert d["metadata"]["body"] == "SATURN"

    def test_to_dict_deterministic(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="VENUS", after="SUN"),
            affected_facts=("dasha_lord",),
            provenance="JRE-010",
        )
        d1 = event.to_dict()
        d2 = event.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_frozen(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="A", after="B"),
            affected_facts=(),
            provenance="test",
        )
        with pytest.raises(AttributeError):
            event.exact_timestamp = "changed"  # type: ignore[misc]

    def test_duration_seconds(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="A", after="B"),
            affected_facts=(),
            provenance="test",
            duration_seconds=7889400.0,
        )
        assert event.duration_seconds == 7889400.0

    def test_duration_seconds_none(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.RASHI_INGRESS,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="A", after="B"),
            affected_facts=(),
            provenance="test",
        )
        assert event.duration_seconds is None

    def test_metadata_empty_by_default(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="A", after="B"),
            affected_facts=(),
            provenance="test",
        )
        assert event.metadata == {}


# ── compute_deterministic_id ─────────────────────────────────────────────────


class TestComputeDeterministicId:
    """Tests for the compute_deterministic_id public function."""

    def test_returns_sha256_hex(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="A", after="B"),
            affected_facts=(),
            provenance="test",
        )
        assert len(compute_deterministic_id(event)) == 64

    def test_matches_event_deterministic_id(self) -> None:
        event = TransitionEvent(
            transition_type=TransitionType.DASHA_BOUNDARY,
            exact_timestamp="2025-01-15T12:00:00Z",
            state_change=StateChange(before="A", after="B"),
            affected_facts=(),
            provenance="test",
        )
        assert compute_deterministic_id(event) == event.deterministic_id

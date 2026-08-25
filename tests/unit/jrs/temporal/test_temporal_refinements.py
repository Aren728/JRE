"""Unit tests for JRS-073: Temporal Refinements.

Verifies:
- TemporalModifier construction, validation, and determinism
- Dasha sandhi weight tapering at period boundaries
- Eclipse window malefic/benefic modifiers
- Modifier application to evidence records
- Edge cases (empty inputs, boundary clamping, etc.)
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import pytest

from jrs.temporal.models import ActivationType, TemporalTrigger
from jrs.temporal.refinements.models import (
    ModifierType,
    TemporalModifier,
)
from jrs.temporal.refinements.service import TemporalRefinementService

# ── Helper Fixtures ──────────────────────────────────────────────────────────


def _make_dasha_period(
    planet: str = "VENUS",
    start: str = "2020-01-01T00:00:00+00:00",
    end: str = "2040-01-01T00:00:00+00:00",
) -> TemporalTrigger:
    """Create a Dasha period TemporalTrigger."""
    return TemporalTrigger(
        activation_type=ActivationType.DASHA,
        triggering_planet=planet,
        activation_start_utc=start,
        activation_end_utc=end,
        strength=0.9,
    )


def _make_eclipse_event(
    planet: str = "RAHU",
    start: str = "2025-03-29T10:00:00+00:00",
    end: str = "2025-03-29T14:00:00+00:00",
) -> TemporalTrigger:
    """Create an eclipse TemporalTrigger."""
    return TemporalTrigger(
        activation_type=ActivationType.TRANSIT,
        triggering_planet=planet,
        activation_start_utc=start,
        activation_end_utc=end,
        strength=0.9,
        description=f"{planet} solar eclipse",
    )


@dataclass(frozen=True)
class _MockEvidenceRecord:
    """Mock evidence record for testing modifier application."""

    evidence_id: str = "mock-001"
    outcome_taxonomy: str = "CAREER_PROMINENCE"
    activation_start_utc: str = ""
    activation_end_utc: str = ""
    strength: float = 0.8


# ── TemporalModifier Tests ──────────────────────────────────────────────────


class TestTemporalModifier:
    """Tests for TemporalModifier construction and validation."""

    def test_basic_construction(self) -> None:
        """Modifier should be constructible with required fields."""
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-15T00:00:00+00:00",
            weight_scalar=0.5,
        )
        assert mod.modifier_type is ModifierType.DASHA_SANDHI
        assert mod.weight_scalar == 0.5
        assert mod.deterministic_id != ""

    def test_deterministic_id(self) -> None:
        """Same fields should produce same deterministic_id."""
        m1 = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-15T00:00:00+00:00",
            weight_scalar=0.5,
        )
        m2 = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-15T00:00:00+00:00",
            weight_scalar=0.5,
        )
        assert m1.deterministic_id == m2.deterministic_id

    def test_different_fields_different_id(self) -> None:
        """Different fields should produce different deterministic_ids."""
        m1 = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-15T00:00:00+00:00",
            weight_scalar=0.5,
        )
        m2 = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-15T00:00:00+00:00",
            weight_scalar=0.7,
        )
        assert m1.deterministic_id != m2.deterministic_id

    def test_weight_scalar_validation(self) -> None:
        """Weight scalar outside [0.0, 2.0] should raise ValueError."""
        with pytest.raises(ValueError, match="weight_scalar must be"):
            TemporalModifier(
                modifier_type=ModifierType.DASHA_SANDHI,
                start_time="2025-01-01T00:00:00+00:00",
                end_time="2025-01-15T00:00:00+00:00",
                weight_scalar=2.5,
            )

    def test_weight_scalar_zero_valid(self) -> None:
        """Weight scalar of 0.0 is valid (complete suppression)."""
        mod = TemporalModifier(
            modifier_type=ModifierType.ECLIPSE_WINDOW,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-15T00:00:00+00:00",
            weight_scalar=0.0,
        )
        assert mod.weight_scalar == 0.0

    def test_to_dict(self) -> None:
        """Modifier should serialize to a dict correctly."""
        mod = TemporalModifier(
            modifier_type=ModifierType.ECLIPSE_WINDOW,
            start_time="2025-03-29T10:00:00+00:00",
            end_time="2025-03-29T14:00:00+00:00",
            weight_scalar=1.2,
            description="Eclipse amplification",
        )
        d = mod.to_dict()
        assert d["modifier_type"] == "ECLIPSE_WINDOW"
        assert d["weight_scalar"] == 1.2
        assert d["description"] == "Eclipse amplification"
        assert "deterministic_id" in d

    def test_to_dict_deterministic(self) -> None:
        """Two serializations should produce identical JSON."""
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-15T00:00:00+00:00",
            weight_scalar=0.5,
        )
        d1 = mod.to_dict()
        d2 = mod.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(
            d2, sort_keys=True
        )

    def test_applies_at_inside_window(self) -> None:
        """Timestamp inside the modifier window should return True."""
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        assert mod.applies_at("2025-01-15T12:00:00+00:00") is True

    def test_applies_at_outside_window(self) -> None:
        """Timestamp outside the modifier window should return False."""
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        assert mod.applies_at("2025-02-15T12:00:00+00:00") is False

    def test_applies_at_boundary(self) -> None:
        """Timestamp exactly on the boundary should return True."""
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        assert mod.applies_at("2025-01-01T00:00:00+00:00") is True
        assert mod.applies_at("2025-01-31T00:00:00+00:00") is True

    def test_applies_at_invalid_timestamp(self) -> None:
        """Invalid timestamp should return False."""
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        assert mod.applies_at("not-a-date") is False

    def test_frozen(self) -> None:
        """Modifier should be immutable."""
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        with pytest.raises(AttributeError):
            mod.weight_scalar = 1.0  # type: ignore[misc]


# ── ModifierType Tests ──────────────────────────────────────────────────────


class TestModifierType:
    """Tests for ModifierType enum."""

    def test_values(self) -> None:
        assert ModifierType.DASHA_SANDHI.value == "DASHA_SANDHI"
        assert ModifierType.ECLIPSE_WINDOW.value == "ECLIPSE_WINDOW"

    def test_is_str_enum(self) -> None:
        assert isinstance(ModifierType.DASHA_SANDHI, str)


# ── Dasha Sandhi Tests ──────────────────────────────────────────────────────


class TestDashaSandhi:
    """Tests for TemporalRefinementService.calculate_dasha_sandhi."""

    def test_generates_modifiers_for_single_period(self) -> None:
        """A single Dasha period should generate 2 modifiers (start + end)."""
        svc = TemporalRefinementService()
        periods = (_make_dasha_period(),)
        mods = svc.calculate_dasha_sandhi(periods)
        assert len(mods) == 2

    def test_generates_modifiers_for_multiple_periods(self) -> None:
        """Two Dasha periods should generate 4 modifiers."""
        svc = TemporalRefinementService()
        periods = (
            _make_dasha_period("VENUS", "2020-01-01T00:00:00+00:00",
                               "2040-01-01T00:00:00+00:00"),
            _make_dasha_period("SUN", "2040-01-01T00:00:00+00:00",
                               "2046-01-01T00:00:00+00:00"),
        )
        mods = svc.calculate_dasha_sandhi(periods)
        assert len(mods) == 4

    def test_modifier_type_is_dasha_sandhi(self) -> None:
        """All generated modifiers should be DASHA_SANDHI type."""
        svc = TemporalRefinementService()
        mods = svc.calculate_dasha_sandhi((_make_dasha_period(),))
        for mod in mods:
            assert mod.modifier_type is ModifierType.DASHA_SANDHI

    def test_boundary_weight_is_less_than_one(self) -> None:
        """Sandhi modifiers should have weight < 1.0 at the boundary."""
        svc = TemporalRefinementService()
        mods = svc.calculate_dasha_sandhi((_make_dasha_period(),))
        for mod in mods:
            assert mod.weight_scalar < 1.0

    def test_default_boundary_weight(self) -> None:
        """Default boundary weight should be 0.5."""
        svc = TemporalRefinementService()
        mods = svc.calculate_dasha_sandhi((_make_dasha_period(),))
        for mod in mods:
            assert mod.weight_scalar == 0.5

    def test_buffer_respected(self) -> None:
        """Modifier window should extend buffer_days from boundary.

        Both start and end boundary modifiers are clamped to the
        Dasha period boundaries (we don't want them to apply to
        evidence from adjacent periods).  The buffer extends inward
        from the boundary as expected.
        """
        svc = TemporalRefinementService()
        period = _make_dasha_period(
            start="2015-01-01T00:00:00+00:00",
            end="2025-06-01T00:00:00+00:00",
        )
        mods = svc.calculate_dasha_sandhi((period,), buffer_days=10)
        # half_buffer=5 days.
        # Start boundary (2015-01-01): buffer [2014-12-27, 2015-01-06]
        # clamped to period start: [2015-01-01, 2015-01-06]
        start_mod = mods[0]
        assert start_mod.start_time == "2015-01-01T00:00:00+00:00"
        assert "2015-01-06" in start_mod.end_time
        # End boundary (2025-06-01): buffer [2025-05-27, 2025-06-06]
        # clamped to period end: [2025-05-27, 2025-06-01]
        end_mod = mods[1]
        assert "2025-05-27" in end_mod.start_time
        assert end_mod.end_time == "2025-06-01T00:00:00+00:00"

    def test_clamped_to_period_boundaries(self) -> None:
        """Modifier window should not extend beyond the Dasha period."""
        svc = TemporalRefinementService()
        # Very short period with large buffer
        period = _make_dasha_period(
            start="2025-01-01T00:00:00+00:00",
            end="2025-01-05T00:00:00+00:00",
        )
        mods = svc.calculate_dasha_sandhi((period,), buffer_days=30)
        # Start modifier should be clamped to period start
        start_mod = mods[0]
        assert start_mod.start_time >= "2025-01-01"

    def test_empty_periods_returns_empty(self) -> None:
        """Empty input should return empty tuple."""
        svc = TemporalRefinementService()
        mods = svc.calculate_dasha_sandhi(())
        assert mods == ()

    def test_periods_without_timestamps_skipped(self) -> None:
        """Periods with missing timestamps should be skipped."""
        svc = TemporalRefinementService()
        period = TemporalTrigger(
            activation_type=ActivationType.DASHA,
            triggering_planet="VENUS",
        )
        mods = svc.calculate_dasha_sandhi((period,))
        assert mods == ()

    def test_all_modifiers_have_deterministic_id(self) -> None:
        """Every modifier should have a non-empty deterministic_id."""
        svc = TemporalRefinementService()
        mods = svc.calculate_dasha_sandhi((_make_dasha_period(),))
        for mod in mods:
            assert mod.deterministic_id != ""

    def test_deterministic_output(self) -> None:
        """Two runs should produce identical modifiers."""
        svc = TemporalRefinementService()
        m1 = svc.calculate_dasha_sandhi((_make_dasha_period(),))
        m2 = svc.calculate_dasha_sandhi((_make_dasha_period(),))
        assert len(m1) == len(m2)
        for a, b in zip(m1, m2, strict=True):
            assert a.to_dict() == b.to_dict()

    def test_event_window_preserved(self) -> None:
        """Modifier should preserve the original Dasha period window."""
        svc = TemporalRefinementService()
        start = "2020-01-01T00:00:00+00:00"
        end = "2040-01-01T00:00:00+00:00"
        period = _make_dasha_period(start=start, end=end)
        mods = svc.calculate_dasha_sandhi((period,))
        for mod in mods:
            assert mod.event_window_start_utc == start
            assert mod.event_window_end_utc == end


# ── Eclipse Window Tests ────────────────────────────────────────────────────


class TestEclipseWindows:
    """Tests for TemporalRefinementService.calculate_eclipse_windows."""

    def test_generates_two_modifiers_per_eclipse(self) -> None:
        """Each eclipse should generate 2 modifiers (malefic + benefic)."""
        svc = TemporalRefinementService()
        events = (_make_eclipse_event(),)
        mods = svc.calculate_eclipse_windows(events)
        assert len(mods) == 2

    def test_malefic_amplification(self) -> None:
        """Malefic modifier should have weight > 1.0."""
        svc = TemporalRefinementService()
        mods = svc.calculate_eclipse_windows(
            (_make_eclipse_event(),), malefic_amplify=1.2,
        )
        # First modifier is malefic
        malefic_mod = mods[0]
        assert malefic_mod.weight_scalar == 1.2
        assert "malefic" in malefic_mod.description.lower()

    def test_benefic_dampening(self) -> None:
        """Benefic modifier should have weight < 1.0."""
        svc = TemporalRefinementService()
        mods = svc.calculate_eclipse_windows(
            (_make_eclipse_event(),), benefic_dampen=0.8,
        )
        # Second modifier is benefic
        benefic_mod = mods[1]
        assert benefic_mod.weight_scalar == 0.8
        assert "benefic" in benefic_mod.description.lower()

    def test_modifier_type_is_eclipse_window(self) -> None:
        """All generated modifiers should be ECLIPSE_WINDOW type."""
        svc = TemporalRefinementService()
        mods = svc.calculate_eclipse_windows((_make_eclipse_event(),))
        for mod in mods:
            assert mod.modifier_type is ModifierType.ECLIPSE_WINDOW

    def test_window_matches_event(self) -> None:
        """Modifier window should match the eclipse event window."""
        svc = TemporalRefinementService()
        start = "2025-03-29T10:00:00+00:00"
        end = "2025-03-29T14:00:00+00:00"
        event = _make_eclipse_event(start=start, end=end)
        mods = svc.calculate_eclipse_windows((event,))
        for mod in mods:
            assert mod.start_time == start
            assert mod.end_time == end

    def test_empty_events_returns_empty(self) -> None:
        """Empty input should return empty tuple."""
        svc = TemporalRefinementService()
        mods = svc.calculate_eclipse_windows(())
        assert mods == ()

    def test_events_without_timestamps_skipped(self) -> None:
        """Events with missing timestamps should be skipped."""
        svc = TemporalRefinementService()
        event = TemporalTrigger(
            activation_type=ActivationType.TRANSIT,
            triggering_planet="RAHU",
        )
        mods = svc.calculate_eclipse_windows((event,))
        assert mods == ()

    def test_multiple_eclipses(self) -> None:
        """Two eclipses should generate 4 modifiers."""
        svc = TemporalRefinementService()
        events = (
            _make_eclipse_event("RAHU"),
            _make_eclipse_event("KETU"),
        )
        mods = svc.calculate_eclipse_windows(events)
        assert len(mods) == 4

    def test_custom_weights(self) -> None:
        """Custom malefic/benefic weights should be respected."""
        svc = TemporalRefinementService()
        mods = svc.calculate_eclipse_windows(
            (_make_eclipse_event(),),
            malefic_amplify=1.5,
            benefic_dampen=0.6,
        )
        assert mods[0].weight_scalar == 1.5
        assert mods[1].weight_scalar == 0.6


# ── Apply Modifiers Tests ───────────────────────────────────────────────────


class TestApplyModifiers:
    """Tests for TemporalRefinementService.apply_modifiers."""

    def test_no_modifiers_returns_full_weight(self) -> None:
        """With no modifiers, effective weight should be 1.0."""
        svc = TemporalRefinementService()
        record = _MockEvidenceRecord(
            activation_start_utc="2025-01-15T12:00:00+00:00",
        )
        results = svc.apply_modifiers((record,), ())
        assert len(results) == 1
        assert results[0]["effective_weight"] == 1.0

    def test_modifier_applies_weight(self) -> None:
        """Modifier within the record's time window should apply weight."""
        svc = TemporalRefinementService()
        record = _MockEvidenceRecord(
            activation_start_utc="2025-01-15T12:00:00+00:00",
        )
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        results = svc.apply_modifiers((record,), (mod,))
        assert results[0]["effective_weight"] == 0.5

    def test_modifier_outside_window_no_effect(self) -> None:
        """Modifier outside the record's time window should have no effect."""
        svc = TemporalRefinementService()
        record = _MockEvidenceRecord(
            activation_start_utc="2025-06-15T12:00:00+00:00",
        )
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        results = svc.apply_modifiers((record,), (mod,))
        assert results[0]["effective_weight"] == 1.0

    def test_multiple_modifiers_multiply(self) -> None:
        """Multiple overlapping modifiers should multiply weights."""
        svc = TemporalRefinementService()
        record = _MockEvidenceRecord(
            activation_start_utc="2025-01-15T12:00:00+00:00",
        )
        mod1 = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        mod2 = TemporalModifier(
            modifier_type=ModifierType.ECLIPSE_WINDOW,
            start_time="2025-01-10T00:00:00+00:00",
            end_time="2025-01-20T00:00:00+00:00",
            weight_scalar=0.8,
        )
        results = svc.apply_modifiers((record,), (mod1, mod2))
        # 0.5 * 0.8 = 0.4
        assert results[0]["effective_weight"] == pytest.approx(0.4)

    def test_record_without_timestamp_not_modified(self) -> None:
        """Record without timestamps should not be modified."""
        svc = TemporalRefinementService()
        record = _MockEvidenceRecord()  # no timestamps
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        results = svc.apply_modifiers((record,), (mod,))
        assert results[0]["effective_weight"] == 1.0

    def test_applied_modifiers_tracked(self) -> None:
        """Applied modifier IDs should be tracked in the result."""
        svc = TemporalRefinementService()
        record = _MockEvidenceRecord(
            activation_start_utc="2025-01-15T12:00:00+00:00",
        )
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        results = svc.apply_modifiers((record,), (mod,))
        assert mod.deterministic_id in results[0]["applied_modifiers"]

    def test_multiple_records(self) -> None:
        """Multiple records should each be processed independently."""
        svc = TemporalRefinementService()
        r1 = _MockEvidenceRecord(
            evidence_id="r1",
            activation_start_utc="2025-01-15T12:00:00+00:00",
        )
        r2 = _MockEvidenceRecord(
            evidence_id="r2",
            activation_start_utc="2025-06-15T12:00:00+00:00",
        )
        mod = TemporalModifier(
            modifier_type=ModifierType.DASHA_SANDHI,
            start_time="2025-01-01T00:00:00+00:00",
            end_time="2025-01-31T00:00:00+00:00",
            weight_scalar=0.5,
        )
        results = svc.apply_modifiers((r1, r2), (mod,))
        assert results[0]["effective_weight"] == 0.5
        assert results[1]["effective_weight"] == 1.0


# ── Sandhi Penalty Verification Tests ───────────────────────────────────────


class TestSandhiPenaltyVerification:
    """Verify that events at Dasha boundaries receive sandhi penalty."""

    def test_exact_boundary_receives_penalty(self) -> None:
        """Event exactly on Dasha boundary should receive weight < 1.0."""
        svc = TemporalRefinementService()
        # Boundary is at the START of the Dasha period
        period = _make_dasha_period(
            start="2020-01-01T00:00:00+00:00",
            end="2030-01-01T00:00:00+00:00",
        )
        mods = svc.calculate_dasha_sandhi((period,), buffer_days=15)

        # Record at the exact start boundary
        record = _MockEvidenceRecord(
            activation_start_utc="2020-01-01T00:00:00+00:00",
        )
        results = svc.apply_modifiers((record,), mods)

        assert results[0]["effective_weight"] < 1.0

    def test_outside_buffer_receives_normal_weight(self) -> None:
        """Event well outside sandhi buffer should receive weight 1.0."""
        svc = TemporalRefinementService()
        period = _make_dasha_period(
            start="2020-01-01T00:00:00+00:00",
            end="2030-01-01T00:00:00+00:00",
        )
        mods = svc.calculate_dasha_sandhi((period,), buffer_days=15)

        # Mid-period: 2025-01-01 is well outside the 15-day buffer
        record = _MockEvidenceRecord(
            activation_start_utc="2025-06-15T12:00:00+00:00",
        )
        results = svc.apply_modifiers((record,), mods)

        assert results[0]["effective_weight"] == 1.0

    def test_tapering_near_boundary(self) -> None:
        """Events closer to boundary should have lower weight than those
        further away within the buffer."""
        svc = TemporalRefinementService()
        period = _make_dasha_period(
            start="2020-01-01T00:00:00+00:00",
            end="2030-01-01T00:00:00+00:00",
        )
        mods = svc.calculate_dasha_sandhi((period,), buffer_days=30)

        # half_buffer = 15 days, so modifier window covers
        # [boundary - 15d, boundary + 15d] = [2019-12-17, 2020-01-16]
        # Record near boundary (within buffer)
        near_record = _MockEvidenceRecord(
            activation_start_utc="2020-01-05T00:00:00+00:00",
        )
        # Record well outside buffer (> 15 days from boundary)
        outside_record = _MockEvidenceRecord(
            activation_start_utc="2020-01-28T00:00:00+00:00",
        )

        near_results = svc.apply_modifiers((near_record,), mods)
        outside_results = svc.apply_modifiers((outside_record,), mods)

        # Near boundary should be modified (weight < 1.0)
        assert near_results[0]["effective_weight"] < 1.0
        # Outside buffer should NOT be modified
        assert outside_results[0]["effective_weight"] == 1.0


# ── Eclipse Verification Tests ──────────────────────────────────────────────


class TestEclipseVerification:
    """Verify that events during eclipses receive correct modifiers."""

    def test_malefic_during_eclipse_amplified(self) -> None:
        """Malefic evidence during eclipse should be amplified."""
        svc = TemporalRefinementService()
        eclipse = _make_eclipse_event(
            start="2025-03-29T10:00:00+00:00",
            end="2025-03-29T14:00:00+00:00",
        )
        mods = svc.calculate_eclipse_windows(
            (eclipse,), malefic_amplify=1.2, benefic_dampen=0.8,
        )

        # Malefic record during eclipse
        record = _MockEvidenceRecord(
            activation_start_utc="2025-03-29T12:00:00+00:00",
        )
        results = svc.apply_modifiers((record,), mods)

        # Both malefic (1.2) and benefic (0.8) modifiers apply:
        # 1.2 * 0.8 = 0.96
        assert results[0]["effective_weight"] == pytest.approx(0.96)

    def test_malefic_outside_eclipse_unmodified(self) -> None:
        """Malefic evidence outside eclipse window should be unmodified."""
        svc = TemporalRefinementService()
        eclipse = _make_eclipse_event(
            start="2025-03-29T10:00:00+00:00",
            end="2025-03-29T14:00:00+00:00",
        )
        mods = svc.calculate_eclipse_windows((eclipse,))

        record = _MockEvidenceRecord(
            activation_start_utc="2025-04-15T12:00:00+00:00",
        )
        results = svc.apply_modifiers((record,), mods)

        assert results[0]["effective_weight"] == 1.0

    def test_eclipse_boundary_exact(self) -> None:
        """Event exactly on eclipse boundary should receive modifiers."""
        svc = TemporalRefinementService()
        eclipse = _make_eclipse_event(
            start="2025-03-29T10:00:00+00:00",
            end="2025-03-29T14:00:00+00:00",
        )
        mods = svc.calculate_eclipse_windows((eclipse,))

        record = _MockEvidenceRecord(
            activation_start_utc="2025-03-29T10:00:00+00:00",
        )
        results = svc.apply_modifiers((record,), mods)

        # Should be modified (on the boundary)
        assert results[0]["effective_weight"] != 1.0

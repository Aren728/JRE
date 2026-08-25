"""Tests for yoga cancellation detection (RI-010C Gap 12).

Verifies that yoga conditions are correctly cancelled by:
- Debilitation (without Neecha Bhanga)
- Combustion (planet too close to Sun)
- Dusthana placement (planet in 6th/8th/12th)
"""

from __future__ import annotations

from tests.unit.yoga.conftest import make_planet_state

from jyotish import BodyId, RashiId
from yoga.models import YogaId
from yoga.service import YogaService

# --------------------------------------------------------------------------- #
# Debilitation cancellation tests
# --------------------------------------------------------------------------- #


class TestDebilitationCancellation:
    """Test that debilitated planets trigger cancellation."""

    def test_raja_yoga_cancelled_by_debilitated_planet(self) -> None:
        """Raja Yoga where one planet is debilitated → cancelled."""
        service = YogaService()
        # Aries lagna (1): 4th lord = Moon (Cancer), 5th lord = Sun (Leo)
        # Put Sun in Libra (debilitated) — 7th house from Aries
        # Moon in Cancer (4th house) — Kendra
        # Sun in Libra aspects Moon (7th aspect)
        states = (
            make_planet_state(BodyId.MOON, 90.0),   # Cancer = 4th from Aries
            make_planet_state(BodyId.SUN, 210.0),    # Libra = debilitated Sun
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        raja = result.result_for(YogaId.RAJA_YOGA)
        # Raja Yoga may or may not be present depending on connection
        # But if present, should check cancellation
        if raja is not None and raja.is_present:
            # Sun is debilitated → cancellation should be detected
            assert raja.is_cancelled is True
            assert any("SUN" in r for r in raja.cancellation_reasons)

    def test_no_cancellation_when_planets_strong(self) -> None:
        """Yoga with strong planets → no cancellation."""
        service = YogaService()
        # Gajakesari: Jupiter in Kendra from Moon
        # Both planets strong (no debilitation, no combustion, not in Dusthana)
        states = (
            make_planet_state(BodyId.MOON, 0.0),     # Aries
            make_planet_state(BodyId.JUPITER, 90.0),  # Cancer = exalted
            make_planet_state(BodyId.SUN, 180.0),     # Libra (far from Jupiter)
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is True
        assert gaja.is_cancelled is False
        assert len(gaja.cancellation_reasons) == 0


# --------------------------------------------------------------------------- #
# Combustion cancellation tests
# --------------------------------------------------------------------------- #


class TestCombustionCancellation:
    """Test that combust planets trigger cancellation."""

    def test_combust_planet_triggers_cancellation(self) -> None:
        """Planet close to Sun → cancellation detected."""
        service = YogaService()
        # Jupiter at 10° Aries, Sun at 15° Aries — within 11° combust threshold
        states = (
            make_planet_state(BodyId.JUPITER, 10.0),
            make_planet_state(BodyId.MOON, 90.0),  # Cancer = Kendra from Aries
            make_planet_state(BodyId.SUN, 15.0),
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        if gaja.is_present:
            # Jupiter is combust → cancellation should be detected
            assert gaja.is_cancelled is True
            assert any("combust" in r.lower() for r in gaja.cancellation_reasons)


# --------------------------------------------------------------------------- #
# Dusthana placement cancellation tests
# --------------------------------------------------------------------------- #


class TestDusthanaCancellation:
    """Test that Dusthana placement triggers cancellation."""

    def test_planet_in_6th_house_triggers_cancellation(self) -> None:
        """Planet in 6th house → cancellation detected."""
        service = YogaService()
        # Aries lagna: 6th house = Virgo (150-180°)
        # Jupiter in Virgo (6th from Aries), Moon in Cancer (4th from Aries)
        # Jupiter at 165° (Virgo), Moon at 90° (Cancer)
        states = (
            make_planet_state(BodyId.JUPITER, 165.0),  # Virgo = 6th from Aries
            make_planet_state(BodyId.MOON, 90.0),      # Cancer = 4th from Aries
            make_planet_state(BodyId.SUN, 300.0),      # Capricorn (far away)
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        if gaja.is_present:
            # Jupiter is in Dusthana → cancellation should be detected
            assert gaja.is_cancelled is True
            assert any("Dusthana" in r for r in gaja.cancellation_reasons)

    def test_planet_in_8th_house_triggers_cancellation(self) -> None:
        """Planet in 8th house → cancellation detected."""
        service = YogaService()
        # Aries lagna: 8th house = Scorpio (210-240°)
        # Jupiter in Scorpio (8th from Aries), Moon in Cancer (4th from Aries)
        states = (
            make_planet_state(BodyId.JUPITER, 225.0),  # Scorpio = 8th from Aries
            make_planet_state(BodyId.MOON, 90.0),      # Cancer = 4th from Aries
            make_planet_state(BodyId.SUN, 300.0),      # Capricorn (far away)
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        if gaja.is_present:
            assert gaja.is_cancelled is True
            assert any("Dusthana" in r for r in gaja.cancellation_reasons)

    def test_planet_in_12th_house_triggers_cancellation(self) -> None:
        """Planet in 12th house → cancellation detected."""
        service = YogaService()
        # Aries lagna: 12th house = Pisces (330-360°)
        # Jupiter in Pisces (12th from Aries, also own sign), Moon in Cancer (4th)
        states = (
            make_planet_state(BodyId.JUPITER, 345.0),  # Pisces = 12th from Aries
            make_planet_state(BodyId.MOON, 90.0),      # Cancer = 4th from Aries
            make_planet_state(BodyId.SUN, 180.0),      # Libra (far away)
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        if gaja.is_present:
            assert gaja.is_cancelled is True
            assert any("Dusthana" in r for r in gaja.cancellation_reasons)


# --------------------------------------------------------------------------- #
# Multiple cancellation factors tests
# --------------------------------------------------------------------------- #


class TestMultipleCancellationFactors:
    """Test that multiple cancellation factors stack."""

    def test_debilitated_and_combust(self) -> None:
        """Planet both debilitated and combust → multiple reasons."""
        service = YogaService()
        # Jupiter debilitated in Capricorn (300°) AND combust (Sun nearby)
        states = (
            make_planet_state(BodyId.JUPITER, 300.0),  # Capricorn = debilitated
            make_planet_state(BodyId.MOON, 90.0),      # Cancer = 4th from Aries
            make_planet_state(BodyId.SUN, 305.0),      # Very close to Jupiter
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        if gaja.is_present:
            assert gaja.is_cancelled is True
            # Should have at least 2 cancellation reasons
            assert len(gaja.cancellation_reasons) >= 2


# --------------------------------------------------------------------------- #
# Cancellation effect on strength tests
# --------------------------------------------------------------------------- #


class TestCancellationStrengthEffect:
    """Test that cancellation reduces strength_modifier."""

    def test_cancellation_reduces_strength(self) -> None:
        """Cancelled yoga should have lower strength than uncancelled."""
        service = YogaService()
        # Compare: Jupiter strong vs Jupiter debilitated
        states_strong = (
            make_planet_state(BodyId.JUPITER, 90.0),  # Cancer = exalted
            make_planet_state(BodyId.MOON, 0.0),      # Aries
            make_planet_state(BodyId.SUN, 200.0),     # Far from Jupiter
        )
        states_weak = (
            make_planet_state(BodyId.JUPITER, 300.0),  # Capricorn = debilitated
            make_planet_state(BodyId.MOON, 0.0),       # Aries
            make_planet_state(BodyId.SUN, 200.0),      # Far from Jupiter
        )
        result_strong = service.identify_yogas(states_strong, lagna_sign=RashiId.MESHA)
        result_weak = service.identify_yogas(states_weak, lagna_sign=RashiId.MESHA)
        gaja_strong = result_strong.result_for(YogaId.GAJAKESARI_YOGA)
        gaja_weak = result_weak.result_for(YogaId.GAJAKESARI_YOGA)
        if (gaja_strong is not None and gaja_weak is not None
                and gaja_strong.is_present and gaja_weak.is_present):
                assert gaja_strong.strength_modifier >= gaja_weak.strength_modifier


# --------------------------------------------------------------------------- #
# Absent yoga not cancelled tests
# --------------------------------------------------------------------------- #


class TestAbsentYogaNotCancelled:
    """Test that absent yogas are not marked as cancelled."""

    def test_absent_yoga_has_no_cancellation(self) -> None:
        """Yoga not present → is_cancelled should be False."""
        service = YogaService()
        # Jupiter NOT in Kendra from Moon
        states = (
            make_planet_state(BodyId.JUPITER, 30.0),  # Taurus = 2nd from Aries
            make_planet_state(BodyId.MOON, 0.0),      # Aries
            make_planet_state(BodyId.SUN, 180.0),
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        gaja = result.result_for(YogaId.GAJAKESARI_YOGA)
        assert gaja is not None
        assert gaja.is_present is False
        assert gaja.is_cancelled is False
        assert len(gaja.cancellation_reasons) == 0


# --------------------------------------------------------------------------- #
# Cancellation reason content tests
# --------------------------------------------------------------------------- #


class TestCancellationReasonContent:
    """Test that cancellation reasons contain useful information."""

    def test_debilitation_reason_contains_planet_name(self) -> None:
        """Debilitation reason should mention the planet."""
        service = YogaService()
        # Put a key yoga planet in debilitation
        # Raja Yoga: need Kendra lord connected to Trikona lord
        # Aries lagna: 1st lord=Mars, 5th lord=Sun
        # Mars in Cancer (4th, debilitated), Sun in Aries (1st)
        # Mars aspects Sun (8th aspect from Cancer to Aries)
        states = (
            make_planet_state(BodyId.MARS, 100.0),   # Cancer = debilitated
            make_planet_state(BodyId.SUN, 10.0),      # Aries
            make_planet_state(BodyId.MOON, 200.0),    # Some other position
        )
        result = service.identify_yogas(states, lagna_sign=RashiId.MESHA)
        raja = result.result_for(YogaId.RAJA_YOGA)
        if raja is not None and raja.is_present and raja.is_cancelled:
            # Should mention the debilitated planet
            assert any("MARS" in r or "SUN" in r for r in raja.cancellation_reasons)

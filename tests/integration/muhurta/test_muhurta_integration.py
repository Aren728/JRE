"""Integration tests for JRE-020 Muhurta.

Verifies the full MuhurtaEvaluation against known reference time windows,
ensuring end-to-end correctness from inputs through to
the final structural_flags and fitness_score output.
"""

from __future__ import annotations

from jyotish import NakshatraId

from muhurta.models import (
    Karana,
    MuhurtaCategory,
    MuhurtaEvaluation,
    Tithi,
    Var,
    Yoga,
)
from muhurta.service import MuhurtaService
from tests.unit.muhurta.conftest import make_panchanga, make_window


# --------------------------------------------------------------------------- #
# Reference: Marriage evaluation — highly favorable window
# --------------------------------------------------------------------------- #


class TestReferenceMarriageFavorable:
    """Reference: Marriage evaluation with all favorable elements."""

    def test_high_fitness_score(self) -> None:
        svc = MuhurtaService()
        window = make_window("2024-11-15T06:00:00Z", "2024-11-15T12:00:00Z")
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_TRITIYA,
            vara=Var.THURSDAY,
            nakshatra=NakshatraId.HASTA,
            yoga=Yoga.SUBHA,
            karana=Karana.BALAVA,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.MARRIAGE, panchanga)
        assert isinstance(result, MuhurtaEvaluation)
        # HASTA is required for MARRIAGE, THURSDAY is preferred → favorable flags
        assert any("Favorable" in f for f in result.structural_flags)
        assert any("Preferred" in f for f in result.structural_flags)
        # No inauspicious elements → high score
        assert result.fitness_score >= 1.0

    def test_flags_record_category(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        panchanga = make_panchanga(
            tithi=Tithi.KRISHNA_EKADASHI,
            vara=Var.THURSDAY,
            nakshatra=NakshatraId.HASTA,
            yoga=Yoga.SUBHA,
            karana=Karana.BALAVA,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.MARRIAGE, panchanga)
        # KRISHNA_EKADASHI is in MARRIAGE's avoided_tithis
        assert any("MARRIAGE" in f and "tithi" in f for f in result.structural_flags)


# --------------------------------------------------------------------------- #
# Reference: Marriage evaluation — unfavorable window
# --------------------------------------------------------------------------- #


class TestReferenceMarriageUnfavorable:
    """Reference: Marriage evaluation with multiple unfavorable elements."""

    def test_low_fitness_score(self) -> None:
        svc = MuhurtaService()
        window = make_window("2024-11-20T06:00:00Z", "2024-11-20T12:00:00Z")
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_NAVAMI,
            vara=Var.SATURDAY,
            nakshatra=NakshatraId.ARDRA,
            yoga=Yoga.SHULA,
            karana=Karana.VISHTI,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.MARRIAGE, panchanga)
        assert result.fitness_score < 0.5
        assert len(result.structural_flags) >= 3  # multiple flags

    def test_multiple_inauspicious_flags(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_NAVAMI,
            vara=Var.SATURDAY,
            nakshatra=NakshatraId.MRIGASHIRA,
            yoga=Yoga.SHULA,
            karana=Karana.VISHTI,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.MARRIAGE, panchanga)
        inausp_count = sum(1 for f in result.structural_flags if "Inauspicious" in f)
        assert inausp_count >= 2


# --------------------------------------------------------------------------- #
# Reference: Travel evaluation
# --------------------------------------------------------------------------- #


class TestReferenceTravel:
    """Reference: Travel evaluation against known window."""

    def test_travel_preferred_vara(self) -> None:
        svc = MuhurtaService()
        window = make_window("2024-11-18T06:00:00Z", "2024-11-18T12:00:00Z")
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_DASHAMI,
            vara=Var.MONDAY,
            nakshatra=NakshatraId.ASHWINI,
            yoga=Yoga.SIDDHI,
            karana=Karana.BALAVA,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.TRAVEL, panchanga)
        # ASHWINI is required for TRAVEL, MONDAY is preferred
        assert any("Favorable" in f for f in result.structural_flags)
        assert any("Preferred" in f for f in result.structural_flags)
        assert result.fitness_score >= 1.0

    def test_travel_tuesday_avoided(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_DASHAMI,
            vara=Var.TUESDAY,
            nakshatra=NakshatraId.ASHWINI,
            yoga=Yoga.SIDDHI,
            karana=Karana.BALAVA,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.TRAVEL, panchanga)
        assert any("Avoided vara" in f for f in result.structural_flags)
        assert result.fitness_score < 1.0


# --------------------------------------------------------------------------- #
# Reference: General evaluation
# --------------------------------------------------------------------------- #


class TestReferenceGeneral:
    """Reference: General evaluation — baseline behavior."""

    def test_general_neutral_window(self) -> None:
        svc = MuhurtaService()
        window = make_window("2024-11-15T06:00:00Z", "2024-11-15T12:00:00Z")
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_PANCHAMI,
            vara=Var.WEDNESDAY,
            nakshatra=NakshatraId.PUNARVASU,
            yoga=Yoga.SIDDHI,
            karana=Karana.TAITILA,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.GENERAL, panchanga)
        # No inauspicious elements, PUNARVASU is not in GENERAL's required → neutral
        assert 0.0 <= result.fitness_score <= 1.0

    def test_deterministic_output(self) -> None:
        svc = MuhurtaService()
        window = make_window()
        panchanga = make_panchanga()
        r1 = svc.evaluate_window(window, MuhurtaCategory.GENERAL, panchanga)
        r2 = svc.evaluate_window(window, MuhurtaCategory.GENERAL, panchanga)
        assert r1.to_dict() == r2.to_dict()


# --------------------------------------------------------------------------- #
# Reference: Business evaluation
# --------------------------------------------------------------------------- #


class TestReferenceBusiness:
    """Reference: Business evaluation against known window."""

    def test_business_friday_preferred(self) -> None:
        svc = MuhurtaService()
        window = make_window("2024-11-22T06:00:00Z", "2024-11-22T12:00:00Z")
        panchanga = make_panchanga(
            tithi=Tithi.SHUKLA_SAPTAMI,
            vara=Var.FRIDAY,
            nakshatra=NakshatraId.ROHINI,
            yoga=Yoga.SIDDHI,
            karana=Karana.BALAVA,
        )
        result = svc.evaluate_window(window, MuhurtaCategory.BUSINESS, panchanga)
        # ROHINI is required for BUSINESS, FRIDAY is preferred
        assert any("Favorable" in f for f in result.structural_flags)
        assert any("Preferred" in f for f in result.structural_flags)
        assert result.fitness_score >= 1.0

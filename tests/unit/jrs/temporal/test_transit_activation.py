"""Phase 2 Step 2: Transit Activation & Vedha Foundation tests.

Tests for:
- TransitActivationService with Dasha-First hierarchy (TA-001–005)
- VedhaService with 5 classical Vedha pairs (TA-015–019)
- TaraBalaService with 9-Tara cycle (TA-020–021)
"""

from __future__ import annotations

import pytest

from jrs.temporal.activation_service import (
    ActivationLevel,
    ActivationResult,
    TransitActivationService,
)
from jrs.temporal.tara_bala_service import TaraBalaService, TaraResult, TaraStrength
from jrs.temporal.vedha_service import VedhaResult, VedhaService


# ──────────────────────────────────────────────────────────────────────
# TransitActivationService
# ──────────────────────────────────────────────────────────────────────


class TestTransitActivationService:
    """RI-010D TA-001–005: Dasha-First hierarchy for transit activation."""

    def setup_method(self) -> None:
        self.svc = TransitActivationService()

    def test_dasha_lord_matches_yoga_planet_full_activation(self) -> None:
        """Active Dasha Lord in yoga + transit in Kendra → FULL_ACTIVATION."""
        result = self.svc.evaluate_transit_activation(
            transit_planet="JUPITER",
            transit_house=4,  # Kendra from Moon (house 1): diff=3
            natal_yoga_planets=["SUN", "JUPITER"],
            mahadasha_lord="JUPITER",
            antardasha_lord="MARS",
            natal_moon_house=1,
        )
        assert result.activation_level == ActivationLevel.FULL_ACTIVATION
        assert result.dasha_permission is True
        assert "JUPITER" in result.reason

    def test_antardasha_lord_matches_full_activation(self) -> None:
        """Antardasha Lord in yoga + transit aspect → FULL_ACTIVATION."""
        result = self.svc.evaluate_transit_activation(
            transit_planet="MARS",
            transit_house=4,  # Kendra from Moon (house 1)
            natal_yoga_planets=["SUN", "MERCURY"],
            mahadasha_lord="SATURN",
            antardasha_lord="MERCURY",
            natal_moon_house=1,
        )
        assert result.activation_level == ActivationLevel.FULL_ACTIVATION
        assert result.dasha_permission is True

    def test_no_dasha_alignment_sankalpa_phalam(self) -> None:
        """No Dasha alignment + transit aspect → SANKALPA_PHALAM (latent)."""
        result = self.svc.evaluate_transit_activation(
            transit_planet="SATURN",
            transit_house=7,  # Kendra from Moon (house 1)
            natal_yoga_planets=["SUN", "MERCURY"],
            mahadasha_lord="VENUS",
            antardasha_lord="MOON",
            natal_moon_house=1,
        )
        assert result.activation_level == ActivationLevel.SANKALPA_PHALAM
        assert result.dasha_permission is False

    def test_vedha_blocked_returns_blocked(self) -> None:
        """Vedha obstruction → BLOCKED regardless of Dasha."""
        result = self.svc.evaluate_transit_activation(
            transit_planet="SATURN",
            transit_house=7,
            natal_yoga_planets=["JUPITER"],
            mahadasha_lord="JUPITER",
            vedha_blocked=True,
        )
        assert result.activation_level == ActivationLevel.BLOCKED
        assert "Vedha" in result.reason

    def test_jupiter_exception_can_activate_without_dasha(self) -> None:
        """Jupiter transiting + Jupiter in yoga → permission (BPHS Ch 50 V.4)."""
        result = self.svc.evaluate_transit_activation(
            transit_planet="JUPITER",
            transit_house=10,  # Kendra from Moon (house 1)
            natal_yoga_planets=["JUPITER", "SUN"],
            mahadasha_lord="VENUS",
            antardasha_lord="MARS",
            natal_moon_house=1,
        )
        assert result.activation_level == ActivationLevel.FULL_ACTIVATION
        assert result.dasha_permission is True

    def test_transit_not_kendra_no_activation(self) -> None:
        """Transit not in Kendra from Moon → no transit relationship."""
        result = self.svc.evaluate_transit_activation(
            transit_planet="SATURN",
            transit_house=3,  # Not Kendra from Moon (house 1)
            natal_yoga_planets=["SUN"],
            mahadasha_lord="SUN",
            natal_moon_house=1,
        )
        # Dasha permission is True but transit doesn't relate
        assert result.activation_level == ActivationLevel.SANKALPA_PHALAM

    def test_activation_result_serialization(self) -> None:
        """ActivationResult.to_dict produces valid dict."""
        result = ActivationResult(
            activation_level=ActivationLevel.FULL_ACTIVATION,
            dasha_permission=True,
            transit_planet="JUPITER",
            transit_house=5,
            natal_yoga_planets=("SUN", "JUPITER"),
            reason="Test reason",
        )
        d = result.to_dict()
        assert d["activation_level"] == "FULL_ACTIVATION"
        assert d["dasha_permission"] is True
        assert d["natal_yoga_planets"] == ["SUN", "JUPITER"]


# ──────────────────────────────────────────────────────────────────────
# VedhaService
# ──────────────────────────────────────────────────────────────────────


class TestVedhaService:
    """RI-010D TA-015–019: Classical Vedha obstruction mechanics."""

    def setup_method(self) -> None:
        self.svc = VedhaService()

    def test_vedha_3_12_pair(self) -> None:
        """House 3 ↔ House 12 mutual Vedha."""
        result = self.svc.check_vedha(
            transit_planet="JUPITER",
            transit_house=3,
            natal_planets={
                "SATURN": {"house": 12, "retrograde": False},
            },
        )
        assert result.is_obstructed is True
        assert result.obstructing_planet == "SATURN"
        assert result.obstructing_house == 12

    def test_vedha_6_9_pair(self) -> None:
        """House 6 ↔ House 9 mutual Vedha."""
        result = self.svc.check_vedha(
            transit_planet="JUPITER",
            transit_house=6,
            natal_planets={
                "MARS": {"house": 9, "retrograde": False},
            },
        )
        assert result.is_obstructed is True
        assert result.obstructing_planet == "MARS"

    def test_vedha_5_11_pair(self) -> None:
        """House 5 ↔ House 11 mutual Vedha."""
        result = self.svc.check_vedha(
            transit_planet="JUPITER",
            transit_house=5,
            natal_planets={
                "SATURN": {"house": 11, "retrograde": False},
            },
        )
        assert result.is_obstructed is True

    def test_vedha_7_2_pair(self) -> None:
        """House 7 ↔ House 2 mutual Vedha (7 ↔ 14 = 7 ↔ 2)."""
        result = self.svc.check_vedha(
            transit_planet="JUPITER",
            transit_house=7,
            natal_planets={
                "MARS": {"house": 2, "retrograde": False},
            },
        )
        assert result.is_obstructed is True

    def test_retrograde_exemption(self) -> None:
        """Retrograde transiting planet is exempt from Vedha (TA-018)."""
        result = self.svc.check_vedha(
            transit_planet="SATURN",
            transit_house=3,
            natal_planets={
                "MARS": {"house": 12, "retrograde": False},
            },
            transit_retrograde=True,
        )
        # Transit SATURN retrograde → exempt from Vedha
        assert result.is_obstructed is False
        assert result.is_retrograde_exempt is True

    def test_benefic_does_not_obstruct(self) -> None:
        """Benefic planets do not cause Vedha (only malefics)."""
        result = self.svc.check_vedha(
            transit_planet="JUPITER",
            transit_house=3,
            natal_planets={
                "JUPITER": {"house": 12, "retrograde": False},
            },
        )
        assert result.is_obstructed is False

    def test_sun_saturn_exclusion(self) -> None:
        """Sun/Saturn are mutual exceptions — no Vedha between them."""
        result = self.svc.check_vedha(
            transit_planet="SUN",
            transit_house=3,
            natal_planets={
                "SATURN": {"house": 12, "retrograde": False},
            },
        )
        assert result.is_obstructed is False

    def test_no_vedha_unrelated_houses(self) -> None:
        """Houses not in Vedha pairs → no obstruction."""
        result = self.svc.check_vedha(
            transit_planet="JUPITER",
            transit_house=4,
            natal_planets={
                "SATURN": {"house": 8, "retrograde": False},
            },
        )
        assert result.is_obstructed is False

    def test_get_obstructing_houses(self) -> None:
        """Get all houses that form Vedha with a given house."""
        houses_3 = self.svc.get_obstructing_houses(3)
        assert 12 in houses_3

        houses_6 = self.svc.get_obstructing_houses(6)
        assert 9 in houses_6

        houses_5 = self.svc.get_obstructing_houses(5)
        assert 11 in houses_5

    def test_vedha_result_serialization(self) -> None:
        """VedhaResult.to_dict produces valid dict."""
        result = VedhaResult(
            is_obstructed=True,
            obstructing_planet="SATURN",
            obstructing_house=12,
            obstructed_house=3,
            reason="Test",
        )
        d = result.to_dict()
        assert d["is_obstructed"] is True
        assert d["obstructing_planet"] == "SATURN"


# ──────────────────────────────────────────────────────────────────────
# TaraBalaService
# ──────────────────────────────────────────────────────────────────────


class TestTaraBalaService:
    """RI-010D TA-020–021: Nakshatra-based Tara Bala strength."""

    def setup_method(self) -> None:
        self.svc = TaraBalaService()

    def test_tara_1_janma_neutral(self) -> None:
        """Same Nakshatra → Tara 1 (Janma) → NEUTRAL."""
        result = self.svc.evaluate_tara_bala("ASHWINI", "ASHWINI")
        assert result.tara_position == 1
        assert result.tara_name == "Janma"
        assert result.strength == TaraStrength.NEUTRAL

    def test_tara_2_sampat_favorable(self) -> None:
        """Nakshatra 2 from Moon → Tara 2 (Sampat) → FAVORABLE."""
        result = self.svc.evaluate_tara_bala("BHARANI", "ASHWINI")
        assert result.tara_position == 2
        assert result.tara_name == "Sampat"
        assert result.strength == TaraStrength.FAVORABLE

    def test_tara_3_vipat_unfavorable(self) -> None:
        """Nakshatra 3 from Moon → Tara 3 (Vipat) → UNFAVORABLE."""
        result = self.svc.evaluate_tara_bala("KRITTIKA", "ASHWINI")
        assert result.tara_position == 3
        assert result.tara_name == "Vipat"
        assert result.strength == TaraStrength.UNFAVORABLE

    def test_tara_7_naidhana_unfavorable(self) -> None:
        """Nakshatra 7 from Moon → Tara 7 (Naidhana) → UNFAVORABLE."""
        result = self.svc.evaluate_tara_bala("PUNARVASU", "ASHWINI")
        assert result.tara_position == 7
        assert result.tara_name == "Naidhana"
        assert result.strength == TaraStrength.UNFAVORABLE

    def test_tara_9_parama_mitra_favorable(self) -> None:
        """Nakshatra 9 from Moon → Tara 9 (Parama Mitra) → FAVORABLE."""
        result = self.svc.evaluate_tara_bala("ASHLESHA", "ASHWINI")
        assert result.tara_position == 9
        assert result.tara_name == "Parama Mitra"
        assert result.strength == TaraStrength.FAVORABLE

    def test_tara_wraps_around_27(self) -> None:
        """Tara calculation wraps correctly past Nakshatra 27."""
        # REVATI (27th) from ASHWINI (1st): raw_tara = 27
        # Tara = (27-1) mod 9 + 1 = 9 (Parama Mitra)
        result = self.svc.evaluate_tara_bala("REVATI", "ASHWINI")
        assert result.tara_position == 9
        assert result.strength == TaraStrength.FAVORABLE

    def test_tara_multiplier_favorable(self) -> None:
        """Favorable Tara gets multiplier ≥ 1.0."""
        result = TaraResult(
            tara_position=2,
            tara_name="Sampat",
            strength=TaraStrength.FAVORABLE,
        )
        mult = self.svc.get_tara_multiplier(result)
        assert mult >= 1.0

    def test_tara_multiplier_parama_mitra_highest(self) -> None:
        """Parama Mitra (9) gets highest favorable multiplier (1.2)."""
        result = TaraResult(
            tara_position=9,
            tara_name="Parama Mitra",
            strength=TaraStrength.FAVORABLE,
        )
        mult = self.svc.get_tara_multiplier(result)
        assert mult == 1.2

    def test_tara_multiplier_unfavorable(self) -> None:
        """Unfavorable Tara gets multiplier < 1.0."""
        result = TaraResult(
            tara_position=3,
            tara_name="Vipat",
            strength=TaraStrength.UNFAVORABLE,
        )
        mult = self.svc.get_tara_multiplier(result)
        assert mult < 1.0

    def test_tara_multiplier_naidhana_lowest(self) -> None:
        """Naidhana (7) gets lowest unfavorable multiplier (0.6)."""
        result = TaraResult(
            tara_position=7,
            tara_name="Naidhana",
            strength=TaraStrength.UNFAVORABLE,
        )
        mult = self.svc.get_tara_multiplier(result)
        assert mult == 0.6

    def test_unknown_nakshatra_returns_neutral(self) -> None:
        """Unknown Nakshatra returns neutral result."""
        result = self.svc.evaluate_tara_bala("UNKNOWN", "ASHWINI")
        assert result.tara_position == 0
        assert result.strength == TaraStrength.NEUTRAL

    def test_tara_result_serialization(self) -> None:
        """TaraResult.to_dict produces valid dict."""
        result = TaraResult(
            tara_position=2,
            tara_name="Sampat",
            strength=TaraStrength.FAVORABLE,
            transit_nakshatra="BHARANI",
            natal_moon_nakshatra="ASHWINI",
            reason="Test",
        )
        d = result.to_dict()
        assert d["tara_position"] == 2
        assert d["strength"] == "FAVORABLE"

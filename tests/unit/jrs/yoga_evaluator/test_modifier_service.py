"""Tests for ModifierEvaluationService (Phase 1, RI-010G).

Tests the 5-tier modifier priority pipeline:
    Tier 1: Combustion → CANCELLED (unless exalted/own-sign → WEAKENED)
    Tier 2: Debilitation / Neecha Bhanga
    Tier 3: Graha Yuddha (Planetary War)
    Tier 4: Cheshta Bala (Retrograde)
    Tier 5: Node Taint (Rahu/Ketu)
"""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.modifier_service import (
    ModifierEvaluationService,
    ModifierReport,
    ModifierResult,
    ModifierStatus,
    ModifierType,
)


class TestCombustionTier:
    """Tier 1: Combustion checks."""

    def test_combust_cancels_yoga(self) -> None:
        """Combust planet → CANCELLED (BPHS Ch 7)."""
        svc = ModifierEvaluationService()
        # Jupiter in Aries (1) — not exalted (4), not own sign (9/12)
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 1, "house": 5, "combust": True, "debilitated": False},
        )
        assert result.status == ModifierStatus.CANCELLED
        assert ModifierType.COMBUSTION in result.modifier_chain
        assert result.net_strength == 0.0
        assert "combust" in result.cancellation_reason.lower()

    def test_combust_exalted_weakened_not_cancelled(self) -> None:
        """Combust + Exalted → WEAKENED, not CANCELLED (Phaladeepika Ch 1)."""
        svc = ModifierEvaluationService()
        # Jupiter rashi_num 4 = Cancer = exaltation sign
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 4, "house": 1, "combust": True, "debilitated": False},
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.COMBUSTION_OFFSET in result.modifier_chain
        assert 0.0 < result.net_strength <= 0.5

    def test_combust_own_sign_weakened_not_cancelled(self) -> None:
        """Combust + Own Sign → WEAKENED, not CANCELLED (Saravali Ch 9)."""
        svc = ModifierEvaluationService()
        # Jupiter rashi_num 9 = Sagittarius = own sign
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 9, "house": 1, "combust": True, "debilitated": False},
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.COMBUSTION_OFFSET in result.modifier_chain

    def test_not_combust_not_cancelled(self) -> None:
        """Non-combust planet → not cancelled by combustion."""
        svc = ModifierEvaluationService()
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 9, "house": 1, "combust": False, "debilitated": False},
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.COMBUSTION not in result.modifier_chain


class TestDebilitationTier:
    """Tier 2: Debilitation / Neecha Bhanga checks."""

    def test_debilitated_cancels_yoga(self) -> None:
        """Debilitated planet without Neecha Bhanga → CANCELLED (BPHS Ch 43)."""
        svc = ModifierEvaluationService()
        # Jupiter rashi_num 10 = Capricorn = debilitated sign
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 10, "house": 6, "combust": False, "debilitated": True},
        )
        assert result.status == ModifierStatus.CANCELLED
        assert ModifierType.DEBILITATION in result.modifier_chain

    def test_neecha_bhanga_restores_yoga(self) -> None:
        """Debilitated + debilitation-sign lord in Kendra → Neecha Bhanga (BPHS Ch 43)."""
        svc = ModifierEvaluationService()
        # Jupiter debilitated in Capricorn (10). Lord of Capricorn = Saturn.
        # If Saturn is in house 1 (Kendra) → Neecha Bhanga
        result = svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 10,
                "house": 5,
                "combust": False,
                "debilitated": True,
                "SATURN_house": 1,  # Saturn in Kendra → Neecha Bhanga
            },
        )
        assert result.status != ModifierStatus.CANCELLED
        assert ModifierType.NEECHA_BHANGA in result.modifier_chain

    def test_not_debilitated_not_cancelled(self) -> None:
        """Non-debilitated planet → not cancelled by debilitation."""
        svc = ModifierEvaluationService()
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 9, "house": 1, "combust": False, "debilitated": False},
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.DEBILITATION not in result.modifier_chain


class TestGrahaYuddhaTier:
    """Tier 3: Planetary War checks."""

    def test_war_victor_maintains_strength(self) -> None:
        """Planet wins war → strength maintained."""
        svc = ModifierEvaluationService()
        # Jupiter rashi_num 2 = Taurus — not own, not exalted
        result = svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 2,
                "house": 1,
                "combust": False,
                "debilitated": False,
                "is_war": True,
                "war_victor": "JUPITER",
            },
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.GRAHA_YUDDHA_VICTOR in result.modifier_chain
        assert result.net_strength >= 0.9  # Strength maintained

    def test_war_loser_suppressed(self) -> None:
        """Planet loses war → strength suppressed."""
        svc = ModifierEvaluationService()
        # Mercury rashi_num 2 = Taurus — not own (3/6), not exalted (6)
        result = svc.evaluate_planet(
            "MERCURY",
            {
                "rashi_num": 2,
                "house": 1,
                "combust": False,
                "debilitated": False,
                "is_war": True,
                "war_victor": "SUN",
            },
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.GRAHA_YUDDHA_DEFEATED in result.modifier_chain
        assert result.net_strength <= 0.4  # Suppressed


class TestCheshtaBalaTier:
    """Tier 4: Retrograde (Cheshta Bala) checks."""

    def test_retrograde_increases_strength(self) -> None:
        """Retrograde planet → strength boost (BPHS Ch 5)."""
        svc = ModifierEvaluationService()
        # Saturn rashi_num 2 = Taurus — not own (10/11), not exalted (7)
        result = svc.evaluate_planet(
            "SATURN",
            {"rashi_num": 2, "house": 1, "combust": False, "debilitated": False, "retrograde": True},
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.CHESHTA_BALA in result.modifier_chain
        assert result.is_retrograde is True
        assert result.net_strength > 1.0  # Boosted above base

    def test_direct_no_retrograde_boost(self) -> None:
        """Direct planet → no retrograde boost."""
        svc = ModifierEvaluationService()
        result = svc.evaluate_planet(
            "SATURN",
            {"rashi_num": 10, "house": 1, "combust": False, "debilitated": False, "retrograde": False},
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.CHESHTA_BALA not in result.modifier_chain
        assert result.is_retrograde is False

    def test_combust_overrides_retrograde(self) -> None:
        """Combust + Retrograde → Combustion takes priority (BPHS Ch 7 v.31)."""
        svc = ModifierEvaluationService()
        # Saturn rashi_num 2 = Taurus — not own, not exalted
        result = svc.evaluate_planet(
            "SATURN",
            {"rashi_num": 2, "house": 1, "combust": True, "debilitated": False, "retrograde": True},
        )
        assert result.status == ModifierStatus.CANCELLED  # Combustion wins
        assert ModifierType.COMBUSTION in result.modifier_chain


class TestNodeTaintTier:
    """Tier 5: Node Taint (Rahu/Ketu) checks."""

    def test_node_conjunct_weakens_yoga(self) -> None:
        """Node conjunct yoga planet → WEAKENED (BPHS Ch 9 v.12)."""
        svc = ModifierEvaluationService()
        result = svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,
                "house": 1,
                "combust": False,
                "debilitated": False,
                "node_conjunct": True,
            },
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.NODE_TAINT in result.modifier_chain
        assert result.is_node_afflicted is True

    def test_no_node_no_taint(self) -> None:
        """No node conjunction → no taint."""
        svc = ModifierEvaluationService()
        result = svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,
                "house": 1,
                "combust": False,
                "debilitated": False,
                "node_conjunct": False,
            },
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.NODE_TAINT not in result.modifier_chain
        assert result.is_node_afflicted is False


class TestDusthanaPlacement:
    """Dusthana placement check."""

    def test_dusthana_weakens(self) -> None:
        """Planet in dusthana (6/8/12) → WEAKENED."""
        svc = ModifierEvaluationService()
        # Jupiter rashi_num 1 = Aries — not own, not exalted
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 1, "house": 6, "combust": False, "debilitated": False},
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.DUSTHANA_PLACEMENT in result.modifier_chain
        assert result.net_strength <= 0.6

    def test_kendra_not_weakened(self) -> None:
        """Planet in Kendra → not weakened by dusthana."""
        svc = ModifierEvaluationService()
        result = svc.evaluate_planet(
            "JUPITER",
            {"rashi_num": 9, "house": 1, "combust": False, "debilitated": False},
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.DUSTHANA_PLACEMENT not in result.modifier_chain


class TestMultiPlanetEvaluation:
    """Test evaluate_modifiers for multiple planets."""

    def test_one_combust_cancels_all(self) -> None:
        """If any planet in yoga is combust → entire yoga CANCELLED."""
        svc = ModifierEvaluationService()
        report = svc.evaluate_modifiers(
            involved_planets=["JUPITER", "MOON"],
            jre_facts={
                "planets": {
                    "JUPITER": {"house": 1, "combust": True, "debilitated": False},
                    "MOON": {"house": 4, "combust": False, "debilitated": False},
                }
            },
        )
        assert report.overall_status == ModifierStatus.CANCELLED
        assert report.overall_strength == 0.0

    def test_no_afflictions_all_formed(self) -> None:
        """No afflictions → all planets FORMED."""
        svc = ModifierEvaluationService()
        report = svc.evaluate_modifiers(
            involved_planets=["JUPITER", "MOON"],
            jre_facts={
                "planets": {
                    "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                    "MOON": {"house": 4, "combust": False, "debilitated": False},
                }
            },
        )
        assert report.overall_status == ModifierStatus.FORMED
        assert report.overall_strength >= 0.9

    def test_weakness_propagates(self) -> None:
        """If any planet is WEAKENED → overall WEAKENED."""
        svc = ModifierEvaluationService()
        report = svc.evaluate_modifiers(
            involved_planets=["JUPITER", "MOON"],
            jre_facts={
                "planets": {
                    "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                    # Moon rashi_num 1 = Aries — not own (4), not exalted (2)
                    "MOON": {"rashi_num": 1, "house": 8, "combust": False, "debilitated": False},
                }
            },
        )
        assert report.overall_status == ModifierStatus.WEAKENED

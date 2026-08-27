"""Phase 1 Integration Tests — YogaEvaluatorService + ModifierEvaluationService.

Verifies core Parashari formation/invalidation rules (KT-001–005, PA-001–012, MY-010–011)
through 6 synthetic chart scenarios.

Source: BPHS Ch 7, 33, 41, 42, 43; Phaladeepika Ch 1, 2, 4.
"""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.modifier_service import ModifierStatus, ModifierType
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


# ──────────────────────────────────────────────────────────────────────────────
# Synthetic Chart Fact Builders
# ──────────────────────────────────────────────────────────────────────────────

def _make_planet(
    house: int,
    combust: bool = False,
    debilitated: bool = False,
    retrograde: bool = False,
    node_conjunct: bool = False,
    rashi_num: int = 0,
    is_war: bool = False,
    war_victor: str | None = None,
) -> dict:
    """Build a minimal planet fact dict."""
    return {
        "house": house,
        "rashi_num": rashi_num,
        "combust": combust,
        "debilitated": debilitated,
        "retrograde": retrograde,
        "node_conjunct": node_conjunct,
        "is_war": is_war,
        "war_victor": war_victor,
    }


def _chart(**planets: dict) -> dict:
    """Wrap planet dicts into a JRE facts structure."""
    return {"planets": dict(planets)}


# ──────────────────────────────────────────────────────────────────────────────
# Test A: Pure Dharma-Karma Raja Yoga (5th Lord + 9th Lord conjunction)
# KT-001: Kendra lords + Trikona lords conjunction = Raja Yoga
# Expected: FORMED, full strength, no modifiers
# ──────────────────────────────────────────────────────────────────────────────

class TestPureDharmaKarmaRajaYoga:
    """Synthetic chart: 5th lord + 9th lord conjunct in 10th house, no afflictions."""

    def test_formation_status(self) -> None:
        """Raja Yoga with no afflictions → FORMED."""
        svc = YogaEvaluatorService()
        # Mars = 4th lord (Kendra), Jupiter = 5th lord (Trikona) conjunct in house 10
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),      # Scorpio
            JUPITER=_make_planet(house=10, rashi_num=8),   # Scorpio (conjunct)
        )
        # Use evaluate_formation directly (KT-001 core)
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.FORMED
        assert result.modifier_report is not None
        assert result.modifier_report.overall_status == ModifierStatus.FORMED

    def test_modifier_report_attached(self) -> None:
        """ModifierReport is attached to the YogaEvaluation."""
        svc = YogaEvaluatorService()
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(house=10, rashi_num=8),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.modifier_report is not None
        assert len(result.modifier_report.planet_results) == 2
        # No modifiers applied — both planets clean
        for pr in result.modifier_report.planet_results:
            assert len(pr.modifier_chain) == 0

    def test_to_dict_includes_modifier(self) -> None:
        """to_dict() includes modifier_report when present."""
        svc = YogaEvaluatorService()
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(house=10, rashi_num=8),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        d = result.to_dict()
        assert "modifier_report" in d
        assert d["modifier_report"]["overall_status"] == "FORMED"


# ──────────────────────────────────────────────────────────────────────────────
# Test B: Combust Dharma-Karma Raja Yoga (9th Lord combust Sun)
# MY-010: Combustion cancels yoga formation
# Expected: CANCELLED, reason = "JUPITER is combust"
# ──────────────────────────────────────────────────────────────────────────────

class TestCombustDharmaKarmaRajaYoga:
    """Synthetic chart: 9th lord Jupiter combust → yoga cancelled."""

    def test_combust_cancels_yoga(self) -> None:
        """Combust 9th lord → CANCELLED (BPHS Ch 7)."""
        svc = YogaEvaluatorService()
        # Jupiter rashi_num 1 = Aries — not own (9/12), not exalted (4)
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(house=10, combust=True, rashi_num=1),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.CANCELLED
        assert "combust" in result.cancellation_reason.lower()

    def test_combust_modifier_chain(self) -> None:
        """Combust planet shows COMBUSTION in modifier chain."""
        svc = YogaEvaluatorService()
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(house=10, combust=True, rashi_num=1),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.modifier_report is not None
        jup_result = next(
            pr for pr in result.modifier_report.planet_results if pr.planet == "JUPITER"
        )
        assert ModifierType.COMBUSTION in jup_result.modifier_chain
        assert jup_result.status == ModifierStatus.CANCELLED


# ──────────────────────────────────────────────────────────────────────────────
# Test C: Exalted Combust Exception
# PA-028: Combustion + exaltation → exaltation partially offsets combustion
# Expected: WEAKENED (not CANCELLED)
# ──────────────────────────────────────────────────────────────────────────────

class TestExaltedCombustException:
    """Synthetic chart: Jupiter exalted (Cancer) but combust → WEAKENED."""

    def test_exalted_combust_weakened(self) -> None:
        """Exalted + combust → WEAKENED, not CANCELLED (Phaladeepika Ch 1)."""
        svc = YogaEvaluatorService()
        # Jupiter rashi_num 4 = Cancer = exaltation
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(house=10, rashi_num=4, combust=True),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.WEAKENED
        assert result.modifier_report is not None
        jup_result = next(
            pr for pr in result.modifier_report.planet_results if pr.planet == "JUPITER"
        )
        assert ModifierType.COMBUSTION_OFFSET in jup_result.modifier_chain


# ──────────────────────────────────────────────────────────────────────────────
# Test D: Neecha Bhanga Raja Yoga
# PA-017: Debilitation-sign lord in Kendra → debilitation cancelled
# Expected: FORMED (via Neecha Bhanga)
# ──────────────────────────────────────────────────────────────────────────────

class TestNeechaBhangaRajaYoga:
    """Synthetic chart: Jupiter debilitated in Capricorn, Saturn (deb-lord) in Kendra."""

    def test_neecha_bhanga_restores_yoga(self) -> None:
        """Debilitated + deb-lord in Kendra → Neecha Bhanga (BPHS Ch 43)."""
        svc = YogaEvaluatorService()
        # Jupiter rashi_num 10 = Capricorn = debilitated
        # Saturn (deb-lord of Jupiter) in house 1 = Kendra
        facts = _chart(
            MARS=_make_planet(house=5, rashi_num=8),
            JUPITER=_make_planet(house=5, rashi_num=10, debilitated=True),
            SATURN=_make_planet(house=1, rashi_num=10),  # Saturn in Kendra
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        # Jupiter is debilitated but Neecha Bhanga applies
        assert result.modifier_report is not None
        jup_result = next(
            pr for pr in result.modifier_report.planet_results if pr.planet == "JUPITER"
        )
        assert ModifierType.NEECHA_BHANGA in jup_result.modifier_chain
        # Overall should be FORMED (via Neecha Bhanga restoration)
        assert result.status == YogaStatus.FORMED


# ──────────────────────────────────────────────────────────────────────────────
# Test E: Graha Yuddha Suppression
# MY-018: Planetary war — loser's results suppressed
# Expected: WEAKENED (loser strength = 0.3x)
# ──────────────────────────────────────────────────────────────────────────────

class TestGrahaYuddhaSuppression:
    """Synthetic chart: Jupiter loses war to Sun → suppressed."""

    def test_war_loser_suppressed(self) -> None:
        """Planet loses war → WEAKENED (Saravali Ch 24)."""
        svc = YogaEvaluatorService()
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(
                house=10, rashi_num=8,
                is_war=True, war_victor="SUN",
            ),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.modifier_report is not None
        jup_result = next(
            pr for pr in result.modifier_report.planet_results if pr.planet == "JUPITER"
        )
        assert ModifierType.GRAHA_YUDDHA in jup_result.modifier_chain
        assert jup_result.net_strength <= 0.4  # Suppressed
        # Overall yoga should be WEAKENED due to low strength
        assert result.status == YogaStatus.WEAKENED

    def test_war_victor_maintains(self) -> None:
        """Planet wins war → strength maintained."""
        svc = YogaEvaluatorService()
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(
                house=10, rashi_num=8,
                is_war=True, war_victor="JUPITER",
            ),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.modifier_report is not None
        jup_result = next(
            pr for pr in result.modifier_report.planet_results if pr.planet == "JUPITER"
        )
        assert jup_result.net_strength >= 0.9  # Maintained


# ──────────────────────────────────────────────────────────────────────────────
# Test F: Parivartana Yoga (Reciprocal Sign Exchange)
# PA-006: Exchange, conjunction, and mutual aspect structurally equivalent
# Expected: FORMED via exchange relationship
# ──────────────────────────────────────────────────────────────────────────────

class TestParivartanaYoga:
    """Synthetic chart: 1st lord and 10th lord in exchange → Raja Yoga."""

    def test_exchange_forms_raja_yoga(self) -> None:
        """Reciprocal exchange between Kendra and Trikona lord → FORMED."""
        svc = YogaEvaluatorService()
        # Mars (4th lord) in Taurus (Venus's sign)
        # Venus (7th lord) in Aries (Mars's sign)
        # This is a Parivartana between two Kendra lords
        facts = _chart(
            MARS=_make_planet(house=4, rashi_num=2),      # Taurus (lord Venus)
            VENUS=_make_planet(house=10, rashi_num=1),    # Aries (lord Mars)
        )
        # Direct formation check — exchange qualifies as connection
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "VENUS"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.FORMED
        assert result.modifier_report is not None

    def test_exchange_no_afflictions_full_strength(self) -> None:
        """Exchange with no afflictions → full modifier strength."""
        svc = YogaEvaluatorService()
        facts = _chart(
            MARS=_make_planet(house=4, rashi_num=2),
            VENUS=_make_planet(house=10, rashi_num=1),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "VENUS"],
            jre_facts=facts,
        )
        assert result.modifier_report is not None
        for pr in result.modifier_report.planet_results:
            assert len(pr.modifier_chain) == 0  # No modifiers applied


# ──────────────────────────────────────────────────────────────────────────────
# Test G: Retrograde Boost (Cheshta Bala)
# MY-012: Retrograde planet gains Cheshta Bala
# Expected: FORMED with strength > 1.0
# ──────────────────────────────────────────────────────────────────────────────

class TestRetrogradeBoost:
    """Synthetic chart: Retrograde Jupiter in Raja Yoga → strength boost."""

    def test_retrograde_increases_strength(self) -> None:
        """Retrograde planet → FORMED with boosted strength (BPHS Ch 5)."""
        svc = YogaEvaluatorService()
        # Jupiter rashi_num 2 = Taurus — not own, not exalted
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(house=10, rashi_num=8, retrograde=True),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.FORMED
        assert result.modifier_report is not None
        jup_result = next(
            pr for pr in result.modifier_report.planet_results if pr.planet == "JUPITER"
        )
        assert ModifierType.CHESHTA_BALA in jup_result.modifier_chain
        assert jup_result.net_strength > 1.0  # Boosted above base


# ──────────────────────────────────────────────────────────────────────────────
# Test H: Node Taint Weakens
# PA-011: Rahu/Ketu conjunct yoga-forming planet → WEAKENED
# Expected: WEAKENED (not cancelled)
# ──────────────────────────────────────────────────────────────────────────────

class TestNodeTaint:
    """Synthetic chart: Rahu conjunct yoga planet → WEAKENED."""

    def test_node_conjunct_weakens(self) -> None:
        """Node conjunct yoga planet → WEAKENED (BPHS Ch 9 v.12)."""
        svc = YogaEvaluatorService()
        facts = _chart(
            MARS=_make_planet(house=10, rashi_num=8),
            JUPITER=_make_planet(house=10, rashi_num=8, node_conjunct=True),
        )
        result = svc.evaluate_formation(
            yoga_name="Raja",
            involved_planets=["MARS", "JUPITER"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.WEAKENED
        assert result.modifier_report is not None
        jup_result = next(
            pr for pr in result.modifier_report.planet_results if pr.planet == "JUPITER"
        )
        assert ModifierType.NODE_TAINT in jup_result.modifier_chain
        assert jup_result.is_node_afflicted is True

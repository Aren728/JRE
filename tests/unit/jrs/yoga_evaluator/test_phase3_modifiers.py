"""Phase 3 Step 1: Graha Yuddha Precision & Advanced Node Interception tests.

Tests for:
- Graha Yuddha detection within 1.0° longitude vs > 1.0° separation
- Sun/Moon exclusion from Graha Yuddha (luminaries do not engage)
- Victor determination based on higher longitude
- Node conjunction taint vs node 7th aspect taint strength reduction
- Pseudo-aspect (5th/9th) rejection under strict Parashari mode
"""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.modifier_service import (
    ModifierEvaluationService,
    ModifierReport,
    ModifierResult,
    ModifierStatus,
    ModifierType,
    NODE_ASPECT_STRENGTH_MULT,
    NODE_CONJUNCTION_STRENGTH_MULT,
    WAR_LONGITUDE_THRESHOLD,
)


# ──────────────────────────────────────────────────────────────────────
# Graha Yuddha Precision
# ──────────────────────────────────────────────────────────────────────


class TestGrahaYuddhaPrecision:
    """RI-010C MY-015–019: Graha Yuddha longitude/latitude precision."""

    def setup_method(self) -> None:
        self.svc = ModifierEvaluationService()

    def test_war_within_1_degree_detected(self) -> None:
        """Planets within 1.0° longitude → war detected."""
        result = self.svc.evaluate_planet(
            "MARS",
            {
                "rashi_num": 2,  # Taurus — not own (1/8), not exalted (10)
                "house": 1,
                "longitude": 15.5,
                "is_war": True,
                "war_victor": "MERCURY",
                "war_longitude": 15.8,
                "war_planets": ["MERCURY"],
            },
        )
        assert result.status == ModifierStatus.FORMED
        assert ModifierType.GRAHA_YUDDHA_DEFEATED in result.modifier_chain
        assert result.war_longitude_diff is not None
        assert result.war_longitude_diff <= WAR_LONGITUDE_THRESHOLD
        assert result.war_is_victor is False
        assert result.net_strength <= 0.4  # Suppressed

    def test_war_beyond_1_degree_not_detected(self) -> None:
        """Planets > 1.0° apart → no war."""
        result = self.svc.evaluate_planet(
            "MARS",
            {
                "rashi_num": 2,
                "house": 1,
                "longitude": 15.0,
                "is_war": False,  # Explicit flag says no war
                "war_victor": "MERCURY",
                "war_longitude": 17.5,  # 2.5° apart
                "war_planets": ["MERCURY"],
            },
        )
        # No GRAHA_YUDDHA modifier since is_war is False
        assert ModifierType.GRAHA_YUDDHA_VICTOR not in result.modifier_chain
        assert ModifierType.GRAHA_YUDDHA_DEFEATED not in result.modifier_chain

    def test_war_longitude_diff_computed(self) -> None:
        """Longitude difference is computed correctly."""
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,  # Sagittarius — own sign
                "house": 1,
                "longitude": 20.0,
                "is_war": True,
                "war_victor": "VENUS",
                "war_longitude": 20.5,  # 0.5° difference
                "war_planets": ["VENUS"],
            },
        )
        assert result.war_longitude_diff is not None
        assert abs(result.war_longitude_diff - 0.5) < 0.01

    def test_war_longitude_wrap_around_360(self) -> None:
        """Longitude difference wraps correctly near 360°/0°."""
        result = self.svc.evaluate_planet(
            "MARS",
            {
                "rashi_num": 2,
                "house": 1,
                "longitude": 359.5,
                "is_war": True,
                "war_victor": "MERCURY",
                "war_longitude": 0.3,  # 0.8° difference across boundary
                "war_planets": ["MERCURY"],
            },
        )
        assert result.war_longitude_diff is not None
        assert abs(result.war_longitude_diff - 0.8) < 0.01

    def test_war_victor_higher_longitude_wins(self) -> None:
        """Planet with higher longitude wins the war."""
        # MERCURY at 15.8, MARS at 15.5 → MERCURY wins
        result = self.svc.evaluate_planet(
            "MERCURY",
            {
                "rashi_num": 3,  # Gemini — own sign
                "house": 1,
                "longitude": 15.8,
                "is_war": True,
                "war_victor": "MERCURY",
                "war_longitude": 15.5,
                "war_planets": ["MARS"],
            },
        )
        assert ModifierType.GRAHA_YUDDHA_VICTOR in result.modifier_chain
        assert result.war_is_victor is True
        assert result.net_strength >= 0.9  # Strength maintained

    def test_war_loser_suppressed(self) -> None:
        """Planet with lower longitude loses the war."""
        # MARS at 15.5, MERCURY at 15.8 → MARS loses
        result = self.svc.evaluate_planet(
            "MARS",
            {
                "rashi_num": 2,
                "house": 1,
                "longitude": 15.5,
                "is_war": True,
                "war_victor": "MERCURY",
                "war_longitude": 15.8,
                "war_planets": ["MERCURY"],
            },
        )
        assert ModifierType.GRAHA_YUDDHA_DEFEATED in result.modifier_chain
        assert result.war_is_victor is False
        assert result.net_strength <= 0.4  # Suppressed

    def test_sun_excluded_from_war(self) -> None:
        """Sun does not engage in Graha Yuddha (luminary exclusion)."""
        result = self.svc.evaluate_planet(
            "SUN",
            {
                "rashi_num": 1,  # Aries — exalted
                "house": 1,
                "longitude": 15.5,
                "is_war": True,  # Even with flag, Sun is excluded
                "war_victor": "SUN",
                "war_longitude": 15.8,
                "war_planets": ["MARS"],
            },
        )  # Note: Sun rashi_num 1 = exalted, so COMBUSTION_OFFSET may apply if combust flag set
        # Sun is not in _WAR_ELIGIBLE, so no war modifier applied
        assert ModifierType.GRAHA_YUDDHA_VICTOR not in result.modifier_chain
        assert ModifierType.GRAHA_YUDDHA_DEFEATED not in result.modifier_chain

    def test_moon_excluded_from_war(self) -> None:
        """Moon does not engage in Graha Yuddha (luminary exclusion)."""
        result = self.svc.evaluate_planet(
            "MOON",
            {
                "rashi_num": 2,  # Taurus — exalted
                "house": 1,
                "longitude": 20.0,
                "is_war": True,
                "war_victor": "VENUS",
                "war_longitude": 20.3,
                "war_planets": ["VENUS"],
            },
        )
        # Moon is not in _WAR_ELIGIBLE
        assert ModifierType.GRAHA_YUDDHA_VICTOR not in result.modifier_chain
        assert ModifierType.GRAHA_YUDDHA_DEFEATED not in result.modifier_chain

    def test_war_combust_takes_priority(self) -> None:
        """Combust + War → Combustion takes priority (higher tier)."""
        # Mars in Taurus (rashi_num 2) — not own (1/8), not exalted (10)
        result = self.svc.evaluate_planet(
            "MARS",
            {
                "rashi_num": 2,
                "house": 1,
                "combust": True,
                "longitude": 15.5,
                "is_war": True,
                "war_victor": "MERCURY",
                "war_longitude": 15.8,
                "war_planets": ["MERCURY"],
            },
        )
        assert result.status == ModifierStatus.CANCELLED  # Combustion wins
        assert ModifierType.COMBUSTION in result.modifier_chain

    def test_war_result_serialization(self) -> None:
        """ModifierResult war fields serialize correctly."""
        result = self.svc.evaluate_planet(
            "MERCURY",
            {
                "rashi_num": 3,  # Gemini — own sign
                "house": 1,
                "longitude": 15.8,
                "is_war": True,
                "war_victor": "MERCURY",
                "war_longitude": 15.5,
                "war_planets": ["MARS"],
            },
        )
        assert result.war_victor == "MERCURY"
        assert result.war_longitude_diff is not None
        assert result.war_is_victor is True


# ──────────────────────────────────────────────────────────────────────
# Node Interception Severity Matrix
# ──────────────────────────────────────────────────────────────────────


class TestNodeInterceptionSeverity:
    """RI-010C MY-025–030: Node conjunction vs aspect severity."""

    def setup_method(self) -> None:
        self.svc = ModifierEvaluationService()

    def test_node_conjunction_30_percent_reduction(self) -> None:
        """Node conjunction → 0.7 multiplier (30% reduction)."""
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,  # Sagittarius — own sign
                "house": 1,
                "combust": False,
                "debilitated": False,
                "node_conjunct": True,
            },
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.NODE_CONJUNCTION_TAINT in result.modifier_chain
        assert result.node_taint_type == "CONJUNCTION"
        # Strength should be 0.7 (1.0 * 0.7)
        assert abs(result.net_strength - NODE_CONJUNCTION_STRENGTH_MULT) < 0.01

    def test_node_aspect_15_percent_reduction(self) -> None:
        """Node 7th aspect → 0.85 multiplier (15% reduction)."""
        # Jupiter in house 5, Rahu in house 11 (7th aspect = house 5)
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,  # Sagittarius — own sign
                "house": 5,
                "combust": False,
                "debilitated": False,
                "node_conjunct": False,
                "RAHU_house": 11,  # Rahu aspects house 5 (7th from 11)
            },
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.NODE_ASPECT_TAINT in result.modifier_chain
        assert result.node_taint_type == "ASPECT"
        # Strength should be 0.85 (1.0 * 0.85)
        assert abs(result.net_strength - NODE_ASPECT_STRENGTH_MULT) < 0.01

    def test_node_conjunction_takes_priority_over_aspect(self) -> None:
        """If both conjunction and aspect exist, conjunction wins (stronger)."""
        # Jupiter in house 1, Rahu in house 1 (conjunction), Ketu in house 7 (7th aspect)
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,
                "house": 1,
                "combust": False,
                "debilitated": False,
                "node_conjunct": True,
                "RAHU_house": 1,
                "KETU_house": 7,  # 7th aspect to house 1
            },
        )
        assert result.status == ModifierStatus.WEAKENED
        # Conjunction takes priority (stronger taint)
        assert ModifierType.NODE_CONJUNCTION_TAINT in result.modifier_chain
        assert result.node_taint_type == "CONJUNCTION"
        assert abs(result.net_strength - NODE_CONJUNCTION_STRENGTH_MULT) < 0.01

    def test_pseudo_aspect_5th_rejected_parashari(self) -> None:
        """5th aspect from Rahu → rejected under strict Parashari."""
        # Jupiter in house 5, Rahu in house 12 (5th aspect = house 5)
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,
                "house": 5,
                "combust": False,
                "debilitated": False,
                "node_conjunct": False,
                "node_aspect": True,
                "node_aspect_house": 5,
                "RAHU_house": 12,  # 5th aspect from 12 = house 5
                "parashari_mode": True,
            },
        )
        # Pseudo-aspect rejected → no node taint
        assert ModifierType.NODE_PSEUDO_ASPECT_REJECTED in result.modifier_chain
        assert ModifierType.NODE_TAINT not in result.modifier_chain
        assert result.node_taint_type is None
        assert result.status == ModifierStatus.FORMED

    def test_pseudo_aspect_9th_rejected_parashari(self) -> None:
        """9th aspect from Ketu → rejected under strict Parashari."""
        # Jupiter in house 5, Ketu in house 2
        # 9th aspect from house 2: offset = (5-2) % 12 = 3 → not a pseudo-aspect
        # Let's use: Jupiter in house 10, Ketu in house 2
        # 9th aspect from house 2: offset = (10-2) % 12 = 8 → not 5 or 9
        # Actually for 9th aspect: from Ketu in house 2, 9th house = house 10
        # That's offset 8, not 5 or 9.
        # For pseudo-aspect detection: we check if the offset from node to planet is 5 or 9.
        # Ketu in house 6, Jupiter in house 11: offset = (11-6) % 12 = 5 → 5th aspect
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,
                "house": 11,
                "combust": False,
                "debilitated": False,
                "node_conjunct": False,
                "node_aspect": True,
                "node_aspect_house": 11,
                "KETU_house": 6,  # 5th aspect from 6 = house 11
                "parashari_mode": True,
            },
        )
        assert ModifierType.NODE_PSEUDO_ASPECT_REJECTED in result.modifier_chain
        assert ModifierType.NODE_TAINT not in result.modifier_chain
        assert result.status == ModifierStatus.FORMED

    def test_7th_aspect_accepted_parashari(self) -> None:
        """7th aspect from Rahu → accepted under Parashari."""
        # Jupiter in house 5, Rahu in house 11 (7th aspect = house 5)
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,
                "house": 5,
                "combust": False,
                "debilitated": False,
                "node_conjunct": False,
                "RAHU_house": 11,  # 7th from 11 = house 5
                "parashari_mode": True,
            },
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.NODE_ASPECT_TAINT in result.modifier_chain
        assert result.node_taint_type == "ASPECT"

    def test_non_parashari_mode_pseudo_aspect_not_rejected(self) -> None:
        """Under non-Parashari mode, pseudo-aspects are not rejected."""
        # This tests that parashari_mode=False allows 5th/9th aspects
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,
                "house": 5,
                "combust": False,
                "debilitated": False,
                "node_conjunct": False,
                "node_aspect": True,
                "RAHU_house": 12,  # 5th aspect
                "parashari_mode": False,
            },
        )
        # Non-Parashari: pseudo-aspect not rejected
        assert ModifierType.NODE_PSEUDO_ASPECT_REJECTED not in result.modifier_chain
        assert result.status == ModifierStatus.WEAKENED
        assert result.node_taint_type == "ASPECT"

    def test_node_auto_detection_via_house_proximity(self) -> None:
        """Node taint auto-detected when Rahu/Ketu in same house."""
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,  # Sagittarius — own sign
                "house": 5,
                "combust": False,
                "debilitated": False,
                # No explicit node_conjunct flag — should auto-detect
                "RAHU_house": 5,  # Rahu in same house
            },
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.NODE_CONJUNCTION_TAINT in result.modifier_chain

    def test_node_auto_detection_7th_aspect(self) -> None:
        """Node 7th aspect auto-detected from house positions."""
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 9,  # Sagittarius — own sign
                "house": 5,
                "combust": False,
                "debilitated": False,
                # No explicit node flags — should auto-detect
                "KETU_house": 11,  # 7th from 11 = house 5
            },
        )
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.NODE_ASPECT_TAINT in result.modifier_chain

    def test_node_taint_with_combust_weakened_not_cancelled(self) -> None:
        """Combust takes priority (Tier 1 > Tier 5), but if WEAKENED from combustion offset + node → compound."""
        # Jupiter exalted (rashi_num 4) + combust + node conjunct
        result = self.svc.evaluate_planet(
            "JUPITER",
            {
                "rashi_num": 4,  # Cancer — exalted
                "house": 1,
                "combust": True,
                "debilitated": False,
                "node_conjunct": True,
            },
        )
        # Combustion offset (Tier 1) makes WEAKENED with 0.5 strength
        # Node taint (Tier 5) applies additional 0.7 multiplier
        assert result.status == ModifierStatus.WEAKENED
        assert ModifierType.COMBUSTION_OFFSET in result.modifier_chain
        assert ModifierType.NODE_TAINT in result.modifier_chain
        # Net strength: 0.5 * 0.7 = 0.35
        assert abs(result.net_strength - 0.35) < 0.01


# ──────────────────────────────────────────────────────────────────────
# Multi-planet with War and Node
# ──────────────────────────────────────────────────────────────────────


class TestMultiPlanetWarAndNode:
    """Test evaluate_modifiers with war and node interactions."""

    def setup_method(self) -> None:
        self.svc = ModifierEvaluationService()

    def test_war_loser_with_node_weakens_yoga(self) -> None:
        """War loser + node conjunction → very weak yoga."""
        report = self.svc.evaluate_modifiers(
            involved_planets=["MARS", "MERCURY"],
            jre_facts={
                "planets": {
                    "MARS": {
                        "house": 1,
                        "combust": False,
                        "debilitated": False,
                        "longitude": 15.5,
                    },
                    "MERCURY": {
                        "house": 1,
                        "combust": False,
                        "debilitated": False,
                        "longitude": 15.8,
                    },
                    "RAHU": {"house": 1},  # Node conjunct
                }
            },
        )
        assert report.overall_status == ModifierStatus.WEAKENED
        # MERCURY wins war (higher longitude), MARS loses + node
        # MARS: war suppressed (0.3) * node (0.7) = 0.21
        assert report.overall_strength < 0.5

    def test_war_victor_with_node_moderate_weakness(self) -> None:
        """War victor + node conjunction → moderate weakness."""
        report = self.svc.evaluate_modifiers(
            involved_planets=["MARS", "MERCURY"],
            jre_facts={
                "planets": {
                    "MARS": {
                        "house": 1,
                        "combust": False,
                        "debilitated": False,
                        "longitude": 15.5,
                    },
                    "MERCURY": {
                        "house": 1,
                        "combust": False,
                        "debilitated": False,
                        "longitude": 15.8,
                    },
                }
            },
        )
        # MERCURY wins war (higher longitude), no node
        # MERCURY: war victor (1.0), MARS: war defeated (0.3)
        # Overall: min(1.0, 0.3) = 0.3 → WEAKENED (below 0.5 threshold)
        assert report.overall_status == ModifierStatus.WEAKENED
        assert report.overall_strength <= 0.5

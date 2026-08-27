"""JRS Phase 1: Modifier Evaluation Service — 5-tier priority pipeline.

Implements the classical modifier priority hierarchy from RI-010C/RI-010G:

    Tier 1: Combustion Check → CANCELLED (unless exalted/own-sign → WEAKENED)
    Tier 2: Debilitation / Neecha Bhanga Check
    Tier 3: Graha Yuddha (Planetary War) Check
    Tier 4: Cheshta Bala (Retrograde) Check → strength modifier
    Tier 5: Node Taint (Rahu/Ketu) Check → WEAKENED

Source: BPHS Ch 7, 33, 41; Phaladeepika Ch 1; Saravali Ch 6, 9, 24.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional


class ModifierStatus(StrEnum):
    """Status after modifier evaluation."""
    FORMED = "FORMED"
    CANCELLED = "CANCELLED"
    WEAKENED = "WEAKENED"


class ModifierType(StrEnum):
    """Types of modifiers applied."""
    COMBUSTION = "COMBUSTION"
    COMBUSTION_OFFSET = "COMBUSTION_OFFSET"
    DEBILITATION = "DEBILITATION"
    NEECHA_BHANGA = "NEECHA_BHANGA"
    GRAHA_YUDDHA = "GRAHA_YUDDHA"
    CHESHTA_BALA = "CHESHTA_BALA"
    NODE_TAINT = "NODE_TAINT"
    DUSTHANA_PLACEMENT = "DUSTHANA_PLACEMENT"


# Exaltation signs (1-indexed rashi number)
_EXALTATION: dict[str, int] = {
    "SUN": 1,       # Aries
    "MOON": 2,      # Taurus
    "MARS": 10,     # Capricorn
    "MERCURY": 6,   # Virgo
    "JUPITER": 4,   # Cancer
    "VENUS": 12,    # Pisces
    "SATURN": 7,    # Libra
}

# Own signs (1-indexed rashi numbers)
_OWN_SIGNS: dict[str, tuple[int, ...]] = {
    "SUN": (5,),
    "MOON": (4,),
    "MARS": (1, 8),
    "MERCURY": (3, 6),
    "JUPITER": (9, 12),
    "VENUS": (2, 7),
    "SATURN": (10, 11),
}

# Debilitation signs (1-indexed rashi number)
_DEBILITATION: dict[str, int] = {
    "SUN": 7,       # Libra
    "MOON": 8,      # Scorpio
    "MARS": 4,      # Cancer
    "MERCURY": 12,  # Pisces
    "JUPITER": 10,  # Capricorn
    "VENUS": 6,     # Virgo
    "SATURN": 1,    # Aries
}

# Debilitation-sign lord mapping (for Neecha Bhanga)
_DEBILITATION_SIGN_LORD: dict[str, str] = {
    "SUN": "VENUS",
    "MOON": "MARS",
    "MARS": "MOON",
    "MERCURY": "JUPITER",
    "JUPITER": "SATURN",
    "VENUS": "MERCURY",
    "SATURN": "MARS",
}

# Dusthana houses
_DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})

# Kendra houses
_KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})

# Rahu/Ketu names
_NODE_NAMES: frozenset[str] = frozenset({"RAHU", "KETU"})


@dataclass(frozen=True)
class ModifierResult:
    """Result of 5-tier modifier evaluation for a single planet."""
    planet: str
    status: ModifierStatus
    modifier_chain: tuple[ModifierType, ...] = ()
    net_strength: float = 1.0
    cancellation_reason: Optional[str] = None
    is_vargottama: bool = False
    is_retrograde: bool = False
    is_combust: bool = False
    is_debilitated: bool = False
    is_node_afflicted: bool = False
    war_victor: Optional[str] = None


@dataclass(frozen=True)
class ModifierReport:
    """Aggregated modifier report for all planets in a yoga."""
    planet_results: tuple[ModifierResult, ...] = ()
    overall_status: ModifierStatus = ModifierStatus.FORMED
    overall_strength: float = 1.0
    cancellation_reason: Optional[str] = None


class ModifierEvaluationService:
    """5-tier modifier priority evaluation for yoga-forming planets.

    Implements the classical modifier hierarchy from RI-010C/RI-010G:
        Tier 1: Combustion → CANCELLED (unless exalted/own-sign → WEAKENED)
        Tier 2: Debilitation / Neecha Bhanga
        Tier 3: Graha Yuddha (Planetary War)
        Tier 4: Cheshta Bala (Retrograde)
        Tier 5: Node Taint (Rahu/Ketu)
    """

    def evaluate_planet(
        self,
        planet: str,
        planet_facts: dict[str, Any],
    ) -> ModifierResult:
        """Evaluate all modifiers for a single planet.

        Args:
            planet: Planet name (e.g., "SUN", "JUPITER").
            planet_facts: Dictionary with planet data:
                {
                    "rashi_num": int,       # 1-indexed rashi number
                    "house": int,           # 1-indexed house number
                    "combust": bool,
                    "debilitated": bool,
                    "retrograde": bool,
                    "longitude": float,     # for war detection
                    "sign_lord": str,       # lord of current sign
                }

        Returns:
            ModifierResult with status and applied modifiers.
        """
        modifiers: list[ModifierType] = []
        strength = 1.0
        cancellation_reason: Optional[str] = None
        status = ModifierStatus.FORMED

        rashi_num = planet_facts.get("rashi_num", 0)
        house = planet_facts.get("house", 0)
        is_combust = planet_facts.get("combust", False)
        is_debilitated = planet_facts.get("debilitated", False)
        is_retrograde = planet_facts.get("retrograde", False)

        # ── Tier 1: Combustion Check ──
        # BPHS Ch 7, v. 28-30: Combust planet's results are "destroyed"
        # Exception: exaltation or own-sign partially offsets (Phaladeepika Ch 1)
        if is_combust:
            is_exalted = rashi_num == _EXALTATION.get(planet, -1)
            is_own_sign = rashi_num in _OWN_SIGNS.get(planet, ())

            if is_exalted or is_own_sign:
                # Phaladeepika: exaltation/own-sign offsets combustion
                modifiers.append(ModifierType.COMBUSTION_OFFSET)
                status = ModifierStatus.WEAKENED
                strength *= 0.5  # Partial offset
                cancellation_reason = f"{planet} combust but {('exalted' if is_exalted else 'own sign')} — partial offset"
            else:
                modifiers.append(ModifierType.COMBUSTION)
                status = ModifierStatus.CANCELLED
                strength = 0.0
                cancellation_reason = f"{planet} is combust"

        # ── Tier 2: Debilitation / Neecha Bhanga Check ──
        # BPHS Ch 43: Debilitation cancels yoga unless Neecha Bhanga
        if status != ModifierStatus.CANCELLED and is_debilitated:
            # Check Neecha Bhanga (simplified: debilitation-sign lord in Kendra)
            deb_lord = _DEBILITATION_SIGN_LORD.get(planet)
            if deb_lord is not None:
                deb_lord_house = planet_facts.get(f"{deb_lord}_house", 0)
                if isinstance(deb_lord_house, int) and deb_lord_house in _KENDRA_HOUSES:
                    # Neecha Bhanga — debilitation cancelled
                    modifiers.append(ModifierType.NEECHA_BHANGA)
                    strength *= 0.7  # Restored but not full strength
                else:
                    modifiers.append(ModifierType.DEBILITATION)
                    status = ModifierStatus.CANCELLED
                    strength = 0.0
                    cancellation_reason = f"{planet} is debilitated (no Neecha Bhanga)"

        # ── Tier 3: Graha Yuddha (Planetary War) Check ──
        # Saravali Ch 24: Planets within 1° — victor dominates
        if status != ModifierStatus.CANCELLED:
            is_war = planet_facts.get("is_war", False)
            war_victor = planet_facts.get("war_victor")
            if is_war and war_victor is not None:
                modifiers.append(ModifierType.GRAHA_YUDDHA)
                if war_victor == planet:
                    # This planet won the war — strength maintained
                    strength *= 1.0
                else:
                    # This planet lost the war — suppressed
                    strength *= 0.3

        # ── Tier 4: Cheshta Bala (Retrograde) Check ──
        # BPHS Ch 5: Retrograde increases Cheshta Bala
        # Phaladeepika Ch 1: Retrograde benefic = stronger; retrograde malefic = stronger
        if status != ModifierStatus.CANCELLED and is_retrograde:
            modifiers.append(ModifierType.CHESHTA_BALA)
            # Retrograde gives modest strength boost (1.2x)
            strength *= 1.2  # Can exceed 1.0 — capped later in report

        # ── Tier 5: Node Taint (Rahu/Ketu) Check ──
        # BPHS Ch 9, v. 12: Node conjunct yoga planet weakens (not cancels)
        if status != ModifierStatus.CANCELLED:
            node_conjunct = planet_facts.get("node_conjunct", False)
            if node_conjunct:
                modifiers.append(ModifierType.NODE_TAINT)
                status = ModifierStatus.WEAKENED if status == ModifierStatus.FORMED else status
                strength *= 0.7

        # ── Dusthana Placement Check ──
        if status != ModifierStatus.CANCELLED and isinstance(house, int) and house in _DUSTHANA_HOUSES:
            modifiers.append(ModifierType.DUSTHANA_PLACEMENT)
            status = ModifierStatus.WEAKENED if status == ModifierStatus.FORMED else status
            strength *= 0.5

        return ModifierResult(
            planet=planet,
            status=status,
            modifier_chain=tuple(modifiers),
            net_strength=max(0.0, strength),  # Allow > 1.0 for retrograde boost
            cancellation_reason=cancellation_reason,
            is_retrograde=is_retrograde,
            is_combust=is_combust,
            is_debilitated=is_debilitated,
            is_node_afflicted=planet_facts.get("node_conjunct", False),
        )

    def evaluate_modifiers(
        self,
        involved_planets: list[str],
        jre_facts: dict[str, Any],
    ) -> ModifierReport:
        """Evaluate modifiers for all planets involved in a yoga.

        Args:
            involved_planets: List of planet names in the yoga.
            jre_facts: JRE facts dictionary with planet data.

        Returns:
            ModifierReport with per-planet results and overall status.
        """
        planets = jre_facts.get("planets", {})
        results: list[ModifierResult] = []

        for planet in involved_planets:
            p_data = planets.get(planet, {})
            result = self.evaluate_planet(planet, p_data)
            results.append(result)

        # Determine overall status
        overall_status = ModifierStatus.FORMED
        overall_strength = 1.0
        cancellation_reason: Optional[str] = None

        for result in results:
            if result.status == ModifierStatus.CANCELLED:
                overall_status = ModifierStatus.CANCELLED
                overall_strength = 0.0
                cancellation_reason = result.cancellation_reason
                break
            if result.status == ModifierStatus.WEAKENED:
                overall_status = ModifierStatus.WEAKENED
                overall_strength = min(overall_strength, result.net_strength)
            else:
                overall_strength = min(overall_strength, result.net_strength)

        return ModifierReport(
            planet_results=tuple(results),
            overall_status=overall_status,
            overall_strength=overall_strength,
            cancellation_reason=cancellation_reason,
        )

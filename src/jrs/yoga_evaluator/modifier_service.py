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
    GRAHA_YUDDHA_VICTOR = "GRAHA_YUDDHA_VICTOR"
    GRAHA_YUDDHA_DEFEATED = "GRAHA_YUDDHA_DEFEATED"
    CHESHTA_BALA = "CHESHTA_BALA"
    NODE_TAINT = "NODE_TAINT"
    NODE_CONJUNCTION_TAINT = "NODE_CONJUNCTION_TAINT"
    NODE_ASPECT_TAINT = "NODE_ASPECT_TAINT"
    NODE_PSEUDO_ASPECT_REJECTED = "NODE_PSEUDO_ASPECT_REJECTED"
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

# Non-luminary planets eligible for Graha Yuddha
_WAR_ELIGIBLE: frozenset[str] = frozenset({"MARS", "MERCURY", "JUPITER", "VENUS", "SATURN"})

# War detection threshold: planets within 1.0° longitude
WAR_LONGITUDE_THRESHOLD: float = 1.0

# Node conjunction taint: strength multiplier 0.7 (30% reduction)
NODE_CONJUNCTION_STRENGTH_MULT: float = 0.7

# Node 7th aspect taint: strength multiplier 0.85 (15% reduction)
NODE_ASPECT_STRENGTH_MULT: float = 0.85

# Node pseudo-aspects (5th/9th) rejected under strict Parashari
_NODE_PSEUDO_ASPECTS: frozenset[int] = frozenset({5, 9})


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
    war_longitude_diff: Optional[float] = None
    war_is_victor: Optional[bool] = None
    node_taint_type: Optional[str] = None  # "CONJUNCTION" or "ASPECT"


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
        # RI-010C MY-015–019: Only non-luminary planets engage in war
        war_longitude_diff: Optional[float] = None
        war_is_victor: Optional[bool] = None
        if status != ModifierStatus.CANCELLED:
            is_war = planet_facts.get("is_war", False)
            war_victor = planet_facts.get("war_victor")
            war_planets = planet_facts.get("war_planets", [])
            longitude = planet_facts.get("longitude")
            war_longitude = planet_facts.get("war_longitude")

            # Check if this planet is eligible for war (non-luminary)
            is_eligible = planet in _WAR_ELIGIBLE

            # Compute longitude difference if both have longitudes
            if isinstance(longitude, (int, float)) and isinstance(war_longitude, (int, float)):
                war_longitude_diff = abs(longitude - war_longitude)
                # Normalize to 0-360 range
                if war_longitude_diff > 180:
                    war_longitude_diff = 360 - war_longitude_diff

            # Detect war: eligible planets within threshold OR explicit flag
            war_detected = False
            if is_war and is_eligible:
                war_detected = True
            elif (
                is_eligible
                and isinstance(war_longitude_diff, float)
                and war_longitude_diff <= WAR_LONGITUDE_THRESHOLD
                and war_victor is not None
            ):
                war_detected = True

            if war_detected and war_victor is not None:
                if war_victor == planet:
                    # This planet won the war
                    modifiers.append(ModifierType.GRAHA_YUDDHA_VICTOR)
                    war_is_victor = True
                    strength *= 1.0
                else:
                    # This planet lost the war — suppressed (Saravali Ch 24)
                    modifiers.append(ModifierType.GRAHA_YUDDHA_DEFEATED)
                    war_is_victor = False
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
        # RI-010C MY-025–030: Severity matrix for node interception
        #   - Conjunction (0°-10°): 0.7 multiplier (30% reduction)
        #   - 7th aspect: 0.85 multiplier (15% reduction)
        #   - Pseudo-aspects (5th/9th): rejected under strict Parashari
        node_taint_type: Optional[str] = None
        if status != ModifierStatus.CANCELLED:
            node_conjunct = planet_facts.get("node_conjunct", False)
            node_aspect = planet_facts.get("node_aspect", False)
            node_aspect_house = planet_facts.get("node_aspect_house", 0)
            is_parashari_mode = planet_facts.get("parashari_mode", True)  # Default: Parashari

            # Check conjunction via explicit flag or house proximity
            if not node_conjunct and isinstance(house, int) and house > 0:
                rahu_house = planet_facts.get("RAHU_house", 0)
                ketu_house = planet_facts.get("KETU_house", 0)
                if (isinstance(rahu_house, int) and rahu_house == house) or (
                    isinstance(ketu_house, int) and ketu_house == house
                ):
                    node_conjunct = True

            # Check 7th aspect from Rahu/Ketu
            if not node_conjunct and not node_aspect and isinstance(house, int) and house > 0:
                rahu_house = planet_facts.get("RAHU_house", 0)
                ketu_house = planet_facts.get("KETU_house", 0)
                for n_house in (rahu_house, ketu_house):
                    if isinstance(n_house, int) and n_house > 0:
                        aspect_house = (n_house + 6) % 12  # 7th aspect offset
                        if aspect_house == 0:
                            aspect_house = 12
                        if aspect_house == house:
                            node_aspect = True
                            node_aspect_house = house
                            break

            # Check for pseudo-aspects (5th/9th) — reject under Parashari
            if node_aspect and is_parashari_mode and isinstance(node_aspect_house, int):
                # Determine which aspect type (5th or 9th) vs 7th
                # If the aspect offset is 5 or 9, it's a pseudo-aspect
                rahu_house = planet_facts.get("RAHU_house", 0)
                ketu_house = planet_facts.get("KETU_house", 0)
                for n_house in (rahu_house, ketu_house):
                    if isinstance(n_house, int) and n_house > 0:
                        offset = (house - n_house) % 12
                        if offset == 0:
                            offset = 12
                        if offset in _NODE_PSEUDO_ASPECTS:
                            # Pseudo-aspect — reject under Parashari
                            modifiers.append(ModifierType.NODE_PSEUDO_ASPECT_REJECTED)
                            node_aspect = False
                            node_taint_type = None
                            break

            # Apply severity based on taint type
            if node_conjunct:
                modifiers.append(ModifierType.NODE_CONJUNCTION_TAINT)
                modifiers.append(ModifierType.NODE_TAINT)
                status = ModifierStatus.WEAKENED if status == ModifierStatus.FORMED else status
                strength *= NODE_CONJUNCTION_STRENGTH_MULT  # 0.7
                node_taint_type = "CONJUNCTION"
                if cancellation_reason is None:
                    cancellation_reason = f"{planet} conjunct node (30% strength reduction)"
            elif node_aspect:
                modifiers.append(ModifierType.NODE_ASPECT_TAINT)
                modifiers.append(ModifierType.NODE_TAINT)
                status = ModifierStatus.WEAKENED if status == ModifierStatus.FORMED else status
                strength *= NODE_ASPECT_STRENGTH_MULT  # 0.85
                node_taint_type = "ASPECT"
                if cancellation_reason is None:
                    cancellation_reason = f"{planet} aspected by node (15% strength reduction)"

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
            is_node_afflicted=planet_facts.get("node_conjunct", False) or bool(node_taint_type),
            war_victor=planet_facts.get("war_victor"),
            war_longitude_diff=war_longitude_diff,
            war_is_victor=war_is_victor,
            node_taint_type=node_taint_type,
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
            p_data = dict(planets.get(planet, {}))  # Copy to avoid mutation
            # Inject cross-planet references for Neecha Bhanga check
            # (debilitation-sign lord's house from other planets)
            deb_lord = _DEBILITATION_SIGN_LORD.get(planet)
            if deb_lord is not None and deb_lord in planets:
                p_data[f"{deb_lord}_house"] = planets[deb_lord].get("house", 0)
            # Inject Rahu/Ketu house for node taint detection
            rahu_data = planets.get("RAHU", {})
            ketu_data = planets.get("KETU", {})
            if rahu_data.get("house") is not None:
                p_data["RAHU_house"] = rahu_data["house"]
            if ketu_data.get("house") is not None:
                p_data["KETU_house"] = ketu_data["house"]
            # Inject war context from other eligible planets
            for other_name, other_data in planets.items():
                if other_name == planet:
                    continue
                if other_name in _WAR_ELIGIBLE and not p_data.get("is_war"):
                    # Check if these two planets are in war
                    p_long = p_data.get("longitude")
                    o_long = other_data.get("longitude")
                    if isinstance(p_long, (int, float)) and isinstance(o_long, (int, float)):
                        diff = abs(p_long - o_long)
                        if diff > 180:
                            diff = 360 - diff
                        if diff <= WAR_LONGITUDE_THRESHOLD:
                            p_data["is_war"] = True
                            p_data.setdefault("war_planets", []).append(other_name)
                            p_data["war_longitude"] = o_long
                            if not p_data.get("war_victor"):
                                # Victor is the one with higher longitude (or northern latitude)
                                p_data["war_victor"] = planet if p_long >= o_long else other_name
            result = self.evaluate_planet(planet, p_data)
            results.append(result)

        # Determine overall status
        overall_status = ModifierStatus.FORMED
        overall_strength = 1.0
        cancellation_reason: Optional[str] = None
        weakening_reason: Optional[str] = None

        for result in results:
            if result.status == ModifierStatus.CANCELLED:
                overall_status = ModifierStatus.CANCELLED
                overall_strength = 0.0
                cancellation_reason = result.cancellation_reason
                break
            if result.status == ModifierStatus.WEAKENED:
                overall_status = ModifierStatus.WEAKENED
                overall_strength = min(overall_strength, result.net_strength)
                if weakening_reason is None and result.cancellation_reason:
                    weakening_reason = result.cancellation_reason
            else:
                overall_strength = min(overall_strength, result.net_strength)

        # Threshold: if overall_strength < 0.5, downgrade to WEAKENED
        if overall_status == ModifierStatus.FORMED and overall_strength < 0.5:
            overall_status = ModifierStatus.WEAKENED

        # Use weakening_reason if no cancellation_reason
        if cancellation_reason is None and weakening_reason is not None:
            cancellation_reason = weakening_reason

        return ModifierReport(
            planet_results=tuple(results),
            overall_status=overall_status,
            overall_strength=overall_strength,
            cancellation_reason=cancellation_reason,
        )

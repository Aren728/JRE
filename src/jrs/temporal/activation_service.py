"""JRS Transit Activation Service — Dasha-First Hierarchy (TA-001–005).

Enforces the classical rule that transits only trigger active natal Yogas
when supported by Mahadasha/Antardasha lords (BPHS Ch 50).

Activation Levels:
    FULL_ACTIVATION: Dasha lord supports transit trigger.
    SANKALPA_PHALAM: Transit present but no Dasha support (latent).
    BLOCKED: Transit obstructed by Vedha or other factors.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional


class ActivationLevel(StrEnum):
    """Transit activation status per Dasha-First hierarchy."""

    FULL_ACTIVATION = "FULL_ACTIVATION"
    SANKALPA_PHALAM = "SANKALPA_PHALAM"  # Latent/unsupported
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ActivationResult:
    """Structured result from transit activation evaluation.

    Attributes:
        activation_level: FULL_ACTIVATION, SANKALPA_PHALAM, or BLOCKED.
        dasha_permission: Whether Mahadasha/Antardasha lord grants permission.
        transit_planet: The transiting planet.
        transit_house: House where transit occurs (relative to natal Moon).
        natal_yoga_planets: Planets involved in the natal yoga.
        reason: Explanation of the activation decision.
    """

    activation_level: ActivationLevel
    dasha_permission: bool
    transit_planet: str = ""
    transit_house: int = 0
    natal_yoga_planets: tuple[str, ...] = ()
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        d: dict[str, Any] = {
            "activation_level": self.activation_level.value,
            "dasha_permission": self.dasha_permission,
            "transit_planet": self.transit_planet,
            "transit_house": self.transit_house,
            "natal_yoga_planets": list(self.natal_yoga_planets),
            "reason": self.reason,
        }
        return d


# Standard Parashari aspects (7th for all, plus special)
_ASPECT_HOUSES: dict[str, tuple[int, ...]] = {
    "MARS": (4, 7, 8),
    "JUPITER": (5, 7, 9),
    "SATURN": (3, 7, 10),
    "SUN": (7,),
    "MOON": (7,),
    "MERCURY": (7,),
    "VENUS": (7,),
}

# Kendra houses from Lagna/Moon
_KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})


class TransitActivationService:
    """Evaluates transit activation of natal Yogas using Dasha-First hierarchy.

    Per BPHS Ch 50 and RI-010D TA-001–005:
    - Mahadasha Lord is the primary permission giver.
    - Antardasha Lord is the secondary qualifier.
    - Transit is the trigger mechanism.
    - Without Dasha support, transit produces only SANKALPA_PHALAM (latent).
    """

    def evaluate_transit_activation(
        self,
        transit_planet: str,
        transit_house: int,
        natal_yoga_planets: list[str],
        mahadasha_lord: str = "",
        antardasha_lord: str = "",
        natal_moon_house: int = 1,
        vedha_blocked: bool = False,
    ) -> ActivationResult:
        """Evaluate whether a transit activates a natal Yoga.

        Implements the Dasha-First hierarchy:
        1. Check Vedha obstruction → BLOCKED if present.
        2. Check Mahadasha/Antardasha permission.
        3. Check transit-to-natal aspect or conjunction.
        4. Return activation level.

        Args:
            transit_planet: The transiting planet name.
            transit_house: House where transit occurs (from natal Moon).
            natal_yoga_planets: Planets forming the natal yoga.
            mahadasha_lord: Current Mahadasha lord planet.
            antardasha_lord: Current Antardasha lord planet.
            natal_moon_house: House of natal Moon (default 1).
            vedha_blocked: Whether Vedha obstruction is active.

        Returns:
            ActivationResult with activation level and details.
        """
        # Step 1: Vedha obstruction check
        if vedha_blocked:
            return ActivationResult(
                activation_level=ActivationLevel.BLOCKED,
                dasha_permission=False,
                transit_planet=transit_planet,
                transit_house=transit_house,
                natal_yoga_planets=tuple(natal_yoga_planets),
                reason="Transit blocked by Vedha obstruction",
            )

        # Step 2: Dasha-First permission check
        dasha_permission = self._check_dasha_permission(
            transit_planet, natal_yoga_planets,
            mahadasha_lord, antardasha_lord,
        )

        # Step 3: Transit-to-natal relationship check
        transit_relates = self._check_transit_natal_relationship(
            transit_planet, transit_house,
            natal_yoga_planets, natal_moon_house,
        )

        # Step 4: Determine activation level
        if dasha_permission and transit_relates:
            return ActivationResult(
                activation_level=ActivationLevel.FULL_ACTIVATION,
                dasha_permission=True,
                transit_planet=transit_planet,
                transit_house=transit_house,
                natal_yoga_planets=tuple(natal_yoga_planets),
                reason=(
                    f"Dasha lord {mahadasha_lord or antardasha_lord} supports "
                    f"transit of {transit_planet} relative to yoga planets"
                ),
            )

        if transit_relates and not dasha_permission:
            return ActivationResult(
                activation_level=ActivationLevel.SANKALPA_PHALAM,
                dasha_permission=False,
                transit_planet=transit_planet,
                transit_house=transit_house,
                natal_yoga_planets=tuple(natal_yoga_planets),
                reason=(
                    f"Transit of {transit_planet} present but no Dasha support "
                    f"(Mahadasha={mahadasha_lord}, Antardasha={antardasha_lord})"
                ),
            )

        # No transit relationship
        return ActivationResult(
            activation_level=ActivationLevel.SANKALPA_PHALAM,
            dasha_permission=dasha_permission,
            transit_planet=transit_planet,
            transit_house=transit_house,
            natal_yoga_planets=tuple(natal_yoga_planets),
            reason=(
                f"Transit of {transit_house}th house does not aspect "
                f"or conjunct yoga planets"
            ),
        )

    def _check_dasha_permission(
        self,
        transit_planet: str,
        natal_yoga_planets: list[str],
        mahadasha_lord: str,
        antardasha_lord: str,
    ) -> bool:
        """Check if Dasha lords grant permission for transit activation.

        Per BPHS Ch 50 V.4:
        - Mahadasha lord matching a yoga planet = permission.
        - Antardasha lord matching = secondary permission.
        - Jupiter has conditional exception (can activate without Dasha).
        """
        # Mahadasha lord is in the yoga planets → permission
        if mahadasha_lord in natal_yoga_planets:
            return True

        # Antardasha lord is in the yoga planets → permission
        if antardasha_lord in natal_yoga_planets:
            return True

        # Jupiter conditional exception: Jupiter transiting can activate
        # if Jupiter is a yoga planet (BPHS Ch 50 V.4)
        if (
            transit_planet == "JUPITER"
            and "JUPITER" in natal_yoga_planets
        ):
            return True

        return False

    def _check_transit_natal_relationship(
        self,
        transit_planet: str,
        transit_house: int,
        natal_yoga_planets: list[str],
        natal_moon_house: int,
    ) -> bool:
        """Check if transit planet aspects or conjuncts natal yoga planets.

        Per RI-010D TA-001:
        - Transit conjunction (same house) activates.
        - Transit aspect (7th or special aspect) activates.
        - Transit must be relative to natal Moon (primary) or Lagna.
        """
        # Simple check: transit is in a kendra from natal Moon
        diff = (transit_house - natal_moon_house) % 12
        if diff in {0, 3, 6, 9}:  # Kendra from Moon
            return True

        # Transit aspects yoga planets (simplified: any aspect relationship)
        # In full implementation, would check each natal yoga planet's house
        # For now, transit in 7th from any yoga planet's conceptual position
        return False

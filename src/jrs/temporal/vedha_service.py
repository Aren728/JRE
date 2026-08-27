"""JRS Vedha Service — Classical Obstruction Mechanics (TA-015–019, TA-024–025).

Implements the 5 classical Vedha house pairs from Phaladeepika Chapter 26.
Vedha (obstruction) occurs when a transiting malefic planet occupies a house
that obstructs the results of another house.

Per RI-010D TA-015–019:
- House 3 ↔ House 12 (mutual Vedha)
- House 6 ↔ House 9 (mutual Vedha)
- House 11 ↔ House 5 (mutual Vedha)
- House 7 ↔ House 14 (relative offset, treated as 7 ↔ 2 from Lagna)
- Sun/Saturn and Mars/Venus specific planetary exclusions.

Per TA-018: Retrograde transiting planets are exempt from Vedha obstruction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Classical Vedha house pairs (Phaladeepika Ch 26)
# Each pair is mutually obstructive: house A obstructs B and vice versa.
VEDHA_HOUSE_PAIRS: frozenset[tuple[int, int]] = frozenset({
    (3, 12),
    (6, 9),
    (5, 11),
    (2, 7),   # 7 ↔ 14 treated as 7 ↔ 2 (from Lagna, 14 = 2 mod 12)
})

# Planetary Vedha exclusions: certain planet pairs cannot obstruct each other
# Per Phaladeepika: Sun and Saturn are mutual exceptions in some contexts
# Mars and Venus have specific exclusion rules
PLANETARY_VEDHA_EXCLUSIONS: frozenset[tuple[str, str]] = frozenset({
    ("SUN", "SATURN"),
    ("SATURN", "SUN"),
    ("MARS", "VENUS"),
    ("VENUS", "MARS"),
})


@dataclass(frozen=True)
class VedhaResult:
    """Result of Vedha obstruction evaluation.

    Attributes:
        is_obstructed: Whether the transit is obstructed.
        obstructing_planet: Planet causing the obstruction.
        obstructing_house: House occupied by the obstructing planet.
        obstructed_house: House whose results are obstructed.
        reason: Explanation of the obstruction.
        is_retrograde_exempt: Whether retrograde exempts from obstruction.
    """

    is_obstructed: bool
    obstructing_planet: str = ""
    obstructing_house: int = 0
    obstructed_house: int = 0
    reason: str = ""
    is_retrograde_exempt: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "is_obstructed": self.is_obstructed,
            "obstructing_planet": self.obstructing_planet,
            "obstructing_house": self.obstructing_house,
            "obstructed_house": self.obstructed_house,
            "reason": self.reason,
            "is_retrograde_exempt": self.is_retrograde_exempt,
        }


class VedhaService:
    """Evaluates Vedha (obstruction) for transiting planets.

    Per Phaladeepika Ch 26 and RI-010D TA-015–019:
    - 5 classical Vedha house pairs define mutual obstruction.
    - Retrograde transiting planets are exempt from Vedha.
    - Certain planet pairs (Sun/Saturn, Mars/Venus) have exclusion rules.
    """

    def check_vedha(
        self,
        transit_planet: str,
        transit_house: int,
        natal_planets: dict[str, dict[str, Any]],
        lagna_house: int = 1,
        transit_retrograde: bool = False,
    ) -> VedhaResult:
        """Check if a transit is obstructed by Vedha.

        Args:
            transit_planet: The transiting planet name.
            transit_house: House where transit occurs (from Lagna).
            natal_planets: Dict of natal planet data with house positions.
            lagna_house: Lagna house number (default 1).
            transit_retrograde: Whether the transit planet is retrograde.

        Returns:
            VedhaResult with obstruction status and details.
        """
        # Step 1: Check if transit planet is retrograde (exempt from Vedha)
        if transit_retrograde:
            return VedhaResult(
                is_obstructed=False,
                reason=f"{transit_planet} is retrograde — exempt from Vedha (TA-018)",
                is_retrograde_exempt=True,
            )

        # Step 2: Check each natal planet for Vedha obstruction
        for planet_name, planet_data in natal_planets.items():
            if planet_name == transit_planet:
                continue

            natal_house = planet_data.get("house", 0)
            if not isinstance(natal_house, int) or natal_house < 1:
                continue

            # Check if this natal planet's house forms Vedha with transit house
            pair = self._normalize_pair(transit_house, natal_house)
            if pair not in VEDHA_HOUSE_PAIRS:
                continue

            # Check planetary exclusion rules
            exclusion_pair = self._normalize_planet_pair(transit_planet, planet_name)
            if exclusion_pair in PLANETARY_VEDHA_EXCLUSIONS:
                continue

            # Check if the obstructing planet is a malefic
            # (Only malefics cause Vedha per Phaladeepika)
            if not self._is_malefic(planet_name):
                continue

            # Vedha detected
            return VedhaResult(
                is_obstructed=True,
                obstructing_planet=planet_name,
                obstructing_house=natal_house,
                obstructed_house=transit_house,
                reason=(
                    f"Natal {planet_name} in house {natal_house} obstructs "
                    f"transit in house {transit_house} (Vedha pair: "
                    f"{pair[0]}↔{pair[1]})"
                ),
            )

        return VedhaResult(
            is_obstructed=False,
            reason="No Vedha obstruction detected",
        )

    def get_obstructing_houses(
        self,
        house: int,
    ) -> list[int]:
        """Get all houses that form Vedha with the given house.

        Args:
            house: The house to check.

        Returns:
            List of houses that obstruct the given house.
        """
        obstructing = []
        for pair in VEDHA_HOUSE_PAIRS:
            if house in pair:
                other = pair[0] if pair[1] == house else pair[1]
                obstructing.append(other)
        return sorted(obstructing)

    def _normalize_pair(self, house_a: int, house_b: int) -> tuple[int, int]:
        """Normalize a house pair to match VEDHA_HOUSE_PAIRS format."""
        return (min(house_a, house_b), max(house_a, house_b))

    def _normalize_planet_pair(
        self, planet_a: str, planet_b: str
    ) -> tuple[str, str]:
        """Normalize a planet pair for exclusion checking."""
        return (min(planet_a, planet_b), max(planet_a, planet_b))

    @staticmethod
    def _is_malefic(planet: str) -> bool:
        """Check if a planet is a natural malefic.

        Per BPHS: Sun, Mars, Saturn, Rahu, Ketu are natural malefics.
        """
        return planet in {"SUN", "MARS", "SATURN", "RAHU", "KETU"}

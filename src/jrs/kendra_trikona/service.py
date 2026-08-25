"""JRS-072 Kendra-Trikona Structural Reasoning service."""

from __future__ import annotations

from typing import Any

from .models import KendraTrikonaType, StructuralYoga

# House classifications
KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})
TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})

# Sign ownership (Vimshottari) — 1-indexed rashi number -> owning planet
_SIGN_LORDS: dict[int, str] = {
    1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
    6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
    11: "SATURN", 12: "JUPITER",
}

_RASHI_ORDER: list[str] = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]


def _rashi_to_number(rashi_str: str) -> int:
    """Convert Rashi string to 1-indexed number."""
    try:
        return _RASHI_ORDER.index(rashi_str) + 1
    except ValueError:
        return 1


class KendraTrikonaService:
    """Deterministic service for identifying Kendra-Trikona structural yogas."""

    def evaluate(self, jre_facts: dict[str, Any]) -> list[StructuralYoga]:
        """Identify Kendra-Trikona yogas from JRE facts.

        Args:
            jre_facts: Dictionary containing planet data and lagna.
                       Expected structure:
                       {
                           "lagna": "MESHA",
                           "planets": {
                               "SUN": {"rashi": "SIMHA", ...},
                               "MARS": {"rashi": "MESHA", ...},
                               ...
                           }
                       }

        Returns:
            List of StructuralYoga objects representing detected yogas.
        """
        lagna_rashi = jre_facts.get("lagna")
        planets = jre_facts.get("planets", {})
        
        if not lagna_rashi or not planets:
            return []

        lagna_num = _rashi_to_number(lagna_rashi)
        yogas: list[StructuralYoga] = []

        # Map house number (1-12) to its lord
        house_lords: dict[int, str] = {}
        for house in range(1, 13):
            sign_num = (lagna_num + house - 2) % 12 + 1
            house_lords[house] = _SIGN_LORDS.get(sign_num, "")

        # Map planet to its house number from Lagna
        planet_houses: dict[str, int] = {}
        for p_name, p_data in planets.items():
            p_rashi = p_data.get("rashi", "")
            p_num = _rashi_to_number(p_rashi)
            p_house = (p_num - lagna_num) % 12 + 1
            planet_houses[p_name] = p_house

        # Check each planet
        for p_name, p_house in planet_houses.items():
            # Check if planet is a Kendra lord
            for k_house in KENDRA_HOUSES:
                if house_lords.get(k_house) == p_name:
                    # Is it placed in a Trikona house?
                    if p_house in TRIKONA_HOUSES:
                        owner_of_placement = house_lords.get(p_house, "")
                        yogas.append(StructuralYoga(
                            yoga_type=KendraTrikonaType.KENDRA_LORD_IN_TRIKONA,
                            planet_a=p_name,
                            planet_b=owner_of_placement,
                            house_a=k_house,
                            house_b=p_house,
                        ))

            # Check if planet is a Trikona lord
            for t_house in TRIKONA_HOUSES:
                if house_lords.get(t_house) == p_name:
                    # Is it placed in a Kendra house?
                    if p_house in KENDRA_HOUSES:
                        owner_of_placement = house_lords.get(p_house, "")
                        yogas.append(StructuralYoga(
                            yoga_type=KendraTrikonaType.TRIKONA_LORD_IN_KENDRA,
                            planet_a=p_name,
                            planet_b=owner_of_placement,
                            house_a=t_house,
                            house_b=p_house,
                        ))

        return yogas

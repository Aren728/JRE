"""JRS-073 Structural service for multi-planet relationship graphs."""

from __future__ import annotations

from typing import Any

from .models import PlanetRelationship, RelationshipType

# Standard Parashari aspects (7th house for all, plus special aspects)
_STANDARD_ASPECTS = {
    "MARS": [4, 7, 8],
    "JUPITER": [5, 7, 9],
    "SATURN": [3, 7, 10],
    "SUN": [7],
    "MOON": [7],
    "MERCURY": [7],
    "VENUS": [7],
}

# Sign ownership (Vimshottari) - 1-indexed rashi number to owning planet
_SIGN_LORDS = {
    1: "MARS", 2: "VENUS", 3: "MERCURY", 4: "MOON", 5: "SUN",
    6: "MERCURY", 7: "VENUS", 8: "MARS", 9: "JUPITER", 10: "SATURN",
    11: "SATURN", 12: "JUPITER",
}

_RASHI_ORDER = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]


class RelationshipGraphService:
    """Deterministic service for extracting multi-planet relationships from JRE facts."""

    def extract_relationships(self, jre_facts: dict[str, Any]) -> list[PlanetRelationship]:
        """Extract basic relationships from JRE facts.

        Args:
            jre_facts: Dictionary containing planet data from JRE engines.
                       Expected structure:
                       {
                           "planets": {
                               "SUN": {"rashi": "MESHA", "longitude": 15.5, ...},
                               "MOON": {"rashi": "MESHA", "longitude": 20.1, ...},
                               ...
                           }
                       }

        Returns:
            List of PlanetRelationship objects representing detected connections.
        """
        planets = jre_facts.get("planets", {})
        if not planets:
            return []

        relationships: list[PlanetRelationship] = []
        seen: set[tuple[str, str, RelationshipType]] = set()

        # 1. Detect Conjunctions (same rashi)
        for p1_name, p1_data in planets.items():
            for p2_name, p2_data in planets.items():
                if p1_name >= p2_name:
                    continue
                if p1_data.get("rashi") == p2_data.get("rashi"):
                    key = (p1_name, p2_name, RelationshipType.CONJUNCTION)
                    if key not in seen:
                        rel = PlanetRelationship(
                            planet_a=p1_name,
                            planet_b=p2_name,
                            relationship_type=RelationshipType.CONJUNCTION,
                        )
                        relationships.append(rel)
                        seen.add(key)

        # 2. Detect Aspects
        for p1_name, p1_data in planets.items():
            p1_rashi_idx = _rashi_to_index(p1_data.get("rashi", ""))
            if p1_rashi_idx is None:
                continue

            aspects = _STANDARD_ASPECTS.get(p1_name, [7])
            for offset in aspects:
                target_idx = (p1_rashi_idx + offset - 1) % 12
                target_rashi = _RASHI_ORDER[target_idx]
                for p2_name, p2_data in planets.items():
                    if p1_name == p2_name:
                        continue
                    if p2_data.get("rashi") == target_rashi:
                        # Avoid duplicate if conjunction already found
                        conj_key = (min(p1_name, p2_name), max(p1_name, p2_name), RelationshipType.CONJUNCTION)
                        if conj_key in seen:
                            continue
                        aspect_key = (p1_name, p2_name, RelationshipType.ASPECT)
                        if aspect_key not in seen:
                            rel = PlanetRelationship(
                                planet_a=p1_name,
                                planet_b=p2_name,
                                relationship_type=RelationshipType.ASPECT,
                            )
                            relationships.append(rel)
                            seen.add(aspect_key)

        # 3. Detect Dispositorship (Planet A in sign owned by Planet B)
        for p1_name, p1_data in planets.items():
            p1_rashi_idx = _rashi_to_index(p1_data.get("rashi", ""))
            if p1_rashi_idx is None:
                continue
            owner = _SIGN_LORDS.get(p1_rashi_idx + 1)
            if owner and owner in planets and owner != p1_name:
                key = (p1_name, owner, RelationshipType.DISPOSITOR)
                if key not in seen:
                    rel = PlanetRelationship(
                        planet_a=p1_name,
                        planet_b=owner,
                        relationship_type=RelationshipType.DISPOSITOR,
                    )
                    relationships.append(rel)
                    seen.add(key)

        return relationships


def _rashi_to_index(rashi_str: str) -> int | None:
    """Convert Rashi string to 0-based index."""
    try:
        return _RASHI_ORDER.index(rashi_str)
    except ValueError:
        return None

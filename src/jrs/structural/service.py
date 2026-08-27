"""JRS-073 Structural service for multi-planet relationship graphs."""

from __future__ import annotations

from typing import Any

from .models import PlanetRelationship, RelationshipType

# Rahu/Ketu names for node involvement detection
_NODE_NAMES: frozenset[str] = frozenset({"RAHU", "KETU"})

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

    def extract_relationships(
        self, jre_facts: dict[str, Any], transit_facts: dict[str, Any] | None = None
    ) -> list[PlanetRelationship]:
        """Extract basic relationships from JRE facts.

        Args:
            jre_facts: Dictionary containing planet data from JRE engines.
            transit_facts: Optional dictionary containing transit planet data.

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
                        node_inv = p1_name in _NODE_NAMES or p2_name in _NODE_NAMES
                        rel = PlanetRelationship(
                            planet_a=p1_name,
                            planet_b=p2_name,
                            relationship_type=RelationshipType.CONJUNCTION,
                            is_directed=False,
                            node_involvement=node_inv,
                        )
                        relationships.append(rel)
                        seen.add(key)

        # 2. Detect Aspects (directed: A aspects B, but B may not aspect A)
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
                            node_inv = p1_name in _NODE_NAMES or p2_name in _NODE_NAMES
                            rel = PlanetRelationship(
                                planet_a=p1_name,
                                planet_b=p2_name,
                                relationship_type=RelationshipType.ASPECT,
                                is_directed=True,
                                node_involvement=node_inv,
                            )
                            relationships.append(rel)
                            seen.add(aspect_key)

        # 3. Detect Dispositorship (Planet A in sign owned by Planet B, directed)
        # Truncation: If terminal lord is combust, break the chain (BPHS Ch 33 v.18)
        for p1_name, p1_data in planets.items():
            p1_rashi_idx = _rashi_to_index(p1_data.get("rashi", ""))
            if p1_rashi_idx is None:
                continue
            owner = _SIGN_LORDS.get(p1_rashi_idx + 1)
            if owner and owner in planets and owner != p1_name:
                # Chain truncation: skip if terminal lord is combust
                owner_data = planets[owner]
                if owner_data.get("combust", False):
                    continue
                key = (p1_name, owner, RelationshipType.DISPOSITOR)
                if key not in seen:
                    rel = PlanetRelationship(
                        planet_a=p1_name,
                        planet_b=owner,
                        relationship_type=RelationshipType.DISPOSITOR,
                        is_directed=True,
                    )
                    relationships.append(rel)
                    seen.add(key)

        # 4. Detect Exchanges (Parivartana: A in B's sign AND B in A's sign)
        for p1_name, p1_data in planets.items():
            p1_rashi_idx = _rashi_to_index(p1_data.get("rashi", ""))
            if p1_rashi_idx is None:
                continue
            p1_lord = _SIGN_LORDS.get(p1_rashi_idx + 1)
            if p1_lord is None or p1_lord not in planets or p1_lord == p1_name:
                continue
            # Check if p1_lord (B) is in a sign owned by p1_name (A)
            p2_name = p1_lord
            p2_data = planets[p2_name]
            p2_rashi_idx = _rashi_to_index(p2_data.get("rashi", ""))
            if p2_rashi_idx is None:
                continue
            p2_lord = _SIGN_LORDS.get(p2_rashi_idx + 1)
            if p2_lord == p1_name:
                # Exchange detected: A in B's sign, B in A's sign
                key = (min(p1_name, p2_name), max(p1_name, p2_name), RelationshipType.EXCHANGE)
                if key not in seen:
                    rel = PlanetRelationship(
                        planet_a=p1_name,
                        planet_b=p2_name,
                        relationship_type=RelationshipType.EXCHANGE,
                        is_directed=False,
                    )
                    relationships.append(rel)
                    seen.add(key)

        # 5. Detect Transit Activation
        if transit_facts:
            transit_planets = transit_facts.get("planets", {})
            active_natal_pairs: set[tuple[str, str]] = set()

            for t_name, t_data in transit_planets.items():
                t_rashi_idx = _rashi_to_index(t_data.get("rashi", ""))
                if t_rashi_idx is None:
                    continue

                # Check Transit Conjunctions
                for n_name, n_data in planets.items():
                    if t_data.get("rashi") == n_data.get("rashi"):
                        key = (t_name, n_name, RelationshipType.TRANSIT_CONJUNCTION)
                        if key not in seen:
                            rel = PlanetRelationship(
                                planet_a=t_name,
                                planet_b=n_name,
                                relationship_type=RelationshipType.TRANSIT_CONJUNCTION,
                                is_active=True,
                            )
                            relationships.append(rel)
                            seen.add(key)
                            active_natal_pairs.add((t_name, n_name))

                # Check Transit Aspects
                t_aspects = _STANDARD_ASPECTS.get(t_name, [7])
                for offset in t_aspects:
                    target_idx = (t_rashi_idx + offset - 1) % 12
                    target_rashi = _RASHI_ORDER[target_idx]
                    for n_name, n_data in planets.items():
                        if t_name == n_name:
                            continue
                        if n_data.get("rashi") == target_rashi:
                            key = (t_name, n_name, RelationshipType.TRANSIT_ASPECT)
                            if key not in seen:
                                rel = PlanetRelationship(
                                    planet_a=t_name,
                                    planet_b=n_name,
                                    relationship_type=RelationshipType.TRANSIT_ASPECT,
                                    is_active=True,
                                )
                                relationships.append(rel)
                                seen.add(key)
                                active_natal_pairs.add((t_name, n_name))

            # Mark natal relationships as active if a transit planet is involved
            updated_rels: list[PlanetRelationship] = []
            # Collect all natal planets that are activated by transit
            activated_natal_planets: set[str] = set()
            for rel in relationships:
                if rel.relationship_type in (
                    RelationshipType.TRANSIT_ASPECT, RelationshipType.TRANSIT_CONJUNCTION
                ):
                    activated_natal_planets.add(rel.planet_b)

            for rel in relationships:
                if (
                    rel.relationship_type
                    in (RelationshipType.ASPECT, RelationshipType.CONJUNCTION, RelationshipType.DISPOSITOR)
                    and (
                        rel.planet_a in activated_natal_planets
                        or rel.planet_b in activated_natal_planets
                    )
                ):
                    # Create a new instance with is_active=True (frozen dataclass)
                    updated_rel = PlanetRelationship(
                        planet_a=rel.planet_a,
                        planet_b=rel.planet_b,
                        relationship_type=rel.relationship_type,
                        strength_modifier=rel.strength_modifier,
                        is_active=True,
                    )
                    updated_rels.append(updated_rel)
                else:
                    updated_rels.append(rel)

            return updated_rels

        return relationships


def _rashi_to_index(rashi_str: str) -> int | None:
    """Convert Rashi string to 0-based index."""
    try:
        return _RASHI_ORDER.index(rashi_str)
    except ValueError:
        return None

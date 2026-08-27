"""JRS-073 Structural models for multi-planet relationship graphs."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional, cast


class RelationshipType(StrEnum):
    """Types of relationships between planets."""
    ASPECT = "ASPECT"
    CONJUNCTION = "CONJUNCTION"
    EXCHANGE = "EXCHANGE"
    DISPOSITOR = "DISPOSITOR"
    TRANSIT_ASPECT = "TRANSIT_ASPECT"
    TRANSIT_CONJUNCTION = "TRANSIT_CONJUNCTION"


@dataclass(frozen=True)
class PlanetRelationship:
    """A deterministic relationship between two planets.

    Fields added in Phase 1 (RI-010G):
    - is_directed: True for aspects (A→B ≠ B→A); False for conjunctions/exchanges.
    - is_war: True when two planets are within 1° (Graha Yuddha).
    - war_victor: The winning planet in a Graha Yuddha.
    - node_involvement: True when Rahu or Ketu is involved in the relationship.
    """
    planet_a: str
    planet_b: str
    relationship_type: RelationshipType
    strength_modifier: str = ""  # e.g., "exalted", "debilitated"
    is_active: bool = False  # True if activated by transit
    is_directed: bool = False  # True for aspects (A→B); False for conjunctions/exchanges
    is_war: bool = False  # True if planets within 1° (Graha Yuddha)
    war_victor: Optional[str] = None  # Winner of planetary war (if is_war)
    node_involvement: bool = False  # True if Rahu or Ketu involved

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "planet_a": self.planet_a,
            "planet_b": self.planet_b,
            "relationship_type": self.relationship_type.value,
            "strength_modifier": self.strength_modifier,
            "is_active": self.is_active,
            "is_directed": self.is_directed,
            "is_war": self.is_war,
        }
        if self.war_victor is not None:
            result["war_victor"] = self.war_victor
        if self.node_involvement:
            result["node_involvement"] = True
        return cast(dict[str, Any], result)

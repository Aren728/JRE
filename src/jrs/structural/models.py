"""JRS-073 Structural models for multi-planet relationship graphs."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast


class RelationshipType(StrEnum):
    """Types of relationships between planets."""
    ASPECT = "ASPECT"
    CONJUNCTION = "CONJUNCTION"
    DISPOSITOR = "DISPOSITOR"


@dataclass(frozen=True)
class PlanetRelationship:
    """A deterministic relationship between two planets."""
    planet_a: str
    planet_b: str
    relationship_type: RelationshipType
    strength_modifier: str = ""  # e.g., "exalted", "debilitated"

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], {
            "planet_a": self.planet_a,
            "planet_b": self.planet_b,
            "relationship_type": self.relationship_type.value,
            "strength_modifier": self.strength_modifier,
        })

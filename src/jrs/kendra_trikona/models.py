"""JRS-072 Kendra-Trikona Structural Reasoning models."""

from __future__ import annotations

import enum
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast


class KendraTrikonaType(StrEnum):
    """Types of Kendra-Trikona structural yogas."""
    KENDRA_LORD_IN_TRIKONA = "KENDRA_LORD_IN_TRIKONA"
    TRIKONA_LORD_IN_KENDRA = "TRIKONA_LORD_IN_KENDRA"
    LORDS_CONJUNCTION = "LORDS_CONJUNCTION"


@dataclass(frozen=True)
class StructuralYoga:
    """A structural yoga formed by Kendra-Trikona lord placement."""
    yoga_type: KendraTrikonaType
    planet_a: str
    planet_b: str
    house_a: int
    house_b: int

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], {
            "yoga_type": self.yoga_type.value,
            "planet_a": self.planet_a,
            "planet_b": self.planet_b,
            "house_a": self.house_a,
            "house_b": self.house_b,
        })

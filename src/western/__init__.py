"""JRE-066: Western Astrology Deterministic Substrate.

Outputs ONLY deterministic facts (tropical longitudes, house cusps,
aspects, dignities) — never interpretations or predictions.
"""

from __future__ import annotations

from .errors import (
    WesternCalculationError,
    WesternInputError,
)
from .models import (
    WesternAspect,
    WesternAspectType,
    WesternChart,
    WesternDignity,
    WesternHouseSystem,
    WesternPlanet,
)
from .service import WesternCalculationService

__all__ = [
    "WesternAspect",
    "WesternAspectType",
    "WesternCalculationError",
    "WesternCalculationService",
    "WesternChart",
    "WesternDignity",
    "WesternHouseSystem",
    "WesternInputError",
    "WesternPlanet",
]

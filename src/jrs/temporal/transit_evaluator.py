"""Transit (Gochar) Evaluator — deterministic transit multiplier computation (RI-012).

Evaluates transit planet conditions and computes a net transit multiplier
using Ashtakavarga bindus and house-from-Moon placement rules.

Multiplier rules:
    - Base transit multiplier = 1.00
    - Ashtakavarga score >= 4 bindus → +0.15 bonus
    - Ashtakavarga score < 4 bindus → -0.20 penalty
    - Transiting in 8th or 12th house from Natal Moon → -0.25 penalty
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ── Constants ────────────────────────────────────────────────────────────────

_BASE_TRANSIT_MULTIPLIER: float = 1.00
_AV_HIGH_BINDUS: int = 4
_AV_HIGH_BONUS: float = 0.15
_AV_LOW_PENALTY: float = 0.20
_DUSTHANA_PENALTY: float = 0.25

# Houses from Moon that apply dusthana penalty
_DUSTHANA_HOUSES_FROM_MOON: frozenset[int] = frozenset({8, 12})


# ── Data Structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class TransitProfile:
    """Immutable result of transit evaluation for a single planet.

    Attributes:
        planet: Planet name (e.g., 'JUPITER').
        transit_house: House number occupied by transiting planet (1–12).
        bindus: Ashtakavarga score for this transit planet (0–8).
        dusthana_penalty: Whether 8th/12th house penalty applied.
        net_transit_multiplier: Final computed transit multiplier.
    """

    planet: str
    transit_house: int
    bindus: int
    dusthana_penalty: bool
    net_transit_multiplier: float


@dataclass(frozen=True)
class TransitEvaluationResult:
    """Aggregated transit evaluation for multiple planets.

    Attributes:
        profiles: Per-planet transit profiles.
        aggregate_multiplier: Combined transit multiplier (product of all).
    """

    profiles: tuple[TransitProfile, ...]
    aggregate_multiplier: float


# ── Transit Evaluator ────────────────────────────────────────────────────────


class TransitEvaluator:
    """Deterministic transit evaluation engine.

    Computes transit multipliers based on Ashtakavarga bindus and
    house-from-Natal-Moon placement.
    """

    def evaluate_planet(
        self,
        planet: str,
        transit_house: int,
        ashtakavarga_scores: dict[str, int],
        natal_moon_house: int,
    ) -> TransitProfile:
        """Evaluate transit conditions for a single planet.

        Args:
            planet: Planet name (e.g., 'JUPITER').
            transit_house: House number occupied by transiting planet (1–12).
            ashtakavarga_scores: Mapping of planet name → Ashtakavarga bindus.
            natal_moon_house: House number of the natal Moon (1–12).

        Returns:
            TransitProfile with computed multiplier.
        """
        bindus = ashtakavarga_scores.get(planet.upper(), 0)

        # Compute house from natal Moon
        house_from_moon = ((transit_house - natal_moon_house) % 12) + 1

        # Base multiplier
        multiplier = _BASE_TRANSIT_MULTIPLIER

        # Ashtakavarga bonus/penalty
        if bindus >= _AV_HIGH_BINDUS:
            multiplier += _AV_HIGH_BONUS
        else:
            multiplier -= _AV_LOW_PENALTY

        # Dusthana penalty (8th or 12th from natal Moon)
        dusthana = house_from_moon in _DUSTHANA_HOUSES_FROM_MOON
        if dusthana:
            multiplier -= _DUSTHANA_PENALTY

        return TransitProfile(
            planet=planet.upper(),
            transit_house=transit_house,
            bindus=bindus,
            dusthana_penalty=dusthana,
            net_transit_multiplier=round(multiplier, 4),
        )

    def evaluate_multiple(
        self,
        planets: list[str],
        transit_houses: dict[str, int],
        ashtakavarga_scores: dict[str, int],
        natal_moon_house: int,
    ) -> TransitEvaluationResult:
        """Evaluate transit conditions for multiple planets.

        Args:
            planets: Planet names to evaluate.
            transit_houses: Mapping of planet → transit house (1–12).
            ashtakavarga_scores: Mapping of planet → Ashtakavarga bindus.
            natal_moon_house: House number of the natal Moon (1–12).

        Returns:
            TransitEvaluationResult with per-planet profiles and aggregate.
        """
        profiles: list[TransitProfile] = []
        for planet in planets:
            house = transit_houses.get(planet.upper(), 1)
            profile = self.evaluate_planet(
                planet=planet,
                transit_house=house,
                ashtakavarga_scores=ashtakavarga_scores,
                natal_moon_house=natal_moon_house,
            )
            profiles.append(profile)

        # Aggregate: product of all multipliers
        aggregate = 1.0
        for p in profiles:
            aggregate *= p.net_transit_multiplier

        return TransitEvaluationResult(
            profiles=tuple(profiles),
            aggregate_multiplier=round(aggregate, 6),
        )

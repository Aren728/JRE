"""JRS-075/076/077 Yoga Formation, Cancellation, Manifestation & Outcome Evaluator service."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .models import YogaEvaluation, YogaStatus

# Dusthana houses — placements that weaken a yoga
DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})


class YogaEvaluatorService:
    """Deterministic service for evaluating yoga formation and cancellation."""

    def evaluate_formation(
        self,
        yoga_name: str,
        involved_planets: list[str],
        jre_facts: dict[str, Any],
    ) -> YogaEvaluation:
        """Evaluate whether a yoga is formed, weakened, or cancelled.

        Args:
            yoga_name: Name of the yoga to evaluate.
            involved_planets: List of planet names involved in the yoga.
            jre_facts: Dictionary containing planet data from JRE.
                       Expected structure:
                       {
                           "planets": {
                               "SUN": {"house": 1, "combust": false, "debilitated": false},
                               ...
                           }
                       }

        Returns:
            YogaEvaluation with status and optional cancellation reason.
        """
        planets = jre_facts.get("planets", {})

        for planet in involved_planets:
            p_data = planets.get(planet, {})

            # Check combustion
            if p_data.get("combust", False):
                return YogaEvaluation(
                    yoga_name=yoga_name,
                    status=YogaStatus.CANCELLED,
                    cancellation_reason=f"{planet} is combust",
                )

            # Check debilitation
            if p_data.get("debilitated", False):
                return YogaEvaluation(
                    yoga_name=yoga_name,
                    status=YogaStatus.CANCELLED,
                    cancellation_reason=f"{planet} is debilitated",
                )

        for planet in involved_planets:
            p_data = planets.get(planet, {})
            house = p_data.get("house")

            # Check dusthana placement
            if isinstance(house, int) and house in DUSTHANA_HOUSES:
                return YogaEvaluation(
                    yoga_name=yoga_name,
                    status=YogaStatus.WEAKENED,
                )

        return YogaEvaluation(
            yoga_name=yoga_name,
            status=YogaStatus.FORMED,
        )

    def evaluate_manifestation(
        self,
        evaluation: YogaEvaluation,
        yoga_planets: list[str],
        active_dasha_lord: str,
        transit_planet: str,
    ) -> YogaEvaluation:
        """Determine if a formed yoga is currently manifesting.

        A yoga manifests when its period lord (Dasha) or a transiting
        planet involved in the yoga is active.

        Args:
            evaluation: The base YogaEvaluation from evaluate_formation.
            yoga_planets: List of planet names involved in the yoga.
            active_dasha_lord: The currently active Vimshottari Dasha lord.
            transit_planet: The planet currently transiting a key house.

        Returns:
            Updated YogaEvaluation with manifestation status.
        """
        if active_dasha_lord in yoga_planets:
            return replace(
                evaluation,
                is_manifesting=True,
                activation_source=f"Dasha: {active_dasha_lord}",
            )

        if transit_planet in yoga_planets:
            return replace(
                evaluation,
                is_manifesting=True,
                activation_source=f"Transit: {transit_planet}",
            )

        return evaluation

    def map_outcome(
        self,
        yoga_name: str,
        involved_houses: list[int],
        involved_planets: list[str],
    ) -> str:
        """Map a yoga to its likely outcome category.

        Args:
            yoga_name: Name of the yoga.
            involved_houses: House numbers involved in the yoga.
            involved_planets: Planet names involved in the yoga.

        Returns:
            One of: CAREER_PROMINENCE, WEALTH_ACCUMULATION,
            DOMESTIC_HARMONY, GENERAL_IMPROVEMENT.
        """
        if 10 in involved_houses or "SUN" in involved_planets:
            return "CAREER_PROMINENCE"
        if 2 in involved_houses or 11 in involved_houses or "JUPITER" in involved_planets or "VENUS" in involved_planets:
            return "WEALTH_ACCUMULATION"
        if 4 in involved_houses or "MOON" in involved_planets:
            return "DOMESTIC_HARMONY"
        return "GENERAL_IMPROVEMENT"

"""Nakshatra Activation Service — derives activation facts from planet positions.

JRE-026 computes NakshatraActivation objects from existing planet positions.
It outputs ONLY facts, NEVER predictions or interpretations.

Usage::

    service = NakshatraActivationService()
    report = service.compute_activations(planet_states)
    activation = report.result_for(BodyId.MOON)
"""

from __future__ import annotations

from jyotish import (
    BodyId,
    NakshatraId,
    PlanetState,
    lord_of,
)

from .errors import InvalidActivationRequestError
from .models import (
    NakshatraActivation,
    NakshatraActivationReport,
    NakshatraRelationshipType,
)


class NakshatraActivationService:
    """Deterministic Nakshatra activation computation facade.

    Takes existing planet positions (from JRE-003) and derives
    NakshatraActivation objects based on lordship, occupancy, and
    transit ingress rules.
    """

    def __init__(self) -> None:
        """Initialize the service."""

    def compute_activations(
        self,
        planet_states: tuple[PlanetState, ...],
        transit_states: tuple[PlanetState, ...] | None = None,
        activation_window_start: str = "",
        activation_window_end: str = "",
    ) -> NakshatraActivationReport:
        """Compute all nakshatra activations from planet positions.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            Natal planet states from JRE-003.
        transit_states : tuple of PlanetState | None
            Optional transit planet states for ingress detection.
        activation_window_start : str
            ISO-UTC start of activation window (empty for natal-only).
        activation_window_end : str
            ISO-UTC end of activation window (empty for natal-only).

        Returns
        -------
        NakshatraActivationReport
            Complete report of all computed activations.
        """
        self._validate_request(planet_states)

        activations: list[NakshatraActivation] = []

        # Build state map by body
        state_map: dict[BodyId, PlanetState] = {}
        for state in planet_states:
            state_map[state.body] = state

        # 1. Compute occupancy activations
        occupancy_activations = self._compute_occupancy_activations(planet_states)
        activations.extend(occupancy_activations)

        # 2. Compute lord activations
        lord_activations = self._compute_lord_activations(planet_states, state_map)
        activations.extend(lord_activations)

        # 3. Compute transit ingress activations
        if transit_states:
            ingress_activations = self._compute_transit_ingress_activations(
                planet_states, transit_states,
                activation_window_start, activation_window_end,
            )
            activations.extend(ingress_activations)

        # 4. Compute mutual exchanges
        exchange_activations = self._compute_mutual_exchanges(planet_states, state_map)
        activations.extend(exchange_activations)

        # 5. Compute dependency activations
        dependency_activations = self._compute_dependencies(planet_states, state_map)
        activations.extend(dependency_activations)

        return NakshatraActivationReport(activations=tuple(activations))

    def _compute_occupancy_activations(
        self,
        planet_states: tuple[PlanetState, ...],
    ) -> list[NakshatraActivation]:
        """Compute activations from natal nakshatra occupancy."""
        activations: list[NakshatraActivation] = []

        for state in planet_states:
            nakshatra_lord = lord_of(state.nakshatra)

            activation = NakshatraActivation(
                source_planet=state.body,
                source_position=state,
                nakshatra=state.nakshatra,
                nakshatra_lord=nakshatra_lord,
                natal_lord_state=None,
                transit_lord_state=None,
                relationship_type=NakshatraRelationshipType.NAKSHATRA_OCCUPANCY,
                provenance="JRE-026 occupancy computation",
            )
            activations.append(activation)

        return activations

    def _compute_lord_activations(
        self,
        planet_states: tuple[PlanetState, ...],
        state_map: dict[BodyId, PlanetState],
    ) -> list[NakshatraActivation]:
        """Compute activations from nakshatra lord relationships."""
        activations: list[NakshatraActivation] = []

        for state in planet_states:
            nakshatra_lord = lord_of(state.nakshatra)

            # Find the natal state of the nakshatra lord
            natal_lord_state = state_map.get(nakshatra_lord)

            # If the nakshatra lord is a different planet, create lord activation
            if nakshatra_lord != state.body:
                activation = NakshatraActivation(
                    source_planet=state.body,
                    source_position=state,
                    nakshatra=state.nakshatra,
                    nakshatra_lord=nakshatra_lord,
                    natal_lord_state=natal_lord_state,
                    transit_lord_state=None,
                    relationship_type=NakshatraRelationshipType.NAKSHATRA_LORD_ACTIVATION,
                    provenance="JRE-026 lord activation computation",
                )
                activations.append(activation)

        return activations

    def _compute_transit_ingress_activations(
        self,
        natal_states: tuple[PlanetState, ...],
        transit_states: tuple[PlanetState, ...],
        window_start: str,
        window_end: str,
    ) -> list[NakshatraActivation]:
        """Compute activations from transit planet ingress into natal nakshatras."""
        activations: list[NakshatraActivation] = []

        # Collect all natal nakshatras
        natal_nakshatras: dict[NakshatraId, PlanetState] = {}
        for state in natal_states:
            natal_nakshatras[state.nakshatra] = state

        # Check each transit planet
        for transit_state in transit_states:
            transit_nakshatra = transit_state.nakshatra

            # If transit planet is in a natal nakshatra, create ingress activation
            if transit_nakshatra in natal_nakshatras:
                natal_state = natal_nakshatras[transit_nakshatra]
                nakshatra_lord = lord_of(transit_nakshatra)

                activation = NakshatraActivation(
                    source_planet=transit_state.body,
                    source_position=transit_state,
                    nakshatra=transit_nakshatra,
                    nakshatra_lord=nakshatra_lord,
                    natal_lord_state=None,
                    transit_lord_state=transit_state,
                    relationship_type=NakshatraRelationshipType.TRANSIT_NAKSHATRA_INGRESS,
                    activation_start=window_start,
                    activation_end=window_end,
                    provenance="JRE-026 transit ingress computation",
                )
                activations.append(activation)

            # Also create natal activation for the natal planet
            if transit_nakshatra in natal_nakshatras:
                natal_state = natal_nakshatras[transit_nakshatra]
                nakshatra_lord = lord_of(transit_nakshatra)

                activation = NakshatraActivation(
                    source_planet=natal_state.body,
                    source_position=natal_state,
                    nakshatra=transit_nakshatra,
                    nakshatra_lord=nakshatra_lord,
                    natal_lord_state=natal_state,
                    transit_lord_state=transit_state,
                    relationship_type=NakshatraRelationshipType.NATAL_NAKSHATRA_ACTIVATION,
                    activation_start=window_start,
                    activation_end=window_end,
                    provenance="JRE-026 natal activation computation",
                )
                activations.append(activation)

        return activations

    def _compute_mutual_exchanges(
        self,
        planet_states: tuple[PlanetState, ...],
        state_map: dict[BodyId, PlanetState],
    ) -> list[NakshatraActivation]:
        """Compute activations from mutual nakshatra lord exchanges.

        A mutual exchange occurs when Planet A is in a nakshatra owned by
        Planet B, AND Planet B is in a nakshatra owned by Planet A.
        """
        activations: list[NakshatraActivation] = []

        # Build mapping: planet -> nakshatra lord of its nakshatra
        planet_to_lord: dict[BodyId, BodyId] = {}
        for state in planet_states:
            planet_to_lord[state.body] = lord_of(state.nakshatra)

        # Check for mutual exchanges
        checked: set[tuple[BodyId, BodyId]] = set()
        for state_a in planet_states:
            lord_a = planet_to_lord.get(state_a.body)
            if lord_a is None:
                continue

            state_b = state_map.get(lord_a)
            if state_b is None:
                continue

            lord_b = planet_to_lord.get(state_b.body)
            if lord_b is None:
                continue

            # Check if mutual: A's lord is B, and B's lord is A
            if lord_b == state_a.body:
                if state_a.body.value < state_b.body.value:
                    pair: tuple[BodyId, BodyId] = (state_a.body, state_b.body)
                else:
                    pair = (state_b.body, state_a.body)
                if pair not in checked:
                    checked.add(pair)

                    nakshatra_lord_a = lord_of(state_a.nakshatra)
                    activation = NakshatraActivation(
                        source_planet=state_a.body,
                        source_position=state_a,
                        nakshatra=state_a.nakshatra,
                        nakshatra_lord=nakshatra_lord_a,
                        natal_lord_state=state_b,
                        transit_lord_state=None,
                        relationship_type=NakshatraRelationshipType.MUTUAL_NAKSHATRA_EXCHANGE,
                        provenance="JRE-026 mutual exchange computation",
                    )
                    activations.append(activation)

        return activations

    def _compute_dependencies(
        self,
        planet_states: tuple[PlanetState, ...],
        state_map: dict[BodyId, PlanetState],
    ) -> list[NakshatraActivation]:
        """Compute activations from nakshatra dependencies.

        A dependency occurs when two planets occupy the same nakshatra,
        creating a shared activation pattern.
        """
        activations: list[NakshatraActivation] = []

        # Group planets by nakshatra
        nakshatra_planets: dict[NakshatraId, list[PlanetState]] = {}
        for state in planet_states:
            if state.nakshatra not in nakshatra_planets:
                nakshatra_planets[state.nakshatra] = []
            nakshatra_planets[state.nakshatra].append(state)

        # Create dependency activations for shared nakshatras
        for nakshatra, planets in nakshatra_planets.items():
            if len(planets) > 1:
                nakshatra_lord = lord_of(nakshatra)
                for state in planets:
                    activation = NakshatraActivation(
                        source_planet=state.body,
                        source_position=state,
                        nakshatra=nakshatra,
                        nakshatra_lord=nakshatra_lord,
                        natal_lord_state=None,
                        transit_lord_state=None,
                        relationship_type=NakshatraRelationshipType.NAKSHATRA_DEPENDENCY,
                        provenance="JRE-026 dependency computation",
                    )
                    activations.append(activation)

        return activations

    def _validate_request(
        self, planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Validate the activation computation request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidActivationRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidActivationRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )

"""JRE-016 AshtakavargaService facade.

``AshtakavargaService.calculate_ashtakavarga`` is the canonical entry point:
it computes Bhinnashtakavarga (individual planet points) and
Sarvashtakavarga (total points) for all 12 rashis.

It produces NO qualitative output.
"""

from __future__ import annotations

from jyotish import PlanetState, RashiId

from .config import load_config
from .errors import InvalidAshtakavargaRequestError
from .models import (
    AshtakavargaConfig,
    AshtakavargaReport,
    PlanetAshtakavarga,
    compute_planet_bindus,
    compute_sarvashtakavarga,
)


class AshtakavargaService:
    """Deterministic Ashtakavarga (eight-fold strength) computation facade."""

    def __init__(self, config: AshtakavargaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> AshtakavargaConfig:
        return self._config

    def calculate_ashtakavarga(
        self,
        planet_states: tuple[PlanetState, ...],
    ) -> AshtakavargaReport:
        """Compute Ashtakavarga for all planets.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            The natal planet states from JRE-003.

        Returns
        -------
        AshtakavargaReport
            Bhinnashtakavarga per planet + Sarvashtakavarga totals.
        """
        self._validate_request(planet_states)

        planet_scores: list[PlanetAshtakavarga] = []

        for state in planet_states:
            rashi_idx = list(RashiId).index(state.rashi)
            bindus = compute_planet_bindus(state.body, rashi_idx)
            planet_scores.append(PlanetAshtakavarga(
                planet=state.body,
                bindus=bindus,
            ))

        sarva = compute_sarvashtakavarga(tuple(planet_scores))

        return AshtakavargaReport(
            bhinnashtakavarga=tuple(planet_scores),
            sarvashtakavarga=sarva,
        )

    def _validate_request(
        self, planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Validate the Ashtakavarga computation request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidAshtakavargaRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidAshtakavargaRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )

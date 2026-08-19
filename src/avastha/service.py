"""JRE-015 AvasthaService facade.

``AvasthaService.calculate_avasthas`` is the canonical entry point: it
assigns classical Jagradadi, Deeptadi, and optionally Baladi states
to each planet, computing a composite strength multiplier.

It produces NO qualitative output.
"""

from __future__ import annotations

from jyotish import PlanetState

from .config import load_config
from .errors import InvalidAvasthaRequestError
from .models import (
    DEFAULT_DEEPTADI_MULTIPLIERS,
    DEFAULT_JAGRADI_MULTIPLIERS,
    AvasthaConfig,
    AvasthaReport,
    AvasthaResult,
    compute_deeptadi,
    compute_jagradadi,
)


class AvasthaService:
    """Deterministic Avastha (planetary state) computation facade."""

    def __init__(self, config: AvasthaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> AvasthaConfig:
        return self._config

    def calculate_avasthas(
        self,
        planet_states: tuple[PlanetState, ...],
    ) -> AvasthaReport:
        """Compute Avastha states for each planet.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            The natal planet states from JRE-003.

        Returns
        -------
        AvasthaReport
            Per-planet state results with composite multiplier.
        """
        self._validate_request(planet_states)

        results: list[AvasthaResult] = []

        for state in planet_states:
            jagradadi = compute_jagradadi(state.degree_in_rashi)
            deeptadi = compute_deeptadi(state.body, state.rashi)
            baladi = None  # V1: Baladi requires varga data; omitted for now

            jag_mult = self._config.jagradadi_multipliers.get(
                jagradadi.value, DEFAULT_JAGRADI_MULTIPLIERS.get(jagradadi, 1.0)
            )
            deep_mult = self._config.deeptadi_multipliers.get(
                deeptadi.value, DEFAULT_DEEPTADI_MULTIPLIERS.get(deeptadi, 1.0)
            )

            # Composite multiplier: geometric mean of jagradadi and deeptadi
            multiplier = jag_mult * deep_mult

            results.append(AvasthaResult(
                planet=state.body,
                jagradadi=jagradadi,
                deeptadi=deeptadi,
                baladi=baladi,
                multiplier=multiplier,
            ))

        return AvasthaReport(results=tuple(results))

    def _validate_request(
        self, planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Validate the Avastha computation request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidAvasthaRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidAvasthaRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )

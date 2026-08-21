"""JRE-018 JaiminiService facade.

``JaiminiService.calculate_jaimini`` is the canonical entry point:
it computes the Chara Dasha sequence and Argala analysis for
a given natal chart.

It produces NO qualitative output.
"""

from __future__ import annotations

from jyotish import PlanetState, RashiId

from .config import load_config
from .errors import InvalidJaiminiRequestError
from .models import (
    JaiminiConfig,
    JaiminiReport,
    classify_lagna_nature,
    compute_argala,
    compute_chara_dasha_sequence,
    compute_starting_sign,
)


class JaiminiService:
    """Deterministic Jaimini (Chara Dasha / Argala) computation facade."""

    def __init__(self, config: JaiminiConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> JaiminiConfig:
        return self._config

    def calculate_jaimini(
        self,
        lagna_rashi: RashiId,
        planet_states: tuple[PlanetState, ...],
    ) -> JaiminiReport:
        """Compute Jaimini (Chara Dasha / Argala) for a given natal chart.

        Parameters
        ----------
        lagna_rashi : RashiId
            The ascendant rashi from the natal chart.
        planet_states : tuple of PlanetState
            Natal planet positions.

        Returns
        -------
        JaiminiReport
            Chara Dasha periods and Argala analysis.
        """
        self._validate_request(lagna_rashi, planet_states)

        lagna_nature = classify_lagna_nature(lagna_rashi)

        # Determine starting sign
        start_house_offset = self._config.chara_dasha_start_sign.get(
            lagna_nature.value, 9,
        )
        starting_sign = compute_starting_sign(
            lagna_rashi=lagna_rashi,
            lagna_nature=lagna_nature,
            planet_states=planet_states,
            start_house_offset=start_house_offset,
        )

        # Generate Chara Dasha sequence
        chara_dasha = compute_chara_dasha_sequence(
            starting_sign=starting_sign,
            period_years=self._config.default_period_years,
            natal_moon_rashi=lagna_rashi,
        )

        # Compute Argala for each rashi
        argala_results = []
        for rashi in RashiId:
            result = compute_argala(
                target_rashi=rashi,
                planet_states=planet_states,
                intervening_houses=self._config.argala_intervening_houses,
                obstructing_houses=self._config.argala_obstructing_houses,
            )
            argala_results.append(result)

        return JaiminiReport(
            chara_dasha=chara_dasha,
            argala=tuple(argala_results),
        )

    def _validate_request(
        self,
        lagna_rashi: RashiId,
        planet_states: tuple[PlanetState, ...],
    ) -> None:
        """Validate the Jaimini computation request."""
        if not isinstance(lagna_rashi, RashiId):
            raise InvalidJaiminiRequestError(
                f"lagna_rashi must be a RashiId, got {type(lagna_rashi).__name__}"
            )
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidJaiminiRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidJaiminiRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )

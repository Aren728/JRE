"""JRE-017 TajikaService facade.

``TajikaService.calculate_tajika`` is the canonical entry point:
it computes the Muntha, Varsheshwar, and classical Sahams for
a given Solar Return chart.

It produces NO qualitative output.
"""

from __future__ import annotations

from jyotish import BodyId, PlanetState, RashiId

from .config import load_config
from .errors import InvalidTajikaRequestError
from .models import (
    SAHAM_FORMULAS,
    MunthaResult,
    SahamResult,
    SahamType,
    TajikaConfig,
    TajikaReport,
    compute_muntha_lord,
    compute_muntha_rashi,
    compute_saham_longitude,
    compute_varsheshwar,
    longitude_to_degree_in_rashi,
    longitude_to_rashi,
)


class TajikaService:
    """Deterministic Tajika (Varshaphala / annual chart) computation facade."""

    def __init__(self, config: TajikaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> TajikaConfig:
        return self._config

    def calculate_tajika(
        self,
        natal_moon_rashi: RashiId,
        lagna_longitude: float,
        planet_states: tuple[PlanetState, ...],
        elapsed_years: int,
        year_lord: BodyId,
        lagna_lord: BodyId,
    ) -> TajikaReport:
        """Compute Tajika (Varshaphala) for a given year.

        Parameters
        ----------
        natal_moon_rashi : RashiId
            Moon's rashi at birth.
        lagna_longitude : float
            Longitude of the Lagna (ascendant) in the solar return chart.
        planet_states : tuple of PlanetState
            Planet positions in the solar return chart.
        elapsed_years : int
            Number of completed years since birth.
        year_lord : BodyId
            Vimshottari year lord for the current year.
        lagna_lord : BodyId
            Lord of the Lagna in the solar return chart.

        Returns
        -------
        TajikaReport
            Muntha, Varsheshwar, and Sahams.
        """
        self._validate_request(
            natal_moon_rashi, planet_states, elapsed_years,
            year_lord, lagna_lord,
        )

        # Compute Muntha
        muntha_rashi = compute_muntha_rashi(natal_moon_rashi, elapsed_years)
        muntha_lord = compute_muntha_lord(muntha_rashi)
        # Muntha house = 1 (from its own position)
        muntha_house = 1

        # Compute Varsheshwar
        varsheshwar = compute_varsheshwar(muntha_lord, year_lord, lagna_lord)

        # Build planet lookup for Saham calculations
        planet_lookup = self._build_planet_lookup(planet_states)

        # Compute Sahams
        sahams = self._compute_sahams(
            lagna_longitude, planet_lookup, self._config.enabled_sahams,
        )

        return TajikaReport(
            muntha=MunthaResult(
                rashi=muntha_rashi,
                house=muntha_house,
                lord=muntha_lord,
            ),
            varsheshwar=varsheshwar,
            sahams=tuple(sahams),
        )

    def _build_planet_lookup(
        self, planet_states: tuple[PlanetState, ...],
    ) -> dict[BodyId, float]:
        """Build a lookup from BodyId to longitude."""
        lookup: dict[BodyId, float] = {}
        for state in planet_states:
            lookup[state.body] = state.longitude_used
        return lookup

    def _compute_sahams(
        self,
        lagna_longitude: float,
        planet_lookup: dict[BodyId, float],
        enabled: tuple[SahamType, ...],
    ) -> list[SahamResult]:
        """Compute enabled Sahams."""
        sahams: list[SahamResult] = []
        for saham_type in enabled:
            formula = SAHAM_FORMULAS.get(saham_type)
            if formula is None:
                continue
            planet_a_id, planet_b_id = formula
            planet_a_lon = planet_lookup.get(planet_a_id, 0.0)
            planet_b_lon = planet_lookup.get(planet_b_id, 0.0)

            saham_lon = compute_saham_longitude(
                lagna_longitude, planet_a_lon, planet_b_lon,
            )
            saham_rashi = longitude_to_rashi(saham_lon)
            saham_deg = longitude_to_degree_in_rashi(saham_lon)

            sahams.append(SahamResult(
                saham_name=saham_type,
                rashi=saham_rashi,
                degree=saham_deg,
            ))
        return sahams

    def _validate_request(
        self,
        natal_moon_rashi: RashiId,
        planet_states: tuple[PlanetState, ...],
        elapsed_years: int,
        year_lord: BodyId,
        lagna_lord: BodyId,
    ) -> None:
        """Validate the Tajika computation request."""
        if not isinstance(natal_moon_rashi, RashiId):
            raise InvalidTajikaRequestError(
                f"natal_moon_rashi must be a RashiId, got {type(natal_moon_rashi).__name__}"
            )
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidTajikaRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidTajikaRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )
        if not isinstance(elapsed_years, int) or elapsed_years < 0:
            raise InvalidTajikaRequestError(
                f"elapsed_years must be a non-negative int, got {elapsed_years!r}"
            )
        if not isinstance(year_lord, BodyId):
            raise InvalidTajikaRequestError(
                f"year_lord must be a BodyId, got {type(year_lord).__name__}"
            )
        if not isinstance(lagna_lord, BodyId):
            raise InvalidTajikaRequestError(
                f"lagna_lord must be a BodyId, got {type(lagna_lord).__name__}"
            )

"""JRE-019 PrashnaService facade.

``PrashnaService.cast_prashna`` is the canonical entry point:
it computes the Query Ascendant (Prashna Lagna) and maps the
relevant houses for a specific inquiry based on the exact time
of the query.

It produces NO qualitative output.
"""

from __future__ import annotations

from jyotish import PlanetState, RashiId

from .config import load_config
from .errors import InvalidPrashnaRequestError
from .models import (
    PrashnaCategory,
    PrashnaChart,
    PrashnaConfig,
    PrashnaReport,
    QueryLocation,
    compute_prashna_lagna,
    lookup_moon_nakshatra_lord,
    resolve_house_mapping,
)


class PrashnaService:
    """Deterministic Prashna (Horary) computation facade."""

    def __init__(self, config: PrashnaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> PrashnaConfig:
        return self._config

    def cast_prashna(
        self,
        query_time_utc: str,
        query_location: QueryLocation,
        query_category: str,
        planet_states: tuple[PlanetState, ...],
    ) -> PrashnaReport:
        """Cast a Prashna (horary) chart and derive the house mapping.

        Parameters
        ----------
        query_time_utc : str
            ISO-UTC timestamp of the query.
        query_location : QueryLocation
            Geographic location of the querent.
        query_category : str
            The category of the query (e.g., "WEALTH", "CAREER").
        planet_states : tuple of PlanetState
            Planet positions at the exact query time.

        Returns
        -------
        PrashnaReport
            The Prashna chart and house mapping.
        """
        self._validate_request(
            query_time_utc, query_location, query_category, planet_states,
        )

        # Determine Prashna Lagna from Moon's Nakshatra lord
        moon_lord = lookup_moon_nakshatra_lord(planet_states)
        prashna_lagna = compute_prashna_lagna(moon_lord)

        # Determine Moon's rashi
        moon_rashi = RashiId.MESHA
        for state in planet_states:
            if state.body == __import__("jyotish", fromlist=["BodyId"]).BodyId.MOON:
                moon_rashi = state.rashi
                break

        # Build PrashnaChart
        chart = PrashnaChart(
            query_time_utc=query_time_utc,
            query_location=query_location,
            prashna_lagna=prashna_lagna,
            query_moon_rashi=moon_rashi,
        )

        # Resolve house mapping
        category = PrashnaCategory(query_category)
        house_mapping = resolve_house_mapping(
            category, self._config.house_mappings,
        )

        return PrashnaReport(
            chart=chart,
            house_mapping=house_mapping,
        )

    def _validate_request(
        self,
        query_time_utc: str,
        query_location: QueryLocation,
        query_category: str,
        planet_states: tuple[PlanetState, ...],
    ) -> None:
        """Validate the Prashna computation request."""
        if not isinstance(query_time_utc, str) or query_time_utc == "":
            raise InvalidPrashnaRequestError(
                f"query_time_utc must be a non-empty string, got {type(query_time_utc).__name__}"
            )
        if not isinstance(query_location, QueryLocation):
            raise InvalidPrashnaRequestError(
                f"query_location must be a QueryLocation, got {type(query_location).__name__}"
            )
        if not isinstance(query_category, str) or query_category == "":
            raise InvalidPrashnaRequestError(
                f"query_category must be a non-empty string, got {type(query_category).__name__}"
            )
        try:
            PrashnaCategory(query_category)
        except ValueError as exc:
            valid = [c.value for c in PrashnaCategory]
            raise InvalidPrashnaRequestError(
                f"query_category must be one of {valid}, got {query_category!r}"
            ) from exc
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidPrashnaRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidPrashnaRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )
        # Check Moon is present
        from jyotish import BodyId
        has_moon = any(s.body == BodyId.MOON for s in planet_states)
        if not has_moon:
            raise InvalidPrashnaRequestError(
                "planet_states must contain the Moon (BodyId.MOON)"
            )

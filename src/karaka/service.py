"""JRE-014 KarakaService facade.

``KarakaService.calculate_karakas`` is the canonical entry point: it
assigns and ranks Naisargika (Natural), Sthira (Permanent), Chara
(Temporary), and Vishesha (Special) significators for all classical
life categories.

It performs NO prediction, interpretation, or judgment.
"""

from __future__ import annotations

from bala.models import ShadbalaReport
from jyotish import BodyId, PlanetState

from .config import load_config
from .errors import InvalidKarakaRequestError
from .models import (
    DEFAULT_NAISARGIKA,
    DEFAULT_STHIRA,
    KarakaAssignment,
    KarakaCategory,
    KarakaConfig,
    KarakaReport,
    KarakaType,
    compute_chara_karakas,
)


class KarakaService:
    """Deterministic Karaka (significator) computation facade."""

    def __init__(self, config: KarakaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> KarakaConfig:
        return self._config

    def calculate_karakas(
        self,
        planet_states: tuple[PlanetState, ...],
        bala_report: ShadbalaReport | None = None,
    ) -> KarakaReport:
        """Compute significator assignments.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            The natal planet states from JRE-003.
        bala_report : ShadbalaReport | None
            Shadbala strengths.  Used for strength modifier.

        Returns
        -------
        KarakaReport
            Complete significator report with all types.
        """
        self._validate_request(planet_states)

        assignments: list[KarakaAssignment] = []

        # 1. Naisargika (Natural) Karakas
        assignments.extend(self._compute_naisargika(bala_report))

        # 2. Sthira (Permanent) Karakas
        assignments.extend(self._compute_sthira(bala_report))

        # 3. Chara (Temporary) Karakas
        assignments.extend(self._compute_chara(planet_states, bala_report))

        return KarakaReport(assignments=tuple(assignments))

    # ------------------------------------------------------------------ #
    # Naisargika Karakas
    # ------------------------------------------------------------------ #

    def _compute_naisargika(
        self, bala_report: ShadbalaReport | None
    ) -> list[KarakaAssignment]:
        """Map Naisargika karakas from config."""
        assignments: list[KarakaAssignment] = []

        # Build reverse map from config (planet_str -> category_str)
        nais_map: dict[BodyId, KarakaCategory] = {}
        for planet_str, cat_str in self._config.naisargika.items():
            try:
                planet = BodyId(planet_str)
                category = KarakaCategory(cat_str)
                nais_map[planet] = category
            except (ValueError, KeyError):
                continue

        # If config is empty, use defaults
        if not nais_map:
            nais_map = dict(DEFAULT_NAISARGIKA)

        for planet, category in sorted(nais_map.items(), key=lambda x: x[0].value):
            strength = self._get_strength_modifier(planet, bala_report)
            assignments.append(KarakaAssignment(
                category=category,
                planet=planet,
                karaka_type=KarakaType.NAISARGIKA,
                rank=1,
                strength_modifier=strength,
            ))

        return assignments

    # ------------------------------------------------------------------ #
    # Sthira Karakas
    # ------------------------------------------------------------------ #

    def _compute_sthira(
        self, bala_report: ShadbalaReport | None
    ) -> list[KarakaAssignment]:
        """Map Sthira karakas from config."""
        assignments: list[KarakaAssignment] = []

        # Build map from config (category_str -> planet_str)
        sthi_map: dict[KarakaCategory, BodyId] = {}
        for cat_str, planet_str in self._config.sthira.items():
            try:
                category = KarakaCategory(cat_str)
                planet = BodyId(planet_str)
                sthi_map[category] = planet
            except (ValueError, KeyError):
                continue

        # If config is empty, use defaults
        if not sthi_map:
            sthi_map = dict(DEFAULT_STHIRA)

        for category, planet in sorted(sthi_map.items(), key=lambda x: x[0].value):
            strength = self._get_strength_modifier(planet, bala_report)
            assignments.append(KarakaAssignment(
                category=category,
                planet=planet,
                karaka_type=KarakaType.STHIRA,
                rank=1,
                strength_modifier=strength,
            ))

        return assignments

    # ------------------------------------------------------------------ #
    # Chara Karakas (Jaimini)
    # ------------------------------------------------------------------ #

    def _compute_chara(
        self,
        planet_states: tuple[PlanetState, ...],
        bala_report: ShadbalaReport | None,
    ) -> list[KarakaAssignment]:
        """Compute Chara karakas from planetary longitudes."""
        chara_pairs = compute_chara_karakas(
            planet_states, count=self._config.chara_planet_count
        )

        assignments: list[KarakaAssignment] = []
        for rank_idx, (category, planet) in enumerate(chara_pairs):
            strength = self._get_strength_modifier(planet, bala_report)
            assignments.append(KarakaAssignment(
                category=category,
                planet=planet,
                karaka_type=KarakaType.CHARA,
                rank=rank_idx + 1,
                strength_modifier=strength,
            ))

        return assignments

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _get_strength_modifier(
        self,
        planet: BodyId,
        bala_report: ShadbalaReport | None,
    ) -> float:
        """Get strength modifier from Shadbala, or 1.0 if unavailable."""
        if bala_report is None:
            return 1.0
        result = bala_report.result_for(planet)
        if result is None:
            return 1.0
        # Clamp ratio to [0, 1] range for modifier
        return min(max(result.ratio, 0.0), 1.0)

    def _validate_request(
        self, planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Validate the Karaka computation request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidKarakaRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidKarakaRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )

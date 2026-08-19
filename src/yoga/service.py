"""JRE-013 YogaService facade.

``YogaService.identify_yogas`` is the canonical entry point: it
evaluates classical structural yoga rules from planetary positions,
Shadbala strengths, and Drik aspect graphs.

Classical yogas (V1):
- Gajakesari Yoga: Jupiter in Kendra from Moon
- Raja Yoga: Kendra lord and Trikona lord connected
- Dhana Yoga: 2nd lord and 11th lord connected
- Viparita Raja Yoga: Dusthana lords exchange or conjoin

It performs NO prediction, interpretation, or judgment.
"""

from __future__ import annotations

from bala.models import ShadbalaReport
from drik.models import DrikResult
from jyotish import BodyId, PlanetState, RashiId

from .config import load_config
from .errors import InvalidYogaRequestError
from .models import (
    DUSTHANA_HOUSES,
    KENDRA_HOUSES,
    SIGN_LORDS,
    TRIKONA_HOUSES,
    ConnectionType,
    YogaCondition,
    YogaConfig,
    YogaId,
    YogaReport,
    YogaResult,
    rashi_number,
)


class YogaService:
    """Deterministic Yoga identification facade."""

    def __init__(self, config: YogaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> YogaConfig:
        return self._config

    def identify_yogas(
        self,
        planet_states: tuple[PlanetState, ...],
        lagna_sign: RashiId | None = None,
        bala_report: ShadbalaReport | None = None,
        drik_result: DrikResult | None = None,
    ) -> YogaReport:
        """Evaluate classical yoga rules.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            The natal planet states from JRE-003.
        lagna_sign : RashiId | None
            The ascendant sign.  Required for house-based yogas.
        bala_report : ShadbalaReport | None
            Shadbala strengths.  Used for strength modifier.
        drik_result : DrikResult | None
            Aspect graph.  Used for aspect-based connections.

        Returns
        -------
        YogaReport
            Complete yoga evaluation with presence, strength, evidence.
        """
        self._validate_request(planet_states)

        # Build lookup structures
        state_map: dict[BodyId, PlanetState] = {s.body: s for s in planet_states}
        lagna_num = rashi_number(lagna_sign) if lagna_sign is not None else None

        # Pre-compute connections between planet pairs
        connections = self._build_connection_map(planet_states, drik_result)

        results: list[YogaResult] = []

        for yoga_id in self._config.enabled_yogas:
            result = self._evaluate_yoga(
                yoga_id, state_map, lagna_num, connections, bala_report
            )
            results.append(result)

        return YogaReport(results=tuple(results))

    # ------------------------------------------------------------------ #
    # Connection detection
    # ------------------------------------------------------------------ #

    def _build_connection_map(
        self,
        planet_states: tuple[PlanetState, ...],
        drik_result: DrikResult | None,
    ) -> dict[tuple[BodyId, BodyId], ConnectionType]:
        """Build a map of planet-pair connections."""
        conns: dict[tuple[BodyId, BodyId], ConnectionType] = {}

        for i, s1 in enumerate(planet_states):
            for s2 in planet_states[i + 1:]:
                conn = self._detect_connection(s1, s2, drik_result)
                if conn != ConnectionType.NONE:
                    conns[(s1.body, s2.body)] = conn
                    conns[(s2.body, s1.body)] = conn

        return conns

    def _detect_connection(
        self,
        s1: PlanetState,
        s2: PlanetState,
        drik_result: DrikResult | None,
    ) -> ConnectionType:
        """Detect the strongest connection between two planets."""
        # Check conjunction (same rashi)
        if s1.rashi == s2.rashi:
            return ConnectionType.CONJUNCTION

        # Check sign exchange (lord of A in B's sign, lord of B in A's sign)
        r1_num = rashi_number(s1.rashi)
        r2_num = rashi_number(s2.rashi)
        lord1 = SIGN_LORDS.get(r1_num)
        lord2 = SIGN_LORDS.get(r2_num)
        if lord1 == s2.body and lord2 == s1.body:
            return ConnectionType.EXCHANGE

        # Check aspect via DrikResult
        if drik_result is not None:
            for asp in drik_result.aspects:
                if asp.source_planet == s1.body and asp.target_planet == s2.body:
                    return ConnectionType.ASPECT
                if asp.source_planet == s2.body and asp.target_planet == s1.body:
                    return ConnectionType.ASPECT

        return ConnectionType.NONE

    # ------------------------------------------------------------------ #
    # Yoga evaluation
    # ------------------------------------------------------------------ #

    def _evaluate_yoga(
        self,
        yoga_id: YogaId,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
        connections: dict[tuple[BodyId, BodyId], ConnectionType],
        bala_report: ShadbalaReport | None,
    ) -> YogaResult:
        """Evaluate a single yoga rule."""
        if yoga_id == YogaId.GAJAKESARI_YOGA:
            return self._eval_gajakesari(state_map, bala_report)
        if yoga_id == YogaId.RAJA_YOGA:
            return self._eval_raja(state_map, lagna_num, connections, bala_report)
        if yoga_id == YogaId.DHANA_YOGA:
            return self._eval_dhana(state_map, lagna_num, connections, bala_report)
        if yoga_id == YogaId.VIPARITA_RAJA_YOGA:
            return self._eval_viparita_raja(state_map, lagna_num, connections, bala_report)
        # Unknown yoga — not present
        return self._absent(yoga_id, "Unknown yoga rule; not evaluated.")

    def _eval_gajakesari(
        self,
        state_map: dict[BodyId, PlanetState],
        bala_report: ShadbalaReport | None,
    ) -> YogaResult:
        """Gajakesari Yoga: Jupiter in Kendra (1,4,7,10) from Moon."""
        jup = state_map.get(BodyId.JUPITER)
        moon = state_map.get(BodyId.MOON)
        if jup is None or moon is None:
            return self._absent(YogaId.GAJAKESARI_YOGA, "Jupiter or Moon not in chart")

        jup_sign = rashi_number(jup.rashi)
        moon_sign = rashi_number(moon.rashi)
        # Signs away from Moon to Jupiter (1-12)
        offset = (jup_sign - moon_sign) % 12 + 1

        if offset not in KENDRA_HOUSES:
            return self._absent(
                YogaId.GAJAKESARI_YOGA,
                f"Jupiter is {offset} signs from Moon (not Kendra)",
            )

        strength = self._compute_strength(
            [BodyId.JUPITER, BodyId.MOON], bala_report
        )
        evidence = (
            f"Jupiter in {jup.rashi.value}, Moon in {moon.rashi.value}",
            f"Jupiter is {offset} signs from Moon (Kendra)",
        )
        conditions = (
            YogaCondition(
                condition_type="KENDRA_FROM",
                planets_involved=(BodyId.JUPITER, BodyId.MOON),
                houses_involved=(offset,),
                details=f"Jupiter {offset} signs from Moon",
            ),
        )
        return YogaResult(
            yoga_id=YogaId.GAJAKESARI_YOGA,
            is_present=True,
            strength_modifier=strength,
            evidence=evidence,
            conditions=conditions,
        )

    def _eval_raja(
        self,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
        connections: dict[tuple[BodyId, BodyId], ConnectionType],
        bala_report: ShadbalaReport | None,
    ) -> YogaResult:
        """Raja Yoga: Kendra lord and Trikona lord connected."""
        if lagna_num is None:
            return self._absent(YogaId.RAJA_YOGA, "Lagna not provided")

        # Find Kendra and Trikona house lords
        kendra_lords: set[BodyId] = set()
        trikona_lords: set[BodyId] = set()
        for house in KENDRA_HOUSES:
            sign_num = (lagna_num - 1 + house - 1) % 12 + 1
            lord = SIGN_LORDS.get(sign_num)
            if lord is not None:
                kendra_lords.add(lord)
        for house in TRIKONA_HOUSES:
            sign_num = (lagna_num - 1 + house - 1) % 12 + 1
            lord = SIGN_LORDS.get(sign_num)
            if lord is not None:
                trikona_lords.add(lord)

        # Check for connections between Kendra and Trikona lords
        for k_lord in kendra_lords:
            for t_lord in trikona_lords:
                if k_lord == t_lord:
                    continue  # Same planet (Lagna lord is both)
                conn = connections.get((k_lord, t_lord), ConnectionType.NONE)
                if conn != ConnectionType.NONE:
                    strength = self._compute_strength(
                        [k_lord, t_lord], bala_report
                    )
                    evidence = (
                        f"Kendra lord {k_lord.value} connected to "
                        f"Trikona lord {t_lord.value} via {conn.value}",
                    )
                    conditions = (
                        YogaCondition(
                            condition_type="KENDRA_TRIKONA_CONNECTION",
                            planets_involved=(k_lord, t_lord),
                            houses_involved=(),
                            connection_type=conn,
                            details=f"{k_lord.value} --{conn.value}--> {t_lord.value}",
                        ),
                    )
                    return YogaResult(
                        yoga_id=YogaId.RAJA_YOGA,
                        is_present=True,
                        strength_modifier=strength,
                        evidence=evidence,
                        conditions=conditions,
                    )

        return self._absent(YogaId.RAJA_YOGA, "No Kendra-Trikona lord connection found")

    def _eval_dhana(
        self,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
        connections: dict[tuple[BodyId, BodyId], ConnectionType],
        bala_report: ShadbalaReport | None,
    ) -> YogaResult:
        """Dhana Yoga: 2nd lord and 11th lord connected."""
        if lagna_num is None:
            return self._absent(YogaId.DHANA_YOGA, "Lagna not provided")

        # 2nd and 11th house signs from Lagna
        sign_2 = (lagna_num - 1 + 1) % 12 + 1  # 2nd house
        sign_11 = (lagna_num - 1 + 10) % 12 + 1  # 11th house
        lord_2 = SIGN_LORDS.get(sign_2)
        lord_11 = SIGN_LORDS.get(sign_11)

        if lord_2 is None or lord_11 is None:
            return self._absent(YogaId.DHANA_YOGA, "Could not determine house lords")

        if lord_2 == lord_11:
            return self._absent(
                YogaId.DHANA_YOGA,
                f"Same lord {lord_2.value} owns 2nd and 11th",
            )

        conn = connections.get((lord_2, lord_11), ConnectionType.NONE)
        if conn == ConnectionType.NONE:
            return self._absent(
                YogaId.DHANA_YOGA,
                f"2nd lord {lord_2.value} and 11th lord {lord_11.value} not connected",
            )

        strength = self._compute_strength([lord_2, lord_11], bala_report)
        evidence = (
            f"2nd lord {lord_2.value} connected to 11th lord {lord_11.value} "
            f"via {conn.value}",
        )
        conditions = (
            YogaCondition(
                condition_type="DHANA_CONNECTION",
                planets_involved=(lord_2, lord_11),
                houses_involved=(2, 11),
                connection_type=conn,
                details=f"{lord_2.value} --{conn.value}--> {lord_11.value}",
            ),
        )
        return YogaResult(
            yoga_id=YogaId.DHANA_YOGA,
            is_present=True,
            strength_modifier=strength,
            evidence=evidence,
            conditions=conditions,
        )

    def _eval_viparita_raja(
        self,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
        connections: dict[tuple[BodyId, BodyId], ConnectionType],
        bala_report: ShadbalaReport | None,
    ) -> YogaResult:
        """Viparita Raja Yoga: Lords of 6, 8, 12 conjoin or exchange."""
        if lagna_num is None:
            return self._absent(YogaId.VIPARITA_RAJA_YOGA, "Lagna not provided")

        # Dusthana house lords
        dusthana_lords: list[BodyId] = []
        for house in DUSTHANA_HOUSES:
            sign_num = (lagna_num - 1 + house - 1) % 12 + 1
            lord = SIGN_LORDS.get(sign_num)
            if lord is not None:
                dusthana_lords.append(lord)

        # Check connections between any pair of dusthana lords
        for i, lord_a in enumerate(dusthana_lords):
            for lord_b in dusthana_lords[i + 1:]:
                conn = connections.get((lord_a, lord_b), ConnectionType.NONE)
                if conn in (ConnectionType.CONJUNCTION, ConnectionType.EXCHANGE):
                    strength = self._compute_strength(
                        [lord_a, lord_b], bala_report
                    )
                    evidence = (
                        f"Dusthana lord {lord_a.value} connected to "
                        f"{lord_b.value} via {conn.value}",
                    )
                    conditions = (
                        YogaCondition(
                            condition_type="VIPARITA_CONNECTION",
                            planets_involved=(lord_a, lord_b),
                            houses_involved=tuple(
                                h for h in DUSTHANA_HOUSES
                                if SIGN_LORDS.get(
                                    (lagna_num - 1 + h - 1) % 12 + 1
                                ) in (lord_a, lord_b)
                            ),
                            connection_type=conn,
                            details=f"{lord_a.value} --{conn.value}--> {lord_b.value}",
                        ),
                    )
                    return YogaResult(
                        yoga_id=YogaId.VIPARITA_RAJA_YOGA,
                        is_present=True,
                        strength_modifier=strength,
                        evidence=evidence,
                        conditions=conditions,
                    )

        return self._absent(
            YogaId.VIPARITA_RAJA_YOGA,
            "No dusthana lord conjunction or exchange found",
        )

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _absent(self, yoga_id: YogaId, reason: str) -> YogaResult:
        """Create a YogaResult for an absent yoga."""
        return YogaResult(
            yoga_id=yoga_id,
            is_present=False,
            strength_modifier=0.0,
            evidence=(reason,),
        )

    def _compute_strength(
        self,
        planets: list[BodyId],
        bala_report: ShadbalaReport | None,
    ) -> float:
        """Compute a strength modifier from Shadbala.

        Returns a value in [0.0, 1.0] based on the minimum ratio
        of the involved planets.
        """
        if bala_report is None:
            return 1.0

        min_ratio = float("inf")
        for planet in planets:
            result = bala_report.result_for(planet)
            if result is not None:
                min_ratio = min(min_ratio, result.ratio)

        if min_ratio == float("inf"):
            return 1.0

        threshold = self._config.min_bala_ratio
        if min_ratio <= threshold:
            return 0.0
        if min_ratio >= 1.0:
            return 1.0
        return (min_ratio - threshold) / (1.0 - threshold)

    def _validate_request(
        self, planet_states: tuple[PlanetState, ...]
    ) -> None:
        """Validate the Yoga computation request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidYogaRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidYogaRequestError(
                    f"planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )

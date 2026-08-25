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
    CONNECTION_STRENGTH,
    DIGNITY_STRENGTH,
    DUSTHANA_HOUSES,
    KENDRA_HOUSES,
    SIGN_LORDS,
    TRIKONA_HOUSES,
    ConnectionType,
    ParivartanaType,
    YogaCondition,
    YogaConfig,
    YogaId,
    YogaReport,
    YogaResult,
    YogaStrength,
    house_from_lagna,
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
            return self._eval_gajakesari(state_map, lagna_num, bala_report)
        if yoga_id == YogaId.RAJA_YOGA:
            return self._eval_raja(state_map, lagna_num, connections, bala_report)
        if yoga_id == YogaId.DHANA_YOGA:
            return self._eval_dhana(state_map, lagna_num, connections, bala_report)
        if yoga_id == YogaId.VIPARITA_RAJA_YOGA:
            return self._eval_viparita_raja(state_map, lagna_num, connections, bala_report)
        if yoga_id == YogaId.PANCHA_MAHAPURUSHA_YOGA:
            return self._eval_pancha_mahapurusha(state_map, lagna_num)
        if yoga_id == YogaId.KENDRADHIPATI_DOSHA:
            return self._eval_kendradhipati_dosha(state_map, lagna_num)
        if yoga_id == YogaId.NEECHA_BHANGA_YOGA:
            return self._eval_neecha_bhanga(state_map, lagna_num, bala_report)
        # Unknown yoga — not present
        return self._absent(yoga_id, "Unknown yoga rule; not evaluated.")

    def _eval_gajakesari(
        self,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
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
            [BodyId.JUPITER, BodyId.MOON], state_map, bala_report, lagna_num
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
        d9_strength = self._check_d9_strength(
            [BodyId.JUPITER], state_map, lagna_num
        )
        raw_result = YogaResult(
            yoga_id=YogaId.GAJAKESARI_YOGA,
            is_present=True,
            strength_modifier=strength,
            evidence=evidence,
            conditions=conditions,
            strength=d9_strength,
        )
        return self._apply_cancellation(raw_result, state_map, lagna_num)

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
                        [k_lord, t_lord], state_map, bala_report, lagna_num, conn
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
                    d9_strength = self._check_d9_strength(
                        [k_lord, t_lord], state_map, lagna_num
                    )
                    raw_result = YogaResult(
                        yoga_id=YogaId.RAJA_YOGA,
                        is_present=True,
                        strength_modifier=strength,
                        evidence=evidence,
                        conditions=conditions,
                        strength=d9_strength,
                    )
                    return self._apply_cancellation(raw_result, state_map, lagna_num)

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

        strength = self._compute_strength(
            [lord_2, lord_11], state_map, bala_report, lagna_num, conn
        )
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
        raw_result = YogaResult(
            yoga_id=YogaId.DHANA_YOGA,
            is_present=True,
            strength_modifier=strength,
            evidence=evidence,
            conditions=conditions,
        )
        return self._apply_cancellation(raw_result, state_map, lagna_num)

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
                        [lord_a, lord_b], state_map, bala_report, lagna_num, conn
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
                    raw_result = YogaResult(
                        yoga_id=YogaId.VIPARITA_RAJA_YOGA,
                        is_present=True,
                        strength_modifier=strength,
                        evidence=evidence,
                        conditions=conditions,
                    )
                    return self._apply_cancellation(raw_result, state_map, lagna_num)

        return self._absent(
            YogaId.VIPARITA_RAJA_YOGA,
            "No dusthana lord conjunction or exchange found",
        )

    def _eval_pancha_mahapurusha(
        self,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
    ) -> YogaResult:
        """Pancha Mahapurusha Yoga: planet in own sign/exaltation in Kendra.

        Five yogas: Ruchaka (Mars), Bhadra (Mercury), Hamsa (Jupiter),
        Malavya (Venus), Sasa (Saturn).
        """
        if lagna_num is None:
            return self._absent(YogaId.PANCHA_MAHAPURUSHA_YOGA, "Lagna not provided")

        _EXALTATION: dict[BodyId, int] = {
            BodyId.MARS: 10,
            BodyId.MERCURY: 6,
            BodyId.JUPITER: 4,
            BodyId.VENUS: 12,
            BodyId.SATURN: 7,
        }
        _OWN_SIGNS: dict[BodyId, tuple[int, ...]] = {
            BodyId.MARS: (1, 8),
            BodyId.MERCURY: (3, 6),
            BodyId.JUPITER: (9, 12),
            BodyId.VENUS: (2, 7),
            BodyId.SATURN: (10, 11),
        }
        _YOGA_NAMES: dict[BodyId, str] = {
            BodyId.MARS: "Ruchaka",
            BodyId.MERCURY: "Bhadra",
            BodyId.JUPITER: "Hamsa",
            BodyId.VENUS: "Malavya",
            BodyId.SATURN: "Sasa",
        }

        for planet in (BodyId.MARS, BodyId.MERCURY, BodyId.JUPITER, BodyId.VENUS, BodyId.SATURN):
            state = state_map.get(planet)
            if state is None:
                continue
            sign_num = rashi_number(state.rashi)
            is_own = planet in _OWN_SIGNS and sign_num in _OWN_SIGNS[planet]
            is_exalted = planet in _EXALTATION and sign_num == _EXALTATION[planet]
            if not (is_own or is_exalted):
                continue
            house = house_from_lagna(lagna_num, sign_num)
            if house not in KENDRA_HOUSES:
                continue
            dignity = "exalted" if is_exalted else "own sign"
            yoga_name = _YOGA_NAMES.get(planet, planet.value)
            strength = self._compute_strength(
                [planet], state_map, bala_report=None, lagna_num=lagna_num
            )
            evidence = (
                f"{yoga_name}: {planet.value} in {state.rashi.value} "
                f"({dignity}) in house {house} (Kendra)",
            )
            conditions = (
                YogaCondition(
                    condition_type="PANCHA_MAHAPURUSHA",
                    planets_involved=(planet,),
                    houses_involved=(house,),
                    details=(
                        f"{yoga_name}: {planet.value} in {state.rashi.value} "
                        f"({dignity}) in {house}th (Kendra)"
                    ),
                ),
            )
            raw_result = YogaResult(
                yoga_id=YogaId.PANCHA_MAHAPURUSHA_YOGA,
                is_present=True,
                strength_modifier=strength,
                evidence=evidence,
                conditions=conditions,
            )
            return self._apply_cancellation(raw_result, state_map, lagna_num)

        return self._absent(
            YogaId.PANCHA_MAHAPURUSHA_YOGA,
            "No planet in own sign/exaltation in Kendra",
        )

    def _eval_kendradhipati_dosha(
        self,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
    ) -> YogaResult:
        """Kendradhipati Dosha: natural benefic ruling Kendra houses."""
        if lagna_num is None:
            return self._absent(YogaId.KENDRADHIPATI_DOSHA, "Lagna not provided")

        # Natural benefics: Jupiter, Venus, Mercury, Moon
        _NATURAL_BENEFICS: tuple[BodyId, ...] = (
            BodyId.JUPITER, BodyId.VENUS, BodyId.MERCURY, BodyId.MOON,
        )

        # Find which planets rule Kendra houses from Lagna
        kendra_lords: set[BodyId] = set()
        for house in KENDRA_HOUSES:
            sign_num = (lagna_num - 1 + house - 1) % 12 + 1
            lord = SIGN_LORDS.get(sign_num)
            if lord is not None:
                kendra_lords.add(lord)

        # Check each natural benefic
        dosha_planets: list[BodyId] = []
        dosha_houses: list[int] = []
        for planet in _NATURAL_BENEFICS:
            if planet in kendra_lords:
                dosha_planets.append(planet)
                # Find which Kendra house(s) it rules
                for house in KENDRA_HOUSES:
                    sign_num = (lagna_num - 1 + house - 1) % 12 + 1
                    lord = SIGN_LORDS.get(sign_num)
                    if lord == planet:
                        dosha_houses.append(house)

        if not dosha_planets:
            return self._absent(
                YogaId.KENDRADHIPATI_DOSHA,
                "No natural benefic rules Kendra houses",
            )

        strength = self._compute_strength(
            dosha_planets, state_map, bala_report=None, lagna_num=lagna_num
        )
        planets_str = ", ".join(p.value for p in dosha_planets)
        houses_str = ", ".join(str(h) for h in sorted(dosha_houses))
        evidence = (
            f"Natural benefic(s) {planets_str} rule Kendra house(s) {houses_str}",
        )
        conditions = (
            YogaCondition(
                condition_type="KENDRADHIPATI_DOSHA",
                planets_involved=tuple(dosha_planets),
                houses_involved=tuple(sorted(dosha_houses)),
                details=f"{planets_str} rule Kendra {houses_str} — Kendradhipati Dosha",
            ),
        )
        raw_result = YogaResult(
            yoga_id=YogaId.KENDRADHIPATI_DOSHA,
            is_present=True,
            strength_modifier=strength,
            evidence=evidence,
            conditions=conditions,
        )
        return self._apply_cancellation(raw_result, state_map, lagna_num)

    def _eval_neecha_bhanga(
        self,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
        bala_report: ShadbalaReport | None,
    ) -> YogaResult:
        """Neecha Bhanga Yoga: debilitation cancelled.

        A debilitated planet triggers this yoga if ANY of:
        1. Lord of the debilitation sign is in Kendra from Lagna or Moon.
        2. The debilitated planet itself is in Kendra from Lagna or Moon.
        3. The planet exalted in that sign is in Kendra from Lagna or Moon.
        """
        _DEBILITATION: dict[BodyId, int] = {
            BodyId.SUN: 7,       # Libra
            BodyId.MOON: 8,      # Scorpio
            BodyId.MARS: 4,      # Cancer
            BodyId.MERCURY: 12,  # Pisces
            BodyId.JUPITER: 10,  # Capricorn
            BodyId.VENUS: 6,     # Virgo
            BodyId.SATURN: 1,    # Aries
        }
        _EXALTED_IN_SIGN: dict[int, BodyId] = {
            1: BodyId.SUN,       # Aries
            2: BodyId.MOON,      # Taurus
            4: BodyId.JUPITER,   # Cancer
            6: BodyId.MERCURY,   # Virgo
            7: BodyId.SATURN,    # Libra
            10: BodyId.MARS,     # Capricorn
            12: BodyId.VENUS,    # Pisces
        }

        moon = state_map.get(BodyId.MOON)
        moon_num = rashi_number(moon.rashi) if moon is not None else None

        ref_signs: list[int] = []
        if lagna_num is not None:
            ref_signs.append(lagna_num)
        if moon_num is not None and moon_num != lagna_num:
            ref_signs.append(moon_num)
        if not ref_signs:
            return self._absent(
                YogaId.NEECHA_BHANGA_YOGA, "Neither Lagna nor Moon available"
            )

        debilitated_planets: list[BodyId] = []
        evidence_parts: list[str] = []

        for planet, deb_sign in _DEBILITATION.items():
            state = state_map.get(planet)
            if state is None:
                continue
            if rashi_number(state.rashi) != deb_sign:
                continue

            planet_sign = rashi_number(state.rashi)
            found = False

            for ref in ref_signs:
                if found:
                    break
                ref_label = "Lagna" if ref == lagna_num else "Moon"

                # Condition 1: Lord of debilitation sign in Kendra from ref
                deb_lord = SIGN_LORDS.get(deb_sign)
                if deb_lord is not None:
                    deb_lord_state = state_map.get(deb_lord)
                    if deb_lord_state is not None:
                        lord_offset = (
                            rashi_number(deb_lord_state.rashi) - ref
                        ) % 12 + 1
                        if lord_offset in KENDRA_HOUSES:
                            debilitated_planets.append(planet)
                            evidence_parts.append(
                                f"{planet.value} debilitated in "
                                f"{state.rashi.value}; lord "
                                f"{deb_lord.value} in "
                                f"{deb_lord_state.rashi.value} "
                                f"({lord_offset}th from "
                                f"{ref_label} — Kendra)"
                            )
                            found = True
                            break

                # Condition 2: Debilitated planet in Kendra from ref
                planet_offset = (planet_sign - ref) % 12 + 1
                if planet_offset in KENDRA_HOUSES:
                    debilitated_planets.append(planet)
                    evidence_parts.append(
                        f"{planet.value} debilitated in "
                        f"{state.rashi.value} ({planet_offset}th from "
                        f"{ref_label} — Kendra)"
                    )
                    found = True
                    break

                # Condition 3: Planet exalted in that sign in Kendra from ref
                exalted_planet = _EXALTED_IN_SIGN.get(deb_sign)
                if exalted_planet is not None:
                    ex_state = state_map.get(exalted_planet)
                    if ex_state is not None:
                        ex_offset = (
                            rashi_number(ex_state.rashi) - ref
                        ) % 12 + 1
                        if ex_offset in KENDRA_HOUSES:
                            debilitated_planets.append(planet)
                            evidence_parts.append(
                                f"{planet.value} debilitated in "
                                f"{state.rashi.value}; "
                                f"{exalted_planet.value} (exalted in "
                                f"{state.rashi.value}) in "
                                f"{ex_state.rashi.value} "
                                f"({ex_offset}th from "
                                f"{ref_label} — Kendra)"
                            )
                            found = True
                            break

        if not debilitated_planets:
            return self._absent(
                YogaId.NEECHA_BHANGA_YOGA,
                "No debilitated planet has Neecha Bhanga",
            )

        strength = self._compute_strength(
            debilitated_planets, state_map, bala_report, lagna_num
        )
        evidence = tuple(evidence_parts)
        conditions = (
            YogaCondition(
                condition_type="NEECHA_BHANGA",
                planets_involved=tuple(debilitated_planets),
                houses_involved=(),
                details="; ".join(evidence_parts),
            ),
        )
        raw_result = YogaResult(
            yoga_id=YogaId.NEECHA_BHANGA_YOGA,
            is_present=True,
            strength_modifier=strength,
            evidence=evidence,
            conditions=conditions,
        )
        return self._apply_cancellation(raw_result, state_map, lagna_num)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _compute_navamsa_rashi_index(self, longitude: float) -> int:
        """Compute navamsa rashi index (0-11) from sidereal longitude."""
        return int(longitude * 9 / 30) % 12

    def _check_d9_strength(
        self,
        planets: list[BodyId],
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
    ) -> YogaStrength:
        """Check D9 (Navamsa) strength for yoga-forming planets.

        If any yoga-forming planet is in Kendra or Trikona in D9 → STRONG.
        Otherwise → MODERATE.
        """
        if lagna_num is None:
            return YogaStrength.MODERATE

        # Compute D9 lagna (navamsa of lagna at 0° of sign)
        lagna_longitude = (lagna_num - 1) * 30.0
        d9_lagna_index = self._compute_navamsa_rashi_index(lagna_longitude)
        d9_lagna_num = d9_lagna_index + 1

        for planet in planets:
            state = state_map.get(planet)
            if state is None:
                continue

            planet_navamsa_index = self._compute_navamsa_rashi_index(
                state.longitude_used
            )
            planet_navamsa_num = planet_navamsa_index + 1

            house = house_from_lagna(d9_lagna_num, planet_navamsa_num)
            if house in KENDRA_HOUSES or house in TRIKONA_HOUSES:
                return YogaStrength.STRONG

        return YogaStrength.MODERATE

    def _absent(self, yoga_id: YogaId, reason: str) -> YogaResult:
        """Create a YogaResult for an absent yoga."""
        return YogaResult(
            yoga_id=yoga_id,
            is_present=False,
            strength_modifier=0.0,
            evidence=(reason,),
        )

    def _check_cancellation(
        self,
        planets: list[BodyId],
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
    ) -> tuple[str, ...]:
        """Check if yoga conditions are cancelled for the given planets.

        Classical cancellation conditions (BPHS Ch.33):
        - Key planet debilitated (without Neecha Bhanga)
        - Key planet combust
        - Key planet in Dusthana (6/8/12)
        - Malefic aspect on yoga planets (requires drik_result)

        Returns tuple of cancellation reason strings.
        """
        reasons: list[str] = []
        for planet in planets:
            state = state_map.get(planet)
            if state is None:
                continue

            # Check debilitation
            dignity = self._get_dignity(state)
            if dignity == "DEBILITATED":
                reasons.append(
                    f"{planet.value} debilitated in {state.rashi.value}"
                )

            # Check combustion
            if planet not in (BodyId.SUN, BodyId.RAHU, BodyId.KETU):
                sun_state = state_map.get(BodyId.SUN)
                if sun_state is not None and self._is_combust(state, sun_state):
                    reasons.append(
                        f"{planet.value} combust near Sun"
                    )

            # Check Dusthana placement
            if lagna_num is not None:
                house = house_from_lagna(
                    lagna_num, rashi_number(state.rashi)
                )
                if house in DUSTHANA_HOUSES:
                    reasons.append(
                        f"{planet.value} in house {house} (Dusthana)"
                    )

        return tuple(reasons)

    def _apply_cancellation(
        self,
        result: YogaResult,
        state_map: dict[BodyId, PlanetState],
        lagna_num: int | None,
    ) -> YogaResult:
        """Apply cancellation detection to a yoga result.

        If cancellation conditions are found, sets is_cancelled=True
        and populates cancellation_reasons. The yoga remains is_present=True
        but with reduced strength_modifier.
        """
        if not result.is_present:
            return result

        # Collect all planets involved in the yoga
        all_planets: list[BodyId] = []
        for cond in result.conditions:
            all_planets.extend(cond.planets_involved)
        # Deduplicate while preserving order
        seen: set[BodyId] = set()
        unique_planets: list[BodyId] = []
        for p in all_planets:
            if p not in seen:
                seen.add(p)
                unique_planets.append(p)

        reasons = self._check_cancellation(unique_planets, state_map, lagna_num)
        if not reasons:
            return result

        # Apply cancellation: reduce strength but keep yoga present
        cancellation_factor = max(0.1, 1.0 - 0.3 * len(reasons))
        new_strength = result.strength_modifier * cancellation_factor

        return YogaResult(
            yoga_id=result.yoga_id,
            is_present=result.is_present,
            strength_modifier=new_strength,
            evidence=result.evidence,
            conditions=result.conditions,
            is_cancelled=True,
            cancellation_reasons=reasons,
            strength=result.strength,
        )

    def _compute_strength(
        self,
        planets: list[BodyId],
        state_map: dict[BodyId, PlanetState],
        bala_report: ShadbalaReport | None,
        lagna_num: int | None = None,
        connection_type: ConnectionType = ConnectionType.NONE,
    ) -> float:
        """Compute a strength modifier incorporating multiple factors.

        Combines (in order):
        1. Shadbala ratio (if available)
        2. Dignity strength (exaltation > own > friend > neutral > enemy > debilitation)
        3. Combustion penalty (planet combust → reduced contribution)
        4. Retrograde bonus (retrograde planet acts stronger)
        5. Connection type weight (conjunction/exchange > aspect)
        6. Dusthana placement penalty (conjunction in 6/8/12)

        Returns a value in [0.0, 1.0].
        """
        # Factor 1: Shadbala ratio
        shadbala_factor = 1.0
        if bala_report is not None:
            min_ratio = float("inf")
            for planet in planets:
                result = bala_report.result_for(planet)
                if result is not None:
                    min_ratio = min(min_ratio, result.ratio)
            if min_ratio != float("inf"):
                threshold = self._config.min_bala_ratio
                if min_ratio <= threshold:
                    shadbala_factor = 0.0
                elif min_ratio >= 1.0:
                    shadbala_factor = 1.0
                else:
                    shadbala_factor = (min_ratio - threshold) / (1.0 - threshold)

        # Factor 2: Dignity strength
        dignity_factor = 1.0
        min_dignity = 1.0
        for planet in planets:
            state = state_map.get(planet)
            if state is not None:
                dignity = self._get_dignity(state)
                weight = DIGNITY_STRENGTH.get(dignity, 0.5)
                min_dignity = min(min_dignity, weight)
        dignity_factor = min_dignity

        # Factor 3: Combustion penalty
        combustion_penalty = 1.0
        for planet in planets:
            if planet == BodyId.SUN:
                continue  # Sun is never combust
            if planet in (BodyId.RAHU, BodyId.KETU):
                continue  # Nodes are never combust
            state = state_map.get(planet)
            sun_state = state_map.get(BodyId.SUN)
            if state is not None and sun_state is not None and self._is_combust(state, sun_state):
                    combustion_penalty *= 0.3  # Significant penalty

        # Factor 4: Retrograde bonus
        retrograde_factor = 1.0
        for planet in planets:
            state = state_map.get(planet)
            if state is not None and state.retrograde.value == "RETROGRADE":
                retrograde_factor = max(retrograde_factor, 1.2)  # Modest bonus

        # Factor 5: Connection type weight
        # When connection_type is NONE (not a connection-based evaluation),
        # do not penalize — default to 1.0.
        if connection_type == ConnectionType.NONE:
            connection_factor = 1.0
        else:
            connection_factor = CONNECTION_STRENGTH.get(connection_type, 1.0)

        # Factor 6: Dusthana placement penalty
        dusthana_penalty = 1.0
        if lagna_num is not None:
            for planet in planets:
                state = state_map.get(planet)
                if state is not None:
                    house = house_from_lagna(lagna_num, rashi_number(state.rashi))
                    if house in DUSTHANA_HOUSES:
                        dusthana_penalty *= 0.5  # Penalty for Dusthana placement

        # Combine all factors (geometric mean for balanced weighting)
        combined = (
            shadbala_factor
            * dignity_factor
            * combustion_penalty
            * retrograde_factor
            * connection_factor
            * dusthana_penalty
        )

        return max(0.0, min(1.0, combined))

    def _get_dignity(self, state: PlanetState) -> str:
        """Determine classical dignity of a planet (simplified Parashari).

        Returns one of: EXALTED, DEBILITATED, OWN, FRIEND, NEUTRAL, ENEMY.
        """
        # Classical exaltation/debilitation signs
        _EXALTATION: dict[BodyId, int] = {
            BodyId.SUN: 1,       # Aries
            BodyId.MOON: 2,      # Taurus
            BodyId.MARS: 10,     # Capricorn
            BodyId.MERCURY: 6,   # Virgo
            BodyId.JUPITER: 4,   # Cancer
            BodyId.VENUS: 12,    # Pisces
            BodyId.SATURN: 7,    # Libra
        }
        _DEBILITATION: dict[BodyId, int] = {
            BodyId.SUN: 7,       # Libra
            BodyId.MOON: 8,      # Scorpio
            BodyId.MARS: 4,      # Cancer
            BodyId.MERCURY: 12,  # Pisces
            BodyId.JUPITER: 10,  # Capricorn
            BodyId.VENUS: 6,     # Virgo
            BodyId.SATURN: 1,    # Aries
        }
        _OWN_SIGNS: dict[BodyId, tuple[int, ...]] = {
            BodyId.SUN: (5,),
            BodyId.MOON: (4,),
            BodyId.MARS: (1, 8),
            BodyId.MERCURY: (3, 6),
            BodyId.JUPITER: (9, 12),
            BodyId.VENUS: (2, 7),
            BodyId.SATURN: (10, 11),
        }

        body = state.body
        sign_num = rashi_number(state.rashi)

        if body in _EXALTATION and sign_num == _EXALTATION[body]:
            return "EXALTED"
        if body in _DEBILITATION and sign_num == _DEBILITATION[body]:
            return "DEBILITATED"
        if body in _OWN_SIGNS and sign_num in _OWN_SIGNS[body]:
            return "OWN"
        # Simplified: treat remaining as NEUTRAL
        # (full implementation would check friendship tables)
        return "NEUTRAL"

    def _is_combust(self, state: PlanetState, sun_state: PlanetState) -> bool:
        """Check if a planet is combust (too close to Sun).

        Classical combustion thresholds (BPHS Ch.7):
        - Most planets: within ~8-17 degrees of Sun
        - Venus: within ~10 degrees
        - Jupiter: within ~11 degrees
        - Mars: within ~17 degrees
        - Mercury: within ~14 degrees (or less if retrograde)
        """
        _COMBUST_DEGREES: dict[BodyId, float] = {
            BodyId.MERCURY: 14.0,
            BodyId.VENUS: 10.0,
            BodyId.MARS: 17.0,
            BodyId.JUPITER: 11.0,
            BodyId.SATURN: 15.0,
        }
        threshold = _COMBUST_DEGREES.get(state.body)
        if threshold is None:
            return False
        # Calculate angular separation using full longitude
        sep = abs(state.longitude_used - sun_state.longitude_used)
        if sep > 180:
            sep = 360 - sep
        return sep <= threshold

    def _classify_parivartana(
        self,
        planet_a: BodyId,
        planet_b: BodyId,
        lagna_num: int | None,
    ) -> ParivartanaType:
        """Classify the type of Parivartana (exchange) between two planets.

        Maha: Kendra lord ↔ Trikona lord exchange
        Kahala: Exchange between auspicious houses (2/5/9/11) not involving Dusthana
        Dainya: Exchange involving Dusthana lords (6/8/12)
        """
        if lagna_num is None:
            return ParivartanaType.NONE

        # Determine which houses the planets' signs correspond to
        # (This is a simplification — full implementation would trace sign ownership)
        # For now, check if either planet is a Kendra/Trikona/Dusthana lord
        kendra_lords: set[BodyId] = set()
        trikona_lords: set[BodyId] = set()
        dusthana_lords: set[BodyId] = set()

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
        for house in DUSTHANA_HOUSES:
            sign_num = (lagna_num - 1 + house - 1) % 12 + 1
            lord = SIGN_LORDS.get(sign_num)
            if lord is not None:
                dusthana_lords.add(lord)

        a_is_kendra = planet_a in kendra_lords
        b_is_kendra = planet_b in kendra_lords
        a_is_trikona = planet_a in trikona_lords
        b_is_trikona = planet_b in trikona_lords
        a_is_dusthana = planet_a in dusthana_lords
        b_is_dusthana = planet_b in dusthana_lords

        # Dainya: either planet is EXCLUSIVELY a Dusthana lord
        # (i.e., only rules Dusthana houses, not also Kendra/Trikona)
        a_only_dusthana = a_is_dusthana and not a_is_kendra and not a_is_trikona
        b_only_dusthana = b_is_dusthana and not b_is_kendra and not b_is_trikona
        if a_only_dusthana or b_only_dusthana:
            return ParivartanaType.DAINYA

        # Maha: Kendra lord ↔ Trikona lord
        if (a_is_kendra and b_is_trikona) or (a_is_trikona and b_is_kendra):
            return ParivartanaType.MAHA

        # Kahala: both involved in functional-positive houses
        return ParivartanaType.KAHALA

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

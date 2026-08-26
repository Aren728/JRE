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

    def evaluate_classical_yogas(
        self,
        jre_facts: dict[str, Any],
        transit_planet: str = "",
    ) -> list[YogaEvaluation]:
        """Evaluate classical yoga formations from JRE facts.

        Checks for:
        - Gajakesari Yoga: Jupiter in kendra from Moon.
        - Raja Yoga: Kendra lord conjunct or mutually aspecting Trikona lord.

        Args:
            jre_facts: Dictionary containing planet data from JRE.
            transit_planet: Optional planet currently transiting. If provided,
                checks for conjunction or aspect with yoga-forming planets
                to mark the yoga as manifesting.

        Returns:
            List of YogaEvaluation for each detected classical yoga.
        """
        results: list[YogaEvaluation] = []
        # Track which planets are involved in each yoga for transit checks
        yoga_involved_planets: list[list[str]] = []
        planets = jre_facts.get("planets", {})

        # ── Gajakesari Yoga ──
        jup_house = planets.get("JUPITER", {}).get("house")
        moon_house = planets.get("MOON", {}).get("house")
        if isinstance(jup_house, int) and isinstance(moon_house, int):
            # Jupiter in kendra from Moon: house distance mod 12 in {0, 3, 6, 9}
            diff = (jup_house - moon_house) % 12
            if diff in {0, 3, 6, 9}:
                # Run formation affliction checks
                eval_ = self.evaluate_formation(
                    yoga_name="Gajakesari",
                    involved_planets=["JUPITER", "MOON"],
                    jre_facts=jre_facts,
                )
                if eval_.status == YogaStatus.FORMED:
                    results.append(eval_)
                    yoga_involved_planets.append(["JUPITER", "MOON"])

        # ── Raja Yoga ──
        kendra_houses = {1, 4, 7, 10}
        trikona_houses = {1, 5, 9}

        # Build lists of kendra-lord and trikona-lord planets with their houses
        kendra_lords: list[tuple[str, int]] = []
        trikona_lords: list[tuple[str, int]] = []
        for pname, pdata in planets.items():
            house = pdata.get("house")
            if not isinstance(house, int):
                continue
            # Check if this planet is a house lord by looking at house_lord_of
            lord_of = pdata.get("house_lord_of")
            if lord_of is not None:
                if isinstance(lord_of, int) and lord_of in kendra_houses:
                    kendra_lords.append((pname, house))
                if isinstance(lord_of, int) and lord_of in trikona_houses:
                    trikona_lords.append((pname, house))

        # Also check using planet ownership mapping from jre_facts
        house_lords = jre_facts.get("house_lords", {})
        for house_num, lord_planet in house_lords.items():
            if not isinstance(house_num, int) or not isinstance(lord_planet, str):
                continue
            pdata = planets.get(lord_planet, {})
            house = pdata.get("house")
            if not isinstance(house, int):
                continue
            if house_num in kendra_houses:
                kendra_lords.append((lord_planet, house))
            if house_num in trikona_houses:
                trikona_lords.append((lord_planet, house))

        # De-duplicate: keep unique (planet, house) pairs
        seen_kendra: dict[str, int] = {}
        for pname, phouse in kendra_lords:
            if pname not in seen_kendra:
                seen_kendra[pname] = phouse
        seen_trikona: dict[str, int] = {}
        for pname, phouse in trikona_lords:
            if pname not in seen_trikona:
                seen_trikona[pname] = phouse

        # Check conjunction (same house) or mutual aspect (7 houses apart)
        for k_name, k_house in seen_kendra.items():
            for t_name, t_house in seen_trikona.items():
                if k_name == t_name:
                    continue
                diff = abs(k_house - t_house)
                is_conjunction = (k_house == t_house)
                is_mutual_aspect = (diff == 7)
                if is_conjunction or is_mutual_aspect:
                    involved = [k_name, t_name]
                    eval_ = self.evaluate_formation(
                        yoga_name="Raja",
                        involved_planets=involved,
                        jre_facts=jre_facts,
                    )
                    if eval_.status == YogaStatus.FORMED:
                        results.append(eval_)
                        yoga_involved_planets.append([k_name, t_name])
                    # Only first valid Raja yoga to avoid duplicates
                    break
            else:
                continue
            break

        # ── Vipareeta Raja Yoga ──
        dusthana_set = {6, 8, 12}
        house_lords = jre_facts.get("house_lords", {})
        for dusthana_house in dusthana_set:
            lord_planet = house_lords.get(dusthana_house)
            if not isinstance(lord_planet, str):
                continue
            lord_pdata = planets.get(lord_planet, {})
            lord_house = lord_pdata.get("house")
            if isinstance(lord_house, int) and lord_house in dusthana_set:
                results.append(
                    YogaEvaluation(
                        yoga_name="Vipareeta Raja",
                        status=YogaStatus.FORMED,
                    )
                )
                yoga_involved_planets.append([lord_planet])
                break

        # ── Dhana Yoga ──
        second_lord_planet = house_lords.get(2)
        eleventh_lord_planet = house_lords.get(11)
        if isinstance(second_lord_planet, str) and isinstance(eleventh_lord_planet, str):
            second_lord_house = planets.get(second_lord_planet, {}).get("house")
            eleventh_lord_house = planets.get(eleventh_lord_planet, {}).get("house")
            if isinstance(second_lord_house, int) and isinstance(eleventh_lord_house, int):
                is_conjunction = second_lord_house == eleventh_lord_house
                is_mutual_aspect = abs(second_lord_house - eleventh_lord_house) == 7
                if is_conjunction or is_mutual_aspect:
                    results.append(
                        YogaEvaluation(
                            yoga_name="Dhana",
                            status=YogaStatus.FORMED,
                        )
                    )
                    yoga_involved_planets.append(
                        [second_lord_planet, eleventh_lord_planet]
                    )

        # ── Neecha Bhanga Yoga ──
        # Debilitation sign → sign lord mapping
        debilitation_sign_lord: dict[str, str] = {
            "SUN": "VENUS",       # Sun debilitated in Libra (lord Venus)
            "MOON": "MARS",        # Moon debilitated in Scorpio (lord Mars)
            "MARS": "MOON",        # Mars debilitated in Cancer (lord Moon)
            "MERCURY": "JUPITER",  # Mercury debilitated in Pisces (lord Jupiter)
            "JUPITER": "SATURN",   # Jupiter debilitated in Capricorn (lord Saturn)
            "VENUS": "MERCURY",    # Venus debilitated in Virgo (lord Mercury)
            "SATURN": "MARS",      # Saturn debilitated in Aries (lord Mars)
        }

        lagna_house = jre_facts.get("lagna_house")
        if isinstance(lagna_house, int):
            for pname, pdata in planets.items():
                if not pdata.get("debilitated", False):
                    continue
                sign_lord = debilitation_sign_lord.get(pname)
                if sign_lord is None:
                    continue
                lord_pdata = planets.get(sign_lord, {})
                lord_house = lord_pdata.get("house")
                if isinstance(lord_house, int) and lord_house in kendra_houses:
                    results.append(
                        YogaEvaluation(
                            yoga_name="Neecha Bhanga",
                            status=YogaStatus.FORMED,
                        )
                    )
                    yoga_involved_planets.append([pname, sign_lord])
                    break

        # ── Transit activation check ──
        if transit_planet:
            tp_house = planets.get(transit_planet, {}).get("house")
            if isinstance(tp_house, int):
                for idx, involved in enumerate(yoga_involved_planets):
                    for planet_name in involved:
                        p_house = planets.get(planet_name, {}).get("house")
                        if not isinstance(p_house, int):
                            continue
                        diff = abs(tp_house - p_house)
                        if diff == 0 or diff == 7:
                            results[idx] = replace(
                                results[idx],
                                is_manifesting=True,
                                activation_source=f"Transit: {transit_planet}",
                            )
                            break

        return results

"""JRS-075/076/077 Yoga Formation, Cancellation, Manifestation & Outcome Evaluator service."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .modifier_service import ModifierEvaluationService, ModifierReport, ModifierStatus
from .models import YogaEvaluation, YogaOutcome, YogaStatus

# Dusthana houses — placements that weaken a yoga
DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})


class YogaEvaluatorService:
    """Deterministic service for evaluating yoga formation and cancellation."""

    def __init__(self) -> None:
        """Initialize with ModifierEvaluationService for Phase 1 pipeline."""
        self._modifier_svc = ModifierEvaluationService()

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
        # ── Phase 1: Run 5-tier modifier pipeline ──
        # All formation checks (combustion, debilitation, dusthana, etc.)
        # are now handled by ModifierEvaluationService per RI-010G.
        modifier_report = self._modifier_svc.evaluate_modifiers(
            involved_planets, jre_facts
        )

        # If modifier pipeline cancels or weakens, override formation status
        if modifier_report.overall_status == ModifierStatus.CANCELLED:
            return YogaEvaluation(
                yoga_name=yoga_name,
                status=YogaStatus.CANCELLED,
                cancellation_reason=modifier_report.cancellation_reason,
                modifier_report=modifier_report,
            )
        if modifier_report.overall_status == ModifierStatus.WEAKENED:
            return YogaEvaluation(
                yoga_name=yoga_name,
                status=YogaStatus.WEAKENED,
                cancellation_reason=modifier_report.cancellation_reason,
                modifier_report=modifier_report,
            )

        return YogaEvaluation(
            yoga_name=yoga_name,
            status=YogaStatus.FORMED,
            modifier_report=modifier_report,
        )

    def evaluate_manifestation(
        self,
        yoga_name_or_evaluation: str | YogaEvaluation | None = None,
        involved_planets_or_yoga_planets: list[str] | None = None,
        dasha_lord_or_active: str | None = None,
        transit_planet: str | None = None,
        *,
        evaluation: YogaEvaluation | None = None,
        yoga_planets: list[str] | None = None,
        active_dasha_lord: str | None = None,
    ) -> bool | YogaEvaluation:
        """Evaluate manifestation of a yoga.

        Supports two call signatures:

        New (JRS-076)::
            evaluate_manifestation(yoga_name, involved_planets, dasha_lord) -> bool

        Legacy (JRS-075)::
            evaluate_manifestation(evaluation=..., yoga_planets=...,
                                  active_dasha_lord=..., transit_planet=...) -> YogaEvaluation
        """
        # ── New signature: (yoga_name, involved_planets, dasha_lord) -> bool ──
        if (
            isinstance(yoga_name_or_evaluation, str)
            and involved_planets_or_yoga_planets is not None
            and isinstance(dasha_lord_or_active, str)
            and evaluation is None
        ):
            return dasha_lord_or_active in involved_planets_or_yoga_planets

        # ── Legacy signature ──
        eval_obj = evaluation if evaluation is not None else yoga_name_or_evaluation
        planets = yoga_planets if yoga_planets is not None else (involved_planets_or_yoga_planets or [])
        active = active_dasha_lord if active_dasha_lord is not None else (dasha_lord_or_active or "")

        if not isinstance(eval_obj, YogaEvaluation):
            raise TypeError("evaluate_manifestation requires a YogaEvaluation for the legacy signature")

        if active in planets:
            return replace(
                eval_obj,
                is_manifesting=True,
                activation_source=f"Dasha: {active}",
            )

        if transit_planet and transit_planet in planets:
            return replace(
                eval_obj,
                is_manifesting=True,
                activation_source=f"Transit: {transit_planet}",
            )

        return eval_obj

    def map_outcome(
        self,
        yoga_name: str,
        involved_houses: list[int] | None = None,
        involved_planets: list[str] | None = None,
    ) -> str | YogaOutcome:
        """Map a yoga to its likely outcome category.

        Supports two call signatures:

        New (JRS-076)::
            map_outcome(yoga_name: str) -> YogaOutcome

        Legacy (JRS-077)::
            map_outcome(yoga_name, involved_houses, involved_planets) -> str
        """
        # ── New signature: single yoga_name string -> YogaOutcome ──
        if involved_houses is None and involved_planets is None:
            _YOGA_OUTCOME_MAP: dict[str, YogaOutcome] = {
                "RAJA": YogaOutcome.CAREER_PROMINENCE,
                "RAJA YOGA": YogaOutcome.CAREER_PROMINENCE,
                "DHANA": YogaOutcome.WEALTH_ACCUMULATION,
                "DHANA YOGA": YogaOutcome.WEALTH_ACCUMULATION,
                "GAJAKESARI": YogaOutcome.GENERAL_IMPROVEMENT,
                "VIPAREETA RAJA": YogaOutcome.CAREER_PROMINENCE,
                "VIPAREETA RAJA YOGA": YogaOutcome.CAREER_PROMINENCE,
                "NEECHA BHANGA": YogaOutcome.GENERAL_IMPROVEMENT,
                # Pancha Mahapurusha Yogas
                "RUCHAKA": YogaOutcome.CAREER_PROMINENCE,
                "BHADRA": YogaOutcome.CAREER_PROMINENCE,
                "HAMSA": YogaOutcome.CAREER_PROMINENCE,
                "MALAVYA": YogaOutcome.RELATIONSHIP_HARMONY,
                "SASA": YogaOutcome.CAREER_PROMINENCE,
                # Chandra Yogas
                "ANAPHA": YogaOutcome.WEALTH_ACCUMULATION,
                "SUNAPHA": YogaOutcome.WEALTH_ACCUMULATION,
                "DHUDHARA": YogaOutcome.WEALTH_ACCUMULATION,
            }
            key = yoga_name.upper().replace("_", " ")
            return _YOGA_OUTCOME_MAP.get(key, YogaOutcome.GENERAL_IMPROVEMENT)

        # ── Legacy signature ──
        houses = involved_houses or []
        planets = involved_planets or []
        if 10 in houses or "SUN" in planets:
            return "CAREER_PROMINENCE"
        if 2 in houses or 11 in houses or "JUPITER" in planets or "VENUS" in planets:
            return "WEALTH_ACCUMULATION"
        if 4 in houses or "MOON" in planets:
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
                # Append if FORMED or WEAKENED (not CANCELLED)
                if eval_.status in (YogaStatus.FORMED, YogaStatus.WEAKENED):
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
                    # Append if FORMED or WEAKENED (not CANCELLED)
                    if eval_.status in (YogaStatus.FORMED, YogaStatus.WEAKENED):
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

        # ── Pancha Mahapurusha Yogas ──
        # Planet in Kendra (1,4,7,10) in own or exaltation sign, non-combust/non-debilitated
        _MAHAPURUSHA_MAP: dict[str, str] = {
            "MARS": "Ruchaka",
            "MERCURY": "Bhadra",
            "JUPITER": "Hamsa",
            "VENUS": "Malavya",
            "SATURN": "Sasa",
        }
        _EXALTATION_SIGNS: dict[str, str] = {
            "SUN": "MESHA",       # Aries
            "MOON": "VRISHABHA",   # Taurus
            "MARS": "MAKARA",      # Capricorn
            "MERCURY": "KANYA",    # Virgo
            "JUPITER": "KARKA",    # Cancer
            "VENUS": "MEENA",      # Pisces
            "SATURN": "TULA",      # Libra
        }
        _OWN_SIGNS: dict[str, str] = {
            "SUN": "SIMHA",        # Leo
            "MOON": "KARKA",       # Cancer
            "MARS": "VRISHCHIKA",  # Scorpio
            "MERCURY": "KANYA",    # Virgo (also Mithuna)
            "JUPITER": "DHANUSHA", # Sagittarius (also Meena)
            "VENUS": "TULA",       # Libra (also Vrishabha)
            "SATURN": "KUMBHA",    # Aquarius (also Makara)
        }

        for pname, yoga_name in _MAHAPURUSHA_MAP.items():
            pdata = planets.get(pname, {})
            house = pdata.get("house")
            if not isinstance(house, int) or house not in kendra_houses:
                continue
            rashi = pdata.get("rashi", "")
            is_own = rashi == _OWN_SIGNS.get(pname, "")
            is_exalted = rashi == _EXALTATION_SIGNS.get(pname, "")
            if not (is_own or is_exalted):
                continue
            # Let modifier pipeline handle combustion/debilitation → may return CANCELLED
            eval_ = self.evaluate_formation(
                yoga_name=yoga_name,
                involved_planets=[pname],
                jre_facts=jre_facts,
            )
            # Include all statuses for complete tracking (FORMED, WEAKENED, CANCELLED)
            results.append(eval_)
            yoga_involved_planets.append([pname])

        # ── Chandra Yogas (Anapha, Sunapha, Dhudhara) ──
        if isinstance(moon_house, int):
            planet_2nd_from_moon = []  # Planets 2nd from Moon (not Sun)
            planet_12th_from_moon = []  # Planets 12th from Moon (not Sun)
            for pname, pdata in planets.items():
                if pname == "MOON" or pname == "SUN":
                    continue
                ph = pdata.get("house")
                if not isinstance(ph, int):
                    continue
                if (ph - moon_house) % 12 == 1:  # 2nd from Moon
                    planet_2nd_from_moon.append(pname)
                elif (moon_house - ph) % 12 == 1:  # 12th from Moon
                    planet_12th_from_moon.append(pname)

            if planet_12th_from_moon:
                # Sunapha: planet 12th from Moon
                for pname in planet_12th_from_moon:
                    eval_ = self.evaluate_formation(
                        yoga_name="Sunapha",
                        involved_planets=["MOON", pname],
                        jre_facts=jre_facts,
                    )
                    # Include all statuses for complete tracking
                    if eval_.status != YogaStatus.CANCELLED:
                        results.append(eval_)
                        yoga_involved_planets.append(["MOON", pname])

            if planet_2nd_from_moon:
                # Anapha: planet 2nd from Moon
                for pname in planet_2nd_from_moon:
                    eval_ = self.evaluate_formation(
                        yoga_name="Anapha",
                        involved_planets=["MOON", pname],
                        jre_facts=jre_facts,
                    )
                    if eval_.status != YogaStatus.CANCELLED:
                        results.append(eval_)
                        yoga_involved_planets.append(["MOON", pname])

            if planet_2nd_from_moon and planet_12th_from_moon:
                # Dhudhara: planets on both sides of Moon
                all_names = ["MOON"] + planet_2nd_from_moon + planet_12th_from_moon
                eval_ = self.evaluate_formation(
                    yoga_name="Dhudhara",
                    involved_planets=all_names,
                    jre_facts=jre_facts,
                )
                if eval_.status != YogaStatus.CANCELLED:
                    results.append(eval_)
                    yoga_involved_planets.append(all_names)

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

        # ── Phase 1: Apply 5-tier modifier pipeline to all FORMED yogas ──
        # Skip Vipareeta Raja: dusthana placement is required, not a weakness
        for idx, (eval_, involved) in enumerate(
            zip(results, yoga_involved_planets)
        ):
            if eval_.status != YogaStatus.FORMED:
                continue
            if eval_.yoga_name == "Vipareeta Raja":
                # Vipareeta Raja yoga requires dusthana lordship — skip modifier
                continue
            modifier_report = self._modifier_svc.evaluate_modifiers(
                involved, jre_facts
            )
            if modifier_report.overall_status == ModifierStatus.CANCELLED:
                results[idx] = replace(
                    eval_,
                    status=YogaStatus.CANCELLED,
                    cancellation_reason=modifier_report.cancellation_reason,
                    modifier_report=modifier_report,
                )
            elif modifier_report.overall_status == ModifierStatus.WEAKENED:
                results[idx] = replace(
                    eval_,
                    status=YogaStatus.WEAKENED,
                    cancellation_reason=modifier_report.cancellation_reason,
                    modifier_report=modifier_report,
                )
            else:
                results[idx] = replace(
                    eval_,
                    modifier_report=modifier_report,
                )

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

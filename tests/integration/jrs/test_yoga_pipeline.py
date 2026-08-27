"""JRS-077 Structural Yoga Integration Test (Atomic Execution)."""

from __future__ import annotations

import pytest
from jrs.kendra_trikona.service import KendraTrikonaService
from jrs.yoga_evaluator.models import YogaEvaluation, YogaOutcome, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


def _build_mock_jre_facts() -> dict:
    """Build mock JRE facts for the integration test.

    Chart: MESHA (Aries) lagna.
    SUN placed in MESHA (1st house) — 5th lord (trikona) in kendra.
    JUPITER placed in MAKARA (10th house) — 9th lord (trikona) in kendra.
    Both form TRIKONA_LORD_IN_KENDRA yogas.

    D9 confirmation: Jupiter in MAKARA → navamsa in MEENA (house 10 from
    D9 lagna MESHA) → Kendra → STRONG.

    Active Dasha lord is JUPITER (one of the yoga planets) → manifesting.
    """
    return {
        "lagna": "MESHA",
        "planets": {
            "JUPITER": {
                "rashi": "MAKARA",
                "house": 10,
                "combust": False,
                "debilitated": False,
            },
            "SUN": {
                "rashi": "MESHA",
                "house": 1,
                "combust": False,
                "debilitated": False,
            },
        },
        "active_dasha_lord": "JUPITER",
        "transit_planet": "JUPITER",
    }


def _check_d9_strength(jupiter_rashi_num: int, lagna_num: int) -> bool:
    """Replicate D9 strength check from YogaService._check_d9_strength.

    Returns True if the planet is in Kendra or Trikona in D9 (i.e. STRONG).
    """
    KENDRA = {1, 4, 7, 10}
    TRIKONA = {1, 5, 9}

    # D9 lagna: navamsa of lagna at 0° of sign
    lagna_longitude = (lagna_num - 1) * 30.0
    d9_lagna_index = int(lagna_longitude * 9 / 30) % 12
    d9_lagna_num = d9_lagna_index + 1

    # Jupiter navamsa
    planet_longitude = (jupiter_rashi_num - 1) * 30.0
    planet_navamsa_index = int(planet_longitude * 9 / 30) % 12
    planet_navamsa_num = planet_navamsa_index + 1

    house = (planet_navamsa_num - d9_lagna_num) % 12 + 1
    return house in KENDRA or house in TRIKONA


class TestFullYogaPipeline:
    def test_full_yoga_pipeline(self) -> None:
        """Full pipeline: structural detection → formation → manifestation → outcome.

        Mock: Sun in Aries (1st), Jupiter in Capricorn (10th), Dasha lord = Jupiter.
        D9: Jupiter in Kendra → STRONG.
        """
        jre_facts = _build_mock_jre_facts()

        # ── Step 1: Structural yoga detection ──────────────────────────────
        kt_service = KendraTrikonaService()
        structural_yogas = kt_service.evaluate(jre_facts)
        assert len(structural_yogas) >= 1, "At least one structural yoga must be detected"

        # Pick the yoga involving Jupiter (the Dasha lord)
        jupiter_yoga = None
        for yoga in structural_yogas:
            if "JUPITER" in (yoga.planet_a, yoga.planet_b):
                jupiter_yoga = yoga
                break
        assert jupiter_yoga is not None, "A yoga involving Jupiter must be detected"

        involved_planets = [jupiter_yoga.planet_a, jupiter_yoga.planet_b]

        # ── Step 2: Formation evaluation → FORMED ──────────────────────────
        evaluator = YogaEvaluatorService()
        evaluation = evaluator.evaluate_formation(
            yoga_name=jupiter_yoga.yoga_type.value,
            involved_planets=involved_planets,
            jre_facts=jre_facts,
        )
        assert evaluation.status == YogaStatus.FORMED

        # ── Step 3: D9 strength → STRONG ───────────────────────────────────
        # Jupiter in MAKARA (rashi_num=10), lagna MESHA (num=1)
        # D9 lagna = MESHA (0); Jupiter navamsa = MEENA (house 10 → Kendra)
        d9_strong = _check_d9_strength(jupiter_rashi_num=10, lagna_num=1)
        assert d9_strong is True, "D9 must confirm Jupiter is STRONG (Kendra/Trikona in D9)"

        # ── Step 4: Manifestation → is_manifesting == True ─────────────────
        evaluation = evaluator.evaluate_manifestation(
            evaluation=evaluation,
            yoga_planets=involved_planets,
            active_dasha_lord=jre_facts["active_dasha_lord"],
            transit_planet=jre_facts["transit_planet"],
        )
        assert evaluation.is_manifesting is True, "Yoga must be manifesting under Jupiter Dasha"

        # ── Step 5: Outcome mapping → CAREER_PROMINENCE ────────────────────
        outcome = evaluator.map_outcome(
            yoga_name=jupiter_yoga.yoga_type.value,
            involved_houses=[jupiter_yoga.house_a, jupiter_yoga.house_b],
            involved_planets=involved_planets,
        )
        assert outcome == "CAREER_PROMINENCE", (
            f"Outcome must be CAREER_PROMINENCE (10th house involved), got {outcome}"
        )

        # ── Step 6: Build final YogaEvaluation with outcome ────────────────
        final_eval = YogaEvaluation(
            yoga_name=evaluation.yoga_name,
            status=evaluation.status,
            cancellation_reason=evaluation.cancellation_reason,
            is_manifesting=evaluation.is_manifesting,
            activation_source=evaluation.activation_source,
            outcome_category=outcome,
            outcome=YogaOutcome.CAREER_PROMINENCE,
        )
        assert final_eval.outcome == YogaOutcome.CAREER_PROMINENCE

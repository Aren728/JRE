"""JRS Health Yoga Rules unit tests — Proposal PROP-2026-001, Section 4.1.

Tests 5 classical Arishta/Health yogas based on:
  - Brihat Parashara Hora Shastra, Chapter 32 (Arishta/Maraka rules)
  - Phaladeepika, Chapter 8 (chronic vs. acute health vulnerabilities)

Yogas tested:
  1. Arishta Dosha   — 6th lord + 8th lord in dusthana → chronic disease
  2. Maraka Dosha    — 2nd lord + 7th lord affliction → death-threatening
  3. Lagna Ashubha   — Multiple malefics in dusthana → health vulnerability
  4. Graha Kutumba   — 3+ planets in dusthana → severe health burden
  5. Dasha Lagna Arishta — Lagna lord in dusthana + malefic → health timing

All tests follow the same pattern as test_classical_yogas.py:
  - Construct minimal jre_facts dicts
  - Call service.evaluate_classical_yogas(facts)
  - Assert presence/absence and status of health yogas

Note: The 5-tier modifier pipeline weakens planets in dusthana houses, so
positive tests accept both FORMED and WEAKENED statuses.
"""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.models import YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


# Acceptable statuses for a detected yoga (FORMED if no weakening, WEAKENED
# if modifier pipeline downgrades due to dusthana placement, etc.)
_YOGA_DETECTED = (YogaStatus.FORMED, YogaStatus.WEAKENED)


# ──────────────────────────────────────────────────────────────────────────────
# Yoga 1: Arishta Dosha (BPHS Ch 32 — chronic disease indicators)
#
# Classical rule: When the 6th lord and 8th lord are both placed in dusthana
# houses (6, 8, 12) — or conjunct in any dusthana — it indicates chronic or
# long-standing disease. (Phaladeepika Ch 8 V.3)
# ──────────────────────────────────────────────────────────────────────────────


class TestArishtaDosha:
    """Arishta Dosha: 6th lord + 8th lord in dusthana → chronic disease."""

    def test_arishta_dosha_both_lords_in_dusthana(self) -> None:
        """T01: 6th lord (Sun) in H6, 8th lord (Venus) in H8 → detected."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 6, "rashi": "SIMHA", "combust": False,
                        "debilitated": False},
                "VENUS": {"house": 8, "rashi": "TULA", "combust": False,
                          "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Arishta Dosha" in names
        arishta = next(r for r in results if r.yoga_name == "Arishta Dosha")
        assert arishta.status in _YOGA_DETECTED

    def test_arishta_dosha_not_formed_lords_in_kendra(self) -> None:
        """T02: 6th lord in H4, 8th lord in H10 (both Kendra) → NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 4, "rashi": "MITHUNA", "combust": False,
                        "debilitated": False},
                "VENUS": {"house": 10, "rashi": "TULA", "combust": False,
                          "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Arishta Dosha" not in names

    def test_arishta_dosha_cancelled_by_debilitation(self) -> None:
        """T03: 6th lord in dusthana but debilitated → CANCELLED by modifier."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                # Sun debilitated in Libra (Tula) — rashi_num=7
                "SUN": {"house": 6, "rashi": "TULA", "rashi_num": 7,
                        "combust": False, "debilitated": True},
                "VENUS": {"house": 8, "rashi": "TULA", "combust": False,
                          "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        # Arishta Dosha should be CANCELLED, not FORMED
        if "Arishta Dosha" in names:
            arishta = next(r for r in results if r.yoga_name == "Arishta Dosha")
            assert arishta.status == YogaStatus.CANCELLED
        else:
            # Alternatively: yoga not detected at all due to cancellation
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Yoga 2: Maraka Dosha (BPHS Ch 32 — death-inflicting periods)
#
# Classical rule: When the 2nd lord and 7th lord are in dusthana, conjunct,
# or mutually aspect each other — especially in 6/8/12 — it indicates
# Maraka (death-inflicting) potential. (BPHS Ch 32 V.12-15)
# ──────────────────────────────────────────────────────────────────────────────


class TestMarakaDosha:
    """Maraka Dosha: 2nd lord + 7th lord affliction → death-threatening."""

    def test_maraka_dosha_both_in_dusthana(self) -> None:
        """T04: 2nd lord (Mars) in H6, 7th lord (Mercury) in H8 → detected."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "MARS": {"house": 6, "rashi": "SIMHA", "combust": False,
                         "debilitated": False},
                "MERCURY": {"house": 8, "rashi": "TULA", "combust": False,
                            "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Maraka Dosha" in names
        maraka = next(r for r in results if r.yoga_name == "Maraka Dosha")
        assert maraka.status in _YOGA_DETECTED

    def test_maraka_dosha_not_formed_in_kendra(self) -> None:
        """T05: 2nd lord in H1, 7th lord in H4 (both Kendra) → NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "MARS": {"house": 1, "rashi": "MEENA", "combust": False,
                         "debilitated": False},
                "MERCURY": {"house": 4, "rashi": "MITHUNA", "combust": False,
                            "debilitated": False},
                "JUPITER": {"house": 5, "rashi": "KARKA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Maraka Dosha" not in names

    def test_maraka_dosha_conjunction_in_dusthana(self) -> None:
        """T06: 2nd lord + 7th lord conjunct in H12 → detected."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                # Both 2nd and 7th lord Mercury in H12 (dusthana)
                "MERCURY": {"house": 12, "rashi": "KUMBHA", "combust": False,
                            "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MERCURY", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Maraka Dosha" in names
        maraka = next(r for r in results if r.yoga_name == "Maraka Dosha")
        assert maraka.status in _YOGA_DETECTED


# ──────────────────────────────────────────────────────────────────────────────
# Yoga 3: Lagna Ashubha (BPHS Ch 32 — health vulnerability)
#
# Classical rule: When 2 or more natural malefics (Saturn, Mars, Rahu) occupy
# dusthana houses (6, 8, 12) from Lagna, it indicates inherent health
# vulnerability. (Phaladeepika Ch 8 V.1)
# ──────────────────────────────────────────────────────────────────────────────


class TestLagnaAshubha:
    """Lagna Ashubha: Multiple malefics in dusthana → health vulnerability."""

    def test_lagna_ashubha_two_malefics_in_dusthana(self) -> None:
        """T07: Saturn in H6, Mars in H8 (2 malefics in dusthana) → detected."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SATURN": {"house": 6, "rashi": "SIMHA", "combust": False,
                           "debilitated": False},
                "MARS": {"house": 8, "rashi": "TULA", "combust": False,
                         "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
                "VENUS": {"house": 4, "rashi": "MITHUNA", "combust": False,
                          "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Lagna Ashubha" in names
        ashubha = next(r for r in results if r.yoga_name == "Lagna Ashubha")
        assert ashubha.status in _YOGA_DETECTED

    def test_lagna_ashubha_not_formed_malefics_in_kendra(self) -> None:
        """T08: Malefics in H1 and H7 (Kendra, not dusthana) → NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SATURN": {"house": 1, "rashi": "MEENA", "combust": False,
                           "debilitated": False},
                "MARS": {"house": 7, "rashi": "KANYA", "combust": False,
                         "debilitated": False},
                "JUPITER": {"house": 5, "rashi": "KARKA", "combust": False,
                            "debilitated": False},
                "VENUS": {"house": 4, "rashi": "MITHUNA", "combust": False,
                          "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Lagna Ashubha" not in names

    def test_lagna_ashubha_only_one_malefic(self) -> None:
        """T09: Only Saturn in H8 (1 malefic) → NOT formed (need 2+)."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SATURN": {"house": 8, "rashi": "TULA", "combust": False,
                           "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
                "VENUS": {"house": 4, "rashi": "MITHUNA", "combust": False,
                          "debilitated": False},
                "MERCURY": {"house": 10, "rashi": "DHANUSHA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Lagna Ashubha" not in names


# ──────────────────────────────────────────────────────────────────────────────
# Yoga 4: Graha Kutumba (Phaladeepika Ch 8 — severe health burden)
#
# Classical rule: When 3 or more planets (any graha) occupy dusthana houses
# (6, 8, 12), it creates a severe health burden — "Kutumba" (family) of
# afflictions. (Phaladeepika Ch 8 V.5)
# ──────────────────────────────────────────────────────────────────────────────


class TestGrahaKutumba:
    """Graha Kutumba: 3+ planets in dusthana → severe health burden."""

    def test_graha_kutumba_three_planets_in_dusthana(self) -> None:
        """T10: Sun in H6, Venus in H8, Saturn in H12 → detected."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 6, "rashi": "SIMHA", "combust": False,
                        "debilitated": False},
                "VENUS": {"house": 8, "rashi": "TULA", "combust": False,
                          "debilitated": False},
                "SATURN": {"house": 12, "rashi": "KUMBHA", "combust": False,
                           "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
                "MERCURY": {"house": 4, "rashi": "MITHUNA", "combust": False,
                            "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Graha Kutumba" in names
        kutumba = next(r for r in results if r.yoga_name == "Graha Kutumba")
        assert kutumba.status in _YOGA_DETECTED

    def test_graha_kutumba_not_formed_two_planets(self) -> None:
        """T11: Only 2 planets in dusthana (need 3+) → NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 6, "rashi": "SIMHA", "combust": False,
                        "debilitated": False},
                "VENUS": {"house": 8, "rashi": "TULA", "combust": False,
                          "debilitated": False},
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                            "debilitated": False},
                "MERCURY": {"house": 4, "rashi": "MITHUNA", "combust": False,
                            "debilitated": False},
                "MARS": {"house": 10, "rashi": "DHANUSHA", "combust": False,
                         "debilitated": False},
            },
            "house_lords": {
                1: "JUPITER", 2: "MARS", 3: "VENUS", 4: "MERCURY",
                5: "MOON", 6: "SUN", 7: "MERCURY", 8: "VENUS",
                9: "MARS", 10: "JUPITER", 11: "SATURN", 12: "SATURN",
            },
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Graha Kutumba" not in names


# ──────────────────────────────────────────────────────────────────────────────
# Yoga 5: Dasha Lagna Arishta (BPHS Ch 50 — health event timing)
#
# Classical rule: When the Lagna lord is placed in a dusthana house (6/8/12)
# AND is aspected by or conjunct a malefic, it creates a structural health
# vulnerability activated during relevant Dasha periods. (BPHS Ch 50 V.18-20)
#
# Chart setup: Capricorn Lagna (Saturn = lagna lord in H1/H2).
#   - Saturn in dusthana → Dasha Lagna Arishta condition met.
#   - Malefic conjunct/aspecting → compound affliction.
#
# NOTE: This test validates the natal pattern. Dasha activation timing is
# handled by activation_service.py (TA-001–005).
# ──────────────────────────────────────────────────────────────────────────────

# Capricorn Lagna house lordships (consistent across T12–T15):
#   H1: Saturn (lagna lord), H2: Saturn, H3: Jupiter, H4: Mars,
#   H5: Venus, H6: Mercury, H7: Moon, H8: Sun, H9: Mercury,
#   H10: Venus, H11: Mars, H12: Jupiter
_CAPRICORN_LAGNA_LORDS = {
    1: "SATURN", 2: "SATURN", 3: "JUPITER", 4: "MARS",
    5: "VENUS", 6: "MERCURY", 7: "MOON", 8: "SUN",
    9: "MERCURY", 10: "VENUS", 11: "MARS", 12: "JUPITER",
}


class TestDashaLagnaArishta:
    """Dasha Lagna Arishta: Lagna lord in dusthana + malefic → health timing."""

    def test_dasha_lagna_arishta_lord_in_dusthana_with_malefic(self) -> None:
        """T12: Saturn (lagna lord) in H6 conjunct Mars → detected."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SATURN": {"house": 6, "rashi": "SIMHA", "combust": False,
                           "debilitated": False},
                "MARS": {"house": 6, "rashi": "SIMHA", "combust": False,
                         "debilitated": False},
                "VENUS": {"house": 10, "rashi": "TULA", "combust": False,
                          "debilitated": False},
            },
            "house_lords": _CAPRICORN_LAGNA_LORDS,
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Dasha Lagna Arishta" in names
        dla = next(r for r in results if r.yoga_name == "Dasha Lagna Arishta")
        assert dla.status in _YOGA_DETECTED

    def test_dasha_lagna_arishta_not_formed_lord_not_in_dusthana(self) -> None:
        """T13: Saturn in H4 (not dusthana) → NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SATURN": {"house": 4, "rashi": "MITHUNA", "combust": False,
                           "debilitated": False},
                "MARS": {"house": 10, "rashi": "TULA", "combust": False,
                         "debilitated": False},
                "VENUS": {"house": 5, "rashi": "KARKA", "combust": False,
                          "debilitated": False},
            },
            "house_lords": _CAPRICORN_LAGNA_LORDS,
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Dasha Lagna Arishta" not in names

    def test_dasha_lagna_arishta_lord_in_8th_with_aspect(self) -> None:
        """T14: Saturn in H8, Mars in H2 (Mars aspects H8 via 7th aspect) →
        detected (8th house placement + malefic aspect)."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SATURN": {"house": 8, "rashi": "VRISHCHIKA", "combust": False,
                           "debilitated": False},
                "MARS": {"house": 2, "rashi": "KUMBHA", "combust": False,
                         "debilitated": False},
                "VENUS": {"house": 10, "rashi": "TULA", "combust": False,
                          "debilitated": False},
            },
            "house_lords": _CAPRICORN_LAGNA_LORDS,
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Dasha Lagna Arishta" in names
        dla = next(r for r in results if r.yoga_name == "Dasha Lagna Arishta")
        assert dla.status in _YOGA_DETECTED

    def test_dasha_lagna_arishta_combined_with_arishta_dosha(self) -> None:
        """T15: Arishta Dosha (6L+8L in dusthana) + Dasha Lagna Arishta
        (lagna lord in H12 conjunct Rahu) → both detected, compound risk."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                # 6th lord (Mercury) in H6, 8th lord (Sun) in H6
                "MERCURY": {"house": 6, "rashi": "SIMHA", "combust": False,
                            "debilitated": False},
                "SUN": {"house": 6, "rashi": "SIMHA", "combust": False,
                        "debilitated": False},
                # Lagna lord (Saturn) in H12 conjunct Rahu
                "SATURN": {"house": 12, "rashi": "MEENA", "combust": False,
                           "debilitated": False},
                "RAHU": {"house": 12, "rashi": "MEENA", "combust": False,
                         "debilitated": False},
            },
            "house_lords": _CAPRICORN_LAGNA_LORDS,
            "lagna_house": 1,
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        # Both health yogas should be detected
        assert "Arishta Dosha" in names, (
            f"Expected Arishta Dosha in {names}"
        )
        assert "Dasha Lagna Arishta" in names, (
            f"Expected Dasha Lagna Arishta in {names}"
        )
        # Both should be detected (FORMED or WEAKENED, not CANCELLED)
        arishta = next(r for r in results if r.yoga_name == "Arishta Dosha")
        dla = next(r for r in results if r.yoga_name == "Dasha Lagna Arishta")
        assert arishta.status in _YOGA_DETECTED
        assert dla.status in _YOGA_DETECTED

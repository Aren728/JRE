"""JRS-087 Classical Yoga Rules unit tests."""

from __future__ import annotations

from jrs.yoga_evaluator.models import YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestClassicalYogas:
    """Tests for classical yoga rule evaluation."""

    def test_gajakesari_yoga_jupiter_moon_kendra(self) -> None:
        """Test A: Jupiter in 1st, Moon in 4th (kendra) -> Gajakesari FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                "MOON": {"house": 4, "combust": False, "debilitated": False},
            },
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Gajakesari" in names
        gaja = next(r for r in results if r.yoga_name == "Gajakesari")
        assert gaja.status == YogaStatus.FORMED

    def test_raja_yoga_kendra_lord_conjunct_trikona_lord(self) -> None:
        """Test B: 1st lord and 5th lord in conjunction -> Raja Yoga FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "MARS": {"house": 5, "combust": False, "debilitated": False},
                "SUN": {"house": 5, "combust": False, "debilitated": False},
            },
            "house_lords": {
                1: "MARS",   # Kendra lord (1st house)
                5: "SUN",    # Trikona lord (5th house)
            },
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Raja" in names
        raja = next(r for r in results if r.yoga_name == "Raja")
        assert raja.status == YogaStatus.FORMED

    def test_budhaditya_sun_mercury_conjunction(self) -> None:
        """Budhaditya: Sun + Mercury same sign, not combust -> FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 6, "rashi": "MAKARA", "longitude_used": 286.9,
                         "combust": False, "debilitated": False},
                "MERCURY": {"house": 6, "rashi": "MAKARA", "longitude_used": 300.0,
                             "combust": False, "debilitated": False},
            },
            "house_lords": {6: "SATURN"},
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Budhaditya" in names
        budha = next(r for r in results if r.yoga_name == "Budhaditya")
        assert budha.status in (YogaStatus.FORMED, YogaStatus.WEAKENED)

    def test_budhaditya_combust_mercury(self) -> None:
        """Budhaditya: Mercury too close to Sun (< 8 deg) -> NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 6, "rashi": "MAKARA", "longitude_used": 286.9,
                         "combust": False, "debilitated": False},
                "MERCURY": {"house": 6, "rashi": "MAKARA", "longitude_used": 287.6,
                             "combust": True, "debilitated": False},
            },
            "house_lords": {6: "SATURN"},
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Budhaditya" not in names

    def test_budhaditya_different_signs(self) -> None:
        """Budhaditya: Sun and Mercury in different signs -> NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 3, "rashi": "MITHUNA", "longitude_used": 85.9,
                         "combust": False, "debilitated": False},
                "MERCURY": {"house": 3, "rashi": "KARKA", "longitude_used": 100.0,
                             "combust": False, "debilitated": False},
            },
            "house_lords": {3: "SUN", 4: "MOON"},
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Budhaditya" not in names

    def test_saraswati_yoga(self) -> None:
        """Saraswati: Jupiter, Mercury, Venus all in favorable houses, Jupiter strong."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "JUPITER": {"house": 1, "rashi": "MEENA", "combust": False,
                             "debilitated": False, "longitude_used": 350.0},
                "MERCURY": {"house": 4, "rashi": "KANYA", "combust": False,
                             "debilitated": False, "longitude_used": 180.0},
                "VENUS": {"house": 7, "rashi": "TULA", "combust": False,
                           "debilitated": False, "longitude_used": 210.0},
            },
            "house_lords": {1: "JUPITER", 4: "MERCURY", 7: "VENUS"},
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Saraswati" in names
        sara = next(r for r in results if r.yoga_name == "Saraswati")
        assert sara.status == YogaStatus.FORMED

    def test_saraswati_not_formed_jupiter_weak(self) -> None:
        """Saraswati: Jupiter debilitated -> NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "JUPITER": {"house": 2, "rashi": "MAKARA", "combust": False,
                             "debilitated": True, "longitude_used": 60.0},
                "MERCURY": {"house": 1, "rashi": "MITHUNA", "combust": False,
                             "debilitated": False, "longitude_used": 30.0},
                "VENUS": {"house": 4, "rashi": "SIMHA", "combust": False,
                           "debilitated": False, "longitude_used": 120.0},
            },
            "house_lords": {1: "MERCURY", 2: "SATURN", 4: "MARS"},
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Saraswati" not in names

    def test_amala_yoga_benefic_in_10th(self) -> None:
        """Amala: Benefic planet in H10, no malefic conjunction -> FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "VENUS": {"house": 10, "rashi": "TULA", "combust": False,
                           "debilitated": False},
                "SUN": {"house": 1, "rashi": "MESHA", "combust": False,
                         "debilitated": False},
                "MARS": {"house": 3, "rashi": "MITHUNA", "combust": False,
                          "debilitated": False},
            },
            "house_lords": {1: "SUN", 3: "MARS", 10: "VENUS"},
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Amala" in names
        amala = next(r for r in results if r.yoga_name == "Amala")
        assert amala.status == YogaStatus.FORMED

    def test_amala_not_formed_malefic_conjunction(self) -> None:
        """Amala: Benefic in H10 but malefic also in H10 -> NOT formed."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "VENUS": {"house": 10, "rashi": "TULA", "combust": False,
                           "debilitated": False},
                "MARS": {"house": 10, "rashi": "TULA", "combust": False,
                          "debilitated": False},
            },
            "house_lords": {10: "VENUS"},
        }
        results = service.evaluate_classical_yogas(facts)
        names = [r.yoga_name for r in results]
        assert "Amala" not in names

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

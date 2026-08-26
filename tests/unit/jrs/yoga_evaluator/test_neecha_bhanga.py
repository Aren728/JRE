"""JRS-088 Neecha Bhanga Yoga unit tests."""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestNeechaBhanga:
    def test_neecha_bhanga_formed_when_lord_in_kendra(self) -> None:
        """Test A: Sun debilitated in Libra, Venus (lord) in 1st (Kendra) → FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "lagna_house": 1,
            "planets": {
                "SUN": {"house": 7, "debilitated": True, "combust": False},
                "VENUS": {"house": 1, "debilitated": False, "combust": False},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        neecha = [y for y in yogas if y.yoga_name == "Neecha Bhanga"]
        assert len(neecha) == 1
        assert neecha[0].status.value == "FORMED"

    def test_no_neecha_bhanga_when_lord_not_in_kendra(self) -> None:
        """Test B: Sun debilitated in Libra, Venus in 3rd → no Neecha Bhanga."""
        service = YogaEvaluatorService()
        facts = {
            "lagna_house": 1,
            "planets": {
                "SUN": {"house": 7, "debilitated": True, "combust": False},
                "VENUS": {"house": 3, "debilitated": False, "combust": False},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        neecha = [y for y in yogas if y.yoga_name == "Neecha Bhanga"]
        assert len(neecha) == 0

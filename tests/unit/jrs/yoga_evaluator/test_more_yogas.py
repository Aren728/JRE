"""Tests for Vipareeta Raja and Dhana Yogas (JRS-089)."""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestVipareetaRajaYoga:
    def test_6th_lord_in_8th_house(self) -> None:
        """Test A: 6th lord placed in 8th house -> Vipareeta Raja Yoga FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "house_lords": {
                6: "SATURN",
                8: "JUPITER",
                12: "MARS",
            },
            "planets": {
                "SATURN": {"house": 8},
                "JUPITER": {"house": 5},
                "MARS": {"house": 3},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        names = [y.yoga_name for y in yogas]
        assert "Vipareeta Raja" in names
        vipareeta = next(y for y in yogas if y.yoga_name == "Vipareeta Raja")
        assert vipareeta.status.value == "FORMED"

    def test_no_vipareeta_when_lord_not_in_dusthana(self) -> None:
        """Test A2: 6th lord NOT in 6/8/12 -> no Vipareeta Raja Yoga."""
        service = YogaEvaluatorService()
        facts = {
            "house_lords": {
                6: "SATURN",
                8: "JUPITER",
                12: "MARS",
            },
            "planets": {
                "SATURN": {"house": 1},
                "JUPITER": {"house": 4},
                "MARS": {"house": 7},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        names = [y.yoga_name for y in yogas]
        assert "Vipareeta Raja" not in names


class TestDhanaYoga:
    def test_2nd_lord_and_11th_lord_conjunction(self) -> None:
        """Test B: 2nd lord and 11th lord in same house -> Dhana Yoga FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "house_lords": {
                2: "VENUS",
                11: "SUN",
            },
            "planets": {
                "VENUS": {"house": 5},
                "SUN": {"house": 5},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        names = [y.yoga_name for y in yogas]
        assert "Dhana" in names
        dhana = next(y for y in yogas if y.yoga_name == "Dhana")
        assert dhana.status.value == "FORMED"

    def test_2nd_lord_and_11th_lord_mutual_aspect(self) -> None:
        """Test B2: 2nd lord and 11th lord 7 houses apart -> Dhana Yoga FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "house_lords": {
                2: "VENUS",
                11: "SUN",
            },
            "planets": {
                "VENUS": {"house": 3},
                "SUN": {"house": 10},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        names = [y.yoga_name for y in yogas]
        assert "Dhana" in names

    def test_no_dhana_when_lords_not_connected(self) -> None:
        """Test B3: 2nd lord and 11th lord not conjunct or aspecting -> no Dhana."""
        service = YogaEvaluatorService()
        facts = {
            "house_lords": {
                2: "VENUS",
                11: "SUN",
            },
            "planets": {
                "VENUS": {"house": 1},
                "SUN": {"house": 5},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        names = [y.yoga_name for y in yogas]
        assert "Dhana" not in names

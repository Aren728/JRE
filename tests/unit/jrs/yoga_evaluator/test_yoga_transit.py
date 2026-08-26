"""Tests for transit activation of classical yogas (JRS-090)."""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestYogaTransitActivation:
    """Transit activation tests for classical yogas."""

    def test_dhana_yoga_transit_activates(self) -> None:
        """Test A: Dhana Yoga with transit Jupiter in same house -> manifesting."""
        service = YogaEvaluatorService()
        facts = {
            "house_lords": {
                2: "VENUS",
                11: "SUN",
            },
            "planets": {
                "VENUS": {"house": 5},
                "SUN": {"house": 5},
                "JUPITER": {"house": 5},
            },
        }
        yogas = service.evaluate_classical_yogas(facts, transit_planet="JUPITER")
        dhana = [y for y in yogas if y.yoga_name == "Dhana"]
        assert len(dhana) == 1
        assert dhana[0].is_manifesting is True
        assert dhana[0].activation_source == "Transit: JUPITER"

    def test_dhana_yoga_no_transit(self) -> None:
        """Test B: Dhana Yoga with no transit -> not manifesting."""
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
        dhana = [y for y in yogas if y.yoga_name == "Dhana"]
        assert len(dhana) == 1
        assert dhana[0].is_manifesting is False
        assert dhana[0].activation_source is None

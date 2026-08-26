"""JRS-077 Yoga Outcome Mapping unit tests."""

from __future__ import annotations

import pytest
from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestYogaOutcomeMapping:
    def test_career_prominence(self) -> None:
        """Test A: Yoga involving 10th house and Sun -> CAREER_PROMINENCE."""
        service = YogaEvaluatorService()
        result = service.map_outcome(
            yoga_name="Sun in 10th",
            involved_houses=[10],
            involved_planets=["SUN"],
        )
        assert result == "CAREER_PROMINENCE"

    def test_wealth_accumulation(self) -> None:
        """Test B: Yoga involving 2nd house and Jupiter -> WEALTH_ACCUMULATION."""
        service = YogaEvaluatorService()
        result = service.map_outcome(
            yoga_name="Jupiter in 2nd",
            involved_houses=[2],
            involved_planets=["JUPITER"],
        )
        assert result == "WEALTH_ACCUMULATION"

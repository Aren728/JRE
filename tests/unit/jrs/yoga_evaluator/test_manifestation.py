"""JRS-076 Yoga Manifestation & Outcome Mapping unit tests."""

from __future__ import annotations

import pytest
from jrs.yoga_evaluator.models import YogaOutcome
from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestYogaManifestation:
    def test_dasha_lord_matches_involved_planet(self) -> None:
        """Test A: Dasha lord matches an involved planet -> evaluate_manifestation returns True."""
        service = YogaEvaluatorService()
        result = service.evaluate_manifestation(
            "Guru Chandra",
            ["JUPITER", "MOON"],
            "JUPITER",
        )
        assert result is True

    def test_dasha_lord_does_not_match(self) -> None:
        """Test A2: Dasha lord does NOT match -> evaluate_manifestation returns False."""
        service = YogaEvaluatorService()
        result = service.evaluate_manifestation(
            "Guru Chandra",
            ["JUPITER", "MOON"],
            "SATURN",
        )
        assert result is False


class TestYogaOutcomeMapping:
    def test_dhana_yoga_maps_to_wealth_accumulation(self) -> None:
        """Test B: map_outcome("DHANA_YOGA") returns WEALTH_ACCUMULATION."""
        service = YogaEvaluatorService()
        result = service.map_outcome("DHANA_YOGA")
        assert result == YogaOutcome.WEALTH_ACCUMULATION

    def test_raja_yoga_maps_to_career_prominence(self) -> None:
        """Test B2: map_outcome("RAJA_YOGA") returns CAREER_PROMINENCE."""
        service = YogaEvaluatorService()
        result = service.map_outcome("RAJA_YOGA")
        assert result == YogaOutcome.CAREER_PROMINENCE

    def test_unknown_yoga_maps_to_general_improvement(self) -> None:
        """Test B3: Unknown yoga name returns GENERAL_IMPROVEMENT."""
        service = YogaEvaluatorService()
        result = service.map_outcome("SOME_RANDOM_YOGA")
        assert result == YogaOutcome.GENERAL_IMPROVEMENT

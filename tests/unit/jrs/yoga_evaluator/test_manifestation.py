"""JRS-076 Yoga Manifestation / Temporal Activation unit tests."""

from __future__ import annotations

import pytest
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestYogaManifestation:
    def test_dasha_activates_yoga(self) -> None:
        """Test A: FORMED yoga with [Jupiter, Moon], Dasha lord = Jupiter -> is_manifesting == True."""
        service = YogaEvaluatorService()
        evaluation = YogaEvaluation(
            yoga_name="Guru Chandra",
            status=YogaStatus.FORMED,
        )
        result = service.evaluate_manifestation(
            evaluation=evaluation,
            yoga_planets=["JUPITER", "MOON"],
            active_dasha_lord="JUPITER",
            transit_planet="SATURN",
        )
        assert result.is_manifesting is True
        assert result.activation_source == "Dasha: JUPITER"
        assert result.status == YogaStatus.FORMED

    def test_no_activation_when_lord_not_in_yoga(self) -> None:
        """Test B: FORMED yoga with [Jupiter, Moon], Dasha = Mars, Transit = Mars -> is_manifesting == False."""
        service = YogaEvaluatorService()
        evaluation = YogaEvaluation(
            yoga_name="Guru Chandra",
            status=YogaStatus.FORMED,
        )
        result = service.evaluate_manifestation(
            evaluation=evaluation,
            yoga_planets=["JUPITER", "MOON"],
            active_dasha_lord="MARS",
            transit_planet="MARS",
        )
        assert result.is_manifesting is False
        assert result.activation_source is None
        assert result.status == YogaStatus.FORMED

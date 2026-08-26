"""JRS-075 Yoga Formation & Cancellation Evaluator unit tests."""

from __future__ import annotations

import pytest
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestYogaEvaluatorService:
    def test_combust_planet_cancels_yoga(self) -> None:
        """Test A: Planet A is combust -> yoga is CANCELLED with reason."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "SUN": {"house": 1, "combust": True, "debilitated": False},
                "JUPITER": {"house": 5, "combust": False, "debilitated": False},
            }
        }
        result = service.evaluate_formation(
            yoga_name="Guru Mangala",
            involved_planets=["SUN", "JUPITER"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.CANCELLED
        assert result.cancellation_reason == "SUN is combust"
        assert result.yoga_name == "Guru Mangala"

    def test_no_afflictions_yoga_forms(self) -> None:
        """Test B: No afflictions -> yoga is FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                "VENUS": {"house": 4, "combust": False, "debilitated": False},
            }
        }
        result = service.evaluate_formation(
            yoga_name="Guru Shukra",
            involved_planets=["JUPITER", "VENUS"],
            jre_facts=facts,
        )
        assert result.status == YogaStatus.FORMED
        assert result.cancellation_reason is None

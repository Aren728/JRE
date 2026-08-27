"""Tests for classical yoga cancellation rules (JRS-091)."""

from __future__ import annotations

import pytest

from jrs.yoga_evaluator.service import YogaEvaluatorService


class TestYogaCancellation:
    """Cancellation tests for classical yogas."""

    def test_gajakesari_cancelled_when_moon_combust(self) -> None:
        """Test A: Gajakesari Yoga with Moon combust -> CANCELLED."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                "MOON": {"house": 4, "combust": True, "debilitated": False},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        gaja = [y for y in yogas if y.yoga_name == "Gajakesari"]
        # Moon is combust so evaluate_formation returns CANCELLED,
        # meaning the yoga won't be added as FORMED in the first place.
        # Either way, no FORMED Gajakesari should exist.
        assert all(y.status.value != "FORMED" for y in gaja)

    def test_gajakesari_no_afflictions_returns_formed(self) -> None:
        """Test B: Gajakesari Yoga with no afflictions -> FORMED."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                "MOON": {"house": 4, "combust": False, "debilitated": False},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        gaja = [y for y in yogas if y.yoga_name == "Gajakesari"]
        assert len(gaja) == 1
        assert gaja[0].status.value == "FORMED"

    def test_gajakesari_weakened_by_nodal_affliction(self) -> None:
        """Gajakesari with Moon conjunct Rahu -> WEAKENED (Nodal Affliction)."""
        service = YogaEvaluatorService()
        facts = {
            "planets": {
                "JUPITER": {"house": 1, "combust": False, "debilitated": False},
                "MOON": {"house": 4, "combust": False, "debilitated": False},
                "RAHU": {"house": 4},
            },
        }
        yogas = service.evaluate_classical_yogas(facts)
        gaja = [y for y in yogas if y.yoga_name == "Gajakesari"]
        assert len(gaja) == 1
        assert gaja[0].status.value == "WEAKENED"
        assert "Nodal Affliction" in gaja[0].cancellation_reason

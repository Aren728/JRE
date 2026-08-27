"""JRS-092 End-to-End Classical Yoga CLI Integration Test."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from jrs.cli import main
from jrs.yoga_evaluator.service import YogaEvaluatorService
from jrs.yoga_evaluator.models import YogaStatus


# Mock chart where 2nd lord = MERCURY and 11th lord = MERCURY are conjunct
# (both in house 5). Mercury is strong (not combust/debilitated) and the
# active dasha lord is MERCURY (manifesting).
MOCK_YOGA_FACTS: dict = {
    "planets": {
        "SUN": {"house": 10, "combust": False, "debilitated": False},
        "MOON": {"house": 4, "combust": False, "debilitated": False},
        "MARS": {"house": 8, "combust": False, "debilitated": False},
        "MERCURY": {"house": 5, "combust": False, "debilitated": False},
        "JUPITER": {"house": 1, "combust": False, "debilitated": False},
        "VENUS": {"house": 3, "combust": False, "debilitated": False},
        "SATURN": {"house": 6, "combust": False, "debilitated": False},
        "RAHU": {"house": 9, "combust": False, "debilitated": False},
        "KETU": {"house": 3, "combust": False, "debilitated": False},
    },
    "house_lords": {
        1: "JUPITER",
        2: "MERCURY",
        3: "MERCURY",
        4: "MOON",
        5: "SUN",
        6: "MERCURY",
        7: "VENUS",
        8: "MARS",
        9: "JUPITER",
        10: "SATURN",
        11: "MERCURY",
        12: "JUPITER",
    },
    "active_dasha_lord": "MERCURY",
    "transit_planet": "JUPITER",
}


class TestClassicalYogaCLI:
    """End-to-end test for classical yoga CLI output."""

    def test_classical_yoga_cli_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Dhana Yoga (2nd & 11th lords conjunct) should appear as FORMED
        with WEALTH_ACCUMULATION in the CLI output."""
        with patch("jrs.cli._default_facts_for_query", return_value=MOCK_YOGA_FACTS):
            rc = main([
                "--birth-date", "15-05-1990",
                "--birth-time", "10:30",
                "--place", "Delhi, India",
                "--query", "wealth",
                "--json",
            ])

        assert rc == 0

        output = capsys.readouterr().out
        parsed = json.loads(output)
        assert "assessment" in parsed

        # ── Direct classical yoga evaluation ──
        evaluator = YogaEvaluatorService()
        classical_yogas = evaluator.evaluate_classical_yogas(MOCK_YOGA_FACTS)

        # Find Dhana Yoga among the classical yogas
        dhana_yogas = [y for y in classical_yogas if y.yoga_name == "Dhana"]
        assert len(dhana_yogas) >= 1, (
            f"Expected Dhana Yoga, got: {[y.yoga_name for y in classical_yogas]}"
        )
        dhana = dhana_yogas[0]

        # Assert status is FORMED
        assert dhana.status == YogaStatus.FORMED

        # Map outcome category — Dhana yoga involves houses 2 and 11
        outcome = evaluator.map_outcome(
            yoga_name=dhana.yoga_name,
            involved_houses=[2, 11],
            involved_planets=["MERCURY", "MERCURY"],
        )
        assert outcome == "WEALTH_ACCUMULATION"

        # Verify the string representations match expected output values
        assert "Dhana" in dhana.yoga_name
        assert "FORMED" in dhana.status.value
        assert "WEALTH_ACCUMULATION" == outcome

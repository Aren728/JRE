"""JRS-079 Graph-to-Yoga Integration Test (Atomic Execution)."""

from __future__ import annotations

import pytest
from jrs.structural.service import RelationshipGraphService
from jrs.structural.models import RelationshipType
from jrs.yoga_evaluator.models import YogaOutcome, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


def _build_mock_jre_facts() -> dict:
    """Build mock JRE facts: Sun and Mercury conjunct in Aries (MESHA)."""
    return {
        "lagna": "MESHA",
        "planets": {
            "SUN": {
                "rashi": "MESHA",
                "house": 1,
                "combust": False,
                "debilitated": False,
            },
            "MERCURY": {
                "rashi": "MESHA",
                "house": 1,
                "combust": False,
                "debilitated": False,
            },
        },
    }


class TestGraphToYoga:
    def test_graph_feeds_yoga_evaluator(self) -> None:
        """Relationship graph detects Sun-Mercury conjunction, yoga evaluator confirms FORMED."""
        mock_facts = _build_mock_jre_facts()

        # Step 1: Extract relationships from the graph service
        graph_service = RelationshipGraphService()
        relationships = graph_service.extract_relationships(mock_facts)

        # Step 2: Verify a CONJUNCTION between Sun and Mercury was detected
        sun_mercury_conjunction = None
        for rel in relationships:
            if (
                rel.relationship_type == RelationshipType.CONJUNCTION
                and {rel.planet_a, rel.planet_b} == {"SUN", "MERCURY"}
            ):
                sun_mercury_conjunction = rel
                break

        assert sun_mercury_conjunction is not None, (
            "RelationshipGraphService must detect a CONJUNCTION between SUN and MERCURY"
        )

        # Step 3: Feed the detected relationship into the yoga evaluator
        yoga_service = YogaEvaluatorService()
        evaluation = yoga_service.evaluate_formation(
            yoga_name="BUDHADITYA_YOGA",
            involved_planets=["SUN", "MERCURY"],
            jre_facts=mock_facts,
        )

        # Step 4: Assert formation status is FORMED
        assert evaluation.status == YogaStatus.FORMED, (
            f"Budhaditya Yoga must be FORMED, got {evaluation.status}"
        )

        # Step 5: Map outcome and assert CAREER_PROMINENCE
        outcome = yoga_service.map_outcome(
            yoga_name="BUDHADITYA_YOGA",
            involved_planets=["SUN", "MERCURY"],
        )
        assert outcome == YogaOutcome.CAREER_PROMINENCE, (
            f"Budhaditya Yoga outcome must be CAREER_PROMINENCE, got {outcome}"
        )

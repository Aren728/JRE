"""JRS-079 Transit Yoga Activation Integration Test (Atomic Execution)."""

from __future__ import annotations

import pytest
from jrs.structural.models import RelationshipType
from jrs.structural.service import RelationshipGraphService
from jrs.yoga_evaluator.models import YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


def _build_natal_facts() -> dict:
    """Build mock JRE natal facts: Sun and Mercury conjunct in Aries (MESHA)."""
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
        "active_dasha_lord": "MERCURY",
    }


def _build_transit_facts() -> dict:
    """Build mock JRE transit facts: Jupiter transiting Libra (TULA).

    Jupiter in TULA (7th from MESHA) aspects MESHA via its 7th aspect,
    activating the natal Sun-Mercury conjunction.
    """
    return {
        "planets": {
            "JUPITER": {
                "rashi": "TULA",
                "house": 7,
            },
        },
    }


class TestTransitYogaActivation:
    def test_transit_activates_yoga(self) -> None:
        """Full pipeline: graph conjunction → yoga formation → transit activation."""
        natal_facts = _build_natal_facts()
        transit_facts = _build_transit_facts()

        # ── Step 1: Natal graph → CONJUNCTION ──────────────────────────────
        graph_service = RelationshipGraphService()
        natal_rels = graph_service.extract_relationships(natal_facts)

        conj = next(
            (r for r in natal_rels if r.relationship_type == RelationshipType.CONJUNCTION),
            None,
        )
        assert conj is not None, "Graph must detect CONJUNCTION between SUN and MERCURY"
        assert {conj.planet_a, conj.planet_b} == {"SUN", "MERCURY"}

        # ── Step 2: Yoga formation → FORMED ────────────────────────────────
        evaluator = YogaEvaluatorService()
        evaluation = evaluator.evaluate_formation(
            yoga_name="BUDHADITYA_YOGA",
            involved_planets=["SUN", "MERCURY"],
            jre_facts=natal_facts,
        )
        assert evaluation.status == YogaStatus.FORMED, (
            f"Budhaditya Yoga must be FORMED, got {evaluation.status}"
        )

        # ── Step 3: Transit graph → TRANSIT_ASPECT ─────────────────────────
        all_rels = graph_service.extract_relationships(natal_facts, transit_facts)

        transit_aspect = next(
            (r for r in all_rels if r.relationship_type == RelationshipType.TRANSIT_ASPECT),
            None,
        )
        assert transit_aspect is not None, (
            "Graph must detect TRANSIT_ASPECT from JUPITER to natal planet"
        )
        assert transit_aspect.planet_a == "JUPITER"
        assert transit_aspect.planet_b in ("SUN", "MERCURY")
        assert transit_aspect.is_active is True

        # ── Step 4: Manifestation → is_manifesting == True ─────────────────
        # Use legacy signature: evaluate the formation with dasha + transit
        result = evaluator.evaluate_manifestation(
            evaluation=evaluation,
            yoga_planets=["SUN", "MERCURY"],
            active_dasha_lord=natal_facts["active_dasha_lord"],
            transit_planet="JUPITER",
        )
        assert result.is_manifesting is True, (
            "Yoga must be manifesting due to transit aspect and Dasha match"
        )

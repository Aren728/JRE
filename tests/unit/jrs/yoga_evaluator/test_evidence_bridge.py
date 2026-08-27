"""JRS-081 Yoga-to-Evidence Bridge unit tests."""

from __future__ import annotations

import pytest
from jrs.evidence.models import EvidenceRecord, EvidenceStrength
from jrs.yoga_evaluator.evidence_service import YogaEvidenceService
from jrs.yoga_evaluator.service import YogaEvaluatorService


def _build_mock_jre_facts() -> dict:
    """Build mock JRE facts that produce a manifesting Raja Yoga.

    Lagna: MESHA (Aries, house 1).
    SUN in house 5 — rules house 5 (trikona lord).
    MARS in house 5 — rules house 1 (kendra lord).
    MERCURY in house 5 — rules house 3.
    Sun (trikona lord) conjunct Mars (kendra lord) in house 5 → Raja Yoga.
    Dasha lord = MERCURY → yoga is manifesting.
    """
    return {
        "lagna_house": 1,
        "planets": {
            "SUN": {
                "house": 5,
                "combust": False,
                "debilitated": False,
            },
            "MARS": {
                "house": 5,
                "combust": False,
                "debilitated": False,
            },
            "MERCURY": {
                "house": 5,
                "combust": False,
                "debilitated": False,
            },
        },
        "house_lords": {
            1: "MARS",
            2: "VENUS",
            3: "MERCURY",
            4: "MOON",
            5: "SUN",
            6: "MERCURY",
            7: "VENUS",
            8: "MARS",
            9: "JUPITER",
            10: "SATURN",
            11: "SATURN",
            12: "JUPITER",
        },
    }


class TestYogaEvidenceBridge:
    def test_generate_yoga_evidence_returns_one_record(self) -> None:
        """Sun/Mercury conjunct, Dasha lord Mercury → exactly 1 EvidenceRecord
        with outcome CAREER_PROMINENCE."""
        jre_facts = _build_mock_jre_facts()
        service = YogaEvidenceService()

        records = service.generate_yoga_evidence(
            jre_facts=jre_facts,
            dasha_lord="MERCURY",
        )

        assert len(records) == 1, (
            f"Expected exactly 1 EvidenceRecord, got {len(records)}"
        )

        rec = records[0]
        assert isinstance(rec, EvidenceRecord)
        assert rec.source_id == "Yoga_Evaluator"
        assert rec.strength == EvidenceStrength.HIGH
        assert rec.supporting_fact_type == "YOGA_FORMATION"
        # Mercury involved in Raja Yoga → CAREER_PROMINENCE via map_outcome
        assert rec.outcome_taxonomy == "CAREER_PROMINENCE"

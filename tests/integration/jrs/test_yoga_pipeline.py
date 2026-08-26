"""End-to-end yoga pipeline integration test (JRS-080)."""

from __future__ import annotations

import pytest
from jrs.convergence.models import DomainAssessment
from jrs.domains.yoga.service import YogaDomainService
from jrs.evidence.models import EvidenceRecord, STRENGTH_VALUES
from jrs.kendra_trikona.service import KendraTrikonaService
from jrs.yoga_evaluator.integration import YogaEvidenceService
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


def _build_valid_jre_facts() -> dict:
    """Build a chart with a valid Kendra-Trikona yoga.

    Chart: MESHA (Aries) lagna.
    SUN placed in MAKARA (Capricorn, 10th house from lagna).
    SUN is 5th lord (trikona lord) placed in 10th house (kendra) → TRIKONA_LORD_IN_KENDRA.
    Both SUN and the 10th-house lord (SATURN) are strong: not combust, not debilitated.
    Active Dasha lord is SUN (one of the yoga planets) → yoga is manifesting.
    """
    # MESHA lagna → house lords: 1=MARS, 5=SUN, 9=JUPITER, 10=SATURN
    # SATURN (10th lord, kendra lord) placed in MESHA (1st house, trikona)
    #   → KENDRA_LORD_IN_TRIKONA with planets [SATURN, MARS]
    # SUN (5th lord, trikona lord) placed in MAKARA (10th house, kendra)
    #   → TRIKONA_LORD_IN_KENDRA with planets [SUN, SATURN]
    # active_dasha_lord=SATURN matches both yoga planet sets → manifesting.
    return {
        "lagna": "MESHA",
        "planets": {
            "SUN": {"rashi": "MAKARA", "house": 10, "combust": False, "debilitated": False},
            "SATURN": {"rashi": "MESHA", "house": 1, "combust": False, "debilitated": False},
        },
        "active_dasha_lord": "SATURN",
        "transit_planet": "JUPITER",
    }


class TestEndToEndYogaPipeline:
    def test_end_to_end_yoga_pipeline(self) -> None:
        """Full pipeline: structural detection → formation → manifestation → evidence."""
        jre_facts = _build_valid_jre_facts()

        # ── Step 1: Run the domain service ──────────────────────────────────
        service = YogaDomainService()
        assessment = service.assess(jre_facts)

        assert isinstance(assessment, DomainAssessment)
        assert assessment.dimensions.supporting_count >= 1, (
            "DomainAssessment should contain at least 1 evidence record"
        )

        # ── Step 2: Re-run sub-services to get the actual EvidenceRecords ───
        # (DomainAssessment does not store records directly, so we replicate
        # the pipeline to access EvidenceRecord fields for detailed assertions.)

        kt_service = KendraTrikonaService()
        evaluator = YogaEvaluatorService()
        evidence_svc = YogaEvidenceService()

        structural_yogas = kt_service.evaluate(jre_facts)
        assert len(structural_yogas) >= 1, "At least one structural yoga must be detected"

        evidence_records: list[EvidenceRecord] = []
        for yoga in structural_yogas:
            involved_planets = [yoga.planet_a, yoga.planet_b]
            involved_houses = [yoga.house_a, yoga.house_b]

            evaluation = evaluator.evaluate_formation(
                yoga_name=yoga.yoga_type.value,
                involved_planets=involved_planets,
                jre_facts=jre_facts,
            )
            assert evaluation.status == YogaStatus.FORMED

            evaluation = evaluator.evaluate_manifestation(
                evaluation=evaluation,
                yoga_planets=involved_planets,
                active_dasha_lord=jre_facts["active_dasha_lord"],
                transit_planet=jre_facts["transit_planet"],
            )
            assert evaluation.is_manifesting is True, "Yoga must be manifesting under the active Dasha"

            outcome = evaluator.map_outcome(
                yoga_name=yoga.yoga_type.value,
                involved_houses=involved_houses,
                involved_planets=involved_planets,
            )
            evaluation = YogaEvaluation(
                yoga_name=evaluation.yoga_name,
                status=evaluation.status,
                cancellation_reason=evaluation.cancellation_reason,
                is_manifesting=evaluation.is_manifesting,
                activation_source=evaluation.activation_source,
                outcome_category=outcome,
            )

            record = evidence_svc.convert_to_evidence(evaluation)
            if record is not None:
                evidence_records.append(record)

        assert len(evidence_records) >= 1

        # ── Step 3: Assert EvidenceRecord properties ────────────────────────
        rec = evidence_records[0]
        assert isinstance(rec, EvidenceRecord)
        assert rec.source_id == "YogaEvaluator"

        weight = STRENGTH_VALUES[rec.strength]
        assert weight > 0.5, f"EvidenceRecord weight {weight} must be > 0.5"

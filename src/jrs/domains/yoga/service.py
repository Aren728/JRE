"""Yoga domain service — orchestrates structural yoga detection, evaluation, and evidence conversion."""

from __future__ import annotations

from typing import Any

from jrs.convergence.models import DomainAssessment, EvidenceDimensions
from jrs.evidence.models import EvidenceRecord
from jrs.kendra_trikona.service import KendraTrikonaService
from jrs.yoga_evaluator.integration import YogaEvidenceService
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


class YogaDomainService:
    """Orchestrates yoga detection, evaluation, manifestation, and evidence integration.

    Usage::

        svc = YogaDomainService()
        assessment = svc.assess(jre_facts)
    """

    def __init__(self) -> None:
        self._kendra_trikona = KendraTrikonaService()
        self._evaluator = YogaEvaluatorService()
        self._evidence = YogaEvidenceService()

    def assess(self, jre_facts: dict[str, Any]) -> DomainAssessment:
        """Evaluate all yoga formations from JRE facts and return a DomainAssessment.

        Steps:
            1. Detect structural yogas via KendraTrikonaService.
            2. For each structural yoga, evaluate formation and manifestation.
            3. Convert manifesting, formed yogas to EvidenceRecords.
            4. Aggregate into a DomainAssessment.

        Args:
            jre_facts: Dictionary of JRE-computed planetary facts.

        Returns:
            A DomainAssessment containing evidence records for all valid yogas.
        """
        structural_yogas = self._kendra_trikona.evaluate(jre_facts)
        evidence_records: list[EvidenceRecord] = []

        active_dasha_lord = jre_facts.get("active_dasha_lord", "")
        transit_planet = jre_facts.get("transit_planet", "")

        for yoga in structural_yogas:
            involved_planets = [yoga.planet_a, yoga.planet_b]
            involved_houses = [yoga.house_a, yoga.house_b]

            # Step 2a: Evaluate formation
            evaluation = self._evaluator.evaluate_formation(
                yoga_name=yoga.yoga_type.value,
                involved_planets=involved_planets,
                jre_facts=jre_facts,
            )

            # Skip cancelled or weakened yogas for evidence generation
            if evaluation.status != YogaStatus.FORMED:
                continue

            # Step 2b: Evaluate manifestation
            evaluation = self._evaluator.evaluate_manifestation(
                evaluation=evaluation,
                yoga_planets=involved_planets,
                active_dasha_lord=active_dasha_lord,
                transit_planet=transit_planet,
            )

            # Step 2c: Map outcome category
            outcome = self._evaluator.map_outcome(
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

            # Step 3: Convert to evidence record
            record = self._evidence.convert_to_evidence(evaluation)
            if record is not None:
                evidence_records.append(record)

        # Step 4: Build DomainAssessment
        dimensions = EvidenceDimensions(
            supporting_count=len(evidence_records),
            independent_channels=len(evidence_records),
        )

        return DomainAssessment(
            outcome_taxonomy="YOGA_FORMATION",
            dimensions=dimensions,
        )

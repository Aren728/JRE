"""JRS-081 Yoga-to-Evidence Bridge service."""

from __future__ import annotations

from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.yoga_evaluator.models import YogaOutcome, YogaStatus
from jrs.yoga_evaluator.service import YogaEvaluatorService


# Weight 0.8 maps to EvidenceStrength.HIGH
_YOGA_EVIDENCE_STRENGTH = EvidenceStrength.HIGH


class YogaEvidenceService:
    """Bridges YogaEvaluatorService output to EvidenceRecord objects."""

    def __init__(self, evaluator: YogaEvaluatorService | None = None) -> None:
        self._evaluator = evaluator or YogaEvaluatorService()

    def generate_yoga_evidence(
        self,
        jre_facts: dict[str, Any],
        dasha_lord: str,
    ) -> list[EvidenceRecord]:
        """Generate EvidenceRecords for active, formed yogas.

        Args:
            jre_facts: JRE chart facts dictionary.
            dasha_lord: Currently active Dasha lord planet name.

        Returns:
            List of EvidenceRecord for yogas that are FORMED and manifesting
            under the given Dasha lord.
        """
        evaluations = self._evaluator.evaluate_classical_yogas(jre_facts)

        evidence_records: list[EvidenceRecord] = []
        for yoga in evaluations:
            if yoga.status != YogaStatus.FORMED:
                continue

            # Check Dasha activation via legacy manifestation signature
            activated = self._evaluator.evaluate_manifestation(
                evaluation=yoga,
                yoga_planets=list(jre_facts.get("planets", {})),
                active_dasha_lord=dasha_lord,
            )

            if not getattr(activated, "is_manifesting", False):
                continue

            # Map outcome using the legacy signature which checks planets
            outcome = self._evaluator.map_outcome(
                yoga_name=yoga.yoga_name,
                involved_planets=list(jre_facts.get("planets", {})),
            )

            evidence_records.append(
                EvidenceRecord(
                    evidence_id=f"yoga_{yoga.yoga_name.lower().replace(' ', '_')}",
                    outcome_taxonomy=str(outcome),
                    supporting_fact_type="YOGA_FORMATION",
                    rule_id=f"rule_{yoga.yoga_name.lower().replace(' ', '_')}",
                    source_id="Yoga_Evaluator",
                    strength=_YOGA_EVIDENCE_STRENGTH,
                    direction=EvidenceDirection.SUPPORT,
                    location=activated.activation_source or "",
                )
            )

        return evidence_records

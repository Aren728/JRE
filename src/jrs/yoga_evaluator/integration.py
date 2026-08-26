"""JRS-078 Yoga to Evidence Record Integration service."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.yoga_evaluator.models import YogaEvaluation, YogaStatus


class Channel(Enum):
    """Standard evidence channels mapped from yoga outcome categories."""

    CAREER = "CAREER"
    WEALTH = "WEALTH"
    DOMESTIC = "DOMESTIC"
    GENERAL = "GENERAL"


# Mapping from yoga outcome_category to Channel
OUTCOME_CHANNEL_MAP: dict[str, Channel] = {
    "CAREER_PROMINENCE": Channel.CAREER,
    "WEALTH_ACCUMULATION": Channel.WEALTH,
    "DOMESTIC_HARMONY": Channel.DOMESTIC,
}

# Mapping from YogaStatus to EvidenceStrength weight
STATUS_STRENGTH_MAP: dict[YogaStatus, EvidenceStrength] = {
    YogaStatus.FORMED: EvidenceStrength.HIGH,
    YogaStatus.WEAKENED: EvidenceStrength.MODERATE,
    YogaStatus.CANCELLED: EvidenceStrength.LOW,
}


class YogaEvidenceService:
    """Converts YogaEvaluation results into EvidenceRecord objects."""

    def convert_to_evidence(
        self,
        evaluation: YogaEvaluation,
    ) -> Optional[EvidenceRecord]:
        """Convert a yoga evaluation into an evidence record.

        Returns None if the yoga is not formed or not manifesting.
        """
        if evaluation.status != YogaStatus.FORMED:
            return None

        if not evaluation.is_manifesting:
            return None

        channel = OUTCOME_CHANNEL_MAP.get(
            evaluation.outcome_category or "", Channel.GENERAL,
        )

        strength = STATUS_STRENGTH_MAP.get(evaluation.status, EvidenceStrength.MODERATE)

        return EvidenceRecord(
            evidence_id=f"yoga_{evaluation.yoga_name.lower().replace(' ', '_')}",
            outcome_taxonomy=channel.value,
            supporting_fact_type="YOGA_FORMATION",
            rule_id=f"rule_{evaluation.yoga_name.lower().replace(' ', '_')}",
            source_id="YogaEvaluator",
            strength=strength,
            direction=EvidenceDirection.SUPPORT,
            location=evaluation.activation_source or "",
        )

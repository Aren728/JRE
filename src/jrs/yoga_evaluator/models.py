"""JRS-075/076/077 Yoga Formation, Cancellation, Manifestation & Outcome Evaluator models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional

# Forward reference for ModifierReport to avoid circular imports
type _ModifierReport = Any  # Resolved at runtime from modifier_service


class YogaStatus(StrEnum):
    """Status of a yoga after affliction checks."""
    FORMED = "FORMED"
    CANCELLED = "CANCELLED"
    WEAKENED = "WEAKENED"


class YogaOutcome(StrEnum):
    """Mapped outcome category for a formed yoga.

    Expanded in Phase E6g to support multi-domain mapping.
    Each yoga can map to multiple relevant outcome domains.
    """
    CAREER_PROMINENCE = "CAREER_PROMINENCE"
    WEALTH_ACCUMULATION = "WEALTH_ACCUMULATION"
    RELATIONSHIP_HARMONY = "RELATIONSHIP_HARMONY"
    DOMESTIC_HARMONY = "DOMESTIC_HARMONY"
    GENERAL_IMPROVEMENT = "GENERAL_IMPROVEMENT"
    # Phase E6g: Expanded domains for multi-domain mapping
    ARTISTIC_EXCELLENCE = "ARTISTIC_EXCELLENCE"
    MENTAL_STRENGTH = "MENTAL_STRENGTH"
    POLITICAL_POWER = "POLITICAL_POWER"
    SOCIAL_STATUS = "SOCIAL_STATUS"
    PUBLIC_RECOGNITION = "PUBLIC_RECOGNITION"
    WISDOM_ACCUMULATION = "WISDOM_ACCUMULATION"
    TEACHING_ABILITY = "TEACHING_ABILITY"
    INTELLECTUAL_EXCELLENCE = "INTELLECTUAL_EXCELLENCE"
    COMMUNICATION_SKILLS = "COMMUNICATION_SKILLS"
    BUSINESS_ACUMEN = "BUSINESS_ACUMEN"
    RECOVERY_FROM_ADVERSITY = "RECOVERY_FROM_ADVERSITY"
    CRISIS_MANAGEMENT = "CRISIS_MANAGEMENT"
    EMOTIONAL_STABILITY = "EMOTIONAL_STABILITY"
    LEADERSHIP = "LEADERSHIP"


@dataclass(frozen=True)
class YogaEvaluation:
    """Result of evaluating whether a yoga is formed, weakened, or cancelled.

    Phase 1 addition:
    - modifier_report: Attached ModifierReport from 5-tier pipeline (RI-010G).
    """
    yoga_name: str
    status: YogaStatus
    cancellation_reason: Optional[str] = None
    is_manifesting: bool = False
    activation_source: Optional[str] = None
    outcome_category: Optional[str] = None
    outcome: Optional[YogaOutcome] = None
    modifier_report: Optional[_ModifierReport] = field(default=None, repr=False)
    chain_impact: Optional[float] = field(default=None, repr=False)
    dasha_multiplier: Optional[float] = field(default=None, repr=False)
    transit_multiplier: Optional[float] = field(default=None, repr=False)
    dynamic_strength: Optional[float] = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "yoga_name": self.yoga_name,
            "status": self.status.value,
        }
        if self.cancellation_reason is not None:
            d["cancellation_reason"] = self.cancellation_reason
        if self.is_manifesting:
            d["is_manifesting"] = True
        if self.activation_source is not None:
            d["activation_source"] = self.activation_source
        if self.outcome_category is not None:
            d["outcome_category"] = self.outcome_category
        if self.modifier_report is not None:
            d["modifier_report"] = {
                "overall_status": self.modifier_report.overall_status.value,
                "overall_strength": self.modifier_report.overall_strength,
                "cancellation_reason": self.modifier_report.cancellation_reason,
            }
        if self.chain_impact is not None:
            d["chain_impact"] = self.chain_impact
        if self.dasha_multiplier is not None:
            d["dasha_multiplier"] = self.dasha_multiplier
        if self.transit_multiplier is not None:
            d["transit_multiplier"] = self.transit_multiplier
        if self.dynamic_strength is not None:
            d["dynamic_strength"] = self.dynamic_strength
        return d

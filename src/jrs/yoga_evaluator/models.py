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
    """Mapped outcome category for a formed yoga."""
    CAREER_PROMINENCE = "CAREER_PROMINENCE"
    WEALTH_ACCUMULATION = "WEALTH_ACCUMULATION"
    RELATIONSHIP_HARMONY = "RELATIONSHIP_HARMONY"
    DOMESTIC_HARMONY = "DOMESTIC_HARMONY"
    GENERAL_IMPROVEMENT = "GENERAL_IMPROVEMENT"


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
        return d

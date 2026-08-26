"""JRS-075/076/077 Yoga Formation, Cancellation, Manifestation & Outcome Evaluator models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional


class YogaStatus(StrEnum):
    """Status of a yoga after affliction checks."""
    FORMED = "FORMED"
    CANCELLED = "CANCELLED"
    WEAKENED = "WEAKENED"


@dataclass(frozen=True)
class YogaEvaluation:
    """Result of evaluating whether a yoga is formed, weakened, or cancelled."""
    yoga_name: str
    status: YogaStatus
    cancellation_reason: Optional[str] = None
    is_manifesting: bool = False
    activation_source: Optional[str] = None
    outcome_category: Optional[str] = None

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
        return d

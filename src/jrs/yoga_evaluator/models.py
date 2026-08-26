"""JRS-075 Yoga Formation & Cancellation Evaluator models."""

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

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "yoga_name": self.yoga_name,
            "status": self.status.value,
        }
        if self.cancellation_reason is not None:
            d["cancellation_reason"] = self.cancellation_reason
        return d

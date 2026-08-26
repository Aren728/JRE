"""Yoga domain data models — outcome taxonomy for yoga-based assessments."""

from __future__ import annotations

from enum import Enum


class YogaDomainOutcome(Enum):
    """High-level yoga domain outcome categories."""

    HIGH_YOGA = "HIGH_YOGA"
    MODERATE_YOGA = "MODERATE_YOGA"
    NO_YOGA = "NO_YOGA"

"""Numerology JRE — Deterministic fact containers for Pythagorean numerology.

All dataclasses are frozen and use SHA-256 deterministic IDs.  No
interpretation is performed here — only fact definitions and pure
computational helpers.

Sources: Pythagorean tradition, Cheiro (Lord of Numbers),
    Dan Millman (The Life You Were Born to Live).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# ── Letter-to-Number Mapping (Pythagorean) ───────────────────────────────────

_PYTHAGOREAN_MAP: dict[str, int] = {
    "A": 1, "J": 1, "S": 1,
    "B": 2, "K": 2, "T": 2,
    "C": 3, "L": 3, "U": 3,
    "D": 4, "M": 4, "V": 4,
    "E": 5, "N": 5, "W": 5,
    "F": 6, "O": 6, "X": 6,
    "G": 7, "P": 7, "Y": 7,
    "H": 8, "Q": 8, "Z": 8,
    "I": 9, "R": 9,
}


def reduce_to_single_digit(n: int) -> int:
    """Reduce a number to a single digit by summing digits repeatedly.

    Master numbers (11, 22, 33) are preserved when they appear as
    the final reduction result.

    Args:
        n: The integer to reduce.

    Returns:
        A single digit (1-9) or a master number (11, 22, 33).
    """
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(abs(n)))
    return n


def reduce_string_to_number(s: str) -> int:
    """Reduce a string to a number using Pythagorean letter values.

    Converts each letter to its Pythagorean value, sums them,
    then reduces to a single digit (preserving master numbers).

    Args:
        s: The input string (case-insensitive, non-alpha chars skipped).

    Returns:
        A single digit (1-9) or master number (11, 22, 33).
    """
    total = 0
    for ch in s.upper():
        val = _PYTHAGOREAN_MAP.get(ch)
        if val is not None:
            total += val
    return reduce_to_single_digit(total)


# ── Enums ────────────────────────────────────────────────────────────────────


class NumerologySystem(StrEnum):
    """Numerology calculation system."""

    PYTHAGOREAN = "PYTHAGOREAN"
    CHALDEAN = "CHALDEAN"


class LifePathType(StrEnum):
    """Classification of Life Path number."""

    LEADER = "LEADER"
    BUILDER = "BUILDER"
    COMMUNICATOR = "COMMUNICATOR"
    NURTURER = "NURTURER"
    FREEDOM_SEEKER = "FREEDOM_SEEKER"
    HARMONIZER = "HARMONIZER"
    THINKER = "THINKER"
    POWERFUL = "POWERFUL"
    HUMANITARIAN = "HUMANITARIAN"
    MASTER_11 = "MASTER_11"
    MASTER_22 = "MASTER_22"
    MASTER_33 = "MASTER_33"


# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class LifePathNumber:
    """Life Path Number — calculated from birth date.

    Derived from the sum of all digits in the full birth date,
    reduced to a single digit (or master number).

    Source: Pythagorean tradition, Cheiro Ch. 1.
    """

    raw_sum: int  # Sum before final reduction
    reduced: int  # Final Life Path number (1-9, 11, 22, 33)
    life_path_type: LifePathType
    calculation_steps: tuple[int, ...]  # Step-by-step reduction

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "raw_sum": self.raw_sum,
            "reduced": self.reduced,
            "life_path_type": self.life_path_type.value,
            "calculation_steps": list(self.calculation_steps),
        }


@dataclass(frozen=True)
class DestinyNumber:
    """Destiny/Expression Number — calculated from full birth name.

    Derived from the sum of all letter values in the full name,
    reduced to a single digit (or master number).

    Source: Pythagorean tradition, Cheiro Ch. 2.
    """

    full_name: str
    raw_sum: int
    reduced: int
    letter_values: dict[str, int]  # Letter -> Pythagorean value

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "full_name": self.full_name,
            "raw_sum": self.raw_sum,
            "reduced": self.reduced,
            "letter_values": self.letter_values,
        }


@dataclass(frozen=True)
class PersonalYearNumber:
    """Personal Year Number — calculated for a specific year.

    Derived from the sum of birth month + birth day + target year,
    reduced to a single digit.

    Source: Pythagorean tradition, Dan Millman Ch. 3.
    """

    birth_month: int
    birth_day: int
    target_year: int
    raw_sum: int
    reduced: int

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "birth_month": self.birth_month,
            "birth_day": self.birth_day,
            "target_year": self.target_year,
            "raw_sum": self.raw_sum,
            "reduced": self.reduced,
        }


@dataclass(frozen=True)
class NumerologyChart:
    """Complete numerology chart — pure deterministic facts.

    Contains all calculated numerology numbers for a given birth data.
    No interpretation is performed.
    """

    birth_date: str  # ISO date string (YYYY-MM-DD)
    birth_name: str  # Full birth name
    system: NumerologySystem = NumerologySystem.PYTHAGOREAN

    life_path: LifePathNumber | None = None
    destiny: DestinyNumber | None = None
    personal_year: PersonalYearNumber | None = None

    deterministic_id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_chart_id(self)
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        result: dict[str, Any] = {
            "birth_date": self.birth_date,
            "birth_name": self.birth_name,
            "system": self.system.value,
            "life_path": self.life_path.to_dict() if self.life_path else None,
            "destiny": self.destiny.to_dict() if self.destiny else None,
            "personal_year": (
                self.personal_year.to_dict() if self.personal_year else None
            ),
            "deterministic_id": self.deterministic_id,
        }
        return result


def _compute_chart_id(chart: NumerologyChart) -> str:
    """SHA-256 deterministic ID from chart contents."""
    payload = json.dumps(chart.to_dict(), sort_keys=True, separators=(",", ":"))
    cleaned = payload.replace(f'"{chart.deterministic_id}"', '""')
    return hashlib.sha256(cleaned.encode()).hexdigest()[:16]

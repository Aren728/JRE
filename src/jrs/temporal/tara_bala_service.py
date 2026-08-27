"""JRS Tara Bala Service — Nakshatra-based Strength Calculation (TA-020–021).

Evaluates the Nakshatra position of a transiting planet relative to the
natal Moon Nakshatra using the 9-Tara (Nakshatra) cycle.

Per RI-010D TA-020–021:
- 9 Tara positions from Janma (1) to Parama Mitra (9).
- Even-numbered Taras are generally favorable.
- Odd-numbered Taras (except 1) are generally unfavorable.

Tara Classification (from Phaladeepika and BPHS):
1. Janma (1)     — Neutral (self)
2. Sampat (2)     — Favorable (wealth)
3. Vipat (3)      — Unfavorable (danger)
4. Kshema (4)     — Favorable (well-being)
5. Pratyak (5)    — Unfavorable (obstacles)
6. Sadhana (6)    — Favorable (achievement)
7. Naidhana (7)   — Unfavorable (death/danger)
8. Mitra (8)      — Favorable (friendship)
9. Parama Mitra (9) — Favorable (great friendship)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TaraStrength(StrEnum):
    """Tara Bala classification."""

    FAVORABLE = "FAVORABLE"
    UNFAVORABLE = "UNFAVORABLE"
    NEUTRAL = "NEUTRAL"


# 9 Tara names indexed by position (1-based)
TARA_NAMES: tuple[str, ...] = (
    "",  # placeholder for 0
    "Janma",
    "Sampat",
    "Vipat",
    "Kshema",
    "Pratyak",
    "Sadhana",
    "Naidhana",
    "Mitra",
    "Parama Mitra",
)

# Favorable Taras: 2, 4, 6, 8, 9 (even + Parama Mitra)
FAVORABLE_TARAS: frozenset[int] = frozenset({2, 4, 6, 8, 9})

# Unfavorable Taras: 3, 5, 7
UNFAVORABLE_TARAS: frozenset[int] = frozenset({3, 5, 7})

# Neutral: 1 (Janma)
NEUTRAL_TARAS: frozenset[int] = frozenset({1})

# Standard 27 Nakshatras in order
_NAKSHATRAS: tuple[str, ...] = (
    "ASHWINI", "BHARANI", "KRITTIKA", "ROHINI", "MRIGASHIRA",
    "ARDRA", "PUNARVASU", "PUSHYA", "ASHLESHA", "MAGHA",
    "PURVA_PHALGUNI", "UTTARA_PHALGUNI", "HASTA", "CHITRA",
    "SWATI", "VISHAKHA", "ANURADHA", "JYESHTHA", "MULA",
    "PURVA_SHADHA", "UTTARA_SHADHA", "SHRAVANA", "DHANISHTA",
    "SHATABHISHA", "PURVA_BHADRAPADA", "UTTARA_BHADRAPADA", "REVATI",
)


@dataclass(frozen=True)
class TaraResult:
    """Result of Tara Bala evaluation.

    Attributes:
        tara_position: 1-based Tara position (1–9).
        tara_name: Name of the Tara (Janma, Sampat, etc.).
        strength: FAVORABLE, UNFAVORABLE, or NEUTRAL.
        transit_nakshatra: Nakshatra of the transiting planet.
        natal_moon_nakshatra: Nakshatra of the natal Moon.
        reason: Explanation of the classification.
    """

    tara_position: int
    tara_name: str
    strength: TaraStrength
    transit_nakshatra: str = ""
    natal_moon_nakshatra: str = ""
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "tara_position": self.tara_position,
            "tara_name": self.tara_name,
            "strength": self.strength.value,
            "transit_nakshatra": self.transit_nakshatra,
            "natal_moon_nakshatra": self.natal_moon_nakshatra,
            "reason": self.reason,
        }


class TaraBalaService:
    """Evaluates Tara Bala for transiting planets relative to natal Moon.

    Per Phaladeepika and RI-010D TA-020–021:
    - Count Nakshatras from natal Moon to transit planet.
    - Result mod 9 gives the Tara position.
    - Even Taras (2,4,6,8) + 9 are favorable.
    - Odd Taras (3,5,7) are unfavorable.
    - Tara 1 (Janma) is neutral.
    """

    def evaluate_tara_bala(
        self,
        transit_nakshatra: str,
        natal_moon_nakshatra: str,
    ) -> TaraResult:
        """Evaluate Tara Bala for a transiting planet.

        Args:
            transit_nakshatra: Nakshatra of the transiting planet.
            natal_moon_nakshatra: Nakshatra of the natal Moon.

        Returns:
            TaraResult with Tara position and strength classification.
        """
        # Find Nakshatra indices
        transit_idx = self._nakshatra_index(transit_nakshatra)
        moon_idx = self._nakshatra_index(natal_moon_nakshatra)

        if transit_idx is None or moon_idx is None:
            return TaraResult(
                tara_position=0,
                tara_name="Unknown",
                strength=TaraStrength.NEUTRAL,
                transit_nakshatra=transit_nakshatra,
                natal_moon_nakshatra=natal_moon_nakshatra,
                reason="Unable to determine Nakshatra positions",
            )

        # Calculate Tara: count from Moon Nakshatra to Transit Nakshatra
        # (transit - moon + 27) mod 27 + 1 gives 1-based position
        raw_tara = ((transit_idx - moon_idx + 27) % 27) + 1

        # Map to 1–9 cycle: Tara position = (raw_tara - 1) mod 9 + 1
        tara_pos = ((raw_tara - 1) % 9) + 1

        # Classify
        if tara_pos in FAVORABLE_TARAS:
            strength = TaraStrength.FAVORABLE
        elif tara_pos in UNFAVORABLE_TARAS:
            strength = TaraStrength.UNFAVORABLE
        else:
            strength = TaraStrength.NEUTRAL

        tara_name = TARA_NAMES[tara_pos] if 1 <= tara_pos <= 9 else "Unknown"

        return TaraResult(
            tara_position=tara_pos,
            tara_name=tara_name,
            strength=strength,
            transit_nakshatra=transit_nakshatra,
            natal_moon_nakshatra=natal_moon_nakshatra,
            reason=(
                f"Tara {tara_pos} ({tara_name}): {transit_nakshatra} "
                f"from {natal_moon_nakshatra} → {strength.value}"
            ),
        )

    def get_tara_multiplier(
        self,
        tara_result: TaraResult,
    ) -> float:
        """Get a strength multiplier based on Tara Bala.

        Per RI-010D TA-021:
        - Favorable: multiplier 1.0–1.2
        - Neutral: multiplier 1.0
        - Unfavorable: multiplier 0.6–0.8

        Args:
            tara_result: The TaraResult to evaluate.

        Returns:
            Strength multiplier (0.0 to 1.2).
        """
        if tara_result.strength == TaraStrength.FAVORABLE:
            # Favorable Taras get 1.0–1.2 multiplier
            # Parama Mitra (9) gets highest
            if tara_result.tara_position == 9:
                return 1.2
            return 1.0
        elif tara_result.strength == TaraStrength.UNFAVORABLE:
            # Unfavorable Taras get 0.6–0.8 multiplier
            # Naidhana (7) gets lowest
            if tara_result.tara_position == 7:
                return 0.6
            if tara_result.tara_position == 3:
                return 0.7
            return 0.8  # Pratyak (5)
        else:
            # Neutral (Janma)
            return 1.0

    def _nakshatra_index(self, nakshatra: str) -> int | None:
        """Get the 0-based index of a Nakshatra."""
        try:
            return _NAKSHATRAS.index(nakshatra.upper())
        except (ValueError, AttributeError):
            return None

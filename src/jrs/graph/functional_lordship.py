"""JRS Graph — Functional Lordship Classifier (RI-011 Phase B).

Implements BPHS Chapter 34 classification of functional planetary roles
relative to a given Lagna sign. Classifies each planet as YOGAKARAKA,
BENEFIC, NEUTRAL, or MALEFIC based on house ownership pattern and
dignity, then assigns a base weight for chain propagation.

Source: Brihat Parashara Hora Shastra (BPHS) Chapter 34.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Optional


# ── Constants ─────────────────────────────────────────────────────────────────

# Standard Vimshottari sign ownership: 1-indexed rashi number → owning planet.
_SIGN_LORDS: dict[int, str] = {
    1: "MARS",
    2: "VENUS",
    3: "MERCURY",
    4: "MOON",
    5: "SUN",
    6: "MERCURY",
    7: "VENUS",
    8: "MARS",
    9: "JUPITER",
    10: "SATURN",
    11: "SATURN",
    12: "JUPITER",
}

# Kendra (angle) houses: 1, 4, 7, 10
KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})

# Trikona (trine) houses: 1, 5, 9
TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})

# Dusthana (malefic) houses: 6, 8, 12
DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})

# Natural benefic planets (BPHS Ch 2)
NATURAL_BENEFICS: frozenset[str] = frozenset({"JUPITER", "VENUS", "MOON", "MERCURY"})

# Natural malefic planets (BPHS Ch 2)
NATURAL_MALEFICS: frozenset[str] = frozenset({"SUN", "MARS", "SATURN", "RAHU", "KETU"})

# All seven classical planets
_ALL_PLANETS: tuple[str, ...] = ("SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN")


# ── Enums ─────────────────────────────────────────────────────────────────────

class FunctionalRole(StrEnum):
    """Functional role of a planet relative to the Lagna."""

    YOGAKARAKA = "YOGAKARAKA"
    BENEFIC = "BENEFIC"
    NEUTRAL = "NEUTRAL"
    MALEFIC = "MALEFIC"


# ── Functional Role Base Weights ──────────────────────────────────────────────

_ROLE_WEIGHTS: dict[FunctionalRole, float] = {
    FunctionalRole.YOGAKARAKA: 1.50,
    FunctionalRole.BENEFIC: 1.00,
    FunctionalRole.NEUTRAL: 0.00,
    FunctionalRole.MALEFIC: -1.00,
}


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LordshipProfile:
    """Immutable result of functional lordship classification.

    Attributes:
        planet: Planet name (e.g., ``"MARS"``).
        lagna_sign: Lagna sign number (1–12, Aries=1).
        owned_houses: Tuple of house numbers owned by this planet relative
            to the Lagna.
        functional_role: Classified functional role.
        base_weight: Numeric weight derived from the functional role.
        description: Human-readable explanation of the classification.
    """

    planet: str
    lagna_sign: int
    owned_houses: tuple[int, ...]
    functional_role: FunctionalRole
    base_weight: float
    description: str


# ── Classifier ────────────────────────────────────────────────────────────────

class FunctionalLordshipClassifier:
    """Classify the functional role of a planet relative to a given Lagna.

    Implements BPHS Chapter 34 rules:

    1. **Yogakaraka** — Mars for Cancer/Leo Lagna; Saturn for Taurus/Libra
       Lagna; or any planet owning both a Kendra and Trikona without being
       the Lagna lord.
    2. **Functional Benefic** — Trikona lord (1st, 5th, or 9th house) without
       8th house (Dusthana) ownership.
    3. **Functional Malefic** — 8th lord (when not also 1st lord), 6th/12th
       lord, or natural benefic with Kendradhipati Dosha (owning Kendra
       without Trikona).
    4. **Neutral / Maraka** — 2nd/7th lord with neutral secondary lordship.

    The classification priority is: Yogakaraka > Benefic > Malefic > Neutral.
    """

    def classify(self, planet: str, lagna_sign: int) -> LordshipProfile:
        """Classify the functional role of *planet* for *lagna_sign*.

        Args:
            planet: Uppercase planet name (e.g., ``"MARS"``).
            lagna_sign: Lagna sign number (1–12, Aries=1).

        Returns:
            Immutable ``LordshipProfile`` with classification and weight.

        Raises:
            ValueError: If *lagna_sign* is outside 1–12 or *planet* is unknown.
        """
        if not 1 <= lagna_sign <= 12:
            raise ValueError(f"lagna_sign must be 1–12, got {lagna_sign}")
        planet = planet.upper()
        if planet not in _ALL_PLANETS:
            raise ValueError(f"Unknown planet: {planet}")

        owned_houses = self._compute_owned_houses(planet, lagna_sign)
        owned_set = frozenset(owned_houses)

        # Determine functional role via BPHS Ch 34 priority cascade
        role, description = self._determine_role(planet, lagna_sign, owned_set)

        return LordshipProfile(
            planet=planet,
            lagna_sign=lagna_sign,
            owned_houses=owned_houses,
            functional_role=role,
            base_weight=_ROLE_WEIGHTS[role],
            description=description,
        )

    # ── House Ownership ───────────────────────────────────────────────────

    def _compute_owned_houses(self, planet: str, lagna_sign: int) -> tuple[int, ...]:
        """Compute which houses (relative to Lagna) the planet owns.

        Uses the formula: H(p) = ((S_owned - S_lagna) mod 12) + 1
        where S_owned is the sign number owned by the planet.

        Args:
            planet: Uppercase planet name.
            lagna_sign: Lagna sign number (1–12).

        Returns:
            Sorted tuple of owned house numbers.
        """
        owned_signs = [
            sign_num for sign_num, lord in _SIGN_LORDS.items() if lord == planet
        ]
        owned_houses = sorted(
            ((sign_num - lagna_sign) % 12) + 1 for sign_num in owned_signs
        )
        return tuple(owned_houses)

    # ── Role Determination ────────────────────────────────────────────────

    def _determine_role(
        self,
        planet: str,
        lagna_sign: int,
        owned_set: frozenset[int],
    ) -> tuple[FunctionalRole, str]:
        """Determine functional role using BPHS Ch 34 priority cascade.

        Priority: Yogakaraka > Benefic > Malefic > Neutral.

        Args:
            planet: Uppercase planet name.
            lagna_sign: Lagna sign number (1–12).
            owned_set: Set of house numbers owned by the planet.

        Returns:
            Tuple of (FunctionalRole, description string).
        """
        lagna_house = 1

        # ── Check Yogakaraka ──────────────────────────────────────────────
        role, desc = self._check_yogakaraka(planet, lagna_sign, owned_set, lagna_house)
        if role is not None:
            return role, desc

        # ── Check Functional Malefic ──────────────────────────────────────
        role, desc = self._check_malefic(planet, owned_set, lagna_house)
        if role is not None:
            return role, desc

        # ── Check Functional Benefic ──────────────────────────────────────
        role, desc = self._check_benefic(planet, owned_set)
        if role is not None:
            return role, desc

        # ── Default: Neutral ──────────────────────────────────────────────
        return FunctionalRole.NEUTRAL, f"{planet} is functionally neutral"

    def _check_yogakaraka(
        self,
        planet: str,
        lagna_sign: int,
        owned_set: frozenset[int],
        lagna_house: int,
    ) -> tuple[Optional[FunctionalRole], Optional[str]]:
        """Check if planet qualifies as Yogakaraka (BPHS Ch 34).

        Rules:
        - Mars is Yogakaraka for Cancer (4) / Leo (5) Lagna.
        - Saturn is Yogakaraka for Taurus (2) / Libra (7) Lagna.
        - General rule: planet owns both a Kendra and Trikona, is NOT
          the Lagna lord, and does not own Lagna as sole Trikona.

        Returns:
            (YOGAKARAKA, description) if matched, else (None, None).
        """
        # Specific Yogakaraka rules (BPHS Ch 34)
        if planet == "MARS" and lagna_sign in {4, 5}:
            return FunctionalRole.YOGAKARAKA, (
                f"Mars is Yogakaraka for {self._sign_name(lagna_sign)} Lagna "
                f"(owns houses {owned_set})"
            )
        if planet == "SATURN" and lagna_sign in {2, 7}:
            return FunctionalRole.YOGAKARAKA, (
                f"Saturn is Yogakaraka for {self._sign_name(lagna_sign)} Lagna "
                f"(owns houses {owned_set})"
            )

        # General Yogakaraka: owns both Kendra and Trikona
        owns_kendra = bool(owned_set & KENDRA_HOUSES)
        owns_trikona = bool(owned_set & TRIKONA_HOUSES)

        if owns_kendra and owns_trikona:
            is_lagna_lord = lagna_house in owned_set
            if not is_lagna_lord:
                # Check: Lagna is not the sole Trikona owned by this planet
                trikona_owned = owned_set & TRIKONA_HOUSES
                owns_lagna = lagna_house in owned_set
                if not (len(trikona_owned) == 1 and owns_lagna):
                    return FunctionalRole.YOGAKARAKA, (
                        f"{planet} is Yogakaraka: owns both Kendra and Trikona "
                        f"houses {owned_set}"
                    )

        return None, None

    def _check_malefic(
        self,
        planet: str,
        owned_set: frozenset[int],
        lagna_house: int,
    ) -> tuple[Optional[FunctionalRole], Optional[str]]:
        """Check if planet qualifies as Functional Malefic (BPHS Ch 34).

        Rules:
        - 8th house lord (when not also 1st lord).
        - 6th or 12th house lord.
        - Natural benefic with Kendradhipati Dosha (owns Kendra, no Trikona).

        Returns:
            (MALEFIC, description) if matched, else (None, None).
        """
        owns_1st = lagna_house in owned_set
        owns_8th = 8 in owned_set
        owns_6th = 6 in owned_set
        owns_12th = 12 in owned_set

        # 8th lord (exception: if also 1st lord, treated as functional benefic)
        if owns_8th and not owns_1st:
            return FunctionalRole.MALEFIC, (
                f"{planet} is functional malefic as 8th house lord "
                f"(owns houses {owned_set})"
            )

        # 6th or 12th lord
        if owns_6th:
            return FunctionalRole.MALEFIC, (
                f"{planet} is functional malefic as 6th house lord "
                f"(owns houses {owned_set})"
            )
        if owns_12th:
            return FunctionalRole.MALEFIC, (
                f"{planet} is functional malefic as 12th house lord "
                f"(owns houses {owned_set})"
            )

        # Kendradhipati Dosha: natural benefic owning Kendra without Trikona
        if planet in NATURAL_BENEFICS:
            owns_kendra = bool(owned_set & KENDRA_HOUSES)
            owns_trikona = bool(owned_set & TRIKONA_HOUSES)
            if owns_kendra and not owns_trikona:
                return FunctionalRole.MALEFIC, (
                    f"{planet} is functional malefic (Kendradhipati Dosha): "
                    f"natural benefic owning Kendra {owned_set & KENDRA_HOUSES} "
                    f"without Trikona"
                )

        return None, None

    def _check_benefic(
        self,
        planet: str,
        owned_set: frozenset[int],
    ) -> tuple[Optional[FunctionalRole], Optional[str]]:
        """Check if planet qualifies as Functional Benefic (BPHS Ch 34).

        Rules:
        - Trikona lord (1st, 5th, or 9th) without owning the 8th house.

        Returns:
            (BENEFIC, description) if matched, else (None, None).
        """
        owns_trikona = bool(owned_set & TRIKONA_HOUSES)
        owns_8th = 8 in owned_set

        if owns_trikona and not owns_8th:
            trikona_houses = owned_set & TRIKONA_HOUSES
            return FunctionalRole.BENEFIC, (
                f"{planet} is functional benefic as Trikona lord "
                f"(houses {trikona_houses})"
            )

        return None, None

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _sign_name(sign_num: int) -> str:
        """Return Western name for a 1-indexed sign number."""
        names = {
            1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
            5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
            9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces",
        }
        return names.get(sign_num, f"Sign-{sign_num}")

    def classify_all(self, lagna_sign: int) -> dict[str, LordshipProfile]:
        """Classify all seven classical planets for a given Lagna.

        Args:
            lagna_sign: Lagna sign number (1–12).

        Returns:
            Dict mapping planet name to its LordshipProfile.
        """
        return {planet: self.classify(planet, lagna_sign) for planet in _ALL_PLANETS}

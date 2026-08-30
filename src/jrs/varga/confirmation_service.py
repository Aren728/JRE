"""JRS-078 Varga Confirmation Service — D9 Navamsha Confirmation Logic.

Implements classical D9 (Navamsha) confirmation rules for yoga evaluation:

- Kendra/Trikona confirmation: Planets in Kendra (1,4,7,10) or Trikona (1,5,9)
  in D9 confirm the yoga's strength.
- Debilitation cancellation: If any yoga-forming planet is debilitated in D9,
  the yoga is cancelled (binary).
- Vargottama detection: If a planet's D1 sign == D9 sign, it gains a 2.0x
  strength multiplier.
- D10 (career) and D7 (progeny) specialized evaluation.

Source: BPHS Ch 35 (Navamsha); Jataka Parijata Ch 2; Phaladeepika Ch 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Optional


class ConfirmationStatus(StrEnum):
    """Status after D9 confirmation check."""
    FORMED = "FORMED"
    CANCELLED = "CANCELLED"
    WEAKENED = "WEAKENED"


class ConfirmationStrength(StrEnum):
    """Strength classification after D9 confirmation."""
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


@dataclass(frozen=True)
class VargaConfirmationResult:
    """Result of D9 confirmation evaluation for a yoga."""
    confirmation_status: ConfirmationStatus
    strength: ConfirmationStrength
    kendra_trikona_count: int
    total_planets: int
    vargottama_planets: tuple[str, ...] = ()
    vargottama_multiplier: float = 1.0
    net_strength_multiplier: float = 1.0
    cancellation_reason: Optional[str] = None
    is_d10_career_strong: bool = False
    is_d7_progeny_strong: bool = False


# House classification constants
_KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})
_TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})
_KENDRA_OR_TRIKONA: frozenset[int] = _KENDRA_HOUSES | _TRIKONA_HOUSES

# D10 exaltation/own signs for career strength check
_D10_EXALTATION: dict[str, str] = {
    "SUN": "MESHA",
    "MOON": "VRISHABHA",
    "MARS": "MAKARA",
    "MERCURY": "KANYA",
    "JUPITER": "KARKA",
    "VENUS": "MEENA",
    "SATURN": "TULA",
}

_D10_OWN_SIGNS: dict[str, tuple[str, ...]] = {
    "SUN": ("SIMHA",),
    "MOON": ("KARKA",),
    "MARS": ("VRISHCHIKA", "MESHA"),
    "MERCURY": ("KANYA", "MITHUNA"),
    "JUPITER": ("DHANUSHA", "MEENA"),
    "VENUS": ("TULA", "VRISHABHA"),
    "SATURN": ("KUMBHA", "MAKARA"),
}

# D7 exaltation/own signs for progeny strength check
_D7_EXALTATION: dict[str, str] = {
    "SUN": "MESHA",
    "MOON": "VRISHABHA",
    "MARS": "MAKARA",
    "MERCURY": "KANYA",
    "JUPITER": "KARKA",
    "VENUS": "MEENA",
    "SATURN": "TULA",
}

_D7_OWN_SIGNS: dict[str, tuple[str, ...]] = {
    "SUN": ("SIMHA",),
    "MOON": ("KARKA",),
    "MARS": ("VRISHCHIKA", "MESHA"),
    "MERCURY": ("KANYA", "MITHUNA"),
    "JUPITER": ("DHANUSHA", "MEENA"),
    "VENUS": ("TULA", "VRISHABHA"),
    "SATURN": ("KUMBHA", "MAKARA"),
}


class VargaConfirmationService:
    """D9 Navamsha confirmation for yoga strength evaluation.

    Implements the classical D9 confirmation hierarchy:
    1. Debilitation in D9 → binary cancellation (if any planet debilitated).
    2. Kendra/Trikona in D9 → confirmation strength classification.
    3. Vargottama → 2.0x strength multiplier.
    4. D10/D7 specialized checks.
    """

    def evaluate_d9_confirmation(
        self,
        involved_planets: list[str],
        jre_facts: dict[str, Any],
    ) -> VargaConfirmationResult:
        """Evaluate D9 confirmation for yoga-forming planets.

        Args:
            involved_planets: Planet names involved in the yoga.
            jre_facts: JRE facts dictionary. Expected keys:
                - ``planets``: dict of planet data (D1 info)
                - ``planet_d9_sign``: {PLANET: D9 sign name}
                - ``planet_d9_house``: {PLANET: D9 house number (from Lagna)}

        Returns:
            VargaConfirmationResult with status, strength, and multipliers.
        """
        total = len(involved_planets)
        if total == 0:
            return VargaConfirmationResult(
                confirmation_status=ConfirmationStatus.FORMED,
                strength=ConfirmationStrength.WEAK,
                kendra_trikona_count=0,
                total_planets=0,
            )

        d9_signs = jre_facts.get("planet_d9_sign", {})
        d9_houses = jre_facts.get("planet_d9_house", {})
        d1_signs = jre_facts.get("planets", {})

        # ── Check for D9 debilitation → binary cancellation ──
        # BPHS Ch 35: Debilitation in Navamsha destroys yoga results
        # Uses sign-based check (not house-position proxy)
        for planet in involved_planets:
            d9_sign = d9_signs.get(planet, "")
            if d9_sign and self._is_debilitated_in_d9(planet, d9_sign):
                return VargaConfirmationResult(
                    confirmation_status=ConfirmationStatus.CANCELLED,
                    strength=ConfirmationStrength.WEAK,
                    kendra_trikona_count=0,
                    total_planets=total,
                    cancellation_reason=(
                        f"{planet} debilitated in D9 (Navamsha)"
                    ),
                )

        # ── Count Kendra/Trikona placements in D9 ──
        kt_count = 0
        for planet in involved_planets:
            d9_house = d9_houses.get(planet)
            if isinstance(d9_house, int) and d9_house in _KENDRA_OR_TRIKONA:
                kt_count += 1

        # ── Classification ──
        if kt_count == total:
            strength = ConfirmationStrength.STRONG
        elif kt_count > 0:
            strength = ConfirmationStrength.MODERATE
        else:
            strength = ConfirmationStrength.WEAK

        # ── Vargottama detection ──
        # Jataka Parijata: D1 sign == D9 sign → Vargottama (2.0x multiplier)
        vargottama_planets: list[str] = []
        for planet in involved_planets:
            d9_sign = d9_signs.get(planet)
            planet_data = d1_signs.get(planet, {})
            d1_sign = planet_data.get("rashi")
            if d9_sign and d1_sign and d9_sign == d1_sign:
                vargottama_planets.append(planet)

        vargottama_multiplier = 2.0 if vargottama_planets else 1.0

        # ── Net strength multiplier ──
        # Base multiplier from classification
        if strength == ConfirmationStrength.STRONG:
            base = 1.5
        elif strength == ConfirmationStrength.MODERATE:
            base = 1.0
        else:
            base = 0.7

        net_multiplier = base * vargottama_multiplier

        # ── D10 and D7 specialized checks ──
        is_d10_strong = self._check_d10_career(involved_planets, jre_facts)
        is_d7_strong = self._check_d7_progeny(involved_planets, jre_facts)

        return VargaConfirmationResult(
            confirmation_status=ConfirmationStatus.FORMED,
            strength=strength,
            kendra_trikona_count=kt_count,
            total_planets=total,
            vargottama_planets=tuple(vargottama_planets),
            vargottama_multiplier=vargottama_multiplier,
            net_strength_multiplier=net_multiplier,
            is_d10_career_strong=is_d10_strong,
            is_d7_progeny_strong=is_d7_strong,
        )

    def evaluate_d10_career(
        self,
        involved_planets: list[str],
        jre_facts: dict[str, Any],
    ) -> VargaConfirmationResult:
        """Evaluate D10 (Dashamsha) confirmation for career yogas.

        Checks D10 positions for career-strengthening factors.

        Args:
            involved_planets: Planet names involved in the yoga.
            jre_facts: JRE facts dictionary with ``planet_d10_sign``.

        Returns:
            VargaConfirmationResult for D10 career confirmation.
        """
        total = len(involved_planets)
        if total == 0:
            return VargaConfirmationResult(
                confirmation_status=ConfirmationStatus.FORMED,
                strength=ConfirmationStrength.WEAK,
                kendra_trikona_count=0,
                total_planets=0,
            )

        d10_signs = jre_facts.get("planet_d10_sign", {})
        kt_count = 0

        for planet in involved_planets:
            d10_sign = d10_signs.get(planet)
            if d10_sign:
                # Check if D10 sign is own/exaltation → strong career indicator
                exalt = _D10_EXALTATION.get(planet, "")
                owns = _D10_OWN_SIGNS.get(planet, ())
                if d10_sign == exalt or d10_sign in owns:
                    kt_count += 1

        if kt_count == total:
            strength = ConfirmationStrength.STRONG
        elif kt_count > 0:
            strength = ConfirmationStrength.MODERATE
        else:
            strength = ConfirmationStrength.WEAK

        return VargaConfirmationResult(
            confirmation_status=ConfirmationStatus.FORMED,
            strength=strength,
            kendra_trikona_count=kt_count,
            total_planets=total,
            net_strength_multiplier=1.0,
        )

    def evaluate_d7_progeny(
        self,
        involved_planets: list[str],
        jre_facts: dict[str, Any],
    ) -> VargaConfirmationResult:
        """Evaluate D7 (Saptamamsha) confirmation for progeny yogas.

        Checks D7 positions for progeny-strengthening factors.

        Args:
            involved_planets: Planet names involved in the yoga.
            jre_facts: JRE facts dictionary with ``planet_d7_sign``.

        Returns:
            VargaConfirmationResult for D7 progeny confirmation.
        """
        total = len(involved_planets)
        if total == 0:
            return VargaConfirmationResult(
                confirmation_status=ConfirmationStatus.FORMED,
                strength=ConfirmationStrength.WEAK,
                kendra_trikona_count=0,
                total_planets=0,
            )

        d7_signs = jre_facts.get("planet_d7_sign", {})
        kt_count = 0

        for planet in involved_planets:
            d7_sign = d7_signs.get(planet)
            if d7_sign:
                exalt = _D7_EXALTATION.get(planet, "")
                owns = _D7_OWN_SIGNS.get(planet, ())
                if d7_sign == exalt or d7_sign in owns:
                    kt_count += 1

        if kt_count == total:
            strength = ConfirmationStrength.STRONG
        elif kt_count > 0:
            strength = ConfirmationStrength.MODERATE
        else:
            strength = ConfirmationStrength.WEAK

        return VargaConfirmationResult(
            confirmation_status=ConfirmationStatus.FORMED,
            strength=strength,
            kendra_trikona_count=kt_count,
            total_planets=total,
            net_strength_multiplier=1.0,
        )

    # ── Private helpers ──

    def _check_d10_career(
        self,
        involved_planets: list[str],
        jre_facts: dict[str, Any],
    ) -> bool:
        """Check if D10 (Dashamsha) career indicators are strong.

        A planet is career-strong in D10 if its D10 sign is its own or
        exaltation sign.
        """
        d10_signs = jre_facts.get("planet_d10_sign", {})
        if not d10_signs:
            return False
        for planet in involved_planets:
            d10_sign = d10_signs.get(planet)
            if d10_sign:
                exalt = _D10_EXALTATION.get(planet, "")
                owns = _D10_OWN_SIGNS.get(planet, ())
                if d10_sign == exalt or d10_sign in owns:
                    return True
        return False

    def _check_d7_progeny(
        self,
        involved_planets: list[str],
        jre_facts: dict[str, Any],
    ) -> bool:
        """Check if D7 (Saptamamsha) progeny indicators are strong.

        A planet is progeny-strong in D7 if its D7 sign is its own or
        exaltation sign.
        """
        d7_signs = jre_facts.get("planet_d7_sign", {})
        if not d7_signs:
            return False
        for planet in involved_planets:
            d7_sign = d7_signs.get(planet)
            if d7_sign:
                exalt = _D7_EXALTATION.get(planet, "")
                owns = _D7_OWN_SIGNS.get(planet, ())
                if d7_sign == exalt or d7_sign in owns:
                    return True
        return False

    # BPHS classical debilitation signs (Neecha signs)
    _DEBILITATION_SIGN: dict[str, str] = {
        "SUN": "TULA",
        "MOON": "VRISHCHIKA",
        "MARS": "KARKA",
        "MERCURY": "MEENA",
        "JUPITER": "MAKARA",
        "VENUS": "KANYA",
        "SATURN": "MESHA",
    }

    @staticmethod
    def _is_debilitated_in_d9(planet: str, d9_sign: str) -> bool:
        """Check if a planet is debilitated in D9 (Navamsha).

        Uses the classical debilitation sign mapping from BPHS:
          Sun  = TULA (Libra)
          Moon = VRISHCHIKA (Scorpio)
          Mars = KARKA (Cancer)
          Mercury = MEENA (Pisces)
          Jupiter = MAKARA (Capricorn)
          Venus = KANYA (Virgo)
          Saturn = MESHA (Aries)

        Args:
            planet: Planet name (e.g., "MERCURY").
            d9_sign: D9 sign name for the planet (e.g., "MEENA").

        Returns:
            True if the planet's D9 sign is its classical debilitation sign.
        """
        deb_sign = VargaConfirmationService._DEBILITATION_SIGN.get(planet)
        if deb_sign is None:
            return False
        return d9_sign == deb_sign

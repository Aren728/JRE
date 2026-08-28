"""Dynamic Temporal Service — pipeline integration layer (RI-012).

Combines static chain strength (Layer 1.5) with Vimshottari Dasha
and Transit multipliers to produce a dynamic strength score.

Formula:
    S_dynamic = S_static × M_dasha × M_transit

The result is clamped between 0.0 and 1.0.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .dasha_engine import DashaHierarchy, DashaMultiplierResult, VimshottariDashaEngine
from .transit_evaluator import TransitEvaluationResult, TransitEvaluator


# ── Constants ────────────────────────────────────────────────────────────────

_SCORE_MIN: float = 0.0
_SCORE_MAX: float = 1.0


# ── Data Structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DynamicStrengthResult:
    """Immutable result of dynamic temporal strength computation.

    Attributes:
        static_strength: Base static score from Layer 1.5 (0.0–1.0).
        dasha_multiplier: Vimshottari Dasha activation multiplier.
        transit_multiplier: Transit (Gochar) evaluation multiplier.
        dynamic_strength: Final dynamic score (clamped 0.0–1.0).
        active_dasha: Active Dasha hierarchy.
        transit_result: Transit evaluation details (if evaluated).
        dasha_match_level: Which Dasha level matched ('MD', 'AD', 'PD', 'NONE').
        dasha_match_planet: Which planet matched the Dasha (or empty).
    """

    static_strength: float
    dasha_multiplier: float
    transit_multiplier: float
    dynamic_strength: float
    active_dasha: DashaHierarchy | None = None
    transit_result: TransitEvaluationResult | None = None
    dasha_match_level: str = "NONE"
    dasha_match_planet: str = ""


# ── Dynamic Temporal Service ─────────────────────────────────────────────────


class DynamicTemporalService:
    """Pipeline integration service combining Dasha and Transit multipliers.

    Computes S_dynamic = S_static × M_dasha × M_transit, clamped to [0.0, 1.0].
    """

    def __init__(self) -> None:
        """Initialize with Dasha and Transit engines."""
        self._dasha_engine = VimshottariDashaEngine()
        self._transit_evaluator = TransitEvaluator()

    def compute_dynamic_strength(
        self,
        static_strength: float,
        target_timestamp: datetime,
        moon_nakshatra: str,
        moon_nakshatra_degree: float,
        yoga_planets: list[str],
        transit_houses: dict[str, int] | None = None,
        ashtakavarga_scores: dict[str, int] | None = None,
        natal_moon_house: int = 1,
    ) -> DynamicStrengthResult:
        """Compute dynamic strength from static score, Dasha, and Transit.

        Args:
            static_strength: Base static score from Layer 1.5 (0.0–1.0).
            target_timestamp: UTC timestamp to evaluate.
            moon_nakshatra: Moon's Nakshatra name (e.g., 'ASHWINI').
            moon_nakshatra_degree: Moon's degree within Nakshatra (0.0–360.0).
            yoga_planets: Planet names involved in the yoga.
            transit_houses: Optional mapping of planet → transit house (1–12).
            ashtakavarga_scores: Optional mapping of planet → AV bindus.
            natal_moon_house: House number of the natal Moon (1–12).

        Returns:
            DynamicStrengthResult with all multiplier details.
        """
        # Clamp static strength
        static_clamped = max(_SCORE_MIN, min(_SCORE_MAX, static_strength))

        # ── Dasha multiplier ──
        hierarchy = self._dasha_engine.compute_dasha_at(
            target_timestamp=target_timestamp,
            moon_nakshatra=moon_nakshatra,
            moon_nakshatra_degree=moon_nakshatra_degree,
        )
        dasha_result = self._dasha_engine.get_dasha_multiplier(
            hierarchy=hierarchy,
            yoga_planets=yoga_planets,
        )
        m_dasha = dasha_result.multiplier

        # ── Transit multiplier ──
        transit_result: TransitEvaluationResult | None = None
        m_transit: float = 1.0

        if transit_houses and ashtakavarga_scores is not None:
            transit_planets = list(transit_houses.keys())
            transit_result = self._transit_evaluator.evaluate_multiple(
                planets=transit_planets,
                transit_houses=transit_houses,
                ashtakavarga_scores=ashtakavarga_scores,
                natal_moon_house=natal_moon_house,
            )
            # Use aggregate multiplier only for planets involved in the yoga
            yoga_upper = {p.upper() for p in yoga_planets}
            relevant_profiles = [
                p for p in transit_result.profiles
                if p.planet in yoga_upper
            ]
            if relevant_profiles:
                m_transit = 1.0
                for p in relevant_profiles:
                    m_transit *= p.net_transit_multiplier

        # ── Dynamic score ──
        dynamic_raw = static_clamped * m_dasha * m_transit
        dynamic_clamped = max(_SCORE_MIN, min(_SCORE_MAX, dynamic_raw))

        return DynamicStrengthResult(
            static_strength=static_clamped,
            dasha_multiplier=m_dasha,
            transit_multiplier=m_transit,
            dynamic_strength=round(dynamic_clamped, 6),
            active_dasha=hierarchy,
            transit_result=transit_result,
            dasha_match_level=dasha_result.matched_level,
            dasha_match_planet=dasha_result.matched_planet,
        )

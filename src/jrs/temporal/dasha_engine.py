"""Vimshottari Dasha Engine — deterministic Dasha period calculation (RI-012).

Computes active Mahadasha (MD), Antardasha (AD), and Pratyantardasha (PD)
lords for a target timestamp given the Moon's Nakshatra position.

Vimshottari period durations (in years):
    Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16,
    Saturn=19, Mercury=17, Ketu=7, Venus=20
    Total = 120 years.

Activation multiplier logic:
    - MD lord matching a yoga planet → 1.50
    - AD lord matching a yoga planet → 1.25
    - PD lord matching a yoga planet → 1.10
    - No match (dormant) → 0.40
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

# ── Vimshottari Period Arrays ────────────────────────────────────────────────

# Classical Vimshottari Dasha order and durations (years)
VIMSHOTTARI_ORDER: tuple[str, ...] = (
    "KETU", "VENUS", "SUN", "MOON", "MARS",
    "RAHU", "JUPITER", "SATURN", "MERCURY",
)

VIMSHOTTARI_DURATIONS: dict[str, float] = {
    "SUN": 6.0,
    "MOON": 10.0,
    "MARS": 7.0,
    "RAHU": 18.0,
    "JUPITER": 16.0,
    "SATURN": 19.0,
    "MERCURY": 17.0,
    "KETU": 7.0,
    "VENUS": 20.0,
}

TOTAL_VIMSHOTTARI_YEARS: float = 120.0

# One Vimshottari cycle = 120 years in days
_VIMSHOTTARI_CYCLE_DAYS: float = TOTAL_VIMSHOTTARI_YEARS * 365.25

# Activation multiplier thresholds
_MD_MULTIPLIER: float = 1.50
_AD_MULTIPLIER: float = 1.25
_PD_MULTIPLIER: float = 1.10
_DORMANT_MULTIPLIER: float = 0.40


# ── Nakshatra-to-Dasha-Lord Mapping ─────────────────────────────────────────

# Each nakshatra's starting Dashalord (0-indexed position in Vimshottari cycle)
# 27 nakshatras, 9 lords repeated 3×
_NAKSHATRA_DASHA_START: dict[str, str] = {
    "ASHWINI": "KETU",
    "BHARANI": "VENUS",
    "KRITTIKA": "SUN",
    "ROHINI": "MOON",
    "MRIGASHIRA": "MARS",
    "ARDRA": "RAHU",
    "PUNARVASU": "JUPITER",
    "PUSHYA": "SATURN",
    "ASHLESHA": "MERCURY",
    "MAGHA": "KETU",
    "PURVA_PHALGUNI": "VENUS",
    "UTTARA_PHALGUNI": "SUN",
    "HASTA": "MOON",
    "CHITRA": "MARS",
    "SWATI": "RAHU",
    "VISHAKHA": "JUPITER",
    "ANURADHA": "SATURN",
    "JYESHTHA": "MERCURY",
    "MULA": "KETU",
    "PURVA_ASHADHA": "VENUS",
    "UTTARA_ASHADHA": "SUN",
    "SHRAVANA": "MOON",
    "DHANISHTHA": "MARS",
    "SHATABHISHA": "RAHU",
    "PURVA_BHADRAPADA": "JUPITER",
    "UTTARA_BHADRAPADA": "SATURN",
    "REVATI": "MERCURY",
}


# ── Data Structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DashaPeriod:
    """A single Vimshottari Dasha period (MD, AD, or PD).

    Attributes:
        lord: Planet name governing this period.
        period_type: 'MD', 'AD', or 'PD'.
        start_utc: Start of the period (datetime).
        end_utc: End of the period (datetime).
        duration_years: Duration in years (fractional).
    """

    lord: str
    period_type: str
    start_utc: datetime
    end_utc: datetime
    duration_years: float

    def contains(self, ts: datetime) -> bool:
        """Check if a timestamp falls within this period."""
        return self.start_utc <= ts < self.end_utc


@dataclass(frozen=True)
class DashaHierarchy:
    """Active Dasha hierarchy at a specific timestamp.

    Attributes:
        mahadasha: Active Mahadasha period.
        antardasha: Active Antardasha period.
        pratyantardasha: Active Pratyantardasha period.
    """

    mahadasha: DashaPeriod
    antardasha: DashaPeriod
    pratyantardasha: DashaPeriod

    @property
    def md_lord(self) -> str:
        """Mahadasha lord planet name."""
        return self.mahadasha.lord

    @property
    def ad_lord(self) -> str:
        """Antardasha lord planet name."""
        return self.antardasha.lord

    @property
    def pd_lord(self) -> str:
        """Pratyantardasha lord planet name."""
        return self.pratyantardasha.lord


@dataclass(frozen=True)
class DashaMultiplierResult:
    """Result of Dasha activation multiplier computation.

    Attributes:
        hierarchy: The active Dasha hierarchy.
        multiplier: Net Dasha multiplier (0.40–1.50).
        matched_level: Which level matched ('MD', 'AD', 'PD', or 'NONE').
        matched_planet: Which yoga planet matched (or empty).
    """

    hierarchy: DashaHierarchy
    multiplier: float
    matched_level: str
    matched_planet: str


# ── Dasha Engine ─────────────────────────────────────────────────────────────


class VimshottariDashaEngine:
    """Deterministic Vimshottari Dasha computation engine.

    Calculates MD, AD, and PD periods from the Moon's Nakshatra position
    and evaluates activation multipliers for yoga-forming planets.
    """

    def compute_dasha_at(
        self,
        target_timestamp: datetime,
        moon_nakshatra: str,
        moon_nakshatra_degree: float,
    ) -> DashaHierarchy:
        """Compute active MD/AD/PD for a target timestamp.

        Args:
            target_timestamp: The UTC timestamp to evaluate.
            moon_nakshatra: Name of the Moon's Nakshatra (e.g., 'ASHWINI').
            moon_nakshatra_degree: Moon's longitude in degrees (0.0–360.0).

        Returns:
            DashaHierarchy with active MD, AD, and PD periods.
        """
        # Determine the birth epoch and MD lord from Nakshatra
        md_lord = self._get_md_lord(moon_nakshatra)

        # Birth epoch: the start of the first MD period
        # For calculation purposes, we treat the birth as occurring at
        # the Moon's current degree within the Nakshatra.
        birth_epoch = self._compute_birth_epoch(
            target_timestamp, moon_nakshatra, moon_nakshatra_degree
        )

        # Compute MD sequence from birth
        md_periods = self._compute_md_periods(birth_epoch)

        # Find active MD
        active_md = self._find_active_period(md_periods, target_timestamp)
        if active_md is None:
            # Fallback: construct a default period around the target
            active_md = DashaPeriod(
                lord=md_lord,
                period_type="MD",
                start_utc=target_timestamp,
                end_utc=target_timestamp + timedelta(days=365.25 * VIMSHOTTARI_DURATIONS.get(md_lord, 10.0)),
                duration_years=VIMSHOTTARI_DURATIONS.get(md_lord, 10.0),
            )

        # Compute AD periods within the active MD
        ad_periods = self._compute_sub_periods(active_md, "AD")
        active_ad = self._find_active_period(ad_periods, target_timestamp)
        if active_ad is None:
            active_ad = DashaPeriod(
                lord=active_md.lord,
                period_type="AD",
                start_utc=active_md.start_utc,
                end_utc=active_md.end_utc,
                duration_years=active_md.duration_years,
            )

        # Compute PD periods within the active AD
        pd_periods = self._compute_sub_periods(active_ad, "PD")
        active_pd = self._find_active_period(pd_periods, target_timestamp)
        if active_pd is None:
            active_pd = DashaPeriod(
                lord=active_ad.lord,
                period_type="PD",
                start_utc=active_ad.start_utc,
                end_utc=active_ad.end_utc,
                duration_years=active_ad.duration_years,
            )

        return DashaHierarchy(
            mahadasha=active_md,
            antardasha=active_ad,
            pratyantardasha=active_pd,
        )

    def get_dasha_multiplier(
        self,
        hierarchy: DashaHierarchy,
        yoga_planets: list[str],
    ) -> DashaMultiplierResult:
        """Compute Dasha activation multiplier for yoga-forming planets.

        Multiplier logic:
            - MD lord matches yoga planet → 1.50
            - AD lord matches yoga planet → 1.25
            - PD lord matches yoga planet → 1.10
            - No match (dormant) → 0.40

        Returns the maximum applicable multiplier across primary participant
        planets.

        Args:
            hierarchy: Active Dasha hierarchy.
            yoga_planets: List of planet names involved in the yoga.

        Returns:
            DashaMultiplierResult with multiplier and match details.
        """
        upper_planets = {p.upper() for p in yoga_planets}

        # Check PD first (weakest match)
        matched_level = "NONE"
        matched_planet = ""
        multiplier = _DORMANT_MULTIPLIER

        # Check MD (strongest)
        if hierarchy.md_lord in upper_planets:
            return DashaMultiplierResult(
                hierarchy=hierarchy,
                multiplier=_MD_MULTIPLIER,
                matched_level="MD",
                matched_planet=hierarchy.md_lord,
            )

        # Check AD
        if hierarchy.ad_lord in upper_planets:
            return DashaMultiplierResult(
                hierarchy=hierarchy,
                multiplier=_AD_MULTIPLIER,
                matched_level="AD",
                matched_planet=hierarchy.ad_lord,
            )

        # Check PD
        if hierarchy.pd_lord in upper_planets:
            return DashaMultiplierResult(
                hierarchy=hierarchy,
                multiplier=_PD_MULTIPLIER,
                matched_level="PD",
                matched_planet=hierarchy.pd_lord,
            )

        # No match — dormant
        return DashaMultiplierResult(
            hierarchy=hierarchy,
            multiplier=_DORMANT_MULTIPLIER,
            matched_level="NONE",
            matched_planet="",
        )

    # ── Internal Methods ─────────────────────────────────────────────────

    @staticmethod
    def _get_md_lord(nakshatra: str) -> str:
        """Get the starting Mahadasha lord for a Nakshatra."""
        return _NAKSHATRA_DASHA_START.get(nakshatra.upper(), "KETU")

    def _compute_birth_epoch(
        self,
        target_timestamp: datetime,
        nakshatra: str,
        degree_in_nakshatra: float,
    ) -> datetime:
        """Compute an effective birth epoch from Nakshatra position.

        Uses the Moon's degree within the Nakshatra to estimate how
        much of the first MD period has elapsed, then back-calculates
        the birth epoch.
        """
        nakshatra_arc = 360.0 / 27.0  # 13.333°
        fraction_elapsed = degree_in_nakshatra / nakshatra_arc
        md_lord = self._get_md_lord(nakshatra)
        md_duration_days = VIMSHOTTARI_DURATIONS.get(md_lord, 10.0) * 365.25
        elapsed_days = fraction_elapsed * md_duration_days
        return target_timestamp - timedelta(days=elapsed_days)

    def _compute_md_periods(
        self, birth_epoch: datetime
    ) -> list[DashaPeriod]:
        """Compute the full MD period sequence starting from birth."""
        periods: list[DashaPeriod] = []
        current_start = birth_epoch

        # Start from the MD lord corresponding to the birth Nakshatra
        # and cycle through all 9 lords
        start_idx = 0  # Will be set by caller context; default to KETU

        for cycle in range(3):  # 3 cycles to cover 120+ years
            for i, lord in enumerate(VIMSHOTTARI_ORDER):
                idx = (start_idx + cycle * 9 + i) % 9
                lord = VIMSHOTTARI_ORDER[idx]
                duration_years = VIMSHOTTARI_DURATIONS[lord]
                duration_days = duration_years * 365.25
                end = current_start + timedelta(days=duration_days)
                periods.append(DashaPeriod(
                    lord=lord,
                    period_type="MD",
                    start_utc=current_start,
                    end_utc=end,
                    duration_years=duration_years,
                ))
                current_start = end

        return periods

    def _compute_sub_periods(
        self, parent: DashaPeriod, sub_type: str
    ) -> list[DashaPeriod]:
        """Compute AD or PD sub-periods within a parent period."""
        periods: list[DashaPeriod] = []
        parent_lord = parent.lord
        parent_duration_days = (parent.end_utc - parent.start_utc).total_seconds() / 86400.0

        # Find the starting lord for sub-periods
        try:
            start_lord_idx = VIMSHOTTARI_ORDER.index(parent_lord)
        except ValueError:
            start_lord_idx = 0

        current_start = parent.start_utc

        for i in range(9):
            sub_lord_idx = (start_lord_idx + i) % 9
            sub_lord = VIMSHOTTARI_ORDER[sub_lord_idx]
            sub_duration_years = VIMSHOTTARI_DURATIONS[sub_lord]

            # Proportion of parent's duration
            sub_fraction = sub_duration_years / TOTAL_VIMSHOTTARI_YEARS
            sub_duration_days = parent_duration_days * sub_fraction

            end = current_start + timedelta(days=sub_duration_days)
            periods.append(DashaPeriod(
                lord=sub_lord,
                period_type=sub_type,
                start_utc=current_start,
                end_utc=end,
                duration_years=sub_duration_years * (parent.duration_years / TOTAL_VIMSHOTTARI_YEARS),
            ))
            current_start = end

        return periods

    @staticmethod
    def _find_active_period(
        periods: list[DashaPeriod], ts: datetime
    ) -> DashaPeriod | None:
        """Find the period containing the given timestamp."""
        for period in periods:
            if period.contains(ts):
                return period
        return None

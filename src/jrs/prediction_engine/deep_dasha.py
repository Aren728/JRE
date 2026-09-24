"""Deep Vimshottari Engine — Pratyantardasha (PD) and Sookshma Dasha (SD).

Extends the existing VimshottariDashaEngine (MD → AD → PD) with:

  - **Pratyantardasha (PD)**: Sub-sub-period (already in base engine, but
    this module computes the *full* PD sequence for any given AD).
  - **Sookshma Dasha (SD)**: The 4th level, sometimes called "Sukshma" or
    "Prana".  Each PD is subdivided into 9 SD periods proportional to the
    Vimshottari durations.

This module does NOT replace the base engine — it provides richer timeline
data for the UI's Dasha visualization.

Vimshottari durations (years):
    Sun=6, Moon=10, Mars=7, Rahu=18, Jupiter=16,
    Saturn=19, Mercury=17, Ketu=7, Venus=20
    Total = 120 years.

Reference: BPHS Ch 46, Vimshottari Dasha Phala.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

# ── Vimshottari arrays (reused from base engine) ────────────────────────────

VIMSHOTTARI_ORDER: tuple[str, ...] = (
    "KETU",
    "VENUS",
    "SUN",
    "MOON",
    "MARS",
    "RAHU",
    "JUPITER",
    "SATURN",
    "MERCURY",
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

TOTAL_YEARS: float = 120.0


# ── Data structures ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class DashaPeriod:
    """A single Dasha period at any level (MD/AD/PD/SD).

    Attributes:
        lord: Planet governing this period.
        level: 'MD', 'AD', 'PD', or 'SD'.
        start_utc: Start datetime (UTC).
        end_utc: End datetime (UTC).
        duration_years: Duration in fractional years.
        fraction_of_parent: What fraction of the parent period this takes.
    """

    lord: str
    level: str
    start_utc: datetime
    end_utc: datetime
    duration_years: float
    fraction_of_parent: float = 0.0

    def contains(self, ts: datetime) -> bool:
        return self.start_utc <= ts < self.end_utc

    def to_dict(self) -> dict[str, Any]:
        return {
            "lord": self.lord,
            "level": self.level,
            "start_utc": self.start_utc.isoformat(),
            "end_utc": self.end_utc.isoformat(),
            "duration_years": round(self.duration_years, 4),
            "fraction_of_parent": round(self.fraction_of_parent, 6),
        }


@dataclass(frozen=True)
class SookshmaPeriod:
    """A single Sookshma (4th level) Dasha period.

    Attributes:
        lord: Planet governing this period.
        start_utc: Start datetime (UTC).
        end_utc: End datetime (UTC).
        duration_years: Duration in fractional years.
        parent_pd_lord: The PD lord this SD falls under.
        parent_md_lord: The MD lord at the top level.
    """

    lord: str
    start_utc: datetime
    end_utc: datetime
    duration_years: float
    parent_pd_lord: str
    parent_md_lord: str

    def contains(self, ts: datetime) -> bool:
        return self.start_utc <= ts < self.end_utc

    def to_dict(self) -> dict[str, Any]:
        return {
            "lord": self.lord,
            "start_utc": self.start_utc.isoformat(),
            "end_utc": self.end_utc.isoformat(),
            "duration_years": round(self.duration_years, 4),
            "parent_pd_lord": self.parent_pd_lord,
            "parent_md_lord": self.parent_md_lord,
        }


@dataclass(frozen=True)
class DeepDashaResult:
    """Complete deep Dasha hierarchy at a target timestamp.

    Attributes:
        md: Active Mahadasha.
        ad: Active Antardasha.
        pd: Active Pratyantardasha.
        sd: Active Sookshma Dasha (4th level).
        ad_timeline: All AD periods within the active MD.
        pd_timeline: All PD periods within the active AD.
        sd_timeline: All SD periods within the active PD.
        activation_multiplier: Composite multiplier across all levels.
    """

    md: DashaPeriod
    ad: DashaPeriod
    pd: DashaPeriod
    sd: SookshmaPeriod
    ad_timeline: tuple[DashaPeriod, ...]
    pd_timeline: tuple[DashaPeriod, ...]
    sd_timeline: tuple[SookshmaPeriod, ...]
    activation_multiplier: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "md": self.md.to_dict(),
            "ad": self.ad.to_dict(),
            "pd": self.pd.to_dict(),
            "sd": self.sd.to_dict(),
            "ad_timeline": [p.to_dict() for p in self.ad_timeline],
            "pd_timeline": [p.to_dict() for p in self.pd_timeline],
            "sd_timeline": [s.to_dict() for s in self.sd_timeline],
            "activation_multiplier": round(self.activation_multiplier, 6),
        }


# ── Activation multiplier constants ──────────────────────────────────────────

_MD_MULT = 1.50
_AD_MULT = 1.25
_PD_MULT = 1.10
_SD_MULT = 1.05
_DORMANT_MULT = 0.40


# ── Engine ───────────────────────────────────────────────────────────────────


class DeepVimshottariEngine:
    """Compute deep Vimshottari Dasha hierarchy down to Sookshma level."""

    def compute(
        self,
        target_timestamp: datetime,
        birth_timestamp: datetime,
        moon_nakshatra: str,
        yoga_planets: list[str] | None = None,
    ) -> DeepDashaResult:
        """Compute the full MD → AD → PD → SD hierarchy at a target time.

        Args:
            target_timestamp: The UTC timestamp to evaluate.
            birth_timestamp: The UTC birth timestamp.
            moon_nakshatra: Moon's Nakshatra at birth (e.g., 'ROHINI').
            yoga_planets: Optional list of yoga-forming planets for multiplier.

        Returns:
            DeepDashaResult with active periods and timelines.
        """
        yoga_set = frozenset(p.upper() for p in (yoga_planets or []))

        # ── MD sequence ──
        md_lord = self._get_md_lord(moon_nakshatra)
        print(
            f"DASHA DEBUG: Starting Mahadasha sequence from BIRTH DATE: {birth_timestamp.date()} — MD Lord: {md_lord} (from Nakshatra: {moon_nakshatra})"
        )
        md_periods = self._compute_md_sequence(birth_timestamp, md_lord)
        active_md = self._find_period(md_periods, target_timestamp)
        if active_md is None:
            active_md = DashaPeriod(
                lord=md_lord,
                level="MD",
                start_utc=birth_timestamp,
                end_utc=birth_timestamp + timedelta(days=365.25 * 20),
                duration_years=20.0,
            )

        # ── AD sequence ──
        ad_periods = self._compute_sub_periods(active_md, "AD")
        active_ad = self._find_period(ad_periods, target_timestamp)
        if active_ad is None:
            active_ad = (
                ad_periods[0]
                if ad_periods
                else DashaPeriod(
                    lord=active_md.lord,
                    level="AD",
                    start_utc=active_md.start_utc,
                    end_utc=active_md.end_utc,
                    duration_years=active_md.duration_years,
                )
            )

        # ── PD sequence ──
        pd_periods = self._compute_sub_periods(active_ad, "PD")
        active_pd = self._find_period(pd_periods, target_timestamp)
        if active_pd is None:
            active_pd = (
                pd_periods[0]
                if pd_periods
                else DashaPeriod(
                    lord=active_ad.lord,
                    level="PD",
                    start_utc=active_ad.start_utc,
                    end_utc=active_ad.end_utc,
                    duration_years=active_ad.duration_years,
                )
            )

        # ── SD sequence (4th level) ──
        sd_periods = self._compute_sookshma_periods(active_pd, md_lord)
        active_sd = self._find_sookshma(sd_periods, target_timestamp)
        if active_sd is None:
            active_sd = (
                sd_periods[0]
                if sd_periods
                else SookshmaPeriod(
                    lord=active_pd.lord,
                    start_utc=active_pd.start_utc,
                    end_utc=active_pd.end_utc,
                    duration_years=active_pd.duration_years,
                    parent_pd_lord=active_pd.lord,
                    parent_md_lord=active_md.lord,
                )
            )

        # ── Activation multiplier ──
        multiplier = self._compute_multiplier(
            active_md.lord,
            active_ad.lord,
            active_pd.lord,
            active_sd.lord,
            yoga_set,
        )

        return DeepDashaResult(
            md=active_md,
            ad=active_ad,
            pd=active_pd,
            sd=active_sd,
            ad_timeline=tuple(ad_periods),
            pd_timeline=tuple(pd_periods),
            sd_timeline=tuple(sd_periods),
            activation_multiplier=multiplier,
        )

    # ── Sequence computation ───────────────────────────────────────────────

    def _compute_md_sequence(self, birth: datetime, md_lord: str) -> list[DashaPeriod]:
        """Compute MD periods starting from birth, beginning with the correct MD lord.

        The MD lord is determined by the Moon's Nakshatra at birth.
        This ensures the 120-year Vimshottari cycle starts correctly.
        """
        periods: list[DashaPeriod] = []
        current = birth

        # Find the starting index for the MD lord from Moon's nakshatra
        try:
            start_idx = VIMSHOTTARI_ORDER.index(md_lord)
        except ValueError:
            start_idx = 0

        for _ in range(3):  # 3 full cycles (~360 years)
            for i in range(9):
                lord = VIMSHOTTARI_ORDER[(start_idx + i) % 9]
                dur_years = VIMSHOTTARI_DURATIONS[lord]
                dur_days = dur_years * 365.25
                end = current + timedelta(days=dur_days)
                periods.append(
                    DashaPeriod(
                        lord=lord,
                        level="MD",
                        start_utc=current,
                        end_utc=end,
                        duration_years=dur_years,
                    )
                )
                current = end
        return periods

    def _compute_sub_periods(
        self,
        parent: DashaPeriod,
        level: str,
    ) -> list[DashaPeriod]:
        """Compute AD or PD sub-periods within a parent."""
        periods: list[DashaPeriod] = []
        parent_days = (parent.end_utc - parent.start_utc).total_seconds() / 86400.0

        try:
            start_idx = VIMSHOTTARI_ORDER.index(parent.lord)
        except ValueError:
            start_idx = 0

        current = parent.start_utc
        for i in range(9):
            sub_lord = VIMSHOTTARI_ORDER[(start_idx + i) % 9]
            sub_dur_years = VIMSHOTTARI_DURATIONS[sub_lord]
            fraction = sub_dur_years / TOTAL_YEARS
            sub_days = parent_days * fraction
            end = current + timedelta(days=sub_days)
            periods.append(
                DashaPeriod(
                    lord=sub_lord,
                    level=level,
                    start_utc=current,
                    end_utc=end,
                    duration_years=sub_dur_years * (parent.duration_years / TOTAL_YEARS),
                    fraction_of_parent=fraction,
                )
            )
            current = end
        return periods

    def _compute_sookshma_periods(
        self,
        pd: DashaPeriod,
        md_lord: str,
    ) -> list[SookshmaPeriod]:
        """Compute Sookshma (4th level) periods within a PD."""
        periods: list[SookshmaPeriod] = []
        pd_days = (pd.end_utc - pd.start_utc).total_seconds() / 86400.0

        try:
            start_idx = VIMSHOTTARI_ORDER.index(pd.lord)
        except ValueError:
            start_idx = 0

        current = pd.start_utc
        for i in range(9):
            sd_lord = VIMSHOTTARI_ORDER[(start_idx + i) % 9]
            sd_dur_years = VIMSHOTTARI_DURATIONS[sd_lord]
            fraction = sd_dur_years / TOTAL_YEARS
            sd_days = pd_days * fraction
            end = current + timedelta(days=sd_days)
            periods.append(
                SookshmaPeriod(
                    lord=sd_lord,
                    start_utc=current,
                    end_utc=end,
                    duration_years=sd_dur_years * (pd.duration_years / TOTAL_YEARS),
                    parent_pd_lord=pd.lord,
                    parent_md_lord=md_lord,
                )
            )
            current = end
        return periods

    # ── Activation multiplier ──────────────────────────────────────────────

    def _compute_multiplier(
        self,
        md_lord: str,
        ad_lord: str,
        pd_lord: str,
        sd_lord: str,
        yoga_planets: frozenset[str],
    ) -> float:
        """Compute composite activation multiplier across all 4 levels."""
        if md_lord in yoga_planets:
            return _MD_MULT
        if ad_lord in yoga_planets:
            return _AD_MULT
        if pd_lord in yoga_planets:
            return _PD_MULT
        if sd_lord in yoga_planets:
            return _SD_MULT
        return _DORMANT_MULT

    # ── Helpers ────────────────────────────────────────────────────────────

    @staticmethod
    def _get_md_lord(nakshatra: str) -> str:
        """Get MD lord for a Nakshatra (inline mapping)."""
        _MAP = {
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
        return _MAP.get(nakshatra.upper(), "KETU")

    @staticmethod
    def _find_period(
        periods: list[DashaPeriod],
        ts: datetime,
    ) -> DashaPeriod | None:
        for p in periods:
            if p.contains(ts):
                return p
        return None

    @staticmethod
    def _find_sookshma(
        periods: list[SookshmaPeriod],
        ts: datetime,
    ) -> SookshmaPeriod | None:
        for p in periods:
            if p.contains(ts):
                return p
        return None


# ── Yoga Activation Timings ────────────────────────────────────────────────


def compute_yoga_activation_periods(
    ad_timeline: tuple[DashaPeriod, ...],
    involved_planets: list[str],
    yoga_name: str = "",
) -> dict[str, Any]:
    """Compute when a yoga activates based on Dasha periods.

    A yoga activates when the Mahadasha or Antardasha lord matches
    any of the yoga's involved planets.

    Args:
        ad_timeline: All AD periods within the active MD.
        involved_planets: Planets involved in the yoga.
        yoga_name: Name of the yoga for narrative generation.

    Returns:
        Dict with past, present, and future activation periods.
    """
    now = datetime.now(timezone.utc)
    yoga_planets_upper = {p.upper() for p in involved_planets}

    past_periods: list[dict[str, Any]] = []
    present_periods: list[dict[str, Any]] = []
    future_periods: list[dict[str, Any]] = []

    for period in ad_timeline:
        lord_upper = period.lord.upper()
        if lord_upper not in yoga_planets_upper:
            continue

        period_info = {
            "lord": period.lord,
            "level": period.level,
            "start": period.start_utc.isoformat(),
            "end": period.end_utc.isoformat(),
            "duration_years": round(period.duration_years, 2),
        }

        if period.end_utc < now:
            past_periods.append(period_info)
        elif period.start_utc <= now <= period.end_utc:
            present_periods.append(period_info)
        else:
            future_periods.append(period_info)

    # Generate activation narrative
    narrative_parts: list[str] = []

    if present_periods:
        current = present_periods[0]
        narrative_parts.append(
            f"Currently during {current['lord']} Mahadasha/Antardasha (until {current['end'][:10]}), "
            f"the {yoga_name} yoga is actively manifesting. This is the prime window for "
            f"experiencing the yoga's full effects."
        )
    elif future_periods:
        next_p = future_periods[0]
        narrative_parts.append(
            f"The {yoga_name} yoga will next activate during {next_p['lord']} "
            f"Mahadasha/Antardasha starting {next_p['start'][:10]}. "
            f"Prepare for this period by strengthening the yoga's planetary significations."
        )
    elif past_periods:
        narrative_parts.append(
            f"The {yoga_name} yoga recently activated during the last matching Dasha period. "
            f"Its effects may still linger in karmic memory."
        )
    else:
        narrative_parts.append(
            f"The {yoga_name} yoga will activate during the Dasha periods of its involved planets "
            f"({', '.join(involved_planets)}). Monitor the Dasha timeline for these planetary periods."
        )

    return {
        "past": past_periods,
        "present": present_periods,
        "future": future_periods,
        "narrative": " ".join(narrative_parts),
        "total_activation_periods": len(past_periods) + len(present_periods) + len(future_periods),
    }

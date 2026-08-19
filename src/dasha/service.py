"""JRE-010 DashaService facade.

``DashaService.generate_timeline`` is the canonical entry point: it
validates the request, computes the Vimshottari balance from the Moon's
natal Nakshatra/Pada, and produces a hierarchical ``DashaTimeline`` of
Mahadasha → Antardasha → Pratyantardasha periods.

``DashaService.get_lord_at`` queries the active lord(s) at any UTC
instant.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from jyotish import BodyId, NakshatraId, PlanetState

from .config import load_config
from .errors import InvalidDashaRequestError
from .models import (
    NAKSHATRA_LORDS,
    VIMSHOTTARI_CYCLE_YEARS,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_YEARS,
    DashaConfig,
    DashaPeriod,
    DashaSystem,
    DashaTimeline,
    _antardasha_duration,
    _next_lord,
    _pratyantardasha_duration,
    compute_antardasha_order,
    compute_balance_at_birth,
)


class DashaService:
    """Deterministic Dasha computation facade."""

    def __init__(self, config: DashaConfig | None = None) -> None:
        self._config = config if config is not None else load_config()

    @property
    def config(self) -> DashaConfig:
        return self._config

    def generate_timeline(
        self,
        moon_state: PlanetState,
        birth_time: datetime,
        duration_years: int = VIMSHOTTARI_CYCLE_YEARS,
    ) -> DashaTimeline:
        """Generate the Vimshottari Dasha timeline from the Moon's natal state.

        Parameters
        ----------
        moon_state : PlanetState
            The Moon's ``PlanetState`` from JRE-003 (must have body == MOON).
        birth_time : datetime
            The birth date/time (timezone-aware preferred).
        duration_years : int
            How many years of timeline to generate (default: 120 = full cycle).

        Returns
        -------
        DashaTimeline
            The hierarchical timeline with balance, periods, and metadata.
        """
        self._validate_request(moon_state, birth_time, duration_years)

        # Ensure UTC for deterministic computation
        birth_utc = self._to_utc(birth_time)

        nakshatra = moon_state.nakshatra
        pada = moon_state.pada
        degree_in_nakshatra = moon_state.degree_in_nakshatra

        balance = compute_balance_at_birth(nakshatra, pada, degree_in_nakshatra)

        # Build the timeline
        periods = self._build_timeline(
            nakshatra=nakshatra,
            birth_utc=birth_utc,
            balance_years=balance,
            duration_years=duration_years,
            max_depth=self._config.max_depth,
        )

        return DashaTimeline(
            birth_nakshatra=nakshatra,
            birth_pada=pada,
            balance_at_birth=balance,
            system=DashaSystem.VIMSHOTTARI,
            periods=tuple(periods),
        )

    def get_lord_at(
        self,
        instant: datetime,
        timeline: DashaTimeline,
    ) -> dict[str, BodyId | None]:
        """Return the active lord(s) at a given UTC instant.

        Returns
        -------
        dict
            Keys: ``"mahadasha"``, ``"antardasha"``, ``"pratyantardasha"``.
            Values: the active ``BodyId`` or ``None`` if not computed at that depth.
        """
        instant_utc = self._to_utc(instant)

        result: dict[str, BodyId | None] = {
            "mahadasha": None,
            "antardasha": None,
            "pratyantardasha": None,
        }

        for period in timeline.periods:
            if period.start_utc <= instant_utc < period.end_utc:
                result["mahadasha"] = period.mahadasha_lord
                result["antardasha"] = period.antardasha_lord
                result["pratyantardasha"] = period.pratyantardasha_lord
                return result

        return result

    # ------------------------------------------------------------------ #
    # Internal computation
    # ------------------------------------------------------------------ #

    def _build_timeline(
        self,
        nakshatra: NakshatraId,
        birth_utc: datetime,
        balance_years: float,
        duration_years: int,
        max_depth: int,
    ) -> list[DashaPeriod]:
        """Build the hierarchical Dasha timeline."""
        first_lord = NAKSHATRA_LORDS[nakshatra]
        periods: list[DashaPeriod] = []

        # Start generating from the first lord
        current_lord = first_lord
        current_start = birth_utc
        remaining_total_years = float(duration_years)

        # First Mahadasha: only the balance applies
        first_maha_years = min(balance_years, remaining_total_years)
        first_maha_end = current_start + timedelta(days=first_maha_years * 365.25)

        if max_depth == 1:
            periods.append(DashaPeriod(
                start_utc=current_start,
                end_utc=first_maha_end,
                mahadasha_lord=current_lord,
            ))
        else:
            sub_periods = self._build_antardashas(
                current_lord, current_start, first_maha_years, max_depth
            )
            periods.extend(sub_periods)

        remaining_total_years -= first_maha_years
        current_start = first_maha_end
        current_lord = _next_lord(current_lord)

        # Subsequent Mahadashas: the last lord in the cycle absorbs any
        # remainder so that exactly 9 Mahadashas span the full duration.
        lords_remaining = len(VIMSHOTTARI_ORDER) - 1  # 8 after the first
        while remaining_total_years > 1e-9 and lords_remaining > 0:
            if lords_remaining == 1:
                # Last lord gets all remaining time
                maha_years = remaining_total_years
            else:
                maha_years = min(
                    float(VIMSHOTTARI_YEARS[current_lord]),
                    remaining_total_years,
                )
            maha_end = current_start + timedelta(days=maha_years * 365.25)

            if max_depth == 1:
                periods.append(DashaPeriod(
                    start_utc=current_start,
                    end_utc=maha_end,
                    mahadasha_lord=current_lord,
                ))
            else:
                sub_periods = self._build_antardashas(
                    current_lord, current_start, maha_years, max_depth
                )
                periods.extend(sub_periods)

            remaining_total_years -= maha_years
            current_start = maha_end
            current_lord = _next_lord(current_lord)
            lords_remaining -= 1

        return periods

    def _build_antardashas(
        self,
        mahadasha_lord: BodyId,
        maha_start: datetime,
        maha_years: float,
        max_depth: int,
    ) -> list[DashaPeriod]:
        """Build Antardasha (and optionally Pratyantardasha) periods."""
        adasha_order = compute_antardasha_order(mahadasha_lord)
        periods: list[DashaPeriod] = []
        current_start = maha_start

        for adasha_lord in adasha_order:
            adasha_years = _antardasha_duration(mahadasha_lord, adasha_lord)
            # Scale if Mahadasha was truncated (first or last)
            adasha_years_scaled = adasha_years * maha_years / VIMSHOTTARI_YEARS[mahadasha_lord]
            adasha_end = current_start + timedelta(days=adasha_years_scaled * 365.25)

            if max_depth == 2:
                periods.append(DashaPeriod(
                    start_utc=current_start,
                    end_utc=adasha_end,
                    mahadasha_lord=mahadasha_lord,
                    antardasha_lord=adasha_lord,
                ))
            else:
                # max_depth == 3: build Pratyantardashas
                praty_periods = self._build_pratyantardashas(
                    mahadasha_lord=mahadasha_lord,
                    antardasha_lord=adasha_lord,
                    adasha_start=current_start,
                    adasha_years=adasha_years_scaled,
                )
                periods.extend(praty_periods)

            current_start = adasha_end

        return periods

    def _build_pratyantardashas(
        self,
        mahadasha_lord: BodyId,
        antardasha_lord: BodyId,
        adasha_start: datetime,
        adasha_years: float,
    ) -> list[DashaPeriod]:
        """Build Pratyantardasha periods within an Antardasha."""
        praty_order = compute_antardasha_order(antardasha_lord)
        periods: list[DashaPeriod] = []
        current_start = adasha_start

        for praty_lord in praty_order:
            praty_years = _pratyantardasha_duration(mahadasha_lord, antardasha_lord, praty_lord)
            # Scale to the actual Antardasha duration
            adasha_total = _antardasha_duration(mahadasha_lord, antardasha_lord)
            praty_years_scaled = (
                praty_years * adasha_years / adasha_total
                if adasha_total > 0
                else 0.0
            )
            praty_end = current_start + timedelta(days=praty_years_scaled * 365.25)

            periods.append(DashaPeriod(
                start_utc=current_start,
                end_utc=praty_end,
                mahadasha_lord=mahadasha_lord,
                antardasha_lord=antardasha_lord,
                pratyantardasha_lord=praty_lord,
            ))

            current_start = praty_end

        return periods

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #

    def _validate_request(
        self,
        moon_state: PlanetState,
        birth_time: datetime,
        duration_years: int,
    ) -> None:
        """Validate the Dasha generation request."""
        if not isinstance(moon_state, PlanetState):
            raise InvalidDashaRequestError(
                f"moon_state must be a PlanetState, got {type(moon_state).__name__}"
            )
        if moon_state.body != BodyId.MOON:
            raise InvalidDashaRequestError(
                f"moon_state.body must be MOON, got {moon_state.body!r}"
            )
        if not isinstance(birth_time, datetime):
            raise InvalidDashaRequestError(
                f"birth_time must be a datetime, got {type(birth_time).__name__}"
            )
        if not isinstance(duration_years, int) or duration_years < 1:
            raise InvalidDashaRequestError(
                f"duration_years must be a positive integer, got {duration_years!r}"
            )

    @staticmethod
    def _to_utc(dt: datetime) -> datetime:
        """Convert a datetime to UTC for deterministic computation."""
        if dt.tzinfo is None:
            # Assume naive datetime is UTC
            return dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

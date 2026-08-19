"""JRE-010 Dasha integration tests.

End-to-end tests verifying:
- Full 120-year timeline generation and correctness
- Period boundary alignment
- Balance calculation integration with service
- Lord querying across the full timeline
- Serialization round-trip of complete timelines
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import pytest
from jyotish import BodyId, NakshatraId, Pada

from dasha.config import load_config
from dasha.models import (
    DashaConfig,
    DashaPeriod,
    DashaSystem,
    NAKSHATRA_LORDS,
    VIMSHOTTARI_CYCLE_YEARS,
    VIMSHOTTARI_ORDER,
    VIMSHOTTARI_YEARS,
    compute_balance_at_birth,
)
from dasha.serialize import result_to_dict, result_to_json, dasha_timeline_from_dict
from dasha.service import DashaService
from tests.unit.dasha.conftest import NAKSHATRA_START, make_moon_state


# --------------------------------------------------------------------------- #
# Reference chart: Moon in Ashwini Pada 1 (KETU lord)
# --------------------------------------------------------------------------- #


class TestAshwiniPada1Timeline:
    """Integration test: Moon at start of Ashwini Pada 1.

    Expected: KETU Mahadasha first (full 7 years), then VENUS (20), SUN (6),
    MOON (10), MARS (7), RAHU (18), JUPITER (16), SATURN (19), MERCURY (17).
    Total = 120 years.
    """

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = DashaService(DashaConfig(max_depth=1))
        self.moon = make_moon_state(NakshatraId.ASHWINI, Pada.PADA_1, 0.0)
        self.birth = datetime(2000, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.timeline = self.service.generate_timeline(
            self.moon, self.birth, duration_years=VIMSHOTTARI_CYCLE_YEARS
        )

    def test_balance_is_full_period(self) -> None:
        """At degree 0 of Pada 1, balance = full lord period."""
        assert math.isclose(self.timeline.balance_at_birth, 7.0, rel_tol=1e-10)

    def test_first_lord_is_ketu(self) -> None:
        assert self.timeline.periods[0].mahadasha_lord == BodyId.KETU

    def test_full_cycle_generates_9_mahadashas(self) -> None:
        assert len(self.timeline.periods) == 9

    def test_order_follows_vimshottari(self) -> None:
        lords = [p.mahadasha_lord for p in self.timeline.periods]
        assert lords == list(VIMSHOTTARI_ORDER)

    def test_total_duration_is_120_years(self) -> None:
        total_days = (self.timeline.periods[-1].end_utc - self.birth).days
        total_years = total_days / 365.25
        assert math.isclose(total_years, 120.0, rel_tol=0.01)

    def test_ketu_period_is_7_years(self) -> None:
        ketu_period = self.timeline.periods[0]
        days = (ketu_period.end_utc - ketu_period.start_utc).days
        assert math.isclose(days / 365.25, 7.0, rel_tol=0.01)

    def test_venus_period_is_20_years(self) -> None:
        venus_period = self.timeline.periods[1]
        days = (venus_period.end_utc - venus_period.start_utc).days
        assert math.isclose(days / 365.25, 20.0, rel_tol=0.01)

    def test_periods_are_contiguous(self) -> None:
        for i in range(len(self.timeline.periods) - 1):
            assert self.timeline.periods[i].end_utc == self.timeline.periods[i + 1].start_utc

    def test_lord_at_birth(self) -> None:
        lords = self.service.get_lord_at(self.birth, self.timeline)
        assert lords["mahadasha"] == BodyId.KETU

    def test_lord_at_venus_start(self) -> None:
        venus_start = self.timeline.periods[1].start_utc
        lords = self.service.get_lord_at(venus_start, self.timeline)
        assert lords["mahadasha"] == BodyId.VENUS

    def test_lord_at_mid_mercury(self) -> None:
        mercury = self.timeline.periods[8]
        mid = mercury.start_utc + (mercury.end_utc - mercury.start_utc) / 2
        lords = self.service.get_lord_at(mid, self.timeline)
        assert lords["mahadasha"] == BodyId.MERCURY

    def test_timeline_serialization_roundtrip(self) -> None:
        d = result_to_dict(self.timeline)
        tl2 = dasha_timeline_from_dict(d)
        assert tl2.birth_nakshatra == self.timeline.birth_nakshatra
        assert tl2.birth_pada == self.timeline.birth_pada
        assert len(tl2.periods) == len(self.timeline.periods)
        for p1, p2 in zip(self.timeline.periods, tl2.periods):
            assert p1.mahadasha_lord == p2.mahadasha_lord
            assert p1.start_utc == p2.start_utc
            assert p1.end_utc == p2.end_utc

    def test_json_roundtrip(self) -> None:
        j = result_to_json(self.timeline)
        assert isinstance(j, str)
        d = result_to_dict(self.timeline)
        import json
        parsed = json.loads(j)
        assert parsed["birth_nakshatra"] == "ASHWINI"


# --------------------------------------------------------------------------- #
# Reference chart: Moon in Rohini Pada 2 (MOON lord)
# --------------------------------------------------------------------------- #


class TestRohiniPada2Timeline:
    """Integration test: Moon in Rohini Pada 2 (MOON lord).

    Expected: MOON Mahadasha first (partial), then MARS, RAHU, JUPITER,
    SATURN, MERCURY, KETU, VENUS, SUN.
    """

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = DashaService(DashaConfig(max_depth=1))
        self.moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_2)
        self.birth = datetime(1990, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        self.timeline = self.service.generate_timeline(
            self.moon, self.birth, duration_years=VIMSHOTTARI_CYCLE_YEARS
        )

    def test_first_lord_is_moon(self) -> None:
        assert self.timeline.periods[0].mahadasha_lord == BodyId.MOON

    def test_moon_period_is_less_than_10(self) -> None:
        """First period should be less than full 10 years (pada 2, not pada 1)."""
        days = (self.timeline.periods[0].end_utc - self.timeline.periods[0].start_utc).days
        years = days / 365.25
        assert years < 10.0
        assert years > 5.0  # Should be ~7.5 years (50% elapsed in pada 2)

    def test_nine_mahadashas(self) -> None:
        assert len(self.timeline.periods) == 9

    def test_full_cycle_sum(self) -> None:
        total_days = (self.timeline.periods[-1].end_utc - self.birth).days
        total_years = total_days / 365.25
        assert math.isclose(total_years, 120.0, rel_tol=0.01)

    def test_lord_at_mid_mars(self) -> None:
        mars_period = self.timeline.periods[1]
        mid = mars_period.start_utc + (mars_period.end_utc - mars_period.start_utc) / 2
        lords = self.service.get_lord_at(mid, self.timeline)
        assert lords["mahadasha"] == BodyId.MARS


# --------------------------------------------------------------------------- #
# Antardasha integration (depth=2)
# --------------------------------------------------------------------------- #


class TestAntardashaIntegration:
    """Integration test: depth=2 Antardasha timeline."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = DashaService(DashaConfig(max_depth=2))
        self.moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        self.birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
        # Use a short duration for test speed
        self.timeline = self.service.generate_timeline(
            self.moon, self.birth, duration_years=5
        )

    def test_all_periods_have_antardasha(self) -> None:
        for p in self.timeline.periods:
            assert p.antardasha_lord is not None

    def test_antardasha_order_starts_with_mahadasha_lord(self) -> None:
        """Within each Mahadasha, Antardashas should start with the
        Mahadasha lord itself."""
        # Find periods for the first Mahadasha
        first_maha = self.timeline.periods[0].mahadasha_lord
        adasha_lords = [
            p.antardasha_lord for p in self.timeline.periods
            if p.mahadasha_lord == first_maha
        ]
        assert adasha_lords[0] == first_maha

    def test_antardasha_period_count_per_mahadasha(self) -> None:
        """Each Mahadasha should have 9 Antardashas."""
        first_maha = self.timeline.periods[0].mahadasha_lord
        count = sum(
            1 for p in self.timeline.periods
            if p.mahadasha_lord == first_maha
        )
        assert count == 9

    def test_lord_query_with_antardasha(self) -> None:
        """get_lord_at should return antardasha lord at depth=2."""
        # Query at start of second antardasha of first mahadasha
        if len(self.timeline.periods) > 1:
            instant = self.timeline.periods[1].start_utc
            lords = self.service.get_lord_at(instant, self.timeline)
            assert lords["mahadasha"] is not None
            assert lords["antardasha"] is not None


# --------------------------------------------------------------------------- #
# Pratyantardasha integration (depth=3)
# --------------------------------------------------------------------------- #


class TestPratyantardashaIntegration:
    """Integration test: depth=3 Pratyantardasha timeline."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.service = DashaService(DashaConfig(max_depth=3))
        self.moon = make_moon_state(NakshatraId.ASHWINI, Pada.PADA_1, 0.0)
        self.birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
        # Very short duration to keep test fast
        self.timeline = self.service.generate_timeline(
            self.moon, self.birth, duration_years=1
        )

    def test_all_periods_are_pratyantardasha(self) -> None:
        for p in self.timeline.periods:
            assert p.depth == 3
            assert p.pratyantardasha_lord is not None

    def test_pratyantardasha_periods_exist(self) -> None:
        assert len(self.timeline.periods) > 9  # More than just antardashas


# --------------------------------------------------------------------------- #
# Cross-nakshatra boundary test
# --------------------------------------------------------------------------- #


class TestBoundaryConditions:
    """Edge cases and boundary conditions."""

    def test_near_end_of_revati(self) -> None:
        """Moon near end of Revati (last nakshatra, MERCURY lord)."""
        service = DashaService(DashaConfig(max_depth=1))
        nak_span = 360.0 / 27.0
        moon = make_moon_state(
            NakshatraId.REVATI, Pada.PADA_4,
            degree_in_nakshatra_deg=nak_span - 0.1,
        )
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)
        tl = service.generate_timeline(moon, birth, duration_years=5)

        # Balance should be very small
        assert tl.balance_at_birth < 1.0
        assert tl.periods[0].mahadasha_lord == BodyId.MERCURY

    def test_specific_balance_rohini_pada3(self) -> None:
        """Verify exact balance calculation for Rohini Pada 3."""
        nak_span = 360.0 / 27.0
        pada_span = nak_span / 4.0
        # Pada 3, at start → 50% elapsed → 5.0 years (MOON = 10)
        balance = compute_balance_at_birth(
            NakshatraId.ROHINI, Pada.PADA_3, 0.0
        )
        assert math.isclose(balance, 5.0, rel_tol=1e-10)

    def test_all_nakshatras_produce_valid_timelines(self) -> None:
        """Every nakshatra should produce a valid 120-year timeline."""
        service = DashaService(DashaConfig(max_depth=1))
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        for nak in NakshatraId:
            moon = make_moon_state(nak, Pada.PADA_1, 0.0)
            tl = service.generate_timeline(moon, birth, duration_years=120)
            assert len(tl.periods) == 9, f"Failed for {nak}"
            total = (tl.periods[-1].end_utc - birth).days / 365.25
            assert math.isclose(total, 120.0, rel_tol=0.01), f"Duration wrong for {nak}"

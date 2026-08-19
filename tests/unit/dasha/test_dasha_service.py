"""JRE-010 DashaService unit tests.

Tests the service facade: timeline generation, lord querying, and input
validation.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import pytest
from jyotish import BodyId, NakshatraId, Pada

from dasha.errors import InvalidDashaRequestError
from dasha.models import (
    DashaConfig,
    DashaPeriod,
    DashaSystem,
    NAKSHATRA_LORDS,
    VIMSHOTTARI_YEARS,
)
from dasha.service import DashaService
from tests.unit.dasha.conftest import make_moon_state, make_sun_state


class TestDashaServiceValidation:
    """Test request validation in DashaService."""

    def test_rejects_non_moon_state(self) -> None:
        service = DashaService(DashaConfig())
        sun_state = make_sun_state()
        with pytest.raises(InvalidDashaRequestError, match="MOON"):
            service.generate_timeline(
                sun_state,
                datetime(2000, 1, 1, tzinfo=timezone.utc),
            )

    def test_rejects_non_planetstate(self) -> None:
        service = DashaService(DashaConfig())
        with pytest.raises(InvalidDashaRequestError, match="PlanetState"):
            service.generate_timeline(  # type: ignore[arg-type]
                "not a state",  # type: ignore[arg-type]
                datetime(2000, 1, 1, tzinfo=timezone.utc),
            )

    def test_rejects_negative_duration(self) -> None:
        service = DashaService(DashaConfig())
        moon = make_moon_state()
        with pytest.raises(InvalidDashaRequestError, match="duration_years"):
            service.generate_timeline(
                moon,
                datetime(2000, 1, 1, tzinfo=timezone.utc),
                duration_years=-1,
            )

    def test_rejects_zero_duration(self) -> None:
        service = DashaService(DashaConfig())
        moon = make_moon_state()
        with pytest.raises(InvalidDashaRequestError, match="duration_years"):
            service.generate_timeline(
                moon,
                datetime(2000, 1, 1, tzinfo=timezone.utc),
                duration_years=0,
            )


class TestDashaServiceGenerateTimeline:
    """Test timeline generation."""

    def test_basic_timeline_structure(self) -> None:
        service = DashaService(DashaConfig())
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth)

        assert tl.system == DashaSystem.VIMSHOTTARI
        assert tl.birth_nakshatra == NakshatraId.ROHINI
        assert tl.birth_pada == Pada.PADA_1
        assert tl.balance_at_birth > 0
        assert len(tl.periods) > 0

    def test_first_period_starts_at_birth(self) -> None:
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth)

        assert tl.periods[0].start_utc == birth

    def test_first_mahadasha_lord_matches_nakshatra(self) -> None:
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth)

        expected_lord = NAKSHATRA_LORDS[NakshatraId.ROHINI]
        assert tl.periods[0].mahadasha_lord == expected_lord

    def test_mahadasha_only_depth1(self) -> None:
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=20)

        for period in tl.periods:
            assert period.depth == 1
            assert period.antardasha_lord is None

    def test_antardasha_depth2(self) -> None:
        config = DashaConfig(max_depth=2)
        service = DashaService(config)
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=10)

        for period in tl.periods:
            assert period.depth == 2
            assert period.antardasha_lord is not None
            assert period.pratyantardasha_lord is None

    def test_pratyantardasha_depth3(self) -> None:
        config = DashaConfig(max_depth=3)
        service = DashaService(config)
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=2)

        for period in tl.periods:
            assert period.depth == 3
            assert period.pratyantardasha_lord is not None

    def test_periods_are_contiguous(self) -> None:
        service = DashaService(DashaConfig(max_depth=2))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=10)

        for i in range(len(tl.periods) - 1):
            assert tl.periods[i].end_utc == tl.periods[i + 1].start_utc, (
                f"Gap between period {i} and {i+1}"
            )

    def test_duration_years_limits_timeline(self) -> None:
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=5)

        last = tl.periods[-1]
        total = (last.end_utc - birth).days / 365.25
        assert total <= 6.0  # Allow some tolerance for the first partial period


class TestDashaServiceGetLordAt:
    """Test lord querying at a specific instant."""

    def test_lord_at_birth(self) -> None:
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=10)
        lords = service.get_lord_at(birth, tl)

        expected_lord = NAKSHATRA_LORDS[NakshatraId.ROHINI]
        assert lords["mahadasha"] == expected_lord
        assert lords["antardasha"] is None  # depth=1

    def test_lord_at_second_period(self) -> None:
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=20)
        # Query at start of second period
        second_start = tl.periods[1].start_utc
        lords = service.get_lord_at(second_start, tl)

        assert lords["mahadasha"] == tl.periods[1].mahadasha_lord

    def test_lord_at_invalid_time(self) -> None:
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=5)
        # Query before birth
        before = datetime(1999, 1, 1, tzinfo=timezone.utc)
        lords = service.get_lord_at(before, tl)

        assert lords["mahadasha"] is None
        assert lords["antardasha"] is None
        assert lords["pratyantardasha"] is None

    def test_lord_at_with_antardasha(self) -> None:
        service = DashaService(DashaConfig(max_depth=2))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=5)
        # Query at a time that falls in an antardasha
        mid = tl.periods[5].start_utc  # Some antardasha
        lords = service.get_lord_at(mid, tl)

        assert lords["mahadasha"] is not None
        assert lords["antardasha"] is not None

    def test_lord_at_naive_datetime(self) -> None:
        """Naive datetime should be treated as UTC."""
        service = DashaService(DashaConfig(max_depth=1))
        moon = make_moon_state(NakshatraId.ROHINI, Pada.PADA_1)
        birth = datetime(2000, 1, 1, tzinfo=timezone.utc)

        tl = service.generate_timeline(moon, birth, duration_years=10)
        naive = datetime(2000, 1, 1)  # No timezone
        lords = service.get_lord_at(naive, tl)

        assert lords["mahadasha"] is not None

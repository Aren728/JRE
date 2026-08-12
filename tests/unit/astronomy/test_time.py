"""Unit tests for time normalization and the pure Julian Day conversion."""

import datetime as dt

import pytest

from astronomy.errors import InvalidTimestampError
from astronomy.time import (
    MIN_GREGORIAN_DATE,
    julian_day_ut,
    local_time_to_utc,
    validate_civil_date,
)


class TestJulianDay:
    def test_j2000(self):
        assert julian_day_ut(dt.datetime(2000, 1, 1, 12, 0, 0, tzinfo=dt.UTC)) == 2451545.0

    def test_midnight(self):
        instant = dt.datetime(2000, 1, 1, 0, 0, 0, tzinfo=dt.UTC)
        assert julian_day_ut(instant) == pytest.approx(2451544.5)

    def test_leap_day(self):
        # 2000-02-29 12:00 UTC: J2000 (2451545.0) + 59 days.
        instant = dt.datetime(2000, 2, 29, 12, 0, 0, tzinfo=dt.UTC)
        assert julian_day_ut(instant) == pytest.approx(2451604.0, abs=1e-6)

    def test_microseconds_preserved(self):
        jd = julian_day_ut(dt.datetime(2000, 1, 1, 12, 0, 0, 500000, tzinfo=dt.UTC))
        assert jd == pytest.approx(2451545.0 + 0.5 / 86400.0)

    def test_naive_rejected(self):
        with pytest.raises(InvalidTimestampError):
            julian_day_ut(dt.datetime(2000, 1, 1, 12, 0, 0))


class TestLocalToUtc:
    def test_utc_zone(self):
        utc_dt, local_iso, utc_iso = local_time_to_utc(dt.date(2000, 1, 1), dt.time(12, 0), "UTC")
        assert utc_dt == dt.datetime(2000, 1, 1, 12, 0, tzinfo=dt.UTC)
        assert utc_iso == "2000-01-01T12:00:00Z"
        assert local_iso == "2000-01-01T12:00:00+00:00"

    def test_kolkata_offset(self):
        utc_dt, local_iso, utc_iso = local_time_to_utc(
            dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata"
        )
        assert utc_dt.hour == 4 and utc_dt.minute == 30
        assert utc_iso == "1990-06-15T04:30:00Z"
        assert local_iso == "1990-06-15T10:00:00+05:30"

    def test_abbreviation_rejected(self):
        for tz in ("IST", "PST", "EST"):
            with pytest.raises(InvalidTimestampError):
                local_time_to_utc(dt.date(2000, 1, 1), dt.time(0, 0), tz)

    def test_unknown_zone_rejected(self):
        with pytest.raises(InvalidTimestampError):
            local_time_to_utc(dt.date(2000, 1, 1), dt.time(0, 0), "Mars/Olympus_Mons")

    def test_nonexistent_dst_time_rejected(self):
        # 2024-03-10 02:30 does not exist in America/New_York (spring-forward).
        with pytest.raises(InvalidTimestampError):
            local_time_to_utc(dt.date(2024, 3, 10), dt.time(2, 30), "America/New_York")

    def test_ambiguous_dst_time_resolves_fold_zero(self):
        # 2024-11-03 01:30 occurs twice; fold=0 => EDT (-4).
        utc_dt, local_iso, _ = local_time_to_utc(
            dt.date(2024, 11, 3), dt.time(1, 30), "America/New_York"
        )
        assert utc_dt == dt.datetime(2024, 11, 3, 5, 30, tzinfo=dt.UTC)
        assert local_iso == "2024-11-03T01:30:00-04:00"

    def test_pre_gregorian_rejected(self):
        with pytest.raises(InvalidTimestampError):
            local_time_to_utc(dt.date(1582, 10, 4), dt.time(0, 0), "UTC")

    def test_gregorian_transition_accepted(self):
        utc_dt, _, _ = local_time_to_utc(dt.date(1582, 10, 15), dt.time(0, 0), "UTC")
        assert utc_dt.year == 1582

    def test_microseconds_round_trip(self):
        utc_dt, _, utc_iso = local_time_to_utc(
            dt.date(2000, 1, 1), dt.time(12, 0, 0, 123456), "UTC"
        )
        assert utc_dt.microsecond == 123456
        assert utc_iso == "2000-01-01T12:00:00.123456Z"


def test_min_gregorian_date_constant():
    assert dt.date(1582, 10, 15) == MIN_GREGORIAN_DATE


def test_validate_civil_date():
    validate_civil_date(dt.date(1582, 10, 15))
    with pytest.raises(InvalidTimestampError):
        validate_civil_date(dt.date(1582, 10, 14))

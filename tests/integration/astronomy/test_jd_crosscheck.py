"""JD cross-check against the Swiss Ephemeris library.

QA found that the original pure JD formula deviated by 1-3 days for accepted
dates before 1900 (and drifted positive beyond 2100). The formula was fixed to
the canonical proleptic-Gregorian algorithm; these tests pin the fixed
behavior:

- ``julian_day_ut`` is BIT-EXACT vs ``swe.julday(..., GREG_CAL)`` across a
  dense fixture set spanning 1583-3000 AD.
- It agrees with ``swe.utc_to_jd``'s UT output within ~5e-6 days (the tiny
  residual is the UT1-vs-UTC offset inside the library, not an error).
"""

from __future__ import annotations

import datetime as dt

import pytest
import swisseph as swe

from astronomy.time import julian_day_ut

FIXTURE_YEARS = (1583, 1600, 1700, 1800, 1900, 2000, 2024, 2100, 2500, 3000)
FIXTURE_MONTHS_DAYS = ((1, 1), (2, 29), (3, 1), (7, 4), (12, 31))

UT1_UTC_TOLERANCE_DAYS = 5e-6


def _instances():
    for year in FIXTURE_YEARS:
        for month, day in FIXTURE_MONTHS_DAYS:
            try:
                yield dt.datetime(year, month, day, 12, 0, 0, tzinfo=dt.UTC)
            except ValueError:
                continue  # non-leap Feb 29


@pytest.mark.parametrize("instant", list(_instances()), ids=str)
def test_pure_jd_bit_exact_with_swe_julday(instant):
    mine = julian_day_ut(instant)
    lib = swe.julday(
        instant.year, instant.month, instant.day, 12.0, swe.GREG_CAL
    )
    assert mine == lib, f"{instant}: pure={mine!r} swe.julday={lib!r}"


@pytest.mark.parametrize("instant", list(_instances()), ids=str)
def test_pure_jd_within_ut1_tolerance_of_utc_to_jd(instant):
    mine = julian_day_ut(instant)
    _jd_et, jd_ut = swe.utc_to_jd(
        instant.year, instant.month, instant.day,
        instant.hour, instant.minute, float(instant.second), swe.GREG_CAL,
    )
    assert abs(mine - jd_ut) < UT1_UTC_TOLERANCE_DAYS, (
        f"{instant}: pure={mine!r} swe.utc_to_jd={jd_ut!r}"
    )


def test_fixed_pre_1900_era_no_longer_drifts(service):
    """Regression guard for the QA-discovered JD defect (was off by days)."""
    from tests.integration.astronomy.conftest import make_request

    result = service.compute(
        make_request(date=dt.date(1600, 1, 1), time=dt.time(12, 0, 0), timezone="UTC")
    )
    assert result.julian_day_ut == 2305448.0

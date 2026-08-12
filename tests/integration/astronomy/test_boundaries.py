"""QA requirement 18: boundary cases.

- Midnight exact.
- Leap day 2000-02-29 computes; 2000-02-28 -> 2000-03-01 spans a leap day.
- Poles (lat +-90) and lon +-180 are accepted.
- Longitude normalization keeps values in [0, 360).
- Sign/degree boundary: longitude near 0/360 stays normalized.
"""

from __future__ import annotations

import datetime as dt

from tests.integration.astronomy.conftest import make_request

from astronomy.models import BodyId


def test_midnight_utc(service):
    result = service.compute(
        make_request(
            date=dt.date(2000, 1, 1),
            time=dt.time(0, 0, 0),
            timezone="UTC",
        )
    )
    assert result.timestamp_utc_iso == "2000-01-01T00:00:00Z"
    assert result.julian_day_ut == 2451544.5
    for pos in result.positions:
        assert 0.0 <= pos.longitude_tropical < 360.0


def test_leap_day_2000(service):
    result = service.compute(
        make_request(
            date=dt.date(2000, 2, 29),
            time=dt.time(12, 0, 0),
            timezone="UTC",
        )
    )
    # J2000 (2451545.0) + 59 days (Jan 31 + Feb 29) at noon.
    assert result.julian_day_ut == 2451604.0


def test_leap_day_span(service):
    before = service.compute(
        make_request(date=dt.date(2000, 2, 28), time=dt.time(12, 0, 0), timezone="UTC")
    )
    after = service.compute(
        make_request(date=dt.date(2000, 3, 1), time=dt.time(12, 0, 0), timezone="UTC")
    )
    # Exactly 2 days apart (Feb 29 in between).
    assert after.julian_day_ut - before.julian_day_ut == 2.0


def test_poles_and_antimeridian(service):
    result = service.compute(
        make_request(latitude=90.0, longitude=180.0)
    )
    assert len(result.positions) == 9
    result = service.compute(make_request(latitude=-90.0, longitude=-180.0))
    assert len(result.positions) == 9


def test_longitude_normalized_everywhere(service):
    """Repeated samples across years keep longitudes in [0, 360)."""
    for year in (1583, 1700, 1900, 2000, 2024, 2500):
        result = service.compute(
            make_request(
                date=dt.date(year, 1, 1),
                time=dt.time(12, 0, 0),
                timezone="UTC",
            )
        )
        for pos in result.positions:
            assert 0.0 <= pos.longitude_tropical < 360.0, f"{year}: {pos.body.value}"
            if pos.longitude_sidereal is not None:
                assert 0.0 <= pos.longitude_sidereal < 360.0


def test_degree_boundary_wraparound(service):
    """A body crossing 0/360 degrees is never emitted outside [0, 360)."""
    for day in range(1, 7):
        result = service.compute(
            make_request(
                date=dt.date(2024, 3, day),
                time=dt.time(0, 0, 0),
                timezone="UTC",
            )
        )
        for pos in result.positions:
            assert 0.0 <= pos.longitude_tropical < 360.0
    # Moon crosses 0-deg longitude every ~27 days; ensure normalization holds
    # by scanning a full lunar month.
    for day in range(1, 31):
        result = service.compute(
            make_request(
                date=dt.date(2024, 1, day),
                time=dt.time(0, 0, 0),
                timezone="UTC",
            )
        )
        moon = next(p for p in result.positions if p.body is BodyId.MOON)
        assert 0.0 <= moon.longitude_tropical < 360.0

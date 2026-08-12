"""QA requirement 5: timezone conversion.

- The same UTC instant written in two different IANA zones must produce
  IDENTICAL positions (the JD is the same).
- The same local wall time in two different zones must produce DIFFERENT
  positions (different instants).
- ``timestamp_local_iso`` must carry the correct numeric offset.
"""

from __future__ import annotations

import datetime as dt

from tests.integration.astronomy.conftest import make_request


def test_same_instant_in_two_zones_identical_positions(service):
    # 1990-06-15 10:00 Asia/Kolkata == 1990-06-15 04:30 UTC ==
    # 1990-06-15 00:30 America/New_York (EDT).
    kolkata = service.compute(make_request(timezone="Asia/Kolkata"))
    ny = service.compute(
        make_request(time=dt.time(0, 30, 0), timezone="America/New_York")
    )
    assert kolkata.timestamp_utc_iso == ny.timestamp_utc_iso
    assert kolkata.julian_day_ut == ny.julian_day_ut
    assert kolkata.positions == ny.positions


def test_same_wall_time_in_two_zones_different_positions(service):
    kolkata = service.compute(make_request(timezone="Asia/Kolkata"))
    utc = service.compute(make_request(timezone="UTC"))
    assert kolkata.timestamp_utc_iso != utc.timestamp_utc_iso
    # Moon moves ~13 deg/day; 5.5h apart is a clear difference.
    moon_k = next(p for p in kolkata.positions if p.body.value == "MOON")
    moon_u = next(p for p in utc.positions if p.body.value == "MOON")
    assert abs(moon_k.longitude_tropical - moon_u.longitude_tropical) > 1.0


def test_local_iso_offset_echoes_zone(service):
    result = service.compute(make_request(timezone="Asia/Kolkata"))
    assert result.timestamp_local_iso.endswith("+05:30")
    result = service.compute(make_request(timezone="UTC"))
    assert result.timestamp_local_iso.endswith("+00:00")


def test_dateline_zone_maps_to_previous_utc_day(service):
    # 2024-01-01 00:00 Pacific/Auckland (NZDT, +13) = 2023-12-31 11:00 UTC.
    result = service.compute(
        make_request(
            date=dt.date(2024, 1, 1),
            time=dt.time(0, 0, 0),
            timezone="Pacific/Auckland",
        )
    )
    assert result.timestamp_utc_iso == "2023-12-31T11:00:00Z"
    assert result.timestamp_local_iso == "2024-01-01T00:00:00+13:00"

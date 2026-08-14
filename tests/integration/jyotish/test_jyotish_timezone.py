"""Timezone handling (test plan §16): same instant, two zones -> identical."""

from __future__ import annotations

import datetime as dt

from tests.integration.jyotish.conftest import make_birth


def test_same_instant_two_zones_identical_states(service):
    # 1990-06-15 10:00 Asia/Kolkata == 1990-06-15 04:30 UTC ==
    # 1990-06-15 00:30 America/New_York (EDT).
    kolkata = service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.209
    )
    ny = service.planetary_state(
        dt.date(1990, 6, 15), dt.time(0, 30, 0), "America/New_York", 28.6139, 77.209
    )
    assert [s.to_dict() for s in kolkata] == [s.to_dict() for s in ny]
    assert kolkata[0].timestamp_utc_iso == ny[0].timestamp_utc_iso


def test_same_wall_time_two_zones_differ(service):
    kolkata = service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "Asia/Kolkata", 28.6139, 77.209
    )
    utc = service.planetary_state(
        dt.date(1990, 6, 15), dt.time(10, 0, 0), "UTC", 28.6139, 77.209
    )
    assert kolkata[0].timestamp_utc_iso != utc[0].timestamp_utc_iso
    # The Moon moves ~13°/day: 5.5h apart is a clear difference.
    moon_k = next(s for s in kolkata if s.body.value == "MOON")
    moon_u = next(s for s in utc if s.body.value == "MOON")
    assert abs(moon_k.longitude_used - moon_u.longitude_used) > 1.0


def test_chart_birth_timezone_correct_instant(service):
    """A birth in Asia/Kolkata maps to the right UTC instant for the lagna."""
    birth = make_birth(time="10:00:00", timezone="Asia/Kolkata")
    chart = service.chart(birth)
    # 1990-06-15T10:00+05:30 = 04:30 UTC.
    assert chart.planet_states[0].timestamp_utc_iso == "1990-06-15T04:30:00Z"


def test_dateline_zone(service):
    # 2024-01-01 00:00 Pacific/Auckland (+13) = 2023-12-31 11:00 UTC.
    states = service.planetary_state(
        dt.date(2024, 1, 1), dt.time(0, 0, 0), "Pacific/Auckland", -36.85, 174.76
    )
    assert states[0].timestamp_utc_iso == "2023-12-31T11:00:00Z"


def test_transit_timezone_consistency(service):
    """Transit-through-houses uses the transit timezone for the transit instant."""
    from jyotish.models import TransitReferencePoint

    birth = make_birth()
    lagna_ist = service.transit_through_houses(
        birth, dt.date(2000, 1, 1), dt.time(10, 0, 0), "Asia/Kolkata",
        reference=TransitReferencePoint.LAGNA,
    )
    assert lagna_ist.transit_instant_utc_iso == "2000-01-01T04:30:00Z"

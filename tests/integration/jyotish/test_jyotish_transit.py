"""Continuous transit events with the real ephemeris (req. E, ADR-005).

Uses known astronomical events:
- Jupiter's sidereal ingress into MESHA (0°): Jupiter was in sidereal Aries
  from mid-2008 through 2009 (sidereal ingress ~ 2008-07). The exact instant
  is validated only structurally here; the deterministic engine behavior is
  covered by the unit suite. Independent reference validation lives in the
  VALIDATOR stage.
"""

from __future__ import annotations

from astronomy.models import BodyId
from jyotish.models import RashiId, TransitEventKind


def test_jupiter_rashi_ingress_found_in_2011(service):
    """Jupiter's sidereal ingress into MESHA occurred 2011-05-08 (~08:44 UTC)."""
    events = service.events_between(
        "2011-05-01T00:00:00Z",
        "2011-06-01T00:00:00Z",
        (BodyId.JUPITER,),
        (TransitEventKind.RASHI_INGRESS,),
    )
    ingresses = [e for e in events if e.kind is TransitEventKind.RASHI_INGRESS]
    assert len(ingresses) == 1
    event = ingresses[0]
    assert event.body is BodyId.JUPITER
    assert event.reached is RashiId.MESHA  # sidereal ingress into Aries
    assert event.event_utc_iso.startswith("2011-05-08")
    # Cross-check the event instant: re-compute the state at that time.
    states = service.position_at(event.event_julian_day_ut, (BodyId.JUPITER,))
    jupiter = states[0]
    assert abs(jupiter.longitude_used - 0.0) < 0.01 or abs(jupiter.longitude_used - 360.0) < 0.01


def test_moon_nakshatra_ingress_daily(service):
    """The Moon crosses nakshatra boundaries ~every 24h/27 -> several in a month."""
    events = service.events_between(
        "2000-01-01T00:00:00Z",
        "2000-01-31T00:00:00Z",
        (BodyId.MOON,),
        (TransitEventKind.NAKSHATRA_INGRESS,),
    )
    ingresses = [e for e in events if e.kind is TransitEventKind.NAKSHATRA_INGRESS]
    assert len(ingresses) >= 25  # 27 nakshatras per ~27.3-day sidereal month


def test_sun_rashi_ingress_per_year(service):
    """The Sun enters each sidereal rashi once per year."""
    events = service.events_between(
        "2001-01-01T00:00:00Z",
        "2002-01-01T00:00:00Z",
        (BodyId.SUN,),
        (TransitEventKind.RASHI_INGRESS,),
    )
    ingresses = [e for e in events if e.kind is TransitEventKind.RASHI_INGRESS]
    assert len(ingresses) == 12


def test_events_deterministic_and_sorted(service):
    first = service.events_between(
        "2001-01-01T00:00:00Z",
        "2001-06-01T00:00:00Z",
        (BodyId.SUN, BodyId.MOON),
        (TransitEventKind.RASHI_INGRESS,),
    )
    second = service.events_between(
        "2001-01-01T00:00:00Z",
        "2001-06-01T00:00:00Z",
        (BodyId.SUN, BodyId.MOON),
        (TransitEventKind.RASHI_INGRESS,),
    )
    assert [e.to_dict() for e in first] == [e.to_dict() for e in second]
    times = [e.event_julian_day_ut for e in first]
    assert times == sorted(times)


def test_station_events_occur_for_outer_planets(service):
    """Jupiter stations at least twice (R->D, D->R) in 2008."""
    events = service.events_between(
        "2008-01-01T00:00:00Z",
        "2009-01-01T00:00:00Z",
        (BodyId.JUPITER,),
        (TransitEventKind.STATION_RETROGRADE, TransitEventKind.STATION_DIRECT),
    )
    kinds = {e.kind for e in events}
    assert TransitEventKind.STATION_RETROGRADE in kinds
    assert TransitEventKind.STATION_DIRECT in kinds

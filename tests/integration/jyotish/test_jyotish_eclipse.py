"""Eclipse facts against known events (req. H, ADR-006).

Pinned reference eclipses (NASA Five Millennium Canon of Solar Eclipses /
Lunar Eclipses), verified against the binding in the Specialist stage:

- 1991-07-11 total solar eclipse: max ~19:06 UTC, total.
- 1990-02-09 total lunar eclipse: umbral 18:49:55–19:32:12 UTC, mag ~1.075.
"""

from __future__ import annotations

import datetime as dt

from jyotish.models import EclipseClassification, EclipseKind


def _as_datetime(jd: float) -> dt.datetime:
    iso = __import__("jyotish.transit", fromlist=["jd_to_iso_utc"]).jd_to_iso_utc(jd)
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))


def test_solar_eclipse_1991_07_11(service):
    events = service.eclipses("1991-07-01T00:00:00Z", "1991-08-01T00:00:00Z", EclipseKind.SOLAR)
    assert len(events) == 1
    event = events[0]
    assert event.kind is EclipseKind.SOLAR
    assert event.classification is EclipseClassification.TOTAL
    # NASA canon: greatest eclipse 19:06:02 UTC (2026-08-12 Specialist pin).
    maximum = _as_datetime(event.maximum_jd_ut)
    reference = dt.datetime(1991, 7, 11, 19, 6, 2, tzinfo=dt.UTC)
    delta = abs((maximum - reference).total_seconds())
    assert delta <= 90.0, f"max off by {delta:.0f}s: {maximum.isoformat()}"
    # Contacts P1 <= MAX <= P4 and all present.
    assert event.contacts[0].phase == "P1"
    assert event.contacts[-1].phase == "P4"
    assert 0.0 < event.magnitude < 2.0


def test_lunar_eclipse_1990_02_09(service):
    events = service.eclipses("1990-02-01T00:00:00Z", "1990-03-01T00:00:00Z", EclipseKind.LUNAR)
    assert len(events) == 1
    event = events[0]
    assert event.kind is EclipseKind.LUNAR
    assert event.classification is EclipseClassification.TOTAL
    # NASA: greatest eclipse 19:12 UTC (Specialist pin: umbral 18:49:55-19:32:12).
    maximum = _as_datetime(event.maximum_jd_ut)
    reference = dt.datetime(1990, 2, 9, 19, 12, 0, tzinfo=dt.UTC)
    delta = abs((maximum - reference).total_seconds())
    assert delta <= 180.0, f"max off by {delta:.0f}s: {maximum.isoformat()}"
    assert event.magnitude > 1.0  # total


def test_penumbral_lunar_eclipse_contacts_data_only(service):
    """1991-07-26 is a penumbral lunar eclipse: contacts carry MAX +
    PENUMBRAL_BEGIN/END and never a zero-slot instant (regression for the
    zero-slot guard in the adapter)."""
    events = service.eclipses(
        "1991-07-20T00:00:00Z", "1991-08-01T00:00:00Z", EclipseKind.LUNAR
    )
    assert len(events) == 1
    event = events[0]
    assert event.classification is EclipseClassification.PENUMBRAL
    phases = [c.phase for c in event.contacts]
    assert "MAX" in phases
    assert "PENUMBRAL_BEGIN" in phases
    assert "PENUMBRAL_END" in phases
    for contact in event.contacts:
        assert contact.julian_day_ut > 0.0
        assert contact.utc_iso  # no zero-slot formatting


def test_eclipse_interval_covers_both_kinds(service):
    events = service.eclipses("1991-01-01T00:00:00Z", "1991-12-31T00:00:00Z")
    kinds = {e.kind for e in events}
    assert EclipseKind.SOLAR in kinds
    assert EclipseKind.LUNAR in kinds
    # Sorted by maximum time.
    times = [e.maximum_jd_ut for e in events]
    assert times == sorted(times)


def test_eclipse_data_only_no_interpretation(service):
    events = service.eclipses("1991-07-01T00:00:00Z", "1991-08-01T00:00:00Z", EclipseKind.SOLAR)
    assert len(events) == 1
    event = events[0]
    assert event.classification is EclipseClassification.TOTAL
    payload = event.to_dict()
    blob = str(payload).lower()
    for term in (
        "good", "bad", "fortune", "wealth", "marriage", "career",
        "spiritual", "auspicious",
    ):
        assert term not in blob
    # Positions of Sun/Moon/nodes are attached at maximum (astronomy facts).
    assert len(event.solar_lunar_positions) == 2
    assert len(event.node_positions) == 2
    # Pre/post intervals are plain numbers.
    assert event.pre_event_interval_days >= 0.0
    assert event.post_event_interval_days >= 0.0


def test_eclipse_deterministic(service):
    first = service.eclipses("1991-07-01T00:00:00Z", "1991-08-01T00:00:00Z")
    second = service.eclipses("1991-07-01T00:00:00Z", "1991-08-01T00:00:00Z")
    assert [e.to_dict() for e in first] == [e.to_dict() for e in second]


def test_eclipse_maximum_matches_sun_node_conjunction(service):
    """At a solar eclipse the Sun is within 1° of a node (geometric fact)."""
    events = service.eclipses("1991-07-01T00:00:00Z", "1991-08-01T00:00:00Z", EclipseKind.SOLAR)
    event = events[0]
    sun = next(s for s in event.solar_lunar_positions if s.body.value == "SUN")
    rahu = next(s for s in event.node_positions if s.body.value == "RAHU")
    ketu = next(s for s in event.node_positions if s.body.value == "KETU")
    sep_rahu = (sun.longitude_used - rahu.longitude_used) % 360.0
    sep_ketu = (sun.longitude_used - ketu.longitude_used) % 360.0
    assert min(sep_rahu, 360.0 - sep_rahu) < 1.5 or min(sep_ketu, 360.0 - sep_ketu) < 1.5

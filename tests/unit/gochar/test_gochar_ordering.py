"""Event ordering tests (TEST-PLAN §2 rows 11/13, SPEC §13.6-§13.7).

The pinned total order is ``(event_julian_day_ut, body.value, kind.value)``
with a stable sort; ties at identical ``(jd, body, kind)`` retain source
order. Simultaneous events (rashi + nakshatra at one instant) sort by
``body.value`` then ``kind.value``. JRE-006 never modifies
``TransitEvent`` fields — identity is the echoed tuple + ordinal.
"""

from __future__ import annotations

from tests.unit.gochar.conftest import make_event

from gochar import sort_events
from gochar.derive import _event_key
from jyotish import BodyId, TransitEventKind


def test_sort_events_orders_by_jd_body_kind() -> None:
    events = (
        make_event(
            body=BodyId.MOON, kind=TransitEventKind.RASHI_INGRESS,
            event_julian_day_ut=3.0,
        ),
        make_event(
            body=BodyId.SUN, kind=TransitEventKind.RASHI_INGRESS,
            event_julian_day_ut=2.0,
        ),
        make_event(
            body=BodyId.SUN, kind=TransitEventKind.STATION_RETROGRADE,
            event_julian_day_ut=1.0,
        ),
    )
    sorted_events = sort_events(events)
    assert [e.event_julian_day_ut for e in sorted_events] == [1.0, 2.0, 3.0]


def test_sort_is_identity_preserving_for_jre003_order() -> None:
    """SPEC §13.6 — the re-sort is identity-preserving for JRE-003 output."""
    events = (
        make_event(body=BodyId.SUN, event_julian_day_ut=1.0),
        make_event(body=BodyId.MOON, event_julian_day_ut=2.0),
    )
    assert sort_events(events) == events


def test_simultaneous_events_tie_break() -> None:
    """SPEC §13.7 — rashi + nakshatra at one instant sort by body then kind."""
    events = (
        make_event(
            body=BodyId.MOON, kind=TransitEventKind.NAKSHATRA_INGRESS,
            event_julian_day_ut=0.0,
        ),
        make_event(
            body=BodyId.MOON, kind=TransitEventKind.RASHI_INGRESS,
            event_julian_day_ut=0.0,
        ),
    )
    sorted_events = sort_events(events)
    assert [e.kind.value for e in sorted_events] == [
        "NAKSHATRA_INGRESS",
        "RASHI_INGRESS",
    ]


def test_stable_sort_preserves_source_order_for_ties() -> None:
    """Identical (jd, body, kind) keep source-stream relative order."""
    a = make_event(body=BodyId.SUN, event_julian_day_ut=1.0)
    b = make_event(body=BodyId.SUN, event_julian_day_ut=1.0)
    # b has a different metadata marker (iterations) to distinguish them.
    from dataclasses import replace

    b = replace(
        b,
        search_metadata=replace(b.search_metadata, iterations=9),
    )
    assert sort_events((b, a)) == (b, a)
    assert sort_events((a, b)) == (a, b)


def test_event_key_is_pinned() -> None:
    event = make_event(
        body=BodyId.MOON, kind=TransitEventKind.RASHI_INGRESS,
        event_julian_day_ut=2451545.0,
    )
    assert _event_key(event) == (2451545.0, "MOON", "RASHI_INGRESS")


def test_events_never_modified_by_gochar() -> None:
    """Event identity = echoed TransitEvent + ordinal; gochar never mutates
    fields (ADR-023)."""
    events = (
        make_event(body=BodyId.SUN, kind=TransitEventKind.RASHI_INGRESS,
                   event_julian_day_ut=2.0),
        make_event(body=BodyId.MOON, kind=TransitEventKind.RASHI_EGRESS,
                   event_julian_day_ut=1.0),
    )
    sorted_events = sort_events(events)
    assert sorted_events[0] is events[1]
    assert sorted_events[1] is events[0]
    # reached bucket preserved verbatim.
    assert sorted_events[0].reached is None


def test_sort_empty() -> None:
    assert sort_events(()) == ()


def test_sort_events_handles_all_kinds() -> None:
    events = tuple(
        make_event(kind=kind, body=BodyId.MOON) for kind in TransitEventKind
    )
    sorted_events = sort_events(events)
    assert len(sorted_events) == len(events)
    assert [e.kind for e in sorted_events] == [e.kind for e in sorted(events, key=_event_key)]

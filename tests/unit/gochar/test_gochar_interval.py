"""Interval unit tests (TEST-PLAN §2 rows 15-16, SPEC §12).

``GocharIntervalResult`` echoes the JRE-003 event stream (re-asserted
pinned order) and the sampled state series; the natal-frame house series
is config-gated (``natal_house_series=true`` + a supplied anchor), each
sample converted to civil UTC and derived through the JRE-005 path.
"""

from __future__ import annotations

from tests.unit.gochar.conftest import make_event

from gochar import (
    GocharConfig,
    GocharIntervalRequest,
    GocharService,
    result_to_dict,
)
from jyotish import BirthData, BodyId, TransitEventKind

BIRTH = BirthData(
    date="1990-06-15",
    time="10:00:00",
    timezone="Asia/Kolkata",
    latitude=28.6139,
    longitude=77.2090,
)


def test_interval_echoes_events_verbatim(fake_service) -> None:
    events = (
        make_event(body=BodyId.MOON, kind=TransitEventKind.RASHI_INGRESS,
                   event_julian_day_ut=100.0),
        make_event(body=BodyId.SUN, kind=TransitEventKind.STATION_RETROGRADE,
                   event_julian_day_ut=50.0),
    )
    fake_service._events = events
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-15T00:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    assert [e.event_julian_day_ut for e in result.events] == [50.0, 100.0]
    assert result.bodies == ("SUN", "MOON")
    assert result.natal_house_series is None
    assert result.natal_anchor is None


def test_interval_state_series_echo_ascending(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-03T00:00:00.000000Z",
            bodies=(BodyId.SUN,),
            config=GocharConfig(sample_step_hours=24.0),
        )
    )
    jds = [s.julian_day_ut for s in result.state_samples]
    assert jds == sorted(jds)
    assert len(jds) == 3  # Jun 1, 2, 3
    assert all(s.body is BodyId.SUN for s in result.state_samples)


def test_interval_natal_house_series_gated(fake_service) -> None:
    """SPEC §12.3 — ``natal_house_series=true`` + anchor produces one
    TransitHouseAnalysis per sample; per-sample civil UTC used."""
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-03T00:00:00.000000Z",
            bodies=(BodyId.SUN,),
            natal_anchor=BIRTH,
            config=GocharConfig(natal_house_series=True, sample_step_hours=24.0),
        )
    )
    assert result.natal_anchor == BIRTH
    assert result.natal_house_series is not None
    assert len(result.natal_house_series) == 3
    # Per-sample facts: frame TRANSIT, canonical body order.
    for analysis in result.natal_house_series:
        assert analysis.birth_snapshot == BIRTH
        assert [f.body.value for f in analysis.transit_facts] == [
            b.value for b in tuple(BodyId)
        ]
        from bhava import FactFrame

        assert all(f.frame is FactFrame.TRANSIT for f in analysis.transit_facts)


def test_interval_natal_series_disabled_by_default(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-03T00:00:00.000000Z",
            bodies=(BodyId.SUN,),
            natal_anchor=BIRTH,  # anchor present but flag off
        )
    )
    assert result.natal_anchor == BIRTH
    assert result.natal_house_series is None


def test_interval_bodies_canonical_echo(fake_service) -> None:
    svc = GocharService(fake_service)
    result = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-15T00:00:00.000000Z",
            bodies=(BodyId.KETU, BodyId.SUN, BodyId.MOON),
        )
    )
    assert result.bodies == ("SUN", "MOON", "KETU")


def test_interval_separation_generic_vs_individual(fake_service) -> None:
    """SPEC §17 — a generic interval has no natal content; an anchored one
    echoes the anchor. Shapes never mix."""
    svc = GocharService(fake_service)
    generic = svc.analyze_interval(
        GocharIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-03T00:00:00.000000Z",
            bodies=(BodyId.SUN,),
        )
    )
    assert generic.natal_anchor is None
    assert generic.natal_house_series is None
    payload = result_to_dict(generic)
    assert payload["natal_anchor"] is None
    assert payload["natal_house_series"] is None

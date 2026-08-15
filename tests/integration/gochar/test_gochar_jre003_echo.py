"""JRE-003 echo identity tests (TEST-PLAN row 10/15, SPEC §12-§13, DC §9).

Hard gates:
- the interval ``events`` tuple is a verbatim echo of
  ``jyotish.events_between`` (byte-identical serialized values);
- ``state_samples`` is a verbatim echo of ``jyotish.state_series`` at the
  configured step, ascending JD.
"""

from __future__ import annotations

from gochar import GocharConfig, GocharIntervalRequest
from jyotish import BodyId


def test_event_stream_echo_byte_identity(gochar_service, jyotish_service) -> None:
    """TEST-PLAN row 10 — JRE-006 events == JRE-003 events_between output."""
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-08-01T00:00:00.000000Z",
        bodies=(BodyId.MOON, BodyId.SUN),
    )
    result = gochar_service.analyze_interval(req)

    # Independent JRE-003 computation (same call the service delegated to):
    # the service passes its resolved JRE-003 config; mirror it exactly.
    from gochar.service import _jyotish_config

    jyotish_cfg = _jyotish_config(GocharConfig().house_system)
    events = jyotish_service.events_between(
        req.start_utc_iso, req.end_utc_iso, (BodyId.MOON, BodyId.SUN), None, jyotish_cfg
    )
    assert len(result.events) == len(events)
    for echoed, independent in zip(result.events, events, strict=True):
        ed, ind = echoed.to_dict(), independent.to_dict()
        # All event content must match. ``search_metadata.position_calls``
        # is documented cache-dependent upstream (JRE-003
        # ``test_position_calls_bounded_and_cache_independent``, ADR-005
        # bounded LRU) — excluded from the echo-identity comparison.
        assert ed["body"] == ind["body"]
        assert ed["kind"] == ind["kind"]
        assert ed["event_julian_day_ut"] == ind["event_julian_day_ut"]
        assert ed["event_utc_iso"] == ind["event_utc_iso"]
        assert ed["boundary_deg"] == ind["boundary_deg"]
        assert ed["reached"] == ind["reached"]
        assert ed["direction"] == ind["direction"]
        assert ed["search_metadata"]["algorithm"] == ind["search_metadata"]["algorithm"]
        assert (
            ed["search_metadata"]["sample_step_hours"]
            == ind["search_metadata"]["sample_step_hours"]
        )
        assert (
            ed["search_metadata"]["tolerance_jd"]
            == ind["search_metadata"]["tolerance_jd"]
        )
        assert ed["search_metadata"]["iterations"] == ind["search_metadata"]["iterations"]


def test_state_series_echo_ascending_jd(gochar_service, jyotish_service) -> None:
    """TEST-PLAN row 15 — state_samples echo state_series at config step."""
    req = GocharIntervalRequest(
        start_utc_iso="2026-06-01T00:00:00.000000Z",
        end_utc_iso="2026-06-05T00:00:00.000000Z",
        bodies=(BodyId.SUN,),
        config=GocharConfig(sample_step_hours=24.0),
    )
    result = gochar_service.analyze_interval(req)

    from gochar.service import _jyotish_config

    jyotish_cfg = _jyotish_config(GocharConfig().house_system)
    series = jyotish_service.state_series(
        req.start_utc_iso, req.end_utc_iso, 1.0, (BodyId.SUN,), jyotish_cfg
    )
    assert len(result.state_samples) == len(series)
    assert [s.to_dict() for s in result.state_samples] == [
        s.to_dict() for s in series
    ]
    # Ascending JD.
    jds = [s.julian_day_ut for s in result.state_samples]
    assert jds == sorted(jds)


def test_events_monotonic_and_ordered(gochar_service) -> None:
    """Re-asserted pinned order (jd, body, kind) is non-decreasing."""
    req = GocharIntervalRequest(
        start_utc_iso="2026-01-01T00:00:00.000000Z",
        end_utc_iso="2026-12-31T00:00:00.000000Z",
        bodies=(BodyId.MOON, BodyId.SUN, BodyId.MARS, BodyId.MERCURY),
    )
    result = gochar_service.analyze_interval(req)
    keys = [
        (e.event_julian_day_ut, e.body.value, e.kind.value) for e in result.events
    ]
    assert keys == sorted(keys)
    # Identity = echoed TransitEvent + positional ordinal in the sorted
    # tuple (DC §4.3): re-running yields identical tuples.
    again = gochar_service.analyze_interval(req)
    assert [e.to_dict() for e in again.events] == [e.to_dict() for e in result.events]

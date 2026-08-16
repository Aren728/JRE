"""Lower-layer echo fidelity (TEST-PLAN row 24-26, SPEC §2/§23).

JRE-007 echoes lower-layer outputs verbatim: snapshot planet states equal
the direct JRE-003 ``planetary_state`` output; the natal chart echo holds
the JRE-003 chart parts; the natal house analysis equals the direct
JRE-005 derivation; interval events/samples equal the direct JRE-003
outputs; eclipse facts are a JRE-003 echo (ADR-006/027).
"""

from __future__ import annotations

import datetime

from bhava import BhavaConfig
from context import (
    ContextEclipseRequest,
    ContextInstantRequest,
    ContextIntervalRequest,
    ContextNatalRequest,
)
from jyotish import BodyId, HouseSystem, JyotishConfig


def _whole_sign_jyotish_config() -> JyotishConfig:
    from dataclasses import replace

    return replace(JyotishConfig(), house_system=HouseSystem.WHOLE_SIGN)


def test_instant_states_echo_direct_jyotish(context_service, jyotish_service) -> None:
    from context import canonical_bodies

    bodies = canonical_bodies((BodyId.SUN, BodyId.MOON, BodyId.MARS))
    direct = jyotish_service.planetary_state(
        datetime.date(2026, 6, 15),
        datetime.time(12, 0, 0),
        "UTC", 0.0, 0.0, bodies, _whole_sign_jyotish_config(),
    )
    snapshot = context_service.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=bodies,
        )
    )
    assert snapshot.planet_states == direct


def test_natal_house_analysis_echoes_jre005(context_service, jyotish_service, birth) -> None:
    from bhava import derive_house_analysis

    chart = jyotish_service.chart(birth, _whole_sign_jyotish_config())
    direct = derive_house_analysis(chart, config=BhavaConfig())
    snapshot = context_service.snapshot_natal(ContextNatalRequest(birth=birth))
    assert snapshot.house_analyses == (direct,)
    # The full JRE-003 NatalChart is echoed verbatim — provider metadata
    # included — never reconstructed by JRE-007 (SPEC §2/§23).
    assert snapshot.natal_chart == chart
    assert snapshot.natal_chart is not None
    assert snapshot.natal_chart.bhavas == chart.bhavas
    assert snapshot.natal_chart.lagna == chart.lagna
    assert snapshot.natal_chart.planet_states == chart.planet_states
    assert snapshot.natal_chart.provider_metadata == chart.provider_metadata


def test_interval_echoes_direct_jyotish(context_service, jyotish_service) -> None:
    # JRE-007 canonicalizes body order (SUN..KETU) deterministically (SPEC
    # §9/DC §4.4); the direct comparison uses the same canonical order so
    # the echo is verified against the identical delegated computation.
    from context import canonical_bodies

    bodies = canonical_bodies((BodyId.MOON, BodyId.SUN))
    events = jyotish_service.events_between(
        "2026-06-01T00:00:00.000000Z", "2026-08-01T00:00:00.000000Z",
        bodies, None, _whole_sign_jyotish_config(),
    )
    samples = jyotish_service.state_series(
        "2026-06-01T00:00:00.000000Z", "2026-08-01T00:00:00.000000Z",
        1.0, bodies, _whole_sign_jyotish_config(),
    )
    snapshot = context_service.snapshot_interval(
        ContextIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-08-01T00:00:00.000000Z",
            bodies=(BodyId.MOON, BodyId.SUN),
        )
    )
    assert snapshot.transit_events == events
    assert snapshot.state_samples == samples


def test_eclipses_echo_direct_jyotish(context_service, jyotish_service) -> None:
    direct = jyotish_service.eclipses(
        "2026-01-01T00:00:00.000000Z", "2026-12-31T00:00:00.000000Z",
        None, _whole_sign_jyotish_config(),
    )
    snapshot = context_service.snapshot_eclipses(
        ContextEclipseRequest(
            start_utc_iso="2026-01-01T00:00:00.000000Z",
            end_utc_iso="2026-12-31T00:00:00.000000Z",
        )
    )
    assert snapshot.eclipses == direct
    # Data-only echo: no significance/classification claims beyond JRE-003.
    for event in snapshot.eclipses:
        assert event.provider_id
        assert event.ephemeris_version


def test_natal_vs_transit_frames_never_merged(context_service) -> None:
    """SPEC §17 / ADR-021/025: a snapshot carries either natal or transit
    sections — the two never co-occur in one fact field."""
    instant = context_service.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN,),
        )
    )
    assert instant.natal_chart is None
    assert instant.transit_events is None  # instant has no interval events
    # Interval snapshots carry transit facts, never natal sections.
    interval = context_service.snapshot_interval(
        ContextIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-08-01T00:00:00.000000Z",
            bodies=(BodyId.SUN,),
        )
    )
    assert interval.natal_chart is None
    assert interval.house_analyses is None
    assert interval.transit_events is not None

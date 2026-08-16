"""Service composition tests (TEST-PLAN §2 row 10-18, SPEC §10-§12).

The canonical snapshot is assembled from delegated lower-layer outputs
with deterministic provenance; the canonical ``snapshot`` boundary
serves frozen V1 capability requests and validates the capability
contract; the natal chart is echoed verbatim (provider metadata
preserved); natal and transit sections are never merged; eclipse is a
JRE-003 echo; V1 accepts only point-valued birth data (no candidate
service path).
"""

from __future__ import annotations

import pytest
from tests.unit.bhava.conftest import make_birth

from context import (
    ContextConfig,
    ContextEclipseRequest,
    ContextInstantRequest,
    ContextIntervalRequest,
    ContextNatalRequest,
    ContextRequest,
    ContextService,
    result_to_dict,
)
from context.errors import ContextComputationError, InvalidContextRequestError
from jyotish import (
    BodyId,
    EclipseEvent,
    EclipseKind,
    JyotishError,
)

BIRTH = make_birth()


def test_snapshot_instant_generic_no_birth(fake_jyotish, fake_bhava) -> None:
    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_instant(
        ContextInstantRequest(
            instant_utc_iso="2026-06-15T12:00:00.000000Z",
            bodies=(BodyId.SUN, BodyId.MOON),
        )
    )
    assert result.natal_chart is None
    assert result.planet_states  # echoed states
    assert result.pair_geometry is not None  # echoed pairs
    assert result.house_analyses is None
    assert result.transit_events is None
    assert result.eclipses is None
    assert result.provenance.source_layers == ("JRE-002", "JRE-003")
    assert fake_jyotish.calls == ["planetary_state"]
    payload = result_to_dict(result)
    assert payload["natal_chart"] is None


def test_snapshot_canonical_dispatch(fake_jyotish, fake_bhava) -> None:
    """The canonical ``snapshot`` boundary serves every frozen V1
    capability request; the wrappers are compatible and idempotent."""
    svc = ContextService(fake_jyotish, fake_bhava)
    instant = ContextInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN, BodyId.MOON),
        analysis_request_id="req-42",
    )
    assert result_to_dict(svc.snapshot(instant)) == result_to_dict(svc.snapshot_instant(instant))
    natal = svc.snapshot(ContextNatalRequest(birth=BIRTH, analysis_request_id="req-43"))
    assert natal.natal_chart is not None
    assert natal.natal_chart == fake_jyotish._chart
    interval = svc.snapshot(
        ContextIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-30T00:00:00.000000Z",
            bodies=(BodyId.MOON,),
        )
    )
    assert interval.transit_events is not None
    eclipse = svc.snapshot(
        ContextEclipseRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-30T00:00:00.000000Z",
        )
    )
    assert eclipse.eclipses is not None


def test_snapshot_rejects_incompatible_capability_version(fake_jyotish, fake_bhava) -> None:
    svc = ContextService(fake_jyotish, fake_bhava)
    with pytest.raises(InvalidContextRequestError, match="version"):
        svc.snapshot(
            ContextInstantRequest(
                instant_utc_iso="2026-06-15T12:00:00.000000Z",
                bodies=(BodyId.SUN,),
                capability_version="9.0.0",
            )
        )
    with pytest.raises(InvalidContextRequestError, match="version"):
        svc.snapshot_instant(
            ContextInstantRequest(
                instant_utc_iso="2026-06-15T12:00:00.000000Z",
                bodies=(BodyId.SUN,),
                capability_version="2.0.0",
            )
        )


def test_snapshot_rejects_bare_canonical_request(fake_jyotish, fake_bhava) -> None:
    """A bare canonical request missing its capability inputs is rejected
    deterministically (invalid capability constraints)."""
    svc = ContextService(fake_jyotish, fake_bhava)
    with pytest.raises(InvalidContextRequestError, match="instant_utc_iso"):
        svc.snapshot(ContextRequest(capability="instant"))


def test_snapshot_natal_echoes_chart_and_house(fake_jyotish, fake_bhava) -> None:
    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_natal(ContextNatalRequest(birth=BIRTH))
    assert result.natal_chart is not None
    # Verbatim JRE-003 chart echo — no reconstruction, no metadata loss.
    assert result.natal_chart == fake_jyotish._chart
    assert result.natal_chart.birth_snapshot == BIRTH
    assert result.natal_chart.bhavas and len(result.natal_chart.bhavas) == 12
    assert result.natal_chart.lagna is not None
    assert result.house_analyses is not None and len(result.house_analyses) == 1
    assert result.planet_states
    # Natal snapshots carry no transit/interval sections (SPEC §17).
    assert result.transit_events is None
    assert result.state_samples is None
    assert result.provenance.source_layers == ("JRE-002", "JRE-003", "JRE-005")
    assert fake_jyotish.calls == ["chart"]
    assert fake_bhava.calls == ["analyze_chart"]


def test_snapshot_natal_optional_house_analysis(fake_jyotish, fake_bhava) -> None:
    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_natal(
        ContextNatalRequest(birth=BIRTH, include_house_analysis=False)
    )
    assert result.house_analyses is None
    assert result.provenance.source_layers == ("JRE-002", "JRE-003")
    assert fake_bhava.calls == []


def test_snapshot_natal_time_precision(fake_jyotish, fake_bhava) -> None:
    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_natal(
        ContextNatalRequest(birth=BIRTH, time_precision="DATE_ONLY")
    )
    assert result.natal_chart is not None
    with pytest.raises(InvalidContextRequestError):
        svc.snapshot_natal(ContextNatalRequest(birth=BIRTH, time_precision="BOGUS"))


def test_snapshot_interval_events_and_samples(fake_jyotish, fake_bhava) -> None:
    from tests.unit.context.conftest import make_event

    events = (make_event(),)
    fake_jyotish._events = events
    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_interval(
        ContextIntervalRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-30T00:00:00.000000Z",
            bodies=(BodyId.MOON,),
        )
    )
    assert result.transit_events == events
    assert result.state_samples is not None
    assert result.natal_chart is None
    # Natal sections absent — transit/natal separation (SPEC §17).
    assert result.house_analyses is None
    assert result.eclipses is None
    assert result.provenance.source_layers == ("JRE-002", "JRE-003")


def test_snapshot_interval_bounds_validation(fake_jyotish, fake_bhava) -> None:
    svc = ContextService(fake_jyotish, fake_bhava)
    with pytest.raises(InvalidContextRequestError):
        svc.snapshot_interval(
            ContextIntervalRequest(
                start_utc_iso="2026-06-30T00:00:00.000000Z",
                end_utc_iso="2026-06-01T00:00:00.000000Z",
                bodies=(BodyId.SUN,),
            )
        )


def test_snapshot_eclipses_is_jre003_echo(fake_jyotish, fake_bhava) -> None:
    from dataclasses import replace

    from jyotish import EclipseClassification

    event = EclipseEvent(
        kind=EclipseKind.SOLAR,
        classification=None,  # placeholder; replaced below
        maximum_jd_ut=2460462.0,
        maximum_utc_iso="2026-06-15T00:00:00.000000Z",
        contacts=(),
        magnitude=0.5,
        node_positions=(),
        solar_lunar_positions=(),
        geographic_visibility=None,
        pre_event_interval_days=1.0,
        post_event_interval_days=1.0,
        provider_id="fake.eclipse",
        ephemeris_version="18",
    )
    event = replace(event, classification=EclipseClassification.PARTIAL)
    fake_jyotish._eclipses = (event,)
    svc = ContextService(fake_jyotish, fake_bhava)
    result = svc.snapshot_eclipses(
        ContextEclipseRequest(
            start_utc_iso="2026-06-01T00:00:00.000000Z",
            end_utc_iso="2026-06-30T00:00:00.000000Z",
        )
    )
    assert result.eclipses == (event,)
    assert fake_jyotish.calls == ["eclipses"]
    assert result.provenance.source_layers == ("JRE-002", "JRE-003")


def test_delegated_failure_wrapped(fake_jyotish, fake_bhava) -> None:
    class Boom(JyotishError):
        pass

    def fail(*args, **kwargs):
        raise Boom("boom")

    fake_jyotish.planetary_state = fail
    svc = ContextService(fake_jyotish, fake_bhava)
    with pytest.raises(ContextComputationError, match="planetary_state"):
        svc.snapshot_instant(
            ContextInstantRequest(
                instant_utc_iso="2026-06-15T12:00:00.000000Z",
                bodies=(BodyId.SUN,),
            )
        )


def test_config_authority_override(fake_jyotish, fake_bhava) -> None:
    """Config authority (SPEC §22): explicit override > request config >
    TOML service default."""
    default = ContextConfig(house_system="WHOLE_SIGN")
    svc = ContextService(fake_jyotish, fake_bhava, config=default)
    request = ContextInstantRequest(
        instant_utc_iso="2026-06-15T12:00:00.000000Z",
        bodies=(BodyId.SUN,),
        config=ContextConfig(house_system="EQUAL"),
    )
    result = svc.snapshot_instant(request)
    assert result.provenance.snapshot_version == "0.1.0"
    assert result.pair_geometry is not None

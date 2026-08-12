"""Unit tests proving the full service pipeline works through the provider
abstraction with a fake provider (no Swiss Ephemeris binding required)."""

import datetime as dt

from tests.unit.astronomy.fake_provider import FakeProvider

from astronomy.models import BodyId, EphemerisRequest
from astronomy.provider import ProviderRegistry
from astronomy.service import AstronomicalService

REQUEST = EphemerisRequest(
    date=dt.date(2000, 1, 1),
    time=dt.time(12, 0, 0),
    timezone="UTC",
    latitude=0.0,
    longitude=0.0,
)


def _service_with_fake() -> AstronomicalService:
    registry = ProviderRegistry()
    registry.register(FakeProvider())
    return AstronomicalService(provider_id="fake", registry=registry)


def test_pipeline_assembles_result_envelope():
    service = _service_with_fake()
    result = service.compute(REQUEST)
    assert result.timestamp_utc_iso == "2000-01-01T12:00:00Z"
    assert result.timestamp_local_iso == "2000-01-01T12:00:00+00:00"
    assert result.julian_day_ut == 2451545.0
    assert result.provider.provider_id == "fake"
    assert result.provider_run.ephemeris_files == ("sepl_18.se1", "semo_18.se1")
    assert result.positions == result.provider_run.positions
    assert result.config is REQUEST.config
    assert result.request_snapshot == REQUEST


def test_pipeline_returns_all_nine_in_canonical_order():
    result = _service_with_fake().compute(REQUEST)
    assert [p.body for p in result.positions] == list(BodyId)


def test_pipeline_deterministic():
    service = _service_with_fake()
    first = service.compute(REQUEST)
    second = service.compute(REQUEST)
    assert first.positions == second.positions
    assert first.to_dict() == second.to_dict()


def test_pipeline_reorders_subset_to_canonical_order():
    service = _service_with_fake()
    request = EphemerisRequest(
        date=dt.date(2000, 1, 1),
        time=dt.time(12, 0, 0),
        timezone="UTC",
        latitude=0.0,
        longitude=0.0,
        bodies=(BodyId.KETU, BodyId.SUN, BodyId.MOON, BodyId.KETU),
    )
    result = service.compute(request)
    assert [p.body for p in result.positions] == [BodyId.SUN, BodyId.MOON, BodyId.KETU]


def test_empty_bodies_rejected():
    service = _service_with_fake()
    from astronomy.errors import EphemerisError

    request = EphemerisRequest(
        date=dt.date(2000, 1, 1),
        time=dt.time(12, 0, 0),
        timezone="UTC",
        latitude=0.0,
        longitude=0.0,
        bodies=(),
    )
    try:
        service.compute(request)
    except EphemerisError as exc:
        assert "bodies must not be empty" in str(exc)
    else:
        raise AssertionError("expected EphemerisError for empty bodies")

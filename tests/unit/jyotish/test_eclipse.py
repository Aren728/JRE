"""Eclipse provider abstraction (req. H, ADR-006): registry, data-only contract."""

from __future__ import annotations

import pytest
from tests.unit.jyotish.conftest import FakeEclipseProvider

from jyotish.eclipse import (
    SWISSEPH_ECLIPSE_PROVIDER_ID,
    EclipseRegistry,
)
from jyotish.errors import EclipseError
from jyotish.models import EclipseKind, JyotishConfig


def test_registry_register_and_default():
    registry = EclipseRegistry()
    provider = FakeEclipseProvider()
    registry.register(provider)
    assert registry.default() is provider
    assert registry.provider_ids == ("fake.eclipse",)


def test_registry_freeze():
    registry = EclipseRegistry()
    registry.register(FakeEclipseProvider())
    registry.freeze()
    with pytest.raises(RuntimeError, match="frozen"):
        registry.register(FakeEclipseProvider())


def test_registry_unknown_provider_raises():
    registry = EclipseRegistry()
    with pytest.raises(EclipseError, match="not registered"):
        registry.get("nope")


def test_registry_default_missing_raises():
    registry = EclipseRegistry()
    with pytest.raises(EclipseError, match="no default"):
        registry.default()


def test_default_provider_id_stable():
    assert SWISSEPH_ECLIPSE_PROVIDER_ID == "swisseph.pysweph.eclipse"


def test_fake_eclipse_event_is_data_only():
    provider = FakeEclipseProvider()
    events = provider.find_eclipses(2451545.0, 2451600.0, EclipseKind.SOLAR, JyotishConfig())
    assert len(events) == 1
    event = events[0]
    payload = event.to_dict()
    # The contract carries only factual fields.
    assert set(payload) == {
        "kind",
        "classification",
        "maximum_jd_ut",
        "maximum_utc_iso",
        "contacts",
        "magnitude",
        "node_positions",
        "solar_lunar_positions",
        "geographic_visibility",
        "pre_event_interval_days",
        "post_event_interval_days",
        "provider_id",
        "ephemeris_version",
    }
    # No interpretation vocabulary in the payload.
    import json

    blob = json.dumps(payload).lower()
    for term in (
        "good", "bad", "fortune", "wealth", "marriage", "career",
        "spiritual", "auspicious",
    ):
        assert term not in blob



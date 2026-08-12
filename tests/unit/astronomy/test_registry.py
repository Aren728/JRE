"""Unit tests for the provider registry (no Swiss Ephemeris required)."""

import pytest
from tests.unit.astronomy.fake_provider import FakeProvider

from astronomy.errors import UnsupportedProviderError
from astronomy.provider import ProviderRegistry


def test_register_and_get():
    registry = ProviderRegistry()
    provider = FakeProvider()
    registry.register(provider)
    assert registry.get("fake") is provider


def test_get_unknown_raises():
    registry = ProviderRegistry()
    with pytest.raises(UnsupportedProviderError):
        registry.get("nope")


def test_default_prefers_swisseph_when_registered():
    registry = ProviderRegistry()
    swiss = FakeProvider(provider_id="swisseph.pysweph")
    other = FakeProvider(provider_id="other")
    registry.register(swiss)
    registry.register(other)
    assert registry.default() is swiss


def test_default_single_provider():
    registry = ProviderRegistry()
    provider = FakeProvider()
    registry.register(provider)
    assert registry.default() is provider


def test_freeze_blocks_registration():
    registry = ProviderRegistry()
    registry.register(FakeProvider())
    registry.freeze()
    with pytest.raises(RuntimeError):
        registry.register(FakeProvider(provider_id="late"))


def test_provider_ids_sorted():
    registry = ProviderRegistry()
    registry.register(FakeProvider(provider_id="zeta"))
    registry.register(FakeProvider(provider_id="alpha"))
    assert registry.provider_ids == ("alpha", "zeta")

"""QA requirements 3 and 14: Swiss Ephemeris provider init; metadata/version.

- Provider initializes and reports stable metadata.
- Ephemeris version 18 is exposed.
- ``ProviderRun`` records the actual mode and files used.
- The registry default resolves to the Swiss Ephemeris provider.
"""

from __future__ import annotations

from tests.integration.astronomy.conftest import make_request

from astronomy.models import EphemerisMode
from astronomy.provider import SWISSEPH_PROVIDER_ID, default_registry, get_provider


def test_provider_initializes_and_reports_metadata(service):
    result = service.compute(make_request())
    meta = result.provider
    assert meta.provider_id == SWISSEPH_PROVIDER_ID
    assert meta.library_name == "pysweph"
    assert meta.library_version  # e.g. 2.10.3.6
    assert meta.ephemeris_version == "18"


def test_provider_run_records_mode_and_files(service):
    result = service.compute(make_request())
    assert result.provider_run.ephemeris_mode is EphemerisMode.SWIEPH
    assert result.provider_run.ephemeris_files == ("sepl_18.se1", "semo_18.se1")


def test_provider_metadata_is_stable_across_calls(service):
    first = service.compute(make_request())
    second = service.compute(make_request())
    assert first.provider == second.provider
    assert first.provider is second.provider  # provider-stable, same instance


def test_get_provider_returns_swisseph(service):
    provider = get_provider(SWISSEPH_PROVIDER_ID)
    assert provider.provider_id == SWISSEPH_PROVIDER_ID
    assert provider.metadata.ephemeris_version == "18"


def test_default_registry_uses_swisseph():
    registry = default_registry()
    assert SWISSEPH_PROVIDER_ID in registry.provider_ids
    assert registry.default().provider_id == SWISSEPH_PROVIDER_ID

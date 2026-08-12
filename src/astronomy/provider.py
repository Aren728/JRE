"""Provider abstraction for the astronomical core (JRE-002).

Ownership split (authoritative): the SERVICE owns all validation, time
normalization, Julian Day computation, and assembly of ``EphemerisResult``.
Providers are pure position engines: in -> ``(jd_ut, bodies, config)``;
out -> ``ProviderRun``. Providers never see raw requests, never validate, and
never touch clocks, timezones, or calendars.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .errors import UnsupportedProviderError
from .models import BodyId, CalculationConfig, ProviderMetadata, ProviderRun

#: Stable identifier of the initial (Swiss Ephemeris) provider.
SWISSEPH_PROVIDER_ID = "swisseph.pysweph"


@runtime_checkable
class EphemerisProvider(Protocol):
    """Contract every provider must satisfy (see Specialist spec §3)."""

    provider_id: str

    @property
    def metadata(self) -> ProviderMetadata: ...

    def compute(
        self, jd_ut: float, bodies: tuple[BodyId, ...], config: CalculationConfig
    ) -> ProviderRun: ...


class ProviderRegistry:
    """Process-scoped provider registry; frozen after the first ``compute``."""

    def __init__(self) -> None:
        self._providers: dict[str, EphemerisProvider] = {}
        self._frozen = False

    def register(self, provider: EphemerisProvider) -> None:
        if self._frozen:
            raise RuntimeError("provider registry is frozen after the first compute")
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> EphemerisProvider:
        try:
            return self._providers[provider_id]
        except KeyError:
            raise UnsupportedProviderError(f"provider {provider_id!r} is not registered") from None

    def default(self) -> EphemerisProvider:
        if SWISSEPH_PROVIDER_ID in self._providers:
            return self._providers[SWISSEPH_PROVIDER_ID]
        if len(self._providers) == 1:
            return next(iter(self._providers.values()))
        raise UnsupportedProviderError("no default provider is registered")

    def freeze(self) -> None:
        self._frozen = True

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))


#: The process-wide registry. Populated lazily with the default provider so
#: that ``astronomy`` imports cleanly without the Swiss Ephemeris binding.
_default_registry: ProviderRegistry | None = None


def default_registry() -> ProviderRegistry:
    """Return the process-wide registry, registering the default provider once."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ProviderRegistry()
        _default_registry.register(get_provider(SWISSEPH_PROVIDER_ID))
    return _default_registry


def get_provider(
    provider_id: str | None = None, registry: ProviderRegistry | None = None
) -> EphemerisProvider:
    """Return a provider instance by id (default: ``swisseph.pysweph``).

    The Swiss Ephemeris adapter is imported lazily here so that unit tests and
    consumers that only use the Protocol never need the binding.
    """
    if provider_id is None or provider_id == SWISSEPH_PROVIDER_ID:
        from .swisseph.provider import SwissEphemerisProvider  # noqa: PLC0415

        return SwissEphemerisProvider()
    if registry is not None:
        return registry.get(provider_id)
    return default_registry().get(provider_id)

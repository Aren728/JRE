"""Eclipse provider abstraction (Specialist spec §3.2, ADR-006).

``EclipseProvider`` returns deterministic, data-only ``EclipseEvent`` facts.
Any future eclipse engine implements this protocol and registers here.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .errors import EclipseError
from .models import EclipseEvent, EclipseKind, JyotishConfig

#: Stable identifier of the initial (Swiss Ephemeris) eclipse provider.
SWISSEPH_ECLIPSE_PROVIDER_ID = "swisseph.pysweph.eclipse"


@runtime_checkable
class EclipseProvider(Protocol):
    """Contract every eclipse provider must satisfy (Specialist §3.2)."""

    provider_id: str

    def find_eclipses(
        self,
        jd_start: float,
        jd_end: float,
        kind: EclipseKind | None,
        config: JyotishConfig,
    ) -> tuple[EclipseEvent, ...]: ...


class EclipseRegistry:
    """Process-scoped eclipse provider registry; frozen after first use."""

    def __init__(self) -> None:
        self._providers: dict[str, EclipseProvider] = {}
        self._frozen = False

    def register(self, provider: EclipseProvider) -> None:
        if self._frozen:
            raise RuntimeError("eclipse registry is frozen after the first use")
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> EclipseProvider:
        try:
            return self._providers[provider_id]
        except KeyError:
            raise EclipseError(f"eclipse provider {provider_id!r} is not registered") from None

    def default(self) -> EclipseProvider:
        if SWISSEPH_ECLIPSE_PROVIDER_ID in self._providers:
            return self._providers[SWISSEPH_ECLIPSE_PROVIDER_ID]
        if len(self._providers) == 1:
            return next(iter(self._providers.values()))
        raise EclipseError("no default eclipse provider is registered")

    def freeze(self) -> None:
        self._frozen = True

    @property
    def provider_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

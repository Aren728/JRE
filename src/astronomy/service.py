"""``AstronomicalService`` — the deterministic public facade of the core.

The service owns, in order: input validation, time normalization, Julian Day
computation, provider selection, and result assembly. It never performs
astrological interpretation and never touches the Swiss Ephemeris binding
directly (only through the ``EphemerisProvider`` protocol).
"""

from __future__ import annotations

from . import time as _time
from .coordinates import validate_coordinates
from .errors import EphemerisError
from .models import (
    CANONICAL_BODIES,
    BodyId,
    EphemerisRequest,
    EphemerisResult,
)
from .provider import ProviderRegistry, default_registry


class AstronomicalService:
    """Deterministic astronomical calculation facade.

    Args:
        provider_id: registry key to use; ``None`` uses the registry default
            (``swisseph.pysweph``).
        registry: provider registry; ``None`` uses the process-wide default.
    """

    def __init__(
        self, provider_id: str | None = None, registry: ProviderRegistry | None = None
    ) -> None:
        self._provider_id = provider_id
        self._registry = registry if registry is not None else default_registry()

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    def compute(self, request: EphemerisRequest) -> EphemerisResult:
        """Compute raw astronomical state for ``request``. Raises typed errors."""
        self._registry.freeze()

        validate_coordinates(request.latitude, request.longitude)
        utc_dt, local_iso, utc_iso = _time.local_time_to_utc(
            request.date, request.time, request.timezone
        )
        jd_ut = _time.julian_day_ut(utc_dt)

        bodies = _resolve_bodies(request.bodies)
        selected_id = request.provider_id if request.provider_id is not None else self._provider_id
        provider = (
            self._registry.get(selected_id)
            if selected_id is not None
            else self._registry.default()
        )

        run = provider.compute(jd_ut, bodies, request.config)

        return EphemerisResult(
            request_snapshot=request,
            timestamp_utc_iso=utc_iso,
            timestamp_local_iso=local_iso,
            julian_day_ut=jd_ut,
            positions=run.positions,
            provider=provider.metadata,
            provider_run=run,
            config=request.config,
        )


def _resolve_bodies(bodies: tuple[BodyId, ...] | None) -> tuple[BodyId, ...]:
    """Canonical-order, deduplicated body list; ``None`` => all nine; never empty."""
    if bodies is None:
        return CANONICAL_BODIES
    if not bodies:
        raise EphemerisError("bodies must not be empty")
    seen: set[BodyId] = set()
    ordered: list[BodyId] = []
    for body in CANONICAL_BODIES:
        if body in bodies and body not in seen:
            seen.add(body)
            ordered.append(body)
    return tuple(ordered)

"""``ContextService`` — the deterministic JRE-007 canonical-context facade
(SPEC §10-§12).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from typing import Any, TypeVar

import bhava
import jyotish
from bhava import BhavaConfig, BhavaService, HouseAnalysis
from jyotish import (
    BodyId,
    HouseSystem,
    JyotishConfig,
    JyotishService,
)

from .config import load_config
from .derive import (
    assemble_snapshot,
    canonical_bodies,
)
from .errors import ContextComputationError, InvalidContextRequestError
from .models import (
    TIME_PRECISION_VALUES,
    CanonicalFactSnapshot,
    ContextConfig,
    ContextEclipseRequest,
    ContextInstantRequest,
    ContextIntervalRequest,
    ContextNatalRequest,
    ContextRequest,
    check_capability,
    validate,
)

#: Generic thunk result for ``ContextService._delegate``.
T = TypeVar("T")


def _jyotish_config(house_system: str) -> JyotishConfig:
    """JRE-003 config for the pinned house system."""
    return dataclasses.replace(
        JyotishConfig(), house_system=HouseSystem(house_system)
    )


def _bhava_config(cfg: ContextConfig) -> BhavaConfig:
    """JRE-005 config for the snapshot."""
    return BhavaConfig(
        house_systems=(HouseSystem(_house_system(cfg)),),
        tradition_profile=cfg.tradition_profile,
    )


def _house_system(cfg: ContextConfig) -> str:
    """JRE-007's house-system passthrough."""
    return cfg.house_system


def _parse_bodies(raw: tuple[BodyId | str, ...] | list[BodyId | str]) -> tuple[BodyId, ...]:
    if not raw:
        raise InvalidContextRequestError("bodies must be non-empty")
    parsed: list[BodyId] = []
    for item in raw:
        if isinstance(item, BodyId):
            parsed.append(item)
        elif isinstance(item, str):
            try:
                parsed.append(BodyId(item))
            except ValueError as exc:
                raise InvalidContextRequestError(f"unknown body value {item!r}") from exc
        else:
            raise InvalidContextRequestError(f"bodies must be BodyId values, got {item!r}")
    return canonical_bodies(tuple(parsed))


def _effective_config(
    default: ContextConfig, request_config: ContextConfig | None, override: ContextConfig | None
) -> ContextConfig:
    """Config authority (SPEC §22): explicit override > request config >
    TOML service default."""
    if override is not None:
        return validate(override)
    if request_config is not None:
        return validate(request_config)
    return default


def _effective_precision(request_value: str | None, cfg: ContextConfig) -> str:
    value = request_value if request_value is not None else cfg.default_time_precision
    if value not in TIME_PRECISION_VALUES:
        raise InvalidContextRequestError(
            f"time_precision must be one of {TIME_PRECISION_VALUES}, got {value!r}"
        )
    return value


class ContextService:
    """Facade for the deterministic canonical-context layer (SPEC §10-§12)."""

    def __init__(
        self,
        jyotish_service: JyotishService | None = None,
        bhava_service: BhavaService | None = None,
        config: ContextConfig | None = None,
    ) -> None:
        self._jyotish = jyotish_service or JyotishService()
        self._bhava = bhava_service or BhavaService(self._jyotish)
        self._default_config = load_config() if config is None else validate(config)

    # ------------------------------------------------------------------ #
    # Canonical request boundary (SPEC §9.5 — capability dispatch)
    # ------------------------------------------------------------------ #

    def snapshot(
        self,
        request: ContextRequest,
        config: ContextConfig | None = None,
    ) -> CanonicalFactSnapshot:
        """Canonical entry point: serve any frozen V1 capability request.
        The capability contract is validated first (``check_capability``),
        then the request is dispatched to its capability implementation.
        The capability-specific wrappers (``snapshot_*``) remain for
        compatibility and validate the same contract."""
        check_capability(request)
        if isinstance(request, ContextInstantRequest):
            return self.snapshot_instant(request, config)
        if isinstance(request, ContextNatalRequest):
            return self.snapshot_natal(request, config)
        if isinstance(request, ContextIntervalRequest):
            return self.snapshot_interval(request, config)
        if isinstance(request, ContextEclipseRequest):
            return self.snapshot_eclipses(request, config)
        raise InvalidContextRequestError(
            f"capability {request.capability!r} has no concrete capability "
            "request model (ContextRequest is the canonical contract; use a "
            "capability-specific request)"
        )

    # ------------------------------------------------------------------ #
    # GENERIC instant
    # ------------------------------------------------------------------ #

    def snapshot_instant(
        self,
        request: ContextInstantRequest,
        config: ContextConfig | None = None,
    ) -> CanonicalFactSnapshot:
        """GENERIC instant snapshot: planet states + pair geometry, no birth
        data anywhere (SPEC §10/§17)."""
        check_capability(request)
        cfg = _effective_config(self._default_config, request.config, config)
        jyotish_cfg = _jyotish_config(_house_system(cfg))
        bodies = _parse_bodies(request.bodies)

        states = self._delegate(
            lambda: self._jyotish.planetary_state(
                *_civil_instant(request.instant_utc_iso), "UTC", 0.0, 0.0, bodies, jyotish_cfg
            ),
            "planetary_state",
        )
        pair_geometry = self._delegate(
            lambda: jyotish.all_pairs(states, jyotish_cfg), "all_pairs"
        )
        return assemble_snapshot(
            birth=None,
            time_precision=cfg.default_time_precision,
            planet_states=states,
            pair_geometry=pair_geometry,
            jyotish_config=jyotish_cfg,
            bhava_config=_bhava_config(cfg),
            context_config=cfg,
            algorithm="assemble-instant-v1",
        )

    # ------------------------------------------------------------------ #
    # INDIVIDUAL natal
    # ------------------------------------------------------------------ #

    def snapshot_natal(
        self,
        request: ContextNatalRequest,
        config: ContextConfig | None = None,
    ) -> CanonicalFactSnapshot:
        """INDIVIDUAL natal snapshot: JRE-003 chart echo (verbatim,
        provider metadata preserved) + optional JRE-005 house analysis
        (SPEC §11)."""
        check_capability(request)
        cfg = _effective_config(self._default_config, request.config, config)
        precision = _effective_precision(request.time_precision, cfg)
        jyotish_cfg = _jyotish_config(_house_system(cfg))
        bhava_cfg = _bhava_config(cfg)

        chart = self._delegate(
            lambda: self._jyotish.chart(request.birth, jyotish_cfg), "chart"
        )
        house_analysis: HouseAnalysis | None = None
        if request.include_house_analysis:
            house_analysis = self._delegate(
                lambda: self._bhava.analyze_chart(chart, config=bhava_cfg),
                "analyze_chart",
            )
        pair_geometry = self._delegate(
            lambda: jyotish.all_pairs(chart.planet_states, jyotish_cfg), "all_pairs"
        )
        return assemble_snapshot(
            birth=request.birth,
            time_precision=precision,
            planet_states=chart.planet_states,
            natal_chart=chart,
            pair_geometry=pair_geometry,
            house_analysis=house_analysis,
            jyotish_config=jyotish_cfg,
            bhava_config=bhava_cfg,
            context_config=cfg,
            algorithm="assemble-natal-v1",
        )

    # ------------------------------------------------------------------ #
    # Interval
    # ------------------------------------------------------------------ #

    def snapshot_interval(
        self,
        request: ContextIntervalRequest,
        config: ContextConfig | None = None,
    ) -> CanonicalFactSnapshot:
        """Interval snapshot: echoed event stream + sampled state series
        (SPEC §12)."""
        check_capability(request)
        cfg = _effective_config(self._default_config, request.config, config)
        _validate_interval(request.start_utc_iso, request.end_utc_iso)
        bodies = _parse_bodies(request.bodies)
        jyotish_cfg = _jyotish_config(_house_system(cfg))

        events = self._delegate(
            lambda: self._jyotish.events_between(
                request.start_utc_iso, request.end_utc_iso, bodies, None, jyotish_cfg
            ),
            "events_between",
        )
        state_samples = self._delegate(
            lambda: self._jyotish.state_series(
                request.start_utc_iso,
                request.end_utc_iso,
                24.0 / 24.0,
                bodies,
                jyotish_cfg,
            ),
            "state_series",
        )
        return assemble_snapshot(
            birth=None,
            time_precision=cfg.default_time_precision,
            planet_states=(),
            transit_events=events,
            state_samples=state_samples,
            jyotish_config=jyotish_cfg,
            bhava_config=_bhava_config(cfg),
            context_config=cfg,
            algorithm="assemble-interval-v1",
        )

    # ------------------------------------------------------------------ #
    # Eclipses (JRE-003 echo — no new eclipse engine, ADR-006/027)
    # ------------------------------------------------------------------ #

    def snapshot_eclipses(
        self,
        request: ContextEclipseRequest,
        config: ContextConfig | None = None,
    ) -> CanonicalFactSnapshot:
        """Eclipse snapshot: JRE-003 eclipse facts echoed (ADR-006/027)."""
        check_capability(request)
        cfg = _effective_config(self._default_config, request.config, config)
        _validate_interval(request.start_utc_iso, request.end_utc_iso)
        jyotish_cfg = _jyotish_config(_house_system(cfg))

        eclipses = self._delegate(
            lambda: self._jyotish.eclipses(
                request.start_utc_iso, request.end_utc_iso, request.kind, jyotish_cfg
            ),
            "eclipses",
        )
        return assemble_snapshot(
            birth=None,
            time_precision=cfg.default_time_precision,
            planet_states=(),
            eclipses=eclipses,
            jyotish_config=jyotish_cfg,
            bhava_config=_bhava_config(cfg),
            context_config=cfg,
            algorithm="assemble-eclipses-v1",
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _delegate(self, fn: Callable[[], T], label: str) -> T:
        """Run a delegated lower-layer call, wrapping typed failures in
        ``ContextComputationError`` (SPEC §7) with the wrapped class name."""
        try:
            return fn()
        except (jyotish.JyotishError, bhava.BhavaError) as exc:
            raise ContextComputationError(
                f"delegated {label} computation failed ({type(exc).__name__}): {exc}"
            ) from exc


def _civil_instant(iso_utc: str) -> tuple[Any, Any]:
    """Validate an ISO-UTC instant; returns the civil (date, time) split."""
    from .derive import civil_split

    return civil_split(iso_utc)


def _validate_interval(start: str, end: str) -> None:
    from .derive import civil_split

    civil_split(start)
    civil_split(end)
    start_jd = jyotish.iso_utc_to_jd(start)
    end_jd = jyotish.iso_utc_to_jd(end)
    if start_jd > end_jd:
        raise InvalidContextRequestError(
            f"interval start {start!r} must be <= end {end!r}"
        )

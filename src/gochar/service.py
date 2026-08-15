"""``GocharService`` — the deterministic JRE-006 gochar facade (SPEC §10-§12).

One deterministic engine serves both modes:
- GENERIC (``analyze_instant``): transit planet states + optional
  transit-transit pair geometry echo — no birth data anywhere.
- INDIVIDUAL (``analyze_natal``): transit-to-natal relationship facts
  (JRE-005 natal-frame house analysis + full transit-to-natal aspect
  echo); birth data is request input only, echoed as ``birth_snapshot``.
- INTERVAL (``analyze_interval``): echoed event stream (re-asserted
  pinned order) + sampled state series + optional config-gated
  natal-frame house series.

JRE-006 composes the public ``jyotish``/``bhava`` APIs and never
recomputes positions, cusps, lagna, geometry, aspects, or event searches
(SPEC §2.3, ADR-022). Delegated failures are wrapped in
``GocharComputationError`` (SPEC §7).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable
from functools import partial
from typing import Any, TypeVar

import bhava
import jyotish
from bhava import BhavaConfig
from jyotish import (
    BodyId,
    HouseSystem,
    JyotishConfig,
    JyotishService,
    TransitReferencePoint,
)

from .config import load_config
from .derive import (
    build_provenance,
    canonical_bodies,
    civil_split,
    derive_natal_house_series,
    sort_events,
)
from .errors import (
    GocharComputationError,
    InvalidGocharRequestError,
)
from .models import (
    GocharConfig,
    GocharInstantRequest,
    GocharInstantResult,
    GocharIntervalRequest,
    GocharIntervalResult,
    GocharNatalRequest,
    GocharNatalResult,
    validate,
)

#: Canonical body order for pair iteration (JRE-003 declaration order).
_CANONICAL_BODIES: tuple[BodyId, ...] = tuple(BodyId)

#: Generic thunk result for ``GocharService._delegate``.
T = TypeVar("T")


def _jyotish_config(house_system: str) -> JyotishConfig:
    """JRE-003 config for the pinned house system; all other JRE-003
    settings keep their TOML defaults (SPEC §5 house_system passthrough)."""
    return dataclasses.replace(
        JyotishConfig(), house_system=HouseSystem(house_system)
    )


def _bhava_config(cfg: GocharConfig) -> BhavaConfig:
    """JRE-005 config for the gochar call: the chart's house system must be
    in ``house_systems`` (JRE-005 ``_validate_chart``), and the tradition
    profile is a validated passthrough echo (SPEC §5)."""
    return BhavaConfig(
        house_systems=(HouseSystem(cfg.house_system),),
        tradition_profile=cfg.tradition_profile,
    )


def _parse_reference(value: str) -> TransitReferencePoint:
    try:
        return TransitReferencePoint(value)
    except ValueError as exc:
        raise InvalidGocharRequestError(f"unsupported reference_point value {value!r}") from exc


def _parse_bodies(raw: tuple[BodyId | str, ...] | list[BodyId | str]) -> tuple[BodyId, ...]:
    if not raw:
        raise InvalidGocharRequestError("bodies must be non-empty")
    parsed: list[BodyId] = []
    for item in raw:
        if isinstance(item, BodyId):
            parsed.append(item)
        elif isinstance(item, str):
            try:
                parsed.append(BodyId(item))
            except ValueError as exc:
                raise InvalidGocharRequestError(f"unknown body value {item!r}") from exc
        else:
            raise InvalidGocharRequestError(f"bodies must be BodyId values, got {item!r}")
    return canonical_bodies(tuple(parsed))


def _parse_instant(iso: str) -> tuple[Any, Any]:
    """Validate an ISO-UTC instant; returns the civil (date, time) split."""
    return civil_split(iso)


def _validate_interval(start: str, end: str) -> None:
    # Both bounds must be valid ISO-8601 UTC instants (SPEC §8) — same
    # checks as civil_split, so the service and the request parser agree.
    civil_split(start)
    civil_split(end)
    start_jd = jyotish.iso_utc_to_jd(start)
    end_jd = jyotish.iso_utc_to_jd(end)
    if start_jd > end_jd:
        raise InvalidGocharRequestError(
            f"interval start {start!r} must be <= end {end!r}"
        )


def _effective_config(
    default: GocharConfig, request_config: GocharConfig | None, override: GocharConfig | None
) -> GocharConfig:
    """Config authority (SPEC §22): explicit override > request config >
    TOML service default."""
    if override is not None:
        return validate(override)
    if request_config is not None:
        return validate(request_config)
    return default


class GocharService:
    """Facade for the deterministic gochar/transit state layer (SPEC §10-§12)."""

    def __init__(
        self,
        jyotish_service: JyotishService | None = None,
        config: GocharConfig | None = None,
    ) -> None:
        self._jyotish = jyotish_service or JyotishService()
        self._default_config = load_config() if config is None else validate(config)

    # ------------------------------------------------------------------ #
    # GENERIC instant
    # ------------------------------------------------------------------ #

    def analyze_instant(
        self,
        request: GocharInstantRequest,
        config: GocharConfig | None = None,
    ) -> GocharInstantResult:
        """Instant generic gochar state (SPEC §10)."""
        cfg = _effective_config(self._default_config, request.config, config)
        date, time = _parse_instant(request.instant_utc_iso)
        bodies = _parse_bodies(request.bodies)
        jyotish_cfg = _jyotish_config(cfg.house_system)

        states = self._delegate(
            lambda: self._jyotish.planetary_state(
                date, time, "UTC", 0.0, 0.0, bodies, jyotish_cfg
            ),
            "planetary_state",
        )
        pair_geometry: tuple[Any, ...] | None = None
        algorithm = "echo-jre003-planetary-state"
        if cfg.aspect_echo:
            pair_geometry = self._delegate(
                lambda: jyotish.all_pairs(states, jyotish_cfg), "all_pairs"
            )
            algorithm += "+echo-jre003-pair-geometry"

        input_echo = {
            "instant_utc_iso": request.instant_utc_iso,
            "bodies": [body.value for body in bodies],
            "reference_point": cfg.reference_point,
            "house_system": cfg.house_system,
            "sample_step_hours": cfg.sample_step_hours,
            "aspect_echo": cfg.aspect_echo,
        }
        provenance = build_provenance(
            derivation_id="gochar.instant.v1",
            source_layers=("JRE-002", "JRE-003"),
            input_echo=input_echo,
            algorithm=algorithm,
            ephemeris_version=states[0].ephemeris_version,
            config=cfg,
        )
        return GocharInstantResult(
            instant_utc_iso=request.instant_utc_iso,
            planet_states=states,
            pair_geometry=pair_geometry,
            config_echo={
                "reference_point": cfg.reference_point,
                "house_system": cfg.house_system,
                "aspect_echo": cfg.aspect_echo,
            },
            provenance=provenance,
        )

    # ------------------------------------------------------------------ #
    # INDIVIDUAL instant
    # ------------------------------------------------------------------ #

    def analyze_natal(
        self,
        request: GocharNatalRequest,
        config: GocharConfig | None = None,
    ) -> GocharNatalResult:
        """Instant transit-to-natal relationship facts (SPEC §11)."""
        cfg = _effective_config(self._default_config, request.config, config)
        date, time = _parse_instant(request.instant_utc_iso)
        bodies = _parse_bodies(request.bodies)
        reference = _parse_reference(request.reference_point or cfg.reference_point)
        jyotish_cfg = _jyotish_config(cfg.house_system)
        bhava_cfg = _bhava_config(cfg)

        natal_chart = self._delegate(
            lambda: self._jyotish.chart(request.birth, jyotish_cfg), "chart"
        )
        transit = self._delegate(
            lambda: self._jyotish.transit_through_houses(
                request.birth, date, time, "UTC", reference, jyotish_cfg
            ),
            "transit_through_houses",
        )
        analysis = self._delegate(
            lambda: bhava.derive_transit_analysis(
                transit, natal_chart, config=bhava_cfg
            ),
            "derive_transit_analysis",
        )

        transit_to_natal_aspects: tuple[Any, ...] | None = None
        algorithm = "derive-transit-houses-jre005"
        if cfg.aspect_echo:
            pairs: list[Any] = []
            for transit_state in transit.planet_states:
                if transit_state.body not in bodies:
                    continue
                for natal_state in natal_chart.planet_states:
                    pairs.append(
                        self._delegate(
                            partial(
                                jyotish.pair_geometry,
                                transit_state,
                                natal_state,
                                jyotish_cfg,
                            ),
                            "pair_geometry",
                        )
                    )
            transit_to_natal_aspects = tuple(pairs)
            algorithm += "+echo-jre003-pair-geometry"

        input_echo = {
            "instant_utc_iso": request.instant_utc_iso,
            "bodies": [body.value for body in bodies],
            "reference_point": reference.value,
            "house_system": cfg.house_system,
            "sample_step_hours": cfg.sample_step_hours,
            "aspect_echo": cfg.aspect_echo,
        }
        ephemeris_version = (
            transit.planet_states[0].ephemeris_version
            if transit.planet_states
            else natal_chart.planet_states[0].ephemeris_version
        )
        provenance = build_provenance(
            derivation_id="gochar.natal.v1",
            source_layers=("JRE-002", "JRE-003", "JRE-005"),
            input_echo=input_echo,
            algorithm=algorithm,
            ephemeris_version=ephemeris_version,
            config=cfg,
        )
        return GocharNatalResult(
            instant_utc_iso=request.instant_utc_iso,
            birth_snapshot=request.birth,
            transit_house_analysis=analysis,
            transit_to_natal_aspects=transit_to_natal_aspects,
            reference_point=reference.value,
            provenance=provenance,
        )

    # ------------------------------------------------------------------ #
    # Interval
    # ------------------------------------------------------------------ #

    def analyze_interval(
        self,
        request: GocharIntervalRequest,
        config: GocharConfig | None = None,
    ) -> GocharIntervalResult:
        """Interval facts: echoed event stream + state series + optional
        natal-frame house series (SPEC §12)."""
        cfg = _effective_config(self._default_config, request.config, config)
        _validate_interval(request.start_utc_iso, request.end_utc_iso)
        bodies = _parse_bodies(request.bodies)
        if cfg.natal_house_series and request.natal_anchor is None:
            raise InvalidGocharRequestError(
                "natal_house_series=true requires a natal_anchor on the request"
            )
        jyotish_cfg = _jyotish_config(cfg.house_system)
        bhava_cfg = _bhava_config(cfg)

        events = self._delegate(
            lambda: self._jyotish.events_between(
                request.start_utc_iso, request.end_utc_iso, bodies, None, jyotish_cfg
            ),
            "events_between",
        )
        events = sort_events(events)
        state_samples = self._delegate(
            lambda: self._jyotish.state_series(
                request.start_utc_iso,
                request.end_utc_iso,
                cfg.sample_step_hours / 24.0,
                bodies,
                jyotish_cfg,
            ),
            "state_series",
        )

        natal_house_series: tuple[bhava.TransitHouseAnalysis, ...] | None = None
        source_layers: tuple[str, ...] = ("JRE-002", "JRE-003")
        algorithm = "echo-jre003-events-bisection+echo-jre003-state-series"
        anchor = request.natal_anchor
        if cfg.natal_house_series and anchor is not None:
            reference = _parse_reference(cfg.reference_point)
            natal_chart = self._delegate(
                lambda: self._jyotish.chart(anchor, jyotish_cfg), "chart"
            )
            sample_jds: list[float] = []
            seen: list[float] = []
            for state in state_samples:
                if state.julian_day_ut not in seen:
                    seen.append(state.julian_day_ut)
                    sample_jds.append(state.julian_day_ut)
            natal_house_series = derive_natal_house_series(
                natal_chart=natal_chart,
                sample_jds=tuple(sample_jds),
                jyotish_config=jyotish_cfg,
                bhava_config=bhava_cfg,
                transit_fn=lambda d, t: self._delegate(
                    lambda: self._jyotish.transit_through_houses(
                        anchor, d, t, "UTC", reference, jyotish_cfg
                    ),
                    "transit_through_houses",
                ),
            )
            source_layers = ("JRE-002", "JRE-003", "JRE-005")
            algorithm += "+derive-transit-houses-jre005"

        input_echo = {
            "start_utc_iso": request.start_utc_iso,
            "end_utc_iso": request.end_utc_iso,
            "bodies": [body.value for body in bodies],
            "reference_point": cfg.reference_point,
            "house_system": cfg.house_system,
            "sample_step_hours": cfg.sample_step_hours,
            "aspect_echo": cfg.aspect_echo,
            "natal_house_series": cfg.natal_house_series,
        }
        ephemeris_version = (
            state_samples[0].ephemeris_version if state_samples else "unknown"
        )
        provenance = build_provenance(
            derivation_id="gochar.interval.v1",
            source_layers=source_layers,
            input_echo=input_echo,
            algorithm=algorithm,
            ephemeris_version=ephemeris_version,
            config=cfg,
        )
        return GocharIntervalResult(
            start_utc_iso=request.start_utc_iso,
            end_utc_iso=request.end_utc_iso,
            bodies=tuple(body.value for body in bodies),
            events=events,
            state_samples=state_samples,
            natal_house_series=natal_house_series,
            natal_anchor=request.natal_anchor,
            provenance=provenance,
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _delegate(self, fn: Callable[[], T], label: str) -> T:
        """Run a delegated JRE-003/JRE-005 call, wrapping typed failures in
        ``GocharComputationError`` (SPEC §7) with the wrapped class name."""
        try:
            return fn()
        except (jyotish.JyotishError, bhava.BhavaError) as exc:
            raise GocharComputationError(
                f"delegated {label} computation failed ({type(exc).__name__}): {exc}"
            ) from exc

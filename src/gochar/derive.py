"""Pure helpers for the JRE-006 gochar layer (SPEC §4).

JRE-006 performs **no** planetary-position, cusp, lagna, geometry, aspect,
or event-search computation — everything is echoed from JRE-003/JRE-005
(§2.3). This module contains only: the pinned event re-sort (§13.6),
provenance assembly (§9.1, ADR-028), the civil-UTC split (§10/§12), and
the natal-frame house-series sampling composition (§12.3).
"""

from __future__ import annotations

import datetime as _dt
from collections.abc import Callable
from typing import Any

import bhava
import jyotish
from jyotish import BodyId, TransitEvent, TransitThroughHouses

from .errors import InvalidGocharRequestError
from .models import GOCHAR_VERSION, GocharConfig, GocharProvenance

# --------------------------------------------------------------------------- #
# Event ordering (SPEC §13.6 — deterministic total order)
# --------------------------------------------------------------------------- #


def _event_key(event: TransitEvent) -> tuple[float, str, str]:
    return (event.event_julian_day_ut, event.body.value, event.kind.value)


def sort_events(events: tuple[TransitEvent, ...]) -> tuple[TransitEvent, ...]:
    """Re-assert the pinned event ordering ``(event_julian_day_ut,
    body.value, kind.value)`` with a **stable** sort (SPEC §13.6). Ties at
    identical ``(jd, body, kind)`` retain source-stream relative order —
    deterministic because the source stream is deterministic. For JRE-003
    output this is identity-preserving (ADR-023)."""
    if not events:
        return ()
    return tuple(sorted(events, key=_event_key))


# --------------------------------------------------------------------------- #
# Civil UTC split (SPEC §10 step 2 / §12.3 step 2)
# --------------------------------------------------------------------------- #


def civil_split(iso_utc: str) -> tuple[_dt.date, _dt.time]:
    """Split an ISO-8601 UTC string into civil date/time (UTC), using only
    the standard library. ``Z`` is normalized to ``+00:00``; a naive string
    is treated as UTC (JRE-003 semantics). Date-only strings are rejected
    (SPEC §8)."""
    if "T" not in iso_utc:
        raise InvalidGocharRequestError(
            f"instant must include a time component, got {iso_utc!r} (date-only rejected)"
        )
    value = iso_utc.replace("Z", "+00:00")
    try:
        parsed = _dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise InvalidGocharRequestError(f"invalid ISO-8601 UTC instant {iso_utc!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.UTC)
    if parsed.utcoffset() != _dt.timedelta(0):
        raise InvalidGocharRequestError(
            f"instant must be UTC, got offset {iso_utc!r} (only Z / +00:00 / naive)"
        )
    utc = parsed.astimezone(_dt.UTC)
    return utc.date(), utc.time()


# --------------------------------------------------------------------------- #
# Provenance (SPEC §9.1, ADR-028)
# --------------------------------------------------------------------------- #


def build_provenance(
    *,
    derivation_id: str,
    source_layers: tuple[str, ...],
    input_echo: dict[str, Any],
    algorithm: str,
    ephemeris_version: str,
    config: GocharConfig,
) -> GocharProvenance:
    """Assemble a ``GocharProvenance`` — a pure function of the query and
    the pinned catalog/ephemeris/package versions. Contains no wall-clock
    timestamps, randomness, PIDs, or environment data (ADR-028)."""
    return GocharProvenance(
        derivation_id=derivation_id,
        derivation_version=config.version,
        source_layers=source_layers,
        jyotish_version=jyotish.__version__,
        bhava_version=bhava.__version__,
        gochar_version=GOCHAR_VERSION,
        ephemeris_version=ephemeris_version,
        catalog_versions={
            "rashi": jyotish.RASHI_CATALOG_VERSION,
            "nakshatra": jyotish.NAKSHATRA_CATALOG_VERSION,
        },
        input_echo=input_echo,
        algorithm=algorithm,
    )


# --------------------------------------------------------------------------- #
# Natal-frame house series sampling composition (SPEC §12.3)
# --------------------------------------------------------------------------- #


def derive_natal_house_series(
    *,
    natal_chart: jyotish.NatalChart,
    sample_jds: tuple[float, ...],
    jyotish_config: jyotish.JyotishConfig,
    bhava_config: bhava.BhavaConfig,
    transit_fn: Callable[[_dt.date, _dt.time], TransitThroughHouses],
) -> tuple[bhava.TransitHouseAnalysis, ...]:
    """Sample the natal-frame transit house analysis at each sample JD
    (SPEC §12.3): convert each JD to civil UTC via ``jyotish.jd_to_iso_utc``,
    invoke the caller-supplied ``transit_fn`` (JRE-003
    ``transit_through_houses`` at that instant), and derive the JRE-005
    analysis against the single natal chart computed once. Returns one
    ``TransitHouseAnalysis`` per sample, ascending JD order.

    The natal chart is computed by the caller once; the composition itself
    performs no astronomy. The known v0.1 cost (JRE-003 recomputes the
    natal chart inside each ``transit_through_houses`` call) is accepted
    and documented (ADR-026).
    """
    analyses: list[bhava.TransitHouseAnalysis] = []
    for jd in sample_jds:
        iso = jyotish.jd_to_iso_utc(jd)
        date, time = civil_split(iso)
        transit = transit_fn(date, time)
        analysis = bhava.derive_transit_analysis(
            transit, natal_chart, config=bhava_config
        )
        analyses.append(analysis)
    return tuple(analyses)


def canonical_bodies(bodies: tuple[BodyId, ...]) -> tuple[BodyId, ...]:
    """Return the requested bodies in JRE-003 canonical ``BodyId``
    declaration order (SUN..KETU), deduplicated (deterministic ordering,
    SPEC §9/DC §4.4)."""
    ordered: list[BodyId] = []
    seen: list[BodyId] = []
    for body in tuple(BodyId):
        if body in bodies and body not in seen:
            ordered.append(body)
            seen.append(body)
    return tuple(ordered)

"""Pure helpers for the JRE-007 canonical-context layer (SPEC §4).

JRE-007 performs **no** planetary-position, cusp, lagna, geometry, aspect,
event-search, eclipse, or house computation — everything is echoed from
JRE-002/JRE-003/JRE-005/JRE-006 (§2). This module contains only: chart
identity (SPEC §3), civil-UTC validation (SPEC §8), canonical body order
(SPEC §9), the six-stage provenance chain (SPEC §16, ADR-028), and the
pure snapshot assembly (SPEC §3). No wall-clock time, randomness, PIDs, or
environment data (ADR-028).

V1 accepts only existing point-valued ``BirthData``: no birth-time
candidate generation, no date-only candidates, no rectification, no
uncertainty candidate sets.
"""

from __future__ import annotations

import datetime as _dt

import bhava
import gochar
import jyotish
from bhava import HouseAnalysis
from gochar import (
    GocharInstantResult,
    GocharIntervalResult,
    GocharNatalResult,
)
from jyotish import (
    BirthData,
    BodyId,
    EclipseEvent,
    NatalChart,
    PairGeometry,
    PlanetState,
    TransitEvent,
)

from .errors import InvalidContextRequestError
from .models import (
    CONTEXT_VERSION,
    TIME_PRECISION_VALUES,
    CanonicalFactSnapshot,
    CanonicalProvenance,
    ContextConfig,
    ProvenanceStage,
    compute_deterministic_id,
)

# --------------------------------------------------------------------------- #
# Chart identity (SPEC §3 — deterministic fingerprint)
# --------------------------------------------------------------------------- #


def chart_identity(
    *,
    birth: BirthData | None,
    jyotish_config: jyotish.JyotishConfig,
    bhava_config: bhava.BhavaConfig,
    catalog_versions: dict[str, str],
) -> str:
    """Deterministic SHA-256 fingerprint of the **chart facts**: the birth
    echo (when present), the fact-determining lower-layer configs (JRE-003
    ayanamsa/zodiac/house-system/node-model, JRE-005 house systems and
    tradition profile), and the catalog versions. Snapshot-assembly options
    are deliberately excluded — two snapshots of the same chart share one
    identity (Varga cross-referencing, caching). A pure function of the
    query — no wall-clock data (ADR-028)."""
    payload = {
        "birth": None if birth is None else birth.to_dict(),
        "jyotish_config": jyotish_config.to_dict(),
        "bhava_config": bhava_config.to_dict(),
        "catalog_versions": catalog_versions,
    }
    return compute_deterministic_id("jre007:chart-identity", payload)


# --------------------------------------------------------------------------- #
# Civil UTC split (SPEC §8 — validation only)
# --------------------------------------------------------------------------- #


def civil_split(iso_utc: str) -> tuple[_dt.date, _dt.time]:
    """Split an ISO-8601 UTC string into civil date/time (UTC), using only
    the standard library. ``Z`` is normalized to ``+00:00``; a naive string
    is treated as UTC (JRE-003 semantics). Date-only strings are rejected
    (SPEC §8)."""
    if "T" not in iso_utc:
        raise InvalidContextRequestError(
            f"instant must include a time component, got {iso_utc!r} (date-only rejected)"
        )
    value = iso_utc.replace("Z", "+00:00")
    try:
        parsed = _dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise InvalidContextRequestError(f"invalid ISO-8601 UTC instant {iso_utc!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=_dt.UTC)
    if parsed.utcoffset() != _dt.timedelta(0):
        raise InvalidContextRequestError(
            f"instant must be UTC, got offset {iso_utc!r} (only Z / +00:00 / naive)"
        )
    utc = parsed.astimezone(_dt.UTC)
    return utc.date(), utc.time()


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


# --------------------------------------------------------------------------- #
# Provenance chain (SPEC §16 — six stages, never conflated)
# --------------------------------------------------------------------------- #


def build_provenance(
    *,
    birth: BirthData | None,
    ephemeris_version: str | None,
    jyotish_config: jyotish.JyotishConfig,
    has_house_analysis: bool,
    has_gochar: bool,
    tradition_profile: str | None,
    catalog_versions: dict[str, str],
    context_config: ContextConfig,
    algorithm: str,
) -> CanonicalProvenance:
    """Assemble the six-stage provenance chain answering *\"where did this
    fact come from?\"* (SPEC §16). Stages: INPUT → ASTRONOMICAL →
    NORMALIZATION → DERIVED → DOCTRINE_RULE → FUTURE_INFERENCE. Each stage
    is echoed with its producing layer and versions. Actual provenance is
    separated from reserved future stages: ``DOCTRINE_RULE`` is emitted
    ONLY when a tradition profile was actually applied (JRE-004), and
    ``FUTURE_INFERENCE`` is always a reserved placeholder
    (``layer_id=None``, ``algorithm='reserved'``) — JRE-007 performs no
    doctrine evaluation and no inference, so no fact is ever attributed to
    a doctrine or inference stage it did not produce. Pure function of the
    query — no environment data (ADR-028)."""
    stages: list[ProvenanceStage] = [
        ProvenanceStage(
            stage="INPUT",
            layer_id="JRE-007",
            version=CONTEXT_VERSION,
            algorithm="echo-input",
        )
    ]
    if ephemeris_version is not None:
        stages.append(
            ProvenanceStage(
                stage="ASTRONOMICAL",
                layer_id="JRE-002",
                version=ephemeris_version,
                algorithm="echo-astronomy",
            )
        )
    stages.append(
        ProvenanceStage(
            stage="NORMALIZATION",
            layer_id="JRE-003",
            version=jyotish.__version__,
            algorithm="echo-jyotish",
            catalog_versions={
                "rashi": jyotish.RASHI_CATALOG_VERSION,
                "nakshatra": jyotish.NAKSHATRA_CATALOG_VERSION,
            },
        )
    )
    if has_house_analysis:
        stages.append(
            ProvenanceStage(
                stage="DERIVED",
                layer_id="JRE-005",
                version=bhava.__version__,
                algorithm="echo-bhava",
            )
        )
    if has_gochar:
        stages.append(
            ProvenanceStage(
                stage="DERIVED",
                layer_id="JRE-006",
                version=gochar.__version__,
                algorithm="echo-gochar",
            )
        )
    # DOCTRINE_RULE appears only when a tradition profile was actually
    # applied — JRE-007 never claims JRE-004 production otherwise (SPEC §16).
    if tradition_profile is not None:
        stages.append(
            ProvenanceStage(
                stage="DOCTRINE_RULE",
                layer_id="JRE-004",
                version=tradition_profile,
                algorithm="echo-tradition-profile",
                catalog_versions={},
            )
        )
    # Reserved forward slot: never claims a producer (SPEC §16).
    stages.append(
        ProvenanceStage(
            stage="FUTURE_INFERENCE",
            layer_id=None,
            version=None,
            algorithm="reserved",
            catalog_versions={},
        )
    )

    source_layers: tuple[str, ...] = ("JRE-002", "JRE-003")
    if has_house_analysis:
        source_layers = (*source_layers, "JRE-005")
    if has_gochar:
        source_layers = (*source_layers, "JRE-006")

    return CanonicalProvenance(
        stages=tuple(stages),
        source_layers=source_layers,
        assembly_algorithm=algorithm,
        snapshot_version=context_config.snapshot_version,
    )


# --------------------------------------------------------------------------- #
# Misc pure helpers
# --------------------------------------------------------------------------- #


def canonical_catalog_versions(jyotish_config: jyotish.JyotishConfig) -> dict[str, str]:
    """The pinned catalog versions JRE-007 echoes (SPEC §3)."""
    return {
        "rashi": jyotish.RASHI_CATALOG_VERSION,
        "nakshatra": jyotish.NAKSHATRA_CATALOG_VERSION,
    }


def ephemeris_version_of(states: tuple[PlanetState, ...]) -> str | None:
    """First non-None ephemeris version among the echoed states, else None."""
    for state in states:
        if state.ephemeris_version:
            return state.ephemeris_version
    return None


def _validate_precision(time_precision: str) -> None:
    if time_precision not in TIME_PRECISION_VALUES:
        raise InvalidContextRequestError(
            f"time_precision must be one of {TIME_PRECISION_VALUES}, got {time_precision!r}"
        )


# --------------------------------------------------------------------------- #
# Canonical snapshot assembly (SPEC §3 — the composition core)
# --------------------------------------------------------------------------- #


def assemble_snapshot(
    *,
    birth: BirthData | None,
    time_precision: str,
    planet_states: tuple[PlanetState, ...],
    natal_chart: NatalChart | None = None,
    pair_geometry: tuple[PairGeometry, ...] | None = None,
    house_analysis: HouseAnalysis | None = None,
    transit_events: tuple[TransitEvent, ...] | None = None,
    state_samples: tuple[PlanetState, ...] | None = None,
    eclipses: tuple[EclipseEvent, ...] | None = None,
    gochar_instant: GocharInstantResult | None = None,
    gochar_natal: GocharNatalResult | None = None,
    gochar_interval: GocharIntervalResult | None = None,
    jyotish_config: jyotish.JyotishConfig,
    bhava_config: bhava.BhavaConfig,
    context_config: ContextConfig,
    algorithm: str,
) -> CanonicalFactSnapshot:
    """Assemble a ``CanonicalFactSnapshot`` from already-computed lower-layer
    outputs (SPEC §3). Pure composition: every section is an echo — no
    position/cusp/geometry/event/eclipse/house computation happens here.

    ``natal_chart`` is echoed verbatim from the JRE-003 ``NatalChart``
    result (SPEC §2/§23) — JRE-007 never reconstructs a replacement chart
    and never drops provider metadata. Natal/transit separation is
    structural: natal sections (``natal_chart`` / ``house_analyses``) and
    transit sections (``transit_events`` / ``state_samples``) are
    independent optional fields and are never merged (SPEC §17,
    ADR-021/025). ``time_precision`` is validated (SPEC §15). V1 accepts
    only point-valued ``BirthData`` — no candidate expansion happens here.
    """
    _validate_precision(time_precision)

    catalog_versions = canonical_catalog_versions(jyotish_config)
    provenance = build_provenance(
        birth=birth,
        ephemeris_version=ephemeris_version_of(planet_states),
        jyotish_config=jyotish_config,
        has_house_analysis=house_analysis is not None,
        has_gochar=False,
        tradition_profile=context_config.tradition_profile,
        catalog_versions=catalog_versions,
        context_config=context_config,
        algorithm=algorithm,
    )

    return CanonicalFactSnapshot(
        snapshot_version=context_config.snapshot_version,
        natal_chart=natal_chart,
        planet_states=planet_states if planet_states else None,
        pair_geometry=pair_geometry,
        house_analyses=(
            (house_analysis,) if house_analysis is not None else None
        ),
        transit_events=transit_events,
        state_samples=state_samples,
        gochar_instant=gochar_instant,
        gochar_natal=gochar_natal,
        gochar_interval=gochar_interval,
        eclipses=eclipses,
        provenance=provenance,
    )

"""JRE-007 Canonical Context models (SPEC §9, DATA-CONTRACT §4-§5).

JRE-007 defines **zero new enums** (SPEC §6): every enum it exposes is
reused by import from the ``jyotish`` / ``bhava`` / ``gochar`` public
roots. Result models *contain* echoed lower-layer values verbatim and
never re-declare them. ``ContextConfig`` is immutable and validated at
construction; ``config/context.toml`` is the single source of defaults.

Canonical Fact Snapshot sections (SPEC §3): identity (``chart_identity``),
birth echo (``birth_snapshot``/``birth_time_known``/``time_precision``),
jyotish echo (``planet_states``, ``pair_geometry``, ``bhavas``, ``lagna``,
``transit_events``, ``state_samples``, ``eclipses``), bhava echo
(``house_analysis``), gochar echo (``gochar`` — FactFrame preserved,
ADR-021/025), candidate contexts (``candidates``), uncertainty metadata,
config/catalog echoes, and the six-stage provenance chain (SPEC §16).
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, cast

from bhava import HouseAnalysis  # noqa: F401  (re-exported type reuse)
from gochar import (  # noqa: F401  (re-exported type reuse)
    GocharInstantResult,
    GocharIntervalResult,
    GocharNatalResult,
)
from jyotish import (
    Bhava,  # noqa: F401
    BirthData,
    BodyId,  # noqa: F401
    EclipseEvent,  # noqa: F401
    EclipseKind,  # noqa: F401
    HouseSystem,  # noqa: F401
    LagnaState,  # noqa: F401
    PairGeometry,  # noqa: F401
    PlanetState,  # noqa: F401
    TransitEvent,  # noqa: F401
)

from .errors import InvalidContextConfigError

#: Environment pin for golden fixtures (same policy as JRE-002/003/004/005/006).
GOLDEN_VERSION = "0.1.0"

#: Pinned package version (SPEC §4/§5).
CONTEXT_VERSION = "0.1.0"

#: Pinned time-precision strings (SPEC §15 — candidate contexts). Values
#: beyond the pinned set are rejected at construction.
TIME_PRECISION_VALUES: tuple[str, ...] = ("EXACT", "HOUR_KNOWN", "DATE_ONLY", "UNKNOWN")

#: Pinned provenance stage ids (SPEC §16 — the six-stage fact chain).
PROVENANCE_STAGES: tuple[str, ...] = (
    "INPUT",
    "ASTRONOMICAL",
    "NORMALIZATION",
    "DERIVED",
    "DOCTRINE_RULE",
    "FUTURE_INFERENCE",
)

#: Known snapshot sections used for missing-section detection (SPEC §15).
SNAPSHOT_SECTIONS: tuple[str, ...] = (
    "pair_geometry",
    "bhavas",
    "lagna",
    "house_analysis",
    "transit_events",
    "state_samples",
    "eclipses",
    "gochar",
)

#: Candidate expansion bounds (SPEC §15 — config authority, bounded).
MIN_CANDIDATE_STEP_MINUTES = 1
MAX_CANDIDATE_STEP_MINUTES = 1440
MIN_MAX_CANDIDATES = 1
MAX_MAX_CANDIDATES = 288


# --------------------------------------------------------------------------- #
# Configuration (SPEC §5 — TOML authority, no hidden defaults)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ContextConfig:
    """Immutable JRE-007 configuration (SPEC §5). TOML is authoritative;
    every default is declared in ``config/context.toml``."""

    snapshot_version: str = "0.1.0"
    candidate_step_minutes: int = 60
    max_candidates: int = 24
    default_time_precision: str = "EXACT"
    house_system: str = "WHOLE_SIGN"
    tradition_profile: str | None = None
    version: str = CONTEXT_VERSION

    def __post_init__(self) -> None:
        validate(self)

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContextConfig:
        """Deserialize from a JSON-shaped dict (missing key → field default;
        explicit ``null`` → ``None`` where the type allows). Unknown enum
        values raise ``InvalidContextConfigError`` (SPEC §5)."""
        config = cls(
            snapshot_version=_as_string(
                data.get("snapshot_version"), "snapshot_version", "0.1.0"
            ),
            candidate_step_minutes=_as_int(
                data.get("candidate_step_minutes"), "candidate_step_minutes", 60
            ),
            max_candidates=_as_int(data.get("max_candidates"), "max_candidates", 24),
            default_time_precision=_as_string(
                data.get("default_time_precision"), "default_time_precision", "EXACT"
            ),
            house_system=_as_string(data.get("house_system"), "house_system", "WHOLE_SIGN"),
            tradition_profile=_as_optional_string(
                data.get("tradition_profile"), "tradition_profile"
            ),
            version=_as_string(data.get("version"), "version", CONTEXT_VERSION),
        )
        return validate(config)


# --------------------------------------------------------------------------- #
# Uncertainty metadata (SPEC §15 — non-interval)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class UncertaintyMetadata:
    """Deterministic uncertainty surface: birth-time precision, candidate
    count, and missing-section flags. No confidence scores, no intervals —
    interval-valued computation belongs to future engines (SPEC §15)."""

    birth_time_known: bool
    time_precision: str
    candidate_count: int
    missing_sections: tuple[str, ...]


# --------------------------------------------------------------------------- #
# Provenance chain (SPEC §16 — six stages, never conflated)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProvenanceStage:
    """One stage of the canonical fact chain (SPEC §16). ``stage`` is a
    pinned id; ``layer_id`` names the producing JRE layer when applicable
    (e.g. ``JRE-003``); ``version``/``algorithm``/``catalog_versions`` are
    echoed deterministically. ``FUTURE_INFERENCE`` is a reserved forward
    slot — future engines append their own provenance there."""

    stage: str
    layer_id: str | None = None
    version: str | None = None
    algorithm: str | None = None
    catalog_versions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalProvenance:
    """The complete answer to *"where did this fact come from?"* — the
    ordered stage chain plus the aggregated source layers (SPEC §16)."""

    stages: tuple[ProvenanceStage, ...]
    source_layers: tuple[str, ...]
    assembly_algorithm: str
    snapshot_version: str


# --------------------------------------------------------------------------- #
# The canonical fact snapshot (SPEC §3)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CanonicalFactSnapshot:
    """One deterministic, provenance-bearing envelope of canonical factual
    state. Every section is an *echo* of an existing lower-layer public
    output (SPEC §2) — JRE-007 computes nothing new. Natal sections
    (``bhavas``/``lagna``/``house_analysis``) and transit sections
    (``transit_events``/``state_samples``) are never merged; the ``gochar``
    echo preserves its own ``FactFrame`` (ADR-021/025)."""

    snapshot_version: str
    chart_identity: str
    birth_snapshot: BirthData | None
    birth_time_known: bool
    time_precision: str
    planet_states: tuple[PlanetState, ...]
    pair_geometry: tuple[PairGeometry, ...] | None
    bhavas: tuple[Bhava, ...] | None
    lagna: LagnaState | None
    house_analysis: HouseAnalysis | None
    transit_events: tuple[TransitEvent, ...] | None
    state_samples: tuple[PlanetState, ...] | None
    eclipses: tuple[EclipseEvent, ...] | None
    gochar: GocharInstantResult | GocharNatalResult | GocharIntervalResult | None
    candidates: tuple[BirthData, ...]
    uncertainty: UncertaintyMetadata
    config_echo: dict[str, Any]
    catalog_versions: dict[str, str]
    provenance: CanonicalProvenance


# --------------------------------------------------------------------------- #
# Request models (SPEC §9.5 — snapshot queries)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ContextInstantRequest:
    """GENERIC instant snapshot query: ISO-UTC instant + bodies + optional
    config. No birth data anywhere (SPEC §17)."""

    instant_utc_iso: str
    bodies: tuple[BodyId, ...]
    config: ContextConfig | None = None


@dataclass(frozen=True)
class ContextNatalRequest:
    """INDIVIDUAL natal snapshot query: birth + optional house analysis and
    config. ``time_precision`` defaults to the config default (SPEC §15)."""

    birth: BirthData
    config: ContextConfig | None = None
    include_house_analysis: bool = True
    time_precision: str | None = None


@dataclass(frozen=True)
class ContextIntervalRequest:
    """Interval snapshot query: start/end ISO-UTC + bodies + optional
    config (echoed event stream + sampled state series)."""

    start_utc_iso: str
    end_utc_iso: str
    bodies: tuple[BodyId, ...]
    config: ContextConfig | None = None


@dataclass(frozen=True)
class ContextEclipseRequest:
    """Eclipse snapshot query: interval + optional kind (JRE-003 echo,
    ADR-006/027 — no new eclipse calculation)."""

    start_utc_iso: str
    end_utc_iso: str
    kind: EclipseKind | None = None
    config: ContextConfig | None = None


@dataclass(frozen=True)
class ContextCandidatesRequest:
    """Date-only birth candidate query: expand a date into a bounded set of
    point-valued ``BirthData`` candidates (SPEC §15/§17)."""

    date: str
    timezone: str
    latitude: float
    longitude: float
    config: ContextConfig | None = None


# --------------------------------------------------------------------------- #
# Validation (SPEC §5/§15)
# --------------------------------------------------------------------------- #


def validate(config: ContextConfig) -> ContextConfig:
    """Validate a ``ContextConfig``; raises ``InvalidContextConfigError``
    with the offending value (SPEC §5)."""
    if not isinstance(config.snapshot_version, str) or config.snapshot_version == "":
        raise InvalidContextConfigError(
            f"snapshot_version must be a non-empty string, got {config.snapshot_version!r}"
        )
    step = config.candidate_step_minutes
    if not isinstance(step, int) or not (
        MIN_CANDIDATE_STEP_MINUTES <= step <= MAX_CANDIDATE_STEP_MINUTES
    ):
        raise InvalidContextConfigError(
            f"candidate_step_minutes must be an int in "
            f"[{MIN_CANDIDATE_STEP_MINUTES}, {MAX_CANDIDATE_STEP_MINUTES}], got {step!r}"
        )
    limit = config.max_candidates
    if not isinstance(limit, int) or not (MIN_MAX_CANDIDATES <= limit <= MAX_MAX_CANDIDATES):
        raise InvalidContextConfigError(
            f"max_candidates must be an int in [{MIN_MAX_CANDIDATES}, {MAX_MAX_CANDIDATES}], "
            f"got {limit!r}"
        )
    if config.default_time_precision not in TIME_PRECISION_VALUES:
        raise InvalidContextConfigError(
            f"default_time_precision must be one of {TIME_PRECISION_VALUES}, "
            f"got {config.default_time_precision!r}"
        )
    try:
        HouseSystem(config.house_system)
    except ValueError as exc:
        raise InvalidContextConfigError(
            f"house_system must be a jyotish.HouseSystem value, got {config.house_system!r}"
        ) from exc
    if config.tradition_profile is not None and (
        not isinstance(config.tradition_profile, str) or config.tradition_profile == ""
    ):
        raise InvalidContextConfigError(
            "tradition_profile must be None or a non-empty string, "
            f"got {config.tradition_profile!r}"
        )
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidContextConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    return config


# --------------------------------------------------------------------------- #
# Generic serialization helpers (mirrors the JRE-003/JRE-005/006 conventions)
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums → ``.value``; tuples → lists; ``-0.0`` → ``0.0``)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {key: _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)


def _as_string(raw: Any, field: str, default: str) -> str:
    if raw is None:
        return default
    if not isinstance(raw, str) or raw == "":
        raise InvalidContextConfigError(f"{field} must be a non-empty string, got {raw!r}")
    return raw


def _as_int(raw: Any, field: str, default: int) -> int:
    if raw is None:
        return default
    if isinstance(raw, bool) or not isinstance(raw, int):
        raise InvalidContextConfigError(f"{field} must be an integer, got {raw!r}")
    return raw


def _as_optional_string(raw: Any, field: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or raw == "":
        raise InvalidContextConfigError(f"{field} must be None or a non-empty string, got {raw!r}")
    return raw

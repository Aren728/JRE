"""JRE-007 Canonical Context models (SPEC §9, DATA-CONTRACT §4-§5).

JRE-007 defines **zero new enums** (SPEC §6) except for context-specific
lifecycle/capability states: every astronomical enum it exposes is
reused by import from the ``jyotish`` / ``bhava`` / ``gochar`` public
roots. Result models *contain* echoed lower-layer values verbatim and
never re-declare them. ``ContextConfig`` is immutable and validated at
construction; ``config/context.toml`` is the single source of defaults.
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, cast

from bhava import HouseAnalysis
from gochar import (
    GocharInstantResult,
    GocharIntervalResult,
    GocharNatalResult,
)
from jyotish import (
    Bhava,
    BirthData,
    BodyId,
    EclipseEvent,
    EclipseKind,
    HouseSystem,
    LagnaState,
    PairGeometry,
    PlanetState,
    TransitEvent,
    NatalChart,
)

from .errors import InvalidContextConfigError, InvalidContextRequestError

#: Environment pin for golden fixtures (same policy as JRE-002/003/004/005/006).
GOLDEN_VERSION = "0.1.0"

#: Pinned package version (SPEC §4/§5).
CONTEXT_VERSION = "0.1.0"

#: Pinned time-precision strings.
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


class CapabilityState(str, enum.Enum):
    """The state of a capability in the manifest."""
    AVAILABLE = "AVAILABLE"
    NOT_REQUESTED = "NOT_REQUESTED"
    UNAVAILABLE = "UNAVAILABLE"


class FactKind(str, enum.Enum):
    """The kind of fact contained in a FactEnvelope."""
    PLANET_STATE = "PLANET_STATE"
    PAIR_GEOMETRY = "PAIR_GEOMETRY"
    HOUSE_ANALYSIS = "HOUSE_ANALYSIS"
    TRANSIT_EVENT = "TRANSIT_EVENT"
    ECLIPSE_EVENT = "ECLIPSE_EVENT"
    LAGNA_STATE = "LAGNA_STATE"


@dataclass(frozen=True)
class CapabilityManifest:
    """The manifest of requested and available capabilities."""
    natal_chart: CapabilityState = CapabilityState.NOT_REQUESTED
    pair_geometry: CapabilityState = CapabilityState.NOT_REQUESTED
    eclipse_facts: CapabilityState = CapabilityState.NOT_REQUESTED
    house_analysis: CapabilityState = CapabilityState.NOT_REQUESTED
    gochar_instant: CapabilityState = CapabilityState.NOT_REQUESTED
    gochar_natal: CapabilityState = CapabilityState.NOT_REQUESTED
    gochar_interval: CapabilityState = CapabilityState.NOT_REQUESTED
    knowledge_profile: CapabilityState = CapabilityState.NOT_REQUESTED


# --------------------------------------------------------------------------- #
# Configuration (SPEC §5 — TOML authority, no hidden defaults)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ContextConfig:
    """Immutable JRE-007 configuration (SPEC §5). TOML is authoritative;
    every default is declared in ``config/context.toml``."""

    snapshot_version: str = "0.1.0"
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
        config = cls(
            snapshot_version=_as_string(
                data.get("snapshot_version"), "snapshot_version", "0.1.0"
            ),
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
# Provenance chain (SPEC §16 — six stages, never conflated)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ProvenanceStage:
    """One stage of the canonical fact chain (SPEC §16)."""

    stage: str
    layer_id: str | None = None
    version: str | None = None
    algorithm: str | None = None
    catalog_versions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class CanonicalProvenance:
    """The complete answer to *"where did this fact come from?"*"""

    stages: tuple[ProvenanceStage, ...]
    source_layers: tuple[str, ...]
    assembly_algorithm: str
    snapshot_version: str


# --------------------------------------------------------------------------- #
# Fact Envelope & Canonical Context
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FactEnvelope:
    """A single self-contained fact with its own identity and provenance."""

    fact_id: str
    kind: FactKind
    capability: str
    provenance: CanonicalProvenance
    payload: Any


@dataclass(frozen=True)
class CanonicalContext:
    """The top-level context container representing a deterministic state."""

    context_id: str
    analysis_request_id: str
    purpose: str
    birth_snapshot: BirthData | None
    configuration: ContextConfig
    chart_identity: str | None
    tradition_profile_identity: str | None
    requested_capabilities: CapabilityManifest
    source_layers: tuple[str, ...]
    version: str = CONTEXT_VERSION


@dataclass(frozen=True)
class CanonicalFactSnapshot:
    """One deterministic, provenance-bearing envelope of canonical factual state."""

    snapshot_version: str
    natal_chart: NatalChart | None
    pair_geometry: tuple[PairGeometry, ...] | None
    house_analyses: tuple[HouseAnalysis, ...] | None
    gochar_instant: GocharInstantResult | None
    gochar_natal: GocharNatalResult | None
    gochar_interval: GocharIntervalResult | None
    eclipses: tuple[EclipseEvent, ...] | None
    provenance: CanonicalProvenance
    version: str = CONTEXT_VERSION


# --------------------------------------------------------------------------- #
# Request models (SPEC §9.5 — snapshot queries)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ContextInstantRequest:
    """GENERIC instant snapshot query: ISO-UTC instant + bodies + optional config."""

    instant_utc_iso: str
    bodies: tuple[BodyId, ...]
    config: ContextConfig | None = None


@dataclass(frozen=True)
class ContextNatalRequest:
    """INDIVIDUAL natal snapshot query: birth + optional house analysis and config."""

    birth: BirthData
    config: ContextConfig | None = None
    include_house_analysis: bool = True
    time_precision: str | None = None


@dataclass(frozen=True)
class ContextIntervalRequest:
    """Interval snapshot query: start/end ISO-UTC + bodies + optional config."""

    start_utc_iso: str
    end_utc_iso: str
    bodies: tuple[BodyId, ...]
    config: ContextConfig | None = None


@dataclass(frozen=True)
class ContextEclipseRequest:
    """Eclipse snapshot query: interval + optional kind."""

    start_utc_iso: str
    end_utc_iso: str
    kind: EclipseKind | None = None
    config: ContextConfig | None = None


# --------------------------------------------------------------------------- #
# Validation (SPEC §5/§15)
# --------------------------------------------------------------------------- #


def validate(config: ContextConfig) -> ContextConfig:
    """Validate a ``ContextConfig``; raises ``InvalidContextConfigError``."""
    if not isinstance(config.snapshot_version, str) or config.snapshot_version == "":
        raise InvalidContextConfigError(
            f"snapshot_version must be a non-empty string, got {config.snapshot_version!r}"
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
# Deterministic Identity / Hashing
# --------------------------------------------------------------------------- #


def compute_deterministic_id(domain: str, data: Any) -> str:
    """Compute a deterministic SHA-256 hash for a given domain and data payload."""
    serialized = json.dumps(
        _model_to_dict(data),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    hasher = hashlib.sha256()
    hasher.update(f"{domain}:".encode("utf-8"))
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> ``.value``; tuples -> lists; ``-0.0`` -> ``0.0``)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {key: _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        if model != model or model in (float("inf"), float("-inf")):
            raise ValueError("NaN and Infinity are not allowed in deterministic serialization")
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


def _as_optional_string(raw: Any, field: str) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or raw == "":
        raise InvalidContextConfigError(f"{field} must be None or a non-empty string, got {raw!r}")
    return raw

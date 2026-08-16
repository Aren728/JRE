"""JRE-007 Canonical Context models (SPEC §9, DATA-CONTRACT §4-§5).

JRE-007 defines **zero new enums** (SPEC §6) except for context-specific
lifecycle/capability states: every astronomical enum it exposes is
reused by import from the ``jyotish`` / ``bhava`` / ``gochar`` public
roots. Result models *contain* echoed lower-layer values verbatim and
never re-declare them. ``ContextConfig`` is immutable and validated at
construction; ``config/context.toml`` is the single source of defaults.

V1 capability contract (SPEC §9.5 / DC §5): ``ContextRequest`` is the
canonical request boundary — a frozen capability id, a requested minimum
capability version, the correlation id, and the optional programmatic
config. The capability-specific request models are thin compatibility
wrappers over it (fixed ``capability``) and cannot alter the canonical
public contract.
"""

from __future__ import annotations

import enum
import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import Any, cast

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
    EclipseKind,
    HouseSystem,
    LagnaState,
    NatalChart,
    PairGeometry,
    PlanetState,
    TransitEvent,
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


class CapabilityState(StrEnum):
    """The state of a capability in the manifest (frozen V1 lifecycle)."""
    AVAILABLE = "AVAILABLE"
    NOT_REQUESTED = "NOT_REQUESTED"
    UNAVAILABLE = "UNAVAILABLE"


class FactKind(StrEnum):
    """The kind of fact contained in a FactEnvelope."""
    PLANET_STATE = "PLANET_STATE"
    PAIR_GEOMETRY = "PAIR_GEOMETRY"
    HOUSE_ANALYSIS = "HOUSE_ANALYSIS"
    TRANSIT_EVENT = "TRANSIT_EVENT"
    ECLIPSE_EVENT = "ECLIPSE_EVENT"
    LAGNA_STATE = "LAGNA_STATE"


#: Narrowest typed ``FactEnvelope`` payload (SPEC §9 / DC §4): exactly the
#: six ``FactKind``-mapped lower-layer fact types. Lower-layer payloads stay
#: source-owned and opaque — JRE-007 never re-declares their schemas.
FactPayload = (
    PlanetState
    | PairGeometry
    | HouseAnalysis
    | TransitEvent
    | EclipseEvent
    | LagnaState
)


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
# Capability contract (SPEC §9.5 / DC §5 — frozen V1 list)
# --------------------------------------------------------------------------- #

#: The capability version this V1 layer provides (pinned to the layer version).
CAPABILITY_VERSION = "0.1.0"

#: Frozen V1 capability ids served by the canonical request boundary.
CAPABILITY_IDS: tuple[str, ...] = ("instant", "natal", "interval", "eclipse")


@dataclass(frozen=True)
class CapabilityDescriptor:
    """Frozen identity + version + required inputs of one V1 capability.

    ``requires`` names the request inputs a capability needs before it can
    be served — the deterministic constraint surface (``check_capability``).
    """

    id: str
    version: str
    requires: tuple[str, ...] = ()


#: Frozen capability registry (immutable view — deterministic constraints).
CAPABILITIES: Mapping[str, CapabilityDescriptor] = MappingProxyType(
    {
        "instant": CapabilityDescriptor(
            id="instant", version=CAPABILITY_VERSION, requires=("instant_utc_iso", "bodies")
        ),
        "natal": CapabilityDescriptor(
            id="natal", version=CAPABILITY_VERSION, requires=("birth",)
        ),
        "interval": CapabilityDescriptor(
            id="interval",
            version=CAPABILITY_VERSION,
            requires=("start_utc_iso", "end_utc_iso", "bodies"),
        ),
        "eclipse": CapabilityDescriptor(
            id="eclipse", version=CAPABILITY_VERSION, requires=("start_utc_iso", "end_utc_iso")
        ),
    }
)


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
    """A single self-contained fact with its own identity and provenance.

    ``payload`` is typed to the six frozen ``FactKind``-mapped lower-layer
    fact types (``FactPayload``) — never an unconstrained ``Any``.
    """

    fact_id: str
    kind: FactKind
    capability: str
    provenance: CanonicalProvenance
    payload: FactPayload


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
    planet_states: tuple[PlanetState, ...] | None
    pair_geometry: tuple[PairGeometry, ...] | None
    house_analyses: tuple[HouseAnalysis, ...] | None
    transit_events: tuple[TransitEvent, ...] | None
    state_samples: tuple[PlanetState, ...] | None
    gochar_instant: GocharInstantResult | None
    gochar_natal: GocharNatalResult | None
    gochar_interval: GocharIntervalResult | None
    eclipses: tuple[EclipseEvent, ...] | None
    provenance: CanonicalProvenance
    version: str = CONTEXT_VERSION


# --------------------------------------------------------------------------- #
# Request models (SPEC §9.5 — the canonical request contract)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ContextRequest:
    """The canonical JRE-007 request boundary (SPEC §9.5 / DC §5).

    Every snapshot query is one ``ContextRequest``: ``capability`` names a
    frozen V1 capability id, ``capability_version`` is the requested
    minimum capability version (compatibility is checked by
    ``check_capability``), ``analysis_request_id`` correlates the request
    with its ``CanonicalContext``, and ``config`` carries the optional
    programmatic override. The capability-specific request models are thin
    compatibility wrappers over this canonical model (fixed
    ``capability``) and cannot alter the canonical public contract.
    """

    capability: str
    capability_version: str = CAPABILITY_VERSION
    config: ContextConfig | None = None
    analysis_request_id: str | None = None

    def __post_init__(self) -> None:
        if self.capability not in CAPABILITY_IDS:
            raise InvalidContextRequestError(
                f"capability must be one of {CAPABILITY_IDS}, got {self.capability!r}"
            )
        if not isinstance(self.capability_version, str) or self.capability_version == "":
            raise InvalidContextRequestError(
                f"capability_version must be a non-empty string, got {self.capability_version!r}"
            )


@dataclass(frozen=True, kw_only=True)
class ContextInstantRequest(ContextRequest):
    """GENERIC instant snapshot query (capability ``instant``): ISO-UTC
    instant + bodies + optional config."""

    instant_utc_iso: str
    bodies: tuple[BodyId, ...]
    capability: str = "instant"


@dataclass(frozen=True, kw_only=True)
class ContextNatalRequest(ContextRequest):
    """INDIVIDUAL natal snapshot query (capability ``natal``): birth +
    optional house analysis and config."""

    birth: BirthData
    include_house_analysis: bool = True
    time_precision: str | None = None
    capability: str = "natal"


@dataclass(frozen=True, kw_only=True)
class ContextIntervalRequest(ContextRequest):
    """Interval snapshot query (capability ``interval``): start/end ISO-UTC
    + bodies + optional config."""

    start_utc_iso: str
    end_utc_iso: str
    bodies: tuple[BodyId, ...]
    capability: str = "interval"


@dataclass(frozen=True, kw_only=True)
class ContextEclipseRequest(ContextRequest):
    """Eclipse snapshot query (capability ``eclipse``): interval + optional
    kind (JRE-003 echo, ADR-006/027 — no new eclipse calculation)."""

    start_utc_iso: str
    end_utc_iso: str
    kind: EclipseKind | None = None
    capability: str = "eclipse"


# --------------------------------------------------------------------------- #
# Capability compatibility (SPEC §9.5 — deterministic constraints)
# --------------------------------------------------------------------------- #


def _version_tuple(version: str) -> tuple[int, ...]:
    """Parse ``MAJOR.MINOR.PATCH``-style versions for deterministic comparison."""
    parts = version.split(".")
    out: list[int] = []
    for part in parts:
        try:
            out.append(int(part))
        except ValueError as exc:
            raise InvalidContextRequestError(
                f"invalid capability version {version!r} (expected dotted integers)"
            ) from exc
    return tuple(out)


def check_capability(request: ContextRequest) -> None:
    """Validate the canonical request's capability contract: frozen V1
    capability identity, requested-minimum/version compatibility, and the
    descriptor's required inputs. Deterministic — raises
    ``InvalidContextRequestError`` with a reason for every violation."""
    descriptor = CAPABILITIES.get(request.capability)
    if descriptor is None:
        raise InvalidContextRequestError(
            f"unknown capability {request.capability!r}; "
            f"frozen V1 capability ids: {list(CAPABILITIES)}"
        )
    if _version_tuple(request.capability_version) > _version_tuple(descriptor.version):
        raise InvalidContextRequestError(
            f"capability {request.capability!r}: requested minimum version "
            f"{request.capability_version!r} exceeds provided {descriptor.version!r}"
        )
    missing = [
        name for name in descriptor.requires if getattr(request, name, None) is None
    ]
    if missing:
        raise InvalidContextRequestError(
            f"capability {request.capability!r} requires inputs "
            f"{descriptor.requires}; missing: {missing}"
        )


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
    hasher.update(f"{domain}:".encode())
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

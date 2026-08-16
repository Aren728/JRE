"""JRE-007 Canonical Context & Fact Snapshot — deterministic factual state
envelope for future JRE engines (SPEC §1-§3).

JRE-007 is a **composition layer**: it assembles one canonical,
provenance-bearing snapshot of *already-computed* lower-layer facts
(JRE-002/003/005/006) and hands it to future engines (Varga, Dasha,
Drishti, Karaka, Avastha, Yoga, Bala, Ashtakavarga, Tajika, Jaimini,
Prashna, Muhurta, Rectification). It computes **nothing new**: no
positions, cusps, lagna, geometry, aspects, event searches, eclipses, or
house facts (SPEC §2.3, ADR-022/023); no doctrine; no rule matching; no
interpretation; no prediction.

V1 accepts ONLY existing point-valued ``BirthData`` (frozen V1 boundary):
no birth-time candidate generation, no date-only candidates, no
rectification, no uncertainty candidate sets.

- ``CanonicalContext`` — the top-level deterministic context container
  (context id, purpose, birth echo, configuration, capability manifest,
  chart identity, source layers).
- ``CanonicalFactSnapshot`` — the envelope: natal chart echo, planet
  states, pair geometry, house analyses, transit event/state echoes,
  gochar echoes, eclipse echoes (JRE-003, ADR-006/027), and the
  six-stage provenance chain (SPEC §3/§16).
- ``FactEnvelope`` / ``FactKind`` / ``CapabilityManifest`` /
  ``CapabilityState`` (``AVAILABLE`` / ``NOT_REQUESTED`` /
  ``UNAVAILABLE``) — the capability-accounting and fact-addressing model.
- ``ContextService`` — facade: ``snapshot_instant`` (GENERIC),
  ``snapshot_natal`` (INDIVIDUAL), ``snapshot_interval``,
  ``snapshot_eclipses`` (JRE-003 echo, ADR-006/027).
- Natal/transit separation is structural: natal sections (``natal_chart``
  / ``house_analyses``) and transit sections (``transit_events`` /
  ``state_samples``) are independent optional fields and are never merged
  (SPEC §17, ADR-021/025).

JRE-007 performs NO interpretation: no dasha, no prediction, no yoga, no
benefic/malefic, no auspiciousness, no varga, no avastha, no bala, no
ashtakavarga, no karaka doctrine, no rule resolution, no confidence, no
eclipse significance, no interval arithmetic (SPEC §3/§15).
"""

from .config import load_config
from .derive import (
    assemble_snapshot,
    build_provenance,
    canonical_bodies,
    chart_identity,
    civil_split,
)
from .errors import (
    ContextComputationError,
    ContextError,
    InvalidContextConfigError,
    InvalidContextRequestError,
)
from .models import (
    CAPABILITIES,
    CAPABILITY_IDS,
    CAPABILITY_VERSION,
    CONTEXT_VERSION,
    GOLDEN_VERSION,
    PROVENANCE_STAGES,
    TIME_PRECISION_VALUES,
    CanonicalContext,
    CanonicalFactSnapshot,
    CanonicalProvenance,
    CapabilityDescriptor,
    CapabilityManifest,
    CapabilityState,
    ContextConfig,
    ContextEclipseRequest,
    ContextInstantRequest,
    ContextIntervalRequest,
    ContextNatalRequest,
    ContextRequest,
    FactEnvelope,
    FactKind,
    ProvenanceStage,
    check_capability,
    compute_deterministic_id,
    validate,
)
from .serialize import (
    SCHEMAS,
    config_from_dict,
    context_request_from_dict,
    eclipse_request_from_dict,
    instant_request_from_dict,
    interval_request_from_dict,
    natal_request_from_dict,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
)
from .service import ContextService

__version__ = CONTEXT_VERSION

__all__ = [
    # service
    "ContextService",
    # config
    "load_config",
    "validate",
    "ContextConfig",
    # context / snapshot / provenance models
    "CanonicalContext",
    "CanonicalFactSnapshot",
    "FactEnvelope",
    "FactKind",
    "CapabilityManifest",
    "CapabilityState",
    "CanonicalProvenance",
    "ProvenanceStage",
    # requests (canonical contract + capability wrappers)
    "ContextRequest",
    "ContextInstantRequest",
    "ContextNatalRequest",
    "ContextIntervalRequest",
    "ContextEclipseRequest",
    # capability contract
    "CAPABILITY_VERSION",
    "CAPABILITY_IDS",
    "CAPABILITIES",
    "CapabilityDescriptor",
    "check_capability",
    # derivation helpers (SPEC §4 — public, unit-testable)
    "assemble_snapshot",
    "chart_identity",
    "build_provenance",
    "civil_split",
    "canonical_bodies",
    # hashing (SPEC §3 — domain-separated content-addressed identity)
    "compute_deterministic_id",
    # errors
    "ContextError",
    "InvalidContextConfigError",
    "InvalidContextRequestError",
    "ContextComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "config_from_dict",
    "context_request_from_dict",
    "instant_request_from_dict",
    "natal_request_from_dict",
    "interval_request_from_dict",
    "eclipse_request_from_dict",
    "schema_for",
    "validate_schema",
    "SCHEMAS",
    # constants
    "CONTEXT_VERSION",
    "GOLDEN_VERSION",
    "TIME_PRECISION_VALUES",
    "PROVENANCE_STAGES",
]

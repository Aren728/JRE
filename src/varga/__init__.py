"""JRE-008 Varga / Divisional Chart Engine — deterministic factual engine.

JRE-008 computes divisional-chart *state* from established JRE-003
``PlanetState`` facts (normative specification §1-§2). It performs NO
prediction, interpretation, yoga/dasha synthesis, strength scoring, rule
evaluation, or inference; NO position/ayanamsa recalculation; NO
ephemeris access. V1 implements exactly D2, D3, D4, D7, D9, D10, D12,
D16, D20, D24, D30, D40, D45, D60 (D1 excluded; D27 deferred).

- ``VargaDefinition`` / ``VargaCalculationMethod`` — frozen, versioned
  definitions; per-varga method identities (never one generic id).
- ``VargaPosition`` / ``VargaChart`` / ``VargaProvenance`` — deterministic
  factual results with JRE-007-style domain-separated identities.
- ``VARGA_REGISTRY`` — the frozen 14-varga catalog; D20 carries two
  distinct methods (``d20-bphs-v1`` canonical, ``d20-saravali-variant-v1``)
  that never merge.
- ``VargaService`` — facade: ``compute_varga_chart``.

JRE-008 is standalone: JRE-007 remains frozen and unmodified; the varga
result may carry an *opaque* JRE-007 ``chart_identity`` join reference
only. Only public ``jyotish`` APIs and the standard library are consumed.
"""

from .config import load_config
from .derive import (
    assemble_varga_chart,
    canonical_body_order,
    compute_varga_position,
    rashi_index,
    sign_at,
)
from .errors import (
    InvalidVargaConfigError,
    InvalidVargaRequestError,
    VargaComputationError,
    VargaError,
)
from .models import (
    VARGA_CATALOG_VERSION,
    VARGA_IDS,
    VARGA_VERSION,
    BoundaryConvention,
    ExplicitTableParams,
    FixedStartParams,
    IntervalEntry,
    MappingStrategy,
    ModalityStartParams,
    OddEvenStartParams,
    RelativeModalityParams,
    SourceCitation,
    SubdivisionStrategy,
    VargaCalculationMethod,
    VargaChart,
    VargaConfig,
    VargaDefinition,
    VargaPosition,
    VargaProvenance,
    compute_deterministic_id,
    source_state_identity,
    validate,
    varga_chart_identity,
    varga_definition_identity,
    varga_position_identity,
)
from .registry import (
    VARGA_REGISTRY,
    available_method_ids,
    canonical_method_id,
    get_varga_definition,
)
from .serialize import (
    SCHEMAS,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
    varga_config_from_dict,
    varga_request_from_dict,
)
from .service import VargaService

__version__ = VARGA_VERSION

__all__ = [
    # service
    "VargaService",
    # config
    "load_config",
    "validate",
    "VargaConfig",
    # models
    "VargaDefinition",
    "VargaCalculationMethod",
    "VargaPosition",
    "VargaChart",
    "VargaProvenance",
    "SourceCitation",
    # enums
    "SubdivisionStrategy",
    "MappingStrategy",
    "BoundaryConvention",
    # mapping parameters
    "ModalityStartParams",
    "RelativeModalityParams",
    "OddEvenStartParams",
    "ExplicitTableParams",
    "IntervalEntry",
    "FixedStartParams",
    # registry / catalog
    "VARGA_REGISTRY",
    "VARGA_IDS",
    "VARGA_VERSION",
    "VARGA_CATALOG_VERSION",
    "get_varga_definition",
    "canonical_method_id",
    "available_method_ids",
    # derivation helpers (public, unit-testable)
    "compute_varga_position",
    "assemble_varga_chart",
    "canonical_body_order",
    "rashi_index",
    "sign_at",
    # identity / hashing
    "compute_deterministic_id",
    "source_state_identity",
    "varga_definition_identity",
    "varga_position_identity",
    "varga_chart_identity",
    # errors
    "VargaError",
    "InvalidVargaConfigError",
    "InvalidVargaRequestError",
    "VargaComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "varga_config_from_dict",
    "varga_request_from_dict",
    "schema_for",
    "validate_schema",
    "SCHEMAS",
]

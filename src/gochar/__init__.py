"""JRE-006 Gochar / Continuous Transit Engine — deterministic gochar state layer.

Consumes ONLY the public ``jyotish`` (JRE-003) and ``bhava`` (JRE-005)
roots plus the standard library (SPEC §2, ADR-022). JRE-006 composes and
echoes; it never recomputes planetary positions, cusps, lagna, geometry,
aspects, or event searches (§2.3). It produces structured transit facts:

- ``GocharInstantResult`` (GENERIC) — instant gochar state, no birth data.
- ``GocharNatalResult`` (INDIVIDUAL) — transit-to-natal relationship facts
  (natal-frame house analysis + full transit-to-natal aspect echo).
- ``GocharIntervalResult`` — echoed event stream (pinned order) + sampled
  state series + optional config-gated natal-frame house series.

JRE-006 performs NO interpretation: no dasha, no prediction, no yoga, no
benefic/malefic, no auspiciousness, no gochar judgements, no drishti
doctrine, no rule resolution, no confidence (§2.4, §24). The word
"transit" denotes structural transit-state handling only.
"""

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
    GocharError,
    InvalidGocharConfigError,
    InvalidGocharRequestError,
)
from .models import (
    GOCHAR_VERSION,
    GOLDEN_VERSION,
    GocharConfig,
    GocharInstantRequest,
    GocharInstantResult,
    GocharIntervalRequest,
    GocharIntervalResult,
    GocharNatalRequest,
    GocharNatalResult,
    GocharProvenance,
    validate,
)
from .serialize import (
    SCHEMAS,
    config_from_dict,
    instant_request_from_dict,
    interval_request_from_dict,
    natal_request_from_dict,
    result_to_dict,
    result_to_json,
    schema_for,
    validate_schema,
)
from .service import GocharService

__version__ = GOCHAR_VERSION

__all__ = [
    # service
    "GocharService",
    # config
    "load_config",
    "validate",
    "GocharConfig",
    # results
    "GocharInstantResult",
    "GocharNatalResult",
    "GocharIntervalResult",
    # requests
    "GocharInstantRequest",
    "GocharNatalRequest",
    "GocharIntervalRequest",
    # provenance
    "GocharProvenance",
    # derivation helpers (SPEC §4 — public, unit-testable)
    "sort_events",
    "build_provenance",
    "derive_natal_house_series",
    "civil_split",
    "canonical_bodies",
    # errors
    "GocharError",
    "InvalidGocharConfigError",
    "InvalidGocharRequestError",
    "GocharComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "config_from_dict",
    "instant_request_from_dict",
    "natal_request_from_dict",
    "interval_request_from_dict",
    "schema_for",
    "validate_schema",
    "SCHEMAS",
    # constants
    "GOLDEN_VERSION",
]

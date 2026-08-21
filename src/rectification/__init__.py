"""JRE-021 Rectification (Birth Time) Engine — deterministic birth time
rectification using classical methods.

JRE-021 computes precise time offsets based on known life events
using classical rectification methods (Transit to Ascendant, Dasha
to Event, Progression to Ascendant), strictly as structural data
points without predictive interpretation.

Strict Boundaries:
- IN SCOPE: src/rectification/, config/rectification.toml
- OUT OF SCOPE: No predictive interpretation, no modification of
  JRE-002 through JRE-020.

Core Models:
- ``LifeEvent``: event_date_utc, event_type, description
- ``RectificationResult``: method, calculated_offset_seconds, confidence_score, evidence
- ``RectificationReport``: input_birth_time, suggested_birth_time, offsets

Service Interface:
- ``RectificationService(config: RectificationConfig)``
- ``calculate_offset(birth_time_utc, events, method, transit_times) -> RectificationReport``
"""

from .config import load_config
from .errors import (
    InvalidRectificationConfigError,
    InvalidRectificationRequestError,
    RectificationComputationError,
    RectificationError,
)
from .models import (
    RECTIFICATION_VERSION,
    EventType,
    LifeEvent,
    RectificationConfig,
    RectificationMethod,
    RectificationReport,
    RectificationResult,
    aggregate_offsets,
    apply_offset_to_birth_time,
    compute_confidence_score,
    compute_offset_seconds,
    event_type_relevant_to_method,
)
from .serialize import (
    rectification_config_from_dict,
    result_to_dict,
    result_to_json,
)
from .service import RectificationService

__version__ = RECTIFICATION_VERSION

__all__ = [
    # service
    "RectificationService",
    # config
    "load_config",
    "RectificationConfig",
    # models
    "LifeEvent",
    "EventType",
    "RectificationMethod",
    "RectificationResult",
    "RectificationReport",
    # derivation helpers
    "compute_offset_seconds",
    "compute_confidence_score",
    "aggregate_offsets",
    "apply_offset_to_birth_time",
    "event_type_relevant_to_method",
    # constants
    "RECTIFICATION_VERSION",
    # errors
    "RectificationError",
    "InvalidRectificationConfigError",
    "InvalidRectificationRequestError",
    "RectificationComputationError",
    # serialization
    "result_to_json",
    "result_to_dict",
    "rectification_config_from_dict",
]

"""JRS Temporal Evidence Layer — Event Windows & Convergence.

Public API
----------
- ``TemporalEvidenceService``  – event window calculation
- ``ActivationType``           – types of temporal activation
- ``ConvergenceLevel``         – convergence classification
- ``TemporalTrigger``          – a single activation trigger
- ``EventWindow``              – time-bound window of convergence
- ``TemporalConfig``           – temporal configuration
- ``load_temporal_config``     – TOML config loader
"""

from __future__ import annotations

from .config import load_temporal_config
from .errors import (
    InvalidEventWindowError,
    InvalidTemporalConfigError,
    InvalidTriggerError,
    OverlapCalculationError,
    TemporalError,
)
from .models import (
    CONVERGENCE_VALUES,
    ActivationType,
    ConvergenceLevel,
    EventWindow,
    TemporalConfig,
    TemporalTrigger,
    classify_convergence,
    compute_overlap_window,
    find_overlapping_triggers,
    parse_iso_timestamp,
    windows_overlap,
)
from .serialize import (
    activation_type_from_str,
    convergence_level_from_str,
    event_window_from_dict,
    result_to_dict,
    result_to_json,
    temporal_config_from_dict,
    temporal_trigger_from_dict,
    trigger_to_json,
)
from .service import TemporalEvidenceService

__all__: tuple[str, ...] = (
    # Errors
    "TemporalError",
    "InvalidTemporalConfigError",
    "InvalidTriggerError",
    "InvalidEventWindowError",
    "OverlapCalculationError",
    # Enums
    "ActivationType",
    "ConvergenceLevel",
    "CONVERGENCE_VALUES",
    # Models
    "TemporalTrigger",
    "EventWindow",
    "TemporalConfig",
    "parse_iso_timestamp",
    "windows_overlap",
    "compute_overlap_window",
    "classify_convergence",
    "find_overlapping_triggers",
    # Config
    "load_temporal_config",
    # Serialize
    "activation_type_from_str",
    "convergence_level_from_str",
    "temporal_trigger_from_dict",
    "event_window_from_dict",
    "temporal_config_from_dict",
    "result_to_dict",
    "result_to_json",
    "trigger_to_json",
    # Service
    "TemporalEvidenceService",
)

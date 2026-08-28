"""JRS Temporal Evidence Layer — Event Windows, Convergence & Transit Activation.

Public API
----------
- ``TemporalEvidenceService``    – event window calculation
- ``TransitActivationService``   – Dasha-First transit activation (TA-001–005)
- ``VedhaService``               – Classical Vedha obstruction (TA-015–019)
- ``TaraBalaService``            – Nakshatra-based strength (TA-020–021)
- ``ActivationType``             – types of temporal activation
- ``ConvergenceLevel``           – convergence classification
- ``TemporalTrigger``            – a single activation trigger
- ``EventWindow``                – time-bound window of convergence
- ``TemporalConfig``             – temporal configuration
- ``load_temporal_config``       – TOML config loader
"""

from __future__ import annotations

from .activation_service import (
    ActivationLevel,
    ActivationResult,
    TransitActivationService,
)
from .config import load_temporal_config
from .dasha_engine import (
    DashaHierarchy,
    DashaMultiplierResult,
    DashaPeriod,
    VimshottariDashaEngine,
)
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
from .timeline_service import DynamicStrengthResult, DynamicTemporalService
from .transit_evaluator import TransitEvaluationResult, TransitEvaluator, TransitProfile
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
from .tara_bala_service import TaraBalaService, TaraResult, TaraStrength
from .vedha_service import VedhaResult, VedhaService

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
    "ActivationLevel",
    "TaraStrength",
    # Models
    "TemporalTrigger",
    "EventWindow",
    "TemporalConfig",
    "ActivationResult",
    "VedhaResult",
    "TaraResult",
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
    # Services
    "TemporalEvidenceService",
    "TransitActivationService",
    "VedhaService",
    "TaraBalaService",
    "VimshottariDashaEngine",
    "TransitEvaluator",
    "DynamicTemporalService",
    # Dasha models
    "DashaPeriod",
    "DashaHierarchy",
    "DashaMultiplierResult",
    # Transit models
    "TransitProfile",
    "TransitEvaluationResult",
    # Dynamic models
    "DynamicStrengthResult",
)

"""Validation — reference-chart validation framework.

Public API
----------
- ``ValidationService``  – runs validation against reference charts
- ``ReferenceChart``     – chart with known events
- ``KnownEvent``         – a known life event with expected triggers
- ``ValidationResult``   – result for a single chart
- ``ValidationReport``   – aggregated results
- ``ValidationConfig``   – validation configuration
- ``load_validation_config`` – TOML config loader
"""

from __future__ import annotations

from .config import load_validation_config
from .errors import (
    InvalidReferenceChartError,
    InvalidValidationConfigError,
    TriggerExtractionError,
    ValidationComputationError,
    ValidationError,
)
from .models import (
    EventType,
    ExtractedTrigger,
    KnownEvent,
    ReferenceChart,
    TriggerSource,
    ValidationConfig,
    ValidationReport,
    ValidationResult,
    compute_match_score,
    extract_triggers_from_engines,
    find_missing_and_false_positives,
)
from .serialize import (
    extracted_trigger_from_dict,
    known_event_from_dict,
    reference_chart_from_dict,
    result_to_dict,
    result_to_json,
    validation_config_from_dict,
    validation_report_from_dict,
    validation_result_from_dict,
)
from .service import ValidationService

__all__: tuple[str, ...] = (
    # Errors
    "ValidationError",
    "InvalidValidationConfigError",
    "InvalidReferenceChartError",
    "TriggerExtractionError",
    "ValidationComputationError",
    # Models
    "EventType",
    "TriggerSource",
    "KnownEvent",
    "ReferenceChart",
    "ExtractedTrigger",
    "ValidationResult",
    "ValidationReport",
    "ValidationConfig",
    "compute_match_score",
    "extract_triggers_from_engines",
    "find_missing_and_false_positives",
    # Config
    "load_validation_config",
    # Serialize
    "known_event_from_dict",
    "reference_chart_from_dict",
    "extracted_trigger_from_dict",
    "validation_result_from_dict",
    "validation_report_from_dict",
    "validation_config_from_dict",
    "result_to_dict",
    "result_to_json",
    # Service
    "ValidationService",
)

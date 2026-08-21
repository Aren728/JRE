"""Validation system deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from .errors import InvalidReferenceChartError
from .models import (
    EventType,
    ExtractedTrigger,
    KnownEvent,
    ReferenceChart,
    TriggerSource,
    ValidationConfig,
    ValidationReport,
    ValidationResult,
)


def known_event_from_dict(data: dict[str, Any]) -> KnownEvent:
    """Deserialize a KnownEvent from a dict."""
    event_type_str = data.get("event_type", "OTHER")
    try:
        event_type = EventType(event_type_str)
    except ValueError as exc:
        raise InvalidReferenceChartError(
            f"Unknown event type: {event_type_str}",
        ) from exc

    return KnownEvent(
        event_date_utc=data.get("event_date_utc", ""),
        event_type=event_type,
        expected_triggers=tuple(data.get("expected_triggers", [])),
        description=data.get("description", ""),
    )


def reference_chart_from_dict(data: dict[str, Any]) -> ReferenceChart:
    """Deserialize a ReferenceChart from a dict."""
    return ReferenceChart(
        chart_id=data["chart_id"],
        birth_data=dict(data.get("birth_data", {})),
        known_events=tuple(
            known_event_from_dict(e) for e in data.get("known_events", [])
        ),
        ground_truth=dict(data.get("ground_truth", {})),
        description=data.get("description", ""),
    )


def extracted_trigger_from_dict(data: dict[str, Any]) -> ExtractedTrigger:
    """Deserialize an ExtractedTrigger from a dict."""
    source_str = data.get("source", "SYNTHESIS")
    try:
        source = TriggerSource(source_str)
    except ValueError:
        source = TriggerSource.SYNTHESIS

    return ExtractedTrigger(
        trigger_id=data.get("trigger_id", ""),
        source=source,
        confidence=float(data.get("confidence", 1.0)),
        metadata=data.get("metadata", ""),
    )


def validation_result_from_dict(data: dict[str, Any]) -> ValidationResult:
    """Deserialize a ValidationResult from a dict."""
    return ValidationResult(
        chart_id=data["chart_id"],
        expected_triggers=tuple(data.get("expected_triggers", [])),
        actual_triggers=tuple(
            extracted_trigger_from_dict(t)
            for t in data.get("actual_triggers", [])
        ),
        match_score=float(data.get("match_score", 0.0)),
        missing_triggers=tuple(data.get("missing_triggers", [])),
        false_positives=tuple(data.get("false_positives", [])),
        total_events=int(data.get("total_events", 0)),
    )


def validation_report_from_dict(data: dict[str, Any]) -> ValidationReport:
    """Deserialize a ValidationReport from a dict."""
    return ValidationReport(
        results=tuple(
            validation_result_from_dict(r)
            for r in data.get("results", [])
        ),
        overall_score=float(data.get("overall_score", 0.0)),
        total_charts=int(data.get("total_charts", 0)),
        timestamp=data.get("timestamp", ""),
    )


def validation_config_from_dict(data: dict[str, Any]) -> ValidationConfig:
    """Deserialize a ValidationConfig from a dict."""
    return ValidationConfig(
        version=data.get("version", "1.0"),
        match_threshold=float(data.get("match_threshold", 0.5)),
        trigger_weights=dict(data.get("trigger_weights", {})),
        source_reliability=dict(data.get("source_reliability", {})),
    )


def result_to_dict(report: ValidationReport) -> dict[str, Any]:
    """Deterministic dict serialization of a ValidationReport."""
    return report.to_dict()


def result_to_json(report: ValidationReport, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a ValidationReport."""
    d = result_to_dict(report)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)

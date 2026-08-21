"""Temporal evidence deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from .models import (
    ActivationType,
    ConvergenceLevel,
    EventWindow,
    TemporalConfig,
    TemporalTrigger,
)


def activation_type_from_str(value: str) -> ActivationType:
    """Deserialize an ActivationType from a string."""
    return ActivationType(value)


def convergence_level_from_str(value: str) -> ConvergenceLevel:
    """Deserialize a ConvergenceLevel from a string."""
    return ConvergenceLevel(value)


def temporal_trigger_from_dict(data: dict[str, Any]) -> TemporalTrigger:
    """Deserialize a TemporalTrigger from a dict."""
    return TemporalTrigger(
        activation_type=ActivationType(data["activation_type"]),
        triggering_planet=data.get("triggering_planet", ""),
        triggering_rashi=data.get("triggering_rashi", ""),
        activation_start_utc=data.get("activation_start_utc", ""),
        activation_end_utc=data.get("activation_end_utc", ""),
        strength=float(data.get("strength", 1.0)),
        description=data.get("description", ""),
    )


def event_window_from_dict(data: dict[str, Any]) -> EventWindow:
    """Deserialize an EventWindow from a dict."""
    return EventWindow(
        candidate_event_taxonomy=data["candidate_event_taxonomy"],
        window_start_utc=data.get("window_start_utc", ""),
        window_end_utc=data.get("window_end_utc", ""),
        triggers=tuple(
            temporal_trigger_from_dict(t)
            for t in data.get("triggers", [])
        ),
        convergence_level=ConvergenceLevel(
            data.get("convergence_level", "NONE"),
        ),
        conflicting_indicators=int(data.get("conflicting_indicators", 0)),
    )


def temporal_config_from_dict(data: dict[str, Any]) -> TemporalConfig:
    """Deserialize a TemporalConfig from a dict."""
    return TemporalConfig(
        version=data.get("version", "1.0"),
        convergence_rules=dict(data.get("convergence_rules", {})),
        min_triggers_for_high=int(data.get("min_triggers_for_high", 3)),
        min_triggers_for_moderate=int(data.get("min_triggers_for_moderate", 2)),
        activation_type_weights=dict(data.get("activation_type_weights", {})),
    )


def result_to_dict(window: EventWindow) -> dict[str, Any]:
    """Deterministic dict serialization of an EventWindow."""
    return window.to_dict()


def result_to_json(window: EventWindow, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of an EventWindow."""
    d = result_to_dict(window)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def trigger_to_json(trigger: TemporalTrigger, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a TemporalTrigger."""
    return json.dumps(trigger.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

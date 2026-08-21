"""Deterministic serialization for JRE-021 Rectification.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import RectificationConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-021 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-021 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def rectification_config_from_dict(data: dict[str, Any]) -> RectificationConfig:
    """Deserialize a ``RectificationConfig`` from a JSON-shaped dict."""
    version = data.get("version", "0.1.0")
    max_offset = data.get("max_offset_seconds", 86400.0)

    raw_weights: Any = data.get("method_weights", {})
    method_weights: dict[str, float] = {}
    if isinstance(raw_weights, dict):
        for key, val in raw_weights.items():
            if isinstance(key, str) and isinstance(val, (int, float)):
                method_weights[key] = float(val)

    raw_tolerances: Any = data.get("method_tolerances", {})
    method_tolerances: dict[str, float] = {}
    if isinstance(raw_tolerances, dict):
        for key, val in raw_tolerances.items():
            if isinstance(key, str) and isinstance(val, (int, float)):
                method_tolerances[key] = float(val)

    raw_evidence: Any = data.get("evidence_weights", {})
    evidence_weights: dict[str, float] = {}
    if isinstance(raw_evidence, dict):
        for key, val in raw_evidence.items():
            if isinstance(key, str) and isinstance(val, (int, float)):
                evidence_weights[key] = float(val)

    return RectificationConfig(
        version=str(version),
        max_offset_seconds=float(max_offset) if isinstance(max_offset, (int, float)) else 86400.0,
        method_weights=method_weights,
        method_tolerances=method_tolerances,
        evidence_weights=evidence_weights,
    )

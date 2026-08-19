"""Deterministic serialization for JRE-013 Yoga.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import YogaConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-013 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-013 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def yoga_config_from_dict(data: dict[str, Any]) -> YogaConfig:
    """Deserialize a ``YogaConfig`` from a JSON-shaped dict."""
    return YogaConfig.from_dict(data)

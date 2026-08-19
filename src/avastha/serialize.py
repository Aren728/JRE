"""Deterministic serialization for JRE-015 Avastha.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import AvasthaConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-015 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-015 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def avastha_config_from_dict(data: dict[str, Any]) -> AvasthaConfig:
    """Deserialize an ``AvasthaConfig`` from a JSON-shaped dict."""
    return AvasthaConfig.from_dict(data)

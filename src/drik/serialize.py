"""Deterministic serialization for JRE-012 Drik.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import DrikConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-012 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-012 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def drik_config_from_dict(data: dict[str, Any]) -> DrikConfig:
    """Deserialize a ``DrikConfig`` from a JSON-shaped dict."""
    return DrikConfig.from_dict(data)

"""Deterministic serialization for JRE-016 Ashtakavarga.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import AshtakavargaConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-016 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-016 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def ashtakavarga_config_from_dict(data: dict[str, Any]) -> AshtakavargaConfig:
    """Deserialize an ``AshtakavargaConfig`` from a JSON-shaped dict."""
    return AshtakavargaConfig(version=data.get("version", "0.1.0"))

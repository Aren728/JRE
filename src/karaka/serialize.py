"""Deterministic serialization for JRE-014 Karaka.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import KarakaConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-014 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-014 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def karaka_config_from_dict(data: dict[str, Any]) -> KarakaConfig:
    """Deserialize a ``KarakaConfig`` from a JSON-shaped dict."""
    return KarakaConfig.from_dict(data)

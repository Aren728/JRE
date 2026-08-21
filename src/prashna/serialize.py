"""Deterministic serialization for JRE-019 Prashna.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import PrashnaConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-019 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-019 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def prashna_config_from_dict(data: dict[str, Any]) -> PrashnaConfig:
    """Deserialize a ``PrashnaConfig`` from a JSON-shaped dict."""
    version = data.get("version", "0.1.0")
    default_category = data.get("default_category", "GENERAL")
    raw_mappings = data.get("house_mappings", {})
    house_mappings: dict[str, tuple[int, int]] = {}
    if isinstance(raw_mappings, dict):
        for cat_name, cat_val in raw_mappings.items():
            if isinstance(cat_val, dict):
                primary = cat_val.get("primary")
                secondary = cat_val.get("secondary")
                if isinstance(primary, int) and isinstance(secondary, int):
                    house_mappings[str(cat_name)] = (primary, secondary)
            elif isinstance(cat_val, (list, tuple)) and len(cat_val) == 2:
                house_mappings[str(cat_name)] = (int(cat_val[0]), int(cat_val[1]))
    return PrashnaConfig(
        version=str(version),
        default_category=str(default_category),
        house_mappings=house_mappings,
    )

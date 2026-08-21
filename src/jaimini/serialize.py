"""Deterministic serialization for JRE-018 Jaimini.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import JaiminiConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-018 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-018 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def jaimini_config_from_dict(data: dict[str, Any]) -> JaiminiConfig:
    """Deserialize a ``JaiminiConfig`` from a JSON-shaped dict."""
    version = data.get("version", "0.1.0")
    period_years = data.get("default_period_years", 7)
    raw_start = data.get("chara_dasha_start_sign", {"MOVABLE": 9, "FIXED": 10, "DUAL": 11})
    raw_int = data.get("argala_intervening_houses", [2, 4, 5, 11])
    raw_obs = data.get("argala_obstructing_houses", [12, 10, 9, 3])
    return JaiminiConfig(
        version=version,
        default_period_years=int(period_years),
        chara_dasha_start_sign=dict(raw_start) if isinstance(raw_start, dict) else raw_start,
        argala_intervening_houses=tuple(raw_int) if isinstance(raw_int, (list, tuple)) else raw_int,
        argala_obstructing_houses=tuple(raw_obs) if isinstance(raw_obs, (list, tuple)) else raw_obs,
    )

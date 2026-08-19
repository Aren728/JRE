"""Deterministic serialization for JRE-011 Bala.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import BalaConfig, to_dict_value

# --------------------------------------------------------------------------- #
# Result serialization
# --------------------------------------------------------------------------- #


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-011 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-011 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


# --------------------------------------------------------------------------- #
# Config parsing
# --------------------------------------------------------------------------- #


def bala_config_from_dict(data: dict[str, Any]) -> BalaConfig:
    """Deserialize a ``BalaConfig`` from a JSON-shaped dict."""
    return BalaConfig.from_dict(data)

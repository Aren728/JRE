"""Deterministic serialization for JRE-017 Tajika.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates rather than
trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from typing import Any

from .models import TajikaConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-017 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-017 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def tajika_config_from_dict(data: dict[str, Any]) -> TajikaConfig:
    """Deserialize a ``TajikaConfig`` from a JSON-shaped dict."""
    version = data.get("version", "0.1.0")
    raw_sahams = data.get("enabled_sahams")
    if isinstance(raw_sahams, list) and raw_sahams:
        from .models import SahamType
        enabled = tuple(SahamType(s) for s in raw_sahams)
    else:
        from .models import SahamType
        enabled = tuple(SahamType)
    return TajikaConfig(version=version, enabled_sahams=enabled)

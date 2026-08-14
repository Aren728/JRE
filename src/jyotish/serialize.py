"""JSON serialization for the Jyotish layer (Specialist spec §21).

Serialization rules (DATA-CONTRACT §0): snake_case keys; enums as their
string values; ``Pada`` as its int; tuples as arrays; ``None`` as ``null``;
floats via Python's round-trip repr so the JSON number decodes to the
identical double. ``-0.0 -> 0.0``.

Input parsers validate on construction (SPEC §21): ``config_from_dict``
raises the documented typed errors (``InvalidConfigError`` for unknown enum
values, ``InvalidOrbError`` for invalid orbs) instead of raw ``ValueError``.
"""

from __future__ import annotations

import json
from typing import Any

from .config import validate
from .errors import InvalidConfigError
from .models import BirthData, JyotishConfig, to_dict_value


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-003 result object (or tuple of objects) to a dict."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-003 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def config_from_dict(data: dict[str, Any]) -> JyotishConfig:
    """Deserialize a ``JyotishConfig`` from a JSON-shaped dict (typed errors,
    validated on construction per SPEC §21)."""
    try:
        config = JyotishConfig.from_dict(data)
    except ValueError as exc:
        raise InvalidConfigError(f"invalid config value: {exc}") from exc
    return validate(config)


def birth_from_dict(data: dict[str, Any]) -> BirthData:
    """Deserialize ``BirthData`` from a JSON-shaped dict."""
    return BirthData(
        date=data["date"],
        time=data["time"],
        timezone=data["timezone"],
        latitude=float(data["latitude"]),
        longitude=float(data["longitude"]),
    )


def planetary_request_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a generic planetary-state query dict."""
    return {
        "date": data["date"],
        "time": data["time"],
        "timezone": data["timezone"],
        "latitude": float(data["latitude"]),
        "longitude": float(data["longitude"]),
        "bodies": data.get("bodies"),
        "config": data.get("config"),
    }


def transit_query_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a transit event query dict."""
    return {
        "start_utc_iso": data["start_utc_iso"],
        "end_utc_iso": data["end_utc_iso"],
        "bodies": data.get("bodies"),
        "kinds": data.get("kinds"),
        "config": data.get("config"),
    }


def eclipse_query_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize an eclipse query dict."""
    return {
        "start_utc_iso": data["start_utc_iso"],
        "end_utc_iso": data["end_utc_iso"],
        "kind": data.get("kind"),
        "config": data.get("config"),
    }

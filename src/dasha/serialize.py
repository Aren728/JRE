"""Deterministic serialization for JRE-010 Dasha.

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates and recomputes
identity rather than trusting externally supplied fingerprints.
"""

from __future__ import annotations

import json
from datetime import UTC
from typing import Any

from .models import (
    DashaConfig,
    DashaPeriod,
    DashaSystem,
    DashaTimeline,
    to_dict_value,
)

# --------------------------------------------------------------------------- #
# Result serialization
# --------------------------------------------------------------------------- #


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-010 result object to a dict (deterministic key
    order = dataclass declaration order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-010 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


# --------------------------------------------------------------------------- #
# Config parsing
# --------------------------------------------------------------------------- #


def dasha_config_from_dict(data: dict[str, Any]) -> DashaConfig:
    """Deserialize a ``DashaConfig`` from a JSON-shaped dict."""
    return DashaConfig.from_dict(data)


# --------------------------------------------------------------------------- #
# Period parsing
# --------------------------------------------------------------------------- #


def dasha_period_from_dict(data: dict[str, Any]) -> DashaPeriod:
    """Deserialize a ``DashaPeriod`` from a JSON-shaped dict."""
    from datetime import datetime

    from jyotish import BodyId

    start_raw = data.get("start_utc", "")
    end_raw = data.get("end_utc", "")
    if isinstance(start_raw, str):
        start_utc = datetime.fromisoformat(start_raw)
    else:
        start_utc = datetime.fromtimestamp(float(start_raw), tz=UTC)
    if isinstance(end_raw, str):
        end_utc = datetime.fromisoformat(end_raw)
    else:
        end_utc = datetime.fromtimestamp(float(end_raw), tz=UTC)

    mahadasha = BodyId(data["mahadasha_lord"])
    antardasha_raw = data.get("antardasha_lord")
    antardasha = BodyId(antardasha_raw) if antardasha_raw is not None else None
    pratyantardasha_raw = data.get("pratyantardasha_lord")
    pratyantardasha = BodyId(pratyantardasha_raw) if pratyantardasha_raw is not None else None

    return DashaPeriod(
        start_utc=start_utc,
        end_utc=end_utc,
        mahadasha_lord=mahadasha,
        antardasha_lord=antardasha,
        pratyantardasha_lord=pratyantardasha,
    )


# --------------------------------------------------------------------------- #
# Timeline parsing
# --------------------------------------------------------------------------- #


def dasha_timeline_from_dict(data: dict[str, Any]) -> DashaTimeline:
    """Deserialize a ``DashaTimeline`` from a JSON-shaped dict."""
    from jyotish import NakshatraId, Pada

    nakshatra = NakshatraId(data["birth_nakshatra"])
    pada = Pada(data["birth_pada"])
    balance = float(data["balance_at_birth"])
    system = DashaSystem(data["system"])
    periods_raw = data.get("periods", [])
    periods = tuple(dasha_period_from_dict(p) for p in periods_raw)

    return DashaTimeline(
        birth_nakshatra=nakshatra,
        birth_pada=pada,
        balance_at_birth=balance,
        system=system,
        periods=periods,
    )

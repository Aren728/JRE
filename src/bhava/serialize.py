"""JSON serialization for the JRE-005 Bhava layer (SPEC §26).

Conventions (DATA-CONTRACT §0): snake_case keys; enums as string values;
tuples as arrays; ``None`` as ``null``; floats via Python's round-trip
repr (``-0.0 -> 0.0``). Input parsers validate on construction with the
typed error taxonomy (SPEC §29); malformed birth data propagates the
JRE-003 ``InvalidBirthDataError`` unchanged.
"""

from __future__ import annotations

import json
from typing import Any

import jyotish
from jyotish import HouseSystem, TransitReferencePoint

from .errors import (
    InvalidAnalysisRequestError,
    InvalidBhavaConfigError,
    UnsupportedReferenceError,
)
from .models import BhavaConfig, to_dict_value, validate


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-005 result object to a dict (deterministic order)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-005 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def _parse_references(raw: Any) -> tuple[TransitReferencePoint, ...]:
    if raw is None:
        return tuple(TransitReferencePoint)
    if not isinstance(raw, (list, tuple)) or not raw:
        raise InvalidAnalysisRequestError(f"references must be a non-empty array, got {raw!r}")
    from .derive import REFERENCE_ORDER

    requested: set[TransitReferencePoint] = set()
    for item in raw:
        if not isinstance(item, TransitReferencePoint):
            try:
                item = TransitReferencePoint(item)
            except ValueError as exc:
                raise UnsupportedReferenceError(f"unsupported reference value {item!r}") from exc
        requested.add(item)
    return tuple(reference for reference in REFERENCE_ORDER if reference in requested)


def analysis_request_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a natal analysis request dict (DATA-CONTRACT §10).

    Returns ``{"birth", "house_systems", "references", "config"}`` with
    typed values. Unknown house system → ``InvalidBhavaConfigError``;
    unknown reference → ``UnsupportedReferenceError``; malformed birth →
    JRE-003 ``InvalidBirthDataError`` (propagates).
    """
    if "birth" not in data:
        raise InvalidAnalysisRequestError("request must contain 'birth'")
    birth = jyotish.birth_from_dict(data["birth"])

    systems_raw = data.get("house_systems", ["WHOLE_SIGN"])
    if not isinstance(systems_raw, (list, tuple)) or not systems_raw:
        raise InvalidAnalysisRequestError(
            f"house_systems must be a non-empty array, got {systems_raw!r}"
        )
    house_systems = tuple(_parse_house_system(item) for item in systems_raw)

    references = _parse_references(data.get("references"))

    config_raw = data.get("config")
    config = (
        BhavaConfig.from_dict(config_raw)
        if isinstance(config_raw, dict)
        else validate(BhavaConfig())
    )

    return {
        "birth": birth,
        "house_systems": house_systems,
        "references": references,
        "config": config,
    }


def transit_request_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a transit analysis request dict (DATA-CONTRACT §10).

    ``natal_chart`` is opaque and passed through unchanged (the caller
    supplies the JRE-003 ``NatalChart``). Returns
    ``{"transit": {"birth", "transit_instant_utc_iso", "reference"},
    "natal_chart", "references", "config"}``.
    """
    transit_raw = data.get("transit")
    if not isinstance(transit_raw, dict):
        raise InvalidAnalysisRequestError("request must contain 'transit'")
    if "birth" not in transit_raw:
        raise InvalidAnalysisRequestError("transit request must contain 'birth'")
    birth = jyotish.birth_from_dict(transit_raw["birth"])
    transit_instant_utc_iso = transit_raw.get("transit_instant_utc_iso")
    if not isinstance(transit_instant_utc_iso, str) or not transit_instant_utc_iso:
        raise InvalidAnalysisRequestError(
            f"transit_instant_utc_iso must be a non-empty string, got {transit_instant_utc_iso!r}"
        )
    reference_raw = transit_raw.get("reference", "LAGNA")
    try:
        reference = (
            reference_raw
            if isinstance(reference_raw, TransitReferencePoint)
            else TransitReferencePoint(reference_raw)
        )
    except ValueError as exc:
        raise UnsupportedReferenceError(f"unsupported reference value {reference_raw!r}") from exc

    natal_chart = data.get("natal_chart")
    if natal_chart is None:
        raise InvalidAnalysisRequestError("request must contain 'natal_chart'")

    references = _parse_references(data.get("references"))
    config_raw = data.get("config")
    config = (
        BhavaConfig.from_dict(config_raw)
        if isinstance(config_raw, dict)
        else validate(BhavaConfig())
    )

    return {
        "transit": {
            "birth": birth,
            "transit_instant_utc_iso": transit_instant_utc_iso,
            "reference": reference,
        },
        "natal_chart": natal_chart,
        "references": references,
        "config": config,
    }


def _parse_house_system(raw: Any) -> HouseSystem:
    if isinstance(raw, HouseSystem):
        return raw
    try:
        return HouseSystem(raw)
    except ValueError as exc:
        raise InvalidBhavaConfigError(f"unknown house_system value {raw!r}") from exc

"""JSON serialization for the astronomical core (Specialist spec §32).

Serialization rules (DATA-CONTRACT §0, §8):

- snake_case keys; enums as their string values; tuples as arrays;
  ``None`` as ``null``; floats as IEEE-754 doubles via Python's round-trip
  repr (``json.dumps`` default) so the JSON number decodes to the identical
  double.
- ``result_to_json`` output validates against the JSON Schema in
  ``docs/architecture/JRE-002-DATA-CONTRACT.md`` §8.
"""

from __future__ import annotations

import json
from typing import Any

from .models import (
    BodyId,
    BodyPosition,
    CalculationConfig,
    EphemerisMode,
    EphemerisRequest,
    EphemerisResult,
    PositionType,
    ProviderMetadata,
    ProviderRun,
    RetrogradeState,
)


def result_to_dict(result: EphemerisResult) -> dict[str, Any]:
    return result.to_dict()


def result_to_json(result: EphemerisResult) -> str:
    """Serialize an ``EphemerisResult`` to JSON (exact float round-trip)."""
    return json.dumps(result.to_dict())


def config_from_dict(data: dict[str, Any]) -> CalculationConfig:
    """Deserialize a ``CalculationConfig`` from a JSON-shaped dict."""
    return CalculationConfig.from_dict(data)


def request_from_dict(data: dict[str, Any]) -> EphemerisRequest:
    """Deserialize an ``EphemerisRequest`` from a JSON-shaped dict."""
    return EphemerisRequest.from_dict(data)


def json_to_result(payload: str) -> EphemerisResult:
    """Deserialize an ``EphemerisResult`` from a JSON string (round-trip helper)."""
    data = json.loads(payload)
    return EphemerisResult(
        request_snapshot=EphemerisRequest.from_dict(data["request_snapshot"]),
        timestamp_utc_iso=data["timestamp_utc_iso"],
        timestamp_local_iso=data["timestamp_local_iso"],
        julian_day_ut=float(data["julian_day_ut"]),
        positions=tuple(_position_from_dict(p) for p in data["positions"]),
        provider=_metadata_from_dict(data["provider"]),
        provider_run=_run_from_dict(data["provider_run"]),
        config=CalculationConfig.from_dict(data["config"]),
    )


def _position_from_dict(data: dict[str, Any]) -> BodyPosition:
    return BodyPosition(
        body=BodyId(data["body"]),
        longitude_tropical=float(data["longitude_tropical"]),
        longitude_sidereal=(
            None if data["longitude_sidereal"] is None else float(data["longitude_sidereal"])
        ),
        latitude=float(data["latitude"]),
        distance_au=float(data["distance_au"]),
        speed_longitude=float(data["speed_longitude"]),
        speed_latitude=float(data["speed_latitude"]),
        speed_distance=float(data["speed_distance"]),
        retrograde=RetrogradeState(data["retrograde"]),
        position_type=PositionType(data["position_type"]),
        ayanamsa_value=None if data["ayanamsa_value"] is None else float(data["ayanamsa_value"]),
    )


def _metadata_from_dict(data: dict[str, Any]) -> ProviderMetadata:
    return ProviderMetadata(
        provider_id=data["provider_id"],
        library_name=data["library_name"],
        library_version=data["library_version"],
        ephemeris_version=data["ephemeris_version"],
    )


def _run_from_dict(data: dict[str, Any]) -> ProviderRun:
    return ProviderRun(
        positions=tuple(_position_from_dict(p) for p in data["positions"]),
        ephemeris_mode=EphemerisMode(data["ephemeris_mode"]),
        ephemeris_files=tuple(data["ephemeris_files"]),
    )

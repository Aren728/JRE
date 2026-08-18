"""Deterministic serialization and Draft 2020-12 JSON Schema for JRE-008
(normative specification §20).

``result_to_dict`` / ``result_to_json`` are deterministic (declaration
order, enum -> value, ``-0.0 -> 0.0``); parsing validates and recomputes
identity rather than trusting externally supplied fingerprints. Schemas
are generated from the frozen dataclasses with ``additionalProperties =
false`` at every object level.
"""

from __future__ import annotations

import enum
import json
import re
import typing
from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints

from jyotish import BodyId, PlanetState

from .errors import InvalidVargaRequestError
from .models import (
    BoundaryConvention,
    ExplicitTableParams,
    FixedStartParams,
    IntervalEntry,
    MappingStrategy,
    ModalityStartParams,
    OddEvenStartParams,
    RelativeModalityParams,
    SourceCitation,
    SubdivisionStrategy,
    VargaCalculationMethod,
    VargaChart,
    VargaConfig,
    VargaDefinition,
    VargaPosition,
    VargaProvenance,
    to_dict_value,
)

#: Enum-typed fields with pinned values (schema constraints).
_PINNED_ENUM_OVERRIDES: dict[str, dict[str, Any]] = {
    "subdivision_strategy": {
        "type": "string",
        "enum": [member.value for member in SubdivisionStrategy],
    },
    "mapping_strategy": {
        "type": "string",
        "enum": [member.value for member in MappingStrategy],
    },
    "boundary_convention": {
        "type": "string",
        "enum": [member.value for member in BoundaryConvention],
    },
    "default_boundary_convention": {
        "type": "string",
        "enum": [BoundaryConvention.HALF_OPEN_LOW.value],
    },
}


# --------------------------------------------------------------------------- #
# Result serialization
# --------------------------------------------------------------------------- #


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-008 result object to a dict (deterministic key
    order = dataclass declaration order; §20)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-008 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


# --------------------------------------------------------------------------- #
# Config parsing (§20)
# --------------------------------------------------------------------------- #


def varga_config_from_dict(data: dict[str, Any]) -> VargaConfig:
    """Deserialize a ``VargaConfig`` from a JSON-shaped dict."""
    return VargaConfig.from_dict(data)


# --------------------------------------------------------------------------- #
# JSON Schema (§20) — generated from the model dataclasses
# --------------------------------------------------------------------------- #


def _type_schema(typ: Any) -> dict[str, Any]:
    """Build a JSON-Schema fragment for a type annotation."""
    origin = get_origin(typ)
    args = get_args(typ)

    if origin is typing.Union or origin is types_union():
        has_null = any(arg is type(None) for arg in args)
        non_null = [arg for arg in args if arg is not type(None)]
        if len(non_null) == 1:
            inner = dict(_type_schema(non_null[0]))
            current = inner.get("type")
            if has_null:
                if isinstance(current, str):
                    inner["type"] = [current, "null"]
                elif isinstance(current, list):
                    inner["type"] = [*current, "null"]
                else:
                    inner["anyOf"] = [{"type": "null"}]
            return inner
        branches = [_type_schema(arg) for arg in non_null]
        if has_null:
            branches.append({"type": "null"})
        return {"anyOf": branches}

    if origin is tuple or origin is list:
        items = _type_schema(args[0]) if args and args[0] is not Ellipsis else {}
        return {"type": "array", "items": items}

    if origin is dict:
        value_schema = _type_schema(args[1]) if len(args) > 1 else {}
        if value_schema == {} or value_schema == {"type": "object"}:
            return {"type": "object"}
        return {"type": "object", "additionalProperties": value_schema}

    if typ is str:
        return {"type": "string"}
    if typ is float:
        return {"type": "number"}
    if typ is int:
        return {"type": "integer"}
    if typ is bool:
        return {"type": "boolean"}
    if typ is type(None):
        return {"type": "null"}
    if typ is Any:
        return {}

    if isinstance(typ, type) and issubclass(typ, enum.Enum):
        if issubclass(typ, enum.IntEnum):
            return {"type": "integer", "enum": [member.value for member in typ]}
        return {"type": "string", "enum": [member.value for member in typ]}

    if isinstance(typ, type) and is_dataclass(typ):
        return _dataclass_schema(typ)

    return {}


def types_union() -> Any:
    import types

    return types.UnionType


def _dataclass_schema(cls: type) -> dict[str, Any]:
    """Object schema for a dataclass: ``additionalProperties=false``."""
    hints = get_type_hints(cls)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for field in fields(cls):
        name = field.name
        required.append(name)
        fragment = _type_schema(hints[name])
        if name in _PINNED_ENUM_OVERRIDES:
            fragment = _PINNED_ENUM_OVERRIDES[name]
        properties[name] = fragment
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }

#: Registry of schemas by result/request type name (public, §20).
SCHEMAS: dict[str, dict[str, Any]] = {
    "VargaConfig": _dataclass_schema(VargaConfig),
    "VargaDefinition": _dataclass_schema(VargaDefinition),
    "VargaCalculationMethod": _dataclass_schema(VargaCalculationMethod),
    "VargaPosition": _dataclass_schema(VargaPosition),
    "VargaChart": _dataclass_schema(VargaChart),
    "VargaProvenance": _dataclass_schema(VargaProvenance),
    "SourceCitation": _dataclass_schema(SourceCitation),
    "ModalityStartParams": _dataclass_schema(ModalityStartParams),
    "RelativeModalityParams": _dataclass_schema(RelativeModalityParams),
    "OddEvenStartParams": _dataclass_schema(OddEvenStartParams),
    "ExplicitTableParams": _dataclass_schema(ExplicitTableParams),
    "IntervalEntry": _dataclass_schema(IntervalEntry),
    "FixedStartParams": _dataclass_schema(FixedStartParams),
}


def schema_for(name: str) -> dict[str, Any]:
    """Return the JSON Schema (draft 2020-12 shape) for a named model."""
    try:
        return SCHEMAS[name]
    except KeyError as exc:
        raise InvalidVargaRequestError(f"unknown schema name {name!r}") from exc


def validate_schema(payload: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Recursively validate ``payload`` against a JSON-Schema dict."""
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                validate_schema(payload, branch, path)
                return
            except InvalidVargaRequestError:
                continue
        raise InvalidVargaRequestError(f"{path}: no anyOf branch matched {payload!r}")

    type_spec = schema.get("type", "any")
    allowed = [type_spec] if isinstance(type_spec, str) else list(type_spec)

    if "enum" in schema:
        if payload not in schema["enum"]:
            raise InvalidVargaRequestError(
                f"{path}: value {payload!r} not in enum {schema['enum']}"
            )
        return

    if "pattern" in schema and isinstance(payload, str) and not re.match(
        schema["pattern"], payload
    ):
        raise InvalidVargaRequestError(
            f"{path}: {payload!r} does not match {schema['pattern']}"
        )

    if "null" in allowed and payload is None:
        return

    if "object" in allowed:
        if not isinstance(payload, dict):
            raise InvalidVargaRequestError(f"{path}: expected object, got {payload!r}")
        extra = set(payload) - set(schema.get("properties", {}))
        if schema.get("additionalProperties") is False and extra:
            raise InvalidVargaRequestError(
                f"{path}: additional properties not allowed: {sorted(extra)}"
            )
        for key in schema.get("required", []):
            if key not in payload:
                raise InvalidVargaRequestError(f"{path}: missing required property {key!r}")
        for key, value in payload.items():
            if key in schema.get("properties", {}):
                validate_schema(value, schema["properties"][key], f"{path}.{key}")
        return

    if "array" in allowed:
        if not isinstance(payload, list):
            raise InvalidVargaRequestError(f"{path}: expected array, got {payload!r}")
        items = schema.get("items", {})
        for index, item in enumerate(payload):
            validate_schema(item, items, f"{path}[{index}]")
        return

    if "string" in allowed:
        if not isinstance(payload, str):
            raise InvalidVargaRequestError(f"{path}: expected string, got {payload!r}")
        return
    if "number" in allowed:
        if not isinstance(payload, (int, float)) or isinstance(payload, bool):
            raise InvalidVargaRequestError(f"{path}: expected number, got {payload!r}")
        return
    if "integer" in allowed:
        if not isinstance(payload, int) or isinstance(payload, bool):
            raise InvalidVargaRequestError(f"{path}: expected integer, got {payload!r}")
        return
    if "boolean" in allowed:
        if not isinstance(payload, bool):
            raise InvalidVargaRequestError(f"{path}: expected boolean, got {payload!r}")
        return
    if "null" in allowed:
        raise InvalidVargaRequestError(f"{path}: expected null, got {payload!r}")


# --------------------------------------------------------------------------- #
# Request parsing (validated construction — same rules as the service)
# --------------------------------------------------------------------------- #


def _parse_bodies(raw: Any) -> tuple[BodyId, ...]:
    if not isinstance(raw, (list, tuple)) or not raw:
        raise InvalidVargaRequestError(f"bodies must be a non-empty array, got {raw!r}")
    parsed: list[BodyId] = []
    for item in raw:
        if isinstance(item, BodyId):
            parsed.append(item)
        elif isinstance(item, str):
            try:
                parsed.append(BodyId(item))
            except ValueError as exc:
                raise InvalidVargaRequestError(f"unknown body value {item!r}") from exc
        else:
            raise InvalidVargaRequestError(f"bodies must be BodyId strings, got {item!r}")
    return tuple(parsed)


def varga_request_from_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Validate/normalize a Varga computation request dict into the
    arguments accepted by ``VargaService.compute_varga_chart``.

    ``states`` must be actual JRE-003 ``PlanetState`` objects (the service
    consumes public facts; JRE-008 never reconstructs states from dicts —
    ``PlanetState`` has no public ``from_dict`` on the JRE-003 root).

    Returns ``{"states": tuple[PlanetState, ...], "varga_id": str,
    "method_id": str | None, "context_chart_identity": str | None}``.
    """
    states_raw = data.get("states")
    if not isinstance(states_raw, (list, tuple)) or not states_raw:
        raise InvalidVargaRequestError(f"states must be a non-empty array, got {states_raw!r}")
    states: list[PlanetState] = []
    for item in states_raw:
        if not isinstance(item, PlanetState):
            raise InvalidVargaRequestError(
                f"states must contain PlanetState objects, got {type(item).__name__}"
            )
        states.append(item)
    varga_id = data.get("varga_id")
    if not isinstance(varga_id, str) or varga_id == "":
        raise InvalidVargaRequestError(f"varga_id must be a non-empty string, got {varga_id!r}")
    method_id = data.get("method_id")
    if method_id is not None and (not isinstance(method_id, str) or method_id == ""):
        raise InvalidVargaRequestError(
            f"method_id must be a string or null, got {method_id!r}"
        )
    context_id = data.get("context_chart_identity")
    if context_id is not None and (not isinstance(context_id, str) or context_id == ""):
        raise InvalidVargaRequestError(
            f"context_chart_identity must be a string or null, got {context_id!r}"
        )
    return {
        "states": tuple(states),
        "varga_id": varga_id,
        "method_id": method_id,
        "context_chart_identity": context_id,
    }

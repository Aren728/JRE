"""JSON serialization for the JRE-006 gochar layer (SPEC §21, DC §6-§8).

Conventions: snake_case keys; enums as their string values (``Pada`` as
its int); tuples as arrays; ``None`` as ``null``; floats via Python's
round-trip repr (``-0.0 -> 0.0``). JSON Schema (draft 2020-12) is
generated from the model dataclasses with ``additionalProperties=false``
at every object level, enums constrained to the pinned string sets, and
ISO-8601 UTC microsecond patterns on timestamp fields. Input parsers
validate on construction with the typed error taxonomy (SPEC §7).
"""

from __future__ import annotations

import enum
import json
import re
import typing
from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints

import jyotish
from jyotish import BirthData, BodyId, HouseSystem

from .derive import civil_split
from .errors import InvalidGocharConfigError, InvalidGocharRequestError
from .models import (
    GocharConfig,
    GocharInstantRequest,
    GocharInstantResult,
    GocharIntervalRequest,
    GocharIntervalResult,
    GocharNatalRequest,
    GocharNatalResult,
    GocharProvenance,
    to_dict_value,
)

#: Fields whose value is an ISO-8601 UTC instant (SPEC §18) — constrained
#: to the microsecond ``Z`` form (``jd_to_iso_utc`` output).
_ISO_UTC_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{6})?Z$"

_TIMESTAMP_FIELDS = frozenset(
    {
        "instant_utc_iso",
        "start_utc_iso",
        "end_utc_iso",
        "event_utc_iso",
        "timestamp_utc_iso",
        "transit_instant_utc_iso",
    }
)


# --------------------------------------------------------------------------- #
# Result serialization
# --------------------------------------------------------------------------- #


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-006 result object to a dict (deterministic key
    order = dataclass declaration order; SPEC §21)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-006 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


# --------------------------------------------------------------------------- #
# Config parsing (SPEC §21/§22)
# --------------------------------------------------------------------------- #


def config_from_dict(data: dict[str, Any]) -> GocharConfig:
    """Deserialize a ``GocharConfig`` from a JSON-shaped dict (missing key →
    field default; unknown enum values → ``InvalidGocharConfigError``)."""
    return GocharConfig.from_dict(data)


# --------------------------------------------------------------------------- #
# Request parsing (DC §5/§8 — same validation as construction)
# --------------------------------------------------------------------------- #


def _parse_bodies(raw: Any) -> tuple[BodyId, ...]:
    if not isinstance(raw, (list, tuple)) or not raw:
        raise InvalidGocharRequestError(f"bodies must be a non-empty array, got {raw!r}")
    parsed: list[BodyId] = []
    for item in raw:
        if isinstance(item, BodyId):
            parsed.append(item)
        elif isinstance(item, str):
            try:
                parsed.append(BodyId(item))
            except ValueError as exc:
                raise InvalidGocharRequestError(f"unknown body value {item!r}") from exc
        else:
            raise InvalidGocharRequestError(f"bodies must be BodyId strings, got {item!r}")
    return tuple(parsed)


def _parse_config(raw: Any) -> GocharConfig | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise InvalidGocharConfigError(f"config must be an object, got {raw!r}")
    return GocharConfig.from_dict(raw)


def instant_request_from_dict(data: dict[str, Any]) -> GocharInstantRequest:
    """Validate/normalize a GENERIC instant request dict (DC §5)."""
    instant = data.get("instant_utc_iso")
    if not isinstance(instant, str):
        raise InvalidGocharRequestError(
            f"instant_utc_iso must be a string, got {instant!r}"
        )
    civil_split(instant)  # validates ISO-UTC + time component (SPEC §8)
    bodies = _parse_bodies(data.get("bodies"))
    return GocharInstantRequest(
        instant_utc_iso=instant, bodies=bodies, config=_parse_config(data.get("config"))
    )


def natal_request_from_dict(data: dict[str, Any]) -> GocharNatalRequest:
    """Validate/normalize an INDIVIDUAL instant request dict (DC §5)."""
    instant = data.get("instant_utc_iso")
    if not isinstance(instant, str):
        raise InvalidGocharRequestError(f"instant_utc_iso must be a string, got {instant!r}")
    civil_split(instant)
    birth_raw = data.get("birth")
    if not isinstance(birth_raw, dict):
        raise InvalidGocharRequestError(f"birth must be an object, got {birth_raw!r}")
    birth = jyotish.birth_from_dict(birth_raw)
    bodies = _parse_bodies(data.get("bodies"))
    reference = data.get("reference_point")
    if reference is not None and not isinstance(reference, str):
        raise InvalidGocharRequestError(
            f"reference_point must be a string, got {reference!r}"
        )
    return GocharNatalRequest(
        birth=birth,
        instant_utc_iso=instant,
        bodies=bodies,
        reference_point=reference,
        config=_parse_config(data.get("config")),
    )


def interval_request_from_dict(data: dict[str, Any]) -> GocharIntervalRequest:
    """Validate/normalize an interval request dict (DC §5)."""
    start = data.get("start_utc_iso")
    end = data.get("end_utc_iso")
    if not isinstance(start, str) or not isinstance(end, str):
        raise InvalidGocharRequestError(
            f"start_utc_iso/end_utc_iso must be strings, got {start!r} / {end!r}"
        )
    civil_split(start)
    civil_split(end)
    bodies = _parse_bodies(data.get("bodies"))
    natal_raw = data.get("natal_anchor")
    natal_anchor: BirthData | None = None
    if natal_raw is not None:
        if not isinstance(natal_raw, dict):
            raise InvalidGocharRequestError(
                f"natal_anchor must be an object, got {natal_raw!r}"
            )
        natal_anchor = jyotish.birth_from_dict(natal_raw)
    return GocharIntervalRequest(
        start_utc_iso=start,
        end_utc_iso=end,
        bodies=bodies,
        natal_anchor=natal_anchor,
        config=_parse_config(data.get("config")),
    )


# --------------------------------------------------------------------------- #
# JSON Schema (DC §6) — generated from the model dataclasses
# --------------------------------------------------------------------------- #


def _type_schema(typ: Any) -> dict[str, Any]:
    """Build a JSON-Schema fragment for a type annotation."""
    origin = get_origin(typ)
    args = get_args(typ)

    # Optional / union: null combined with the members.
    if origin is typing.Union or origin is types_union():
        non_null = [arg for arg in args if arg is not type(None)]
        if len(non_null) == 1:
            inner = _type_schema(non_null[0])
            inner = dict(inner)
            current = inner.get("type")
            if isinstance(current, str):
                inner["type"] = [current, "null"]
            elif isinstance(current, list):
                inner["type"] = [*current, "null"]
            else:
                inner["anyOf"] = [{"type": "null"}]
            return inner
        return {"anyOf": [_type_schema(arg) for arg in non_null]}

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


#: Pinned string-set constraints for ``GocharConfig`` fields that are typed
#: ``str`` in the model but constrained by SPEC §5 (DC §6: "enums constrained
#: to the pinned string sets").
_PINNED_ENUM_OVERRIDES: dict[str, dict[str, Any]] = {
    "reference_point": {
        "type": "string",
        "enum": ["LAGNA", "MOON", "SUN", "ASC"],
    },
    "house_system": {
        "type": "string",
        "enum": [member.value for member in HouseSystem],
    },
}


def _dataclass_schema(cls: type) -> dict[str, Any]:
    """Object schema for a dataclass: ``additionalProperties=false``,
    required = all fields, per-field fragments (DC §6)."""
    hints = get_type_hints(cls)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for field in fields(cls):
        name = field.name
        required.append(name)
        fragment = _type_schema(hints[name])
        if name in _TIMESTAMP_FIELDS:
            fragment = dict(fragment)
            fragment["pattern"] = _ISO_UTC_PATTERN
        if name in _PINNED_ENUM_OVERRIDES:
            fragment = _PINNED_ENUM_OVERRIDES[name]
        properties[name] = fragment
    return {
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
    }


#: Registry of schemas by result/request type name (public, DC §6).
SCHEMAS: dict[str, dict[str, Any]] = {
    "GocharConfig": _dataclass_schema(GocharConfig),
    "GocharProvenance": _dataclass_schema(GocharProvenance),
    "GocharInstantResult": _dataclass_schema(GocharInstantResult),
    "GocharNatalResult": _dataclass_schema(GocharNatalResult),
    "GocharIntervalResult": _dataclass_schema(GocharIntervalResult),
    "GocharInstantRequest": _dataclass_schema(GocharInstantRequest),
    "GocharNatalRequest": _dataclass_schema(GocharNatalRequest),
    "GocharIntervalRequest": _dataclass_schema(GocharIntervalRequest),
}


def schema_for(name: str) -> dict[str, Any]:
    """Return the JSON Schema (draft 2020-12 shape) for a named model."""
    try:
        return SCHEMAS[name]
    except KeyError as exc:
        raise InvalidGocharRequestError(f"unknown schema name {name!r}") from exc


def validate_schema(payload: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Recursively validate ``payload`` against a JSON-Schema dict; raises
    ``InvalidGocharRequestError`` on the first mismatch. Supports ``type``
    (string/number/integer/boolean/object/array/null or lists), ``enum``,
    ``pattern``, ``required``, ``properties``, ``additionalProperties``,
    ``items``, and ``anyOf``."""
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                validate_schema(payload, branch, path)
                return
            except InvalidGocharRequestError:
                continue
        raise InvalidGocharRequestError(f"{path}: no anyOf branch matched {payload!r}")

    type_spec = schema.get("type", "any")
    allowed = [type_spec] if isinstance(type_spec, str) else list(type_spec)

    if "enum" in schema:
        if payload not in schema["enum"]:
            raise InvalidGocharRequestError(
                f"{path}: value {payload!r} not in enum {schema['enum']}"
            )
        return

    if "pattern" in schema and isinstance(payload, str) and not re.match(
        schema["pattern"], payload
    ):
        raise InvalidGocharRequestError(
            f"{path}: {payload!r} does not match {schema['pattern']}"
        )

    if "null" in allowed and payload is None:
        return

    if "object" in allowed:
        if not isinstance(payload, dict):
            raise InvalidGocharRequestError(f"{path}: expected object, got {payload!r}")
        extra = set(payload) - set(schema.get("properties", {}))
        if schema.get("additionalProperties") is False and extra:
            raise InvalidGocharRequestError(
                f"{path}: additional properties not allowed: {sorted(extra)}"
            )
        for key in schema.get("required", []):
            if key not in payload:
                raise InvalidGocharRequestError(f"{path}: missing required property {key!r}")
        for key, value in payload.items():
            if key in schema.get("properties", {}):
                validate_schema(value, schema["properties"][key], f"{path}.{key}")
        return

    if "array" in allowed:
        if not isinstance(payload, list):
            raise InvalidGocharRequestError(f"{path}: expected array, got {payload!r}")
        items = schema.get("items", {})
        for index, item in enumerate(payload):
            validate_schema(item, items, f"{path}[{index}]")
        return

    if "string" in allowed:
        if not isinstance(payload, str):
            raise InvalidGocharRequestError(f"{path}: expected string, got {payload!r}")
        return
    if "number" in allowed:
        if not isinstance(payload, (int, float)) or isinstance(payload, bool):
            raise InvalidGocharRequestError(f"{path}: expected number, got {payload!r}")
        return
    if "integer" in allowed:
        if not isinstance(payload, int) or isinstance(payload, bool):
            raise InvalidGocharRequestError(f"{path}: expected integer, got {payload!r}")
        return
    if "boolean" in allowed:
        if not isinstance(payload, bool):
            raise InvalidGocharRequestError(f"{path}: expected boolean, got {payload!r}")
        return
    if "null" in allowed:
        raise InvalidGocharRequestError(f"{path}: expected null, got {payload!r}")

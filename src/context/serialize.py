"""JSON serialization for the JRE-007 canonical-context layer (SPEC §21,
DC §6-§8).
"""

from __future__ import annotations

import enum
import json
import re
import typing
from collections.abc import Callable
from dataclasses import fields, is_dataclass
from typing import Any, get_args, get_origin, get_type_hints

import jyotish
from jyotish import HouseSystem

from .derive import civil_split
from .errors import InvalidContextConfigError, InvalidContextRequestError
from .models import (
    CAPABILITY_IDS,
    CAPABILITY_VERSION,
    TIME_PRECISION_VALUES,
    CanonicalContext,
    CanonicalFactSnapshot,
    CapabilityDescriptor,
    ContextConfig,
    ContextEclipseRequest,
    ContextInstantRequest,
    ContextIntervalRequest,
    ContextNatalRequest,
    ContextRequest,
    FactEnvelope,
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
    }
)


# --------------------------------------------------------------------------- #
# Result serialization
# --------------------------------------------------------------------------- #


def result_to_dict(result: Any) -> Any:
    """Serialize any JRE-007 result object to a dict (deterministic key
    order = dataclass declaration order; SPEC §21)."""
    return to_dict_value(result)


def result_to_json(result: Any) -> str:
    """Serialize a JRE-007 result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


# --------------------------------------------------------------------------- #
# Config parsing (SPEC §21/§22)
# --------------------------------------------------------------------------- #


def config_from_dict(data: dict[str, Any]) -> ContextConfig:
    """Deserialize a ``ContextConfig`` from a JSON-shaped dict."""
    return ContextConfig.from_dict(data)


# --------------------------------------------------------------------------- #
# Request parsing (DC §5/§8 — same validation as construction)
# --------------------------------------------------------------------------- #


def _parse_bodies(raw: Any) -> tuple[Any, ...]:
    from jyotish import BodyId

    if not isinstance(raw, (list, tuple)) or not raw:
        raise InvalidContextRequestError(f"bodies must be a non-empty array, got {raw!r}")
    parsed: list[BodyId] = []
    for item in raw:
        if isinstance(item, BodyId):
            parsed.append(item)
        elif isinstance(item, str):
            try:
                parsed.append(BodyId(item))
            except ValueError as exc:
                raise InvalidContextRequestError(f"unknown body value {item!r}") from exc
        else:
            raise InvalidContextRequestError(f"bodies must be BodyId strings, got {item!r}")
    return tuple(parsed)


def _parse_config(raw: Any) -> ContextConfig | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise InvalidContextConfigError(f"config must be an object, got {raw!r}")
    return ContextConfig.from_dict(raw)


def _request_capability(data: dict[str, Any], kind: str) -> str:
    """The frozen capability id for a request dict: the kind's own id, or an
    explicit matching value (a mismatched id is a contract violation)."""
    raw = data.get("capability", kind)
    if raw != kind:
        raise InvalidContextRequestError(
            f"capability {raw!r} does not match the {kind} request model"
        )
    return kind


def _request_capability_version(data: dict[str, Any]) -> str:
    """The requested minimum capability version (defaults to the V1 pin)."""
    raw = data.get("capability_version", CAPABILITY_VERSION)
    if not isinstance(raw, str) or raw == "":
        raise InvalidContextRequestError(
            f"capability_version must be a non-empty string, got {raw!r}"
        )
    return raw


def _request_analysis_id(data: dict[str, Any]) -> str | None:
    """The optional request correlation id."""
    raw = data.get("analysis_request_id")
    if raw is not None and not isinstance(raw, str):
        raise InvalidContextRequestError(
            f"analysis_request_id must be a string or null, got {raw!r}"
        )
    return raw


def instant_request_from_dict(data: dict[str, Any]) -> ContextInstantRequest:
    """Validate/normalize a GENERIC instant snapshot request dict (DC §5)."""
    instant = data.get("instant_utc_iso")
    if not isinstance(instant, str):
        raise InvalidContextRequestError(
            f"instant_utc_iso must be a string, got {instant!r}"
        )
    civil_split(instant)  # validates ISO-UTC + time component (SPEC §8)
    bodies = _parse_bodies(data.get("bodies"))
    return ContextInstantRequest(
        instant_utc_iso=instant,
        bodies=bodies,
        config=_parse_config(data.get("config")),
        capability=_request_capability(data, "instant"),
        capability_version=_request_capability_version(data),
        analysis_request_id=_request_analysis_id(data),
    )


def natal_request_from_dict(data: dict[str, Any]) -> ContextNatalRequest:
    """Validate/normalize an INDIVIDUAL natal snapshot request dict (DC §5)."""
    birth_raw = data.get("birth")
    if not isinstance(birth_raw, dict):
        raise InvalidContextRequestError(f"birth must be an object, got {birth_raw!r}")
    birth = jyotish.birth_from_dict(birth_raw)
    include_house_analysis = data.get("include_house_analysis", True)
    if not isinstance(include_house_analysis, bool):
        raise InvalidContextRequestError(
            f"include_house_analysis must be a boolean, got {include_house_analysis!r}"
        )
    time_precision = data.get("time_precision")
    if time_precision is not None and not isinstance(time_precision, str):
        raise InvalidContextRequestError(
            f"time_precision must be a string, got {time_precision!r}"
        )
    return ContextNatalRequest(
        birth=birth,
        config=_parse_config(data.get("config")),
        include_house_analysis=include_house_analysis,
        time_precision=time_precision,
        capability=_request_capability(data, "natal"),
        capability_version=_request_capability_version(data),
        analysis_request_id=_request_analysis_id(data),
    )


def interval_request_from_dict(data: dict[str, Any]) -> ContextIntervalRequest:
    """Validate/normalize an interval snapshot request dict (DC §5)."""
    start = data.get("start_utc_iso")
    end = data.get("end_utc_iso")
    if not isinstance(start, str) or not isinstance(end, str):
        raise InvalidContextRequestError(
            f"start_utc_iso/end_utc_iso must be strings, got {start!r} / {end!r}"
        )
    civil_split(start)
    civil_split(end)
    bodies = _parse_bodies(data.get("bodies"))
    return ContextIntervalRequest(
        start_utc_iso=start,
        end_utc_iso=end,
        bodies=bodies,
        config=_parse_config(data.get("config")),
        capability=_request_capability(data, "interval"),
        capability_version=_request_capability_version(data),
        analysis_request_id=_request_analysis_id(data),
    )


def eclipse_request_from_dict(data: dict[str, Any]) -> ContextEclipseRequest:
    """Validate/normalize an eclipse snapshot request dict (DC §5)."""
    start = data.get("start_utc_iso")
    end = data.get("end_utc_iso")
    if not isinstance(start, str) or not isinstance(end, str):
        raise InvalidContextRequestError(
            f"start_utc_iso/end_utc_iso must be strings, got {start!r} / {end!r}"
        )
    civil_split(start)
    civil_split(end)
    kind_raw = data.get("kind")
    kind = None
    if kind_raw is not None:
        if not isinstance(kind_raw, str):
            raise InvalidContextRequestError(f"kind must be a string, got {kind_raw!r}")
        try:
            kind = jyotish.EclipseKind(kind_raw)
        except ValueError as exc:
            raise InvalidContextRequestError(f"unknown eclipse kind {kind_raw!r}") from exc
    return ContextEclipseRequest(
        start_utc_iso=start,
        end_utc_iso=end,
        kind=kind,
        config=_parse_config(data.get("config")),
        capability=_request_capability(data, "eclipse"),
        capability_version=_request_capability_version(data),
        analysis_request_id=_request_analysis_id(data),
    )


def context_request_from_dict(data: dict[str, Any]) -> ContextRequest:
    """Validate/normalize a canonical request dict (DC §5): a frozen V1
    capability id plus that capability's own inputs. The capability-specific
    parsers remain as compatibility wrappers over this canonical boundary."""
    capability = data.get("capability")
    if not isinstance(capability, str) or capability not in CAPABILITY_IDS:
        raise InvalidContextRequestError(
            f"capability must be one of {CAPABILITY_IDS}, got {capability!r}"
        )
    _request_capability_version(data)  # validates the version shape
    parser = _CAPABILITY_PARSERS[capability]
    return parser(data)


_CAPABILITY_PARSERS: dict[str, Callable[[dict[str, Any]], ContextRequest]] = {
    "instant": instant_request_from_dict,
    "natal": natal_request_from_dict,
    "interval": interval_request_from_dict,
    "eclipse": eclipse_request_from_dict,
}


# --------------------------------------------------------------------------- #
# JSON Schema (DC §6) — generated from the model dataclasses
# --------------------------------------------------------------------------- #


def _type_schema(typ: Any) -> dict[str, Any]:
    """Build a JSON-Schema fragment for a type annotation."""
    origin = get_origin(typ)
    args = get_args(typ)

    if origin is typing.Union or origin is types_union():
        has_null = any(arg is type(None) for arg in args)
        non_null = [arg for arg in args if arg is not type(None)]
        if len(non_null) == 1:
            inner = _type_schema(non_null[0])
            inner = dict(inner)
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


_PINNED_ENUM_OVERRIDES: dict[str, dict[str, Any]] = {
    "default_time_precision": {
        "type": "string",
        "enum": list(TIME_PRECISION_VALUES),
    },
    "house_system": {
        "type": "string",
        "enum": [member.value for member in HouseSystem],
    },
}


def _dataclass_schema(cls: type) -> dict[str, Any]:
    """Object schema for a dataclass: ``additionalProperties=false``."""
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
    "ContextConfig": _dataclass_schema(ContextConfig),
    "CanonicalFactSnapshot": _dataclass_schema(CanonicalFactSnapshot),
    "CanonicalContext": _dataclass_schema(CanonicalContext),
    "FactEnvelope": _dataclass_schema(FactEnvelope),
    "CapabilityDescriptor": _dataclass_schema(CapabilityDescriptor),
    "ContextRequest": _dataclass_schema(ContextRequest),
    "ContextInstantRequest": _dataclass_schema(ContextInstantRequest),
    "ContextNatalRequest": _dataclass_schema(ContextNatalRequest),
    "ContextIntervalRequest": _dataclass_schema(ContextIntervalRequest),
    "ContextEclipseRequest": _dataclass_schema(ContextEclipseRequest),
}


def schema_for(name: str) -> dict[str, Any]:
    """Return the JSON Schema (draft 2020-12 shape) for a named model."""
    try:
        return SCHEMAS[name]
    except KeyError as exc:
        raise InvalidContextRequestError(f"unknown schema name {name!r}") from exc


def validate_schema(payload: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Recursively validate ``payload`` against a JSON-Schema dict."""
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                validate_schema(payload, branch, path)
                return
            except InvalidContextRequestError:
                continue
        raise InvalidContextRequestError(f"{path}: no anyOf branch matched {payload!r}")

    type_spec = schema.get("type", "any")
    allowed = [type_spec] if isinstance(type_spec, str) else list(type_spec)

    if "enum" in schema:
        if payload not in schema["enum"]:
            raise InvalidContextRequestError(
                f"{path}: value {payload!r} not in enum {schema['enum']}"
            )
        return

    if "pattern" in schema and isinstance(payload, str) and not re.match(
        schema["pattern"], payload
    ):
        raise InvalidContextRequestError(
            f"{path}: {payload!r} does not match {schema['pattern']}"
        )

    if "null" in allowed and payload is None:
        return

    if "object" in allowed:
        if not isinstance(payload, dict):
            raise InvalidContextRequestError(f"{path}: expected object, got {payload!r}")
        extra = set(payload) - set(schema.get("properties", {}))
        if schema.get("additionalProperties") is False and extra:
            raise InvalidContextRequestError(
                f"{path}: additional properties not allowed: {sorted(extra)}"
            )
        for key in schema.get("required", []):
            if key not in payload:
                raise InvalidContextRequestError(f"{path}: missing required property {key!r}")
        for key, value in payload.items():
            if key in schema.get("properties", {}):
                validate_schema(value, schema["properties"][key], f"{path}.{key}")
        return

    if "array" in allowed:
        if not isinstance(payload, list):
            raise InvalidContextRequestError(f"{path}: expected array, got {payload!r}")
        items = schema.get("items", {})
        for index, item in enumerate(payload):
            validate_schema(item, items, f"{path}[{index}]")
        return

    if "string" in allowed:
        if not isinstance(payload, str):
            raise InvalidContextRequestError(f"{path}: expected string, got {payload!r}")
        return
    if "number" in allowed:
        if not isinstance(payload, (int, float)) or isinstance(payload, bool):
            raise InvalidContextRequestError(f"{path}: expected number, got {payload!r}")
        return
    if "integer" in allowed:
        if not isinstance(payload, int) or isinstance(payload, bool):
            raise InvalidContextRequestError(f"{path}: expected integer, got {payload!r}")
        return
    if "boolean" in allowed:
        if not isinstance(payload, bool):
            raise InvalidContextRequestError(f"{path}: expected boolean, got {payload!r}")
        return
    if "null" in allowed:
        raise InvalidContextRequestError(f"{path}: expected null, got {payload!r}")

# JRE-002 — Astronomical Core: Data Contract

- Status: SPECIALIZED
- Version: 0.3.0
- Date: 2026-08-11
- Upstream: [Specialist Spec §5–§6, §32](JRE-002-SPECIALIST-SPEC.md)

This document is the **exact field-level contract**. `models.py` implements it
verbatim. Consumers (Gochar engine, Kundali engine) and QA test against it.

## 0. Conventions

- All models are `@dataclass(frozen=True)` (hashable, immutable).
- Enums are `str`-based; JSON value = enum string value.
- Tuples serialize as JSON arrays; `None` as `null`.
- Floats: IEEE-754 doubles, serialized with Python's round-trip repr — the
  JSON number decodes to the identical double.
- All angles in degrees; distances in AU; speeds in deg/day or AU/day.
- Longitude normalization: `[0, 360)`; `-0.0 → 0.0`.

## 1. Enums (string values are the JSON values)

| Enum | Values |
|---|---|
| `BodyId` | `SUN`, `MOON`, `MARS`, `MERCURY`, `JUPITER`, `VENUS`, `SATURN`, `RAHU`, `KETU` |
| `RetrogradeState` | `DIRECT`, `RETROGRADE`, `STATIONARY` |
| `Ayanamsa` | `LAHIRI`, `RAMAN`, `FAGAN_BRADLEY` |
| `EphemerisMode` | `SWIEPH`, `MOSEPH` |
| `PositionType` | `APPARENT`, `TRUE` |
| `NodeType` | `MEAN`, `TRUE` |

## 2. `CalculationConfig` (frozen dataclass)

| Field | Type | Default | Constraint / semantics |
|---|---|---|---|
| `ayanamsa` | `Ayanamsa \| None` | `Ayanamsa.LAHIRI` | `None` ⇒ tropical only |
| `ayanamsa_override` | `tuple[float, float] \| None` | `None` | optional `(t0, ayanamsa_t0)` for `swe.set_sid_mode`; `None` ⇒ `(0.0, 0.0)` (library built-in) |
| `ephemeris_mode` | `EphemerisMode` | `SWIEPH` | requested mode; actual mode echoed in `ProviderRun` |
| `position_type` | `PositionType` | `APPARENT` | `TRUE` adds `SEFLG_TRUEPOS` |
| `node_type` | `NodeType` | `MEAN` | Rahu/Ketu node source |
| `ephemeris_path` | `str \| None` | `None` | resolved to `datasets/ephemeris` |
| `allow_fallback` | `bool` | `True` | SWIEPH→MOSEPH fallback allowed |

JSON shape:

```json
{
  "ayanamsa": "LAHIRI",
  "ayanamsa_override": null,
  "ephemeris_mode": "SWIEPH",
  "position_type": "APPARENT",
  "node_type": "MEAN",
  "ephemeris_path": null,
  "allow_fallback": true
}
```

## 3. `BodyPosition` (frozen dataclass) — per-body raw output

| Field | Type | Semantics |
|---|---|---|
| `body` | `BodyId` | which body |
| `longitude_tropical` | `float` | deg, `[0, 360)`, ecliptic-of-date, geocentric |
| `longitude_sidereal` | `float \| None` | deg, `[0, 360)`; `None` iff `ayanamsa is None` |
| `latitude` | `float` | deg, `[-90, 90]`; `+` = north of ecliptic |
| `distance_au` | `float` | AU |
| `speed_longitude` | `float` | deg/day |
| `speed_latitude` | `float` | deg/day |
| `speed_distance` | `float` | AU/day |
| `retrograde` | `RetrogradeState` | from `speed_longitude` sign vs `ε` (default `1e-9` deg/day) |
| `position_type` | `PositionType` | as computed |
| `ayanamsa_value` | `float \| None` | deg, ayanamsa applied; `None` iff `ayanamsa is None` |

## 4. `ProviderMetadata` (frozen dataclass) — provider-stable

| Field | Type | Example |
|---|---|---|
| `provider_id` | `str` | `"swisseph.pysweph"` |
| `library_name` | `str` | `"pysweph"` |
| `library_version` | `str` | `"2.10.3.6"` |
| `ephemeris_version` | `str` | `"18"` |

## 5. `ProviderRun` (frozen dataclass) — per-call provider outcome

| Field | Type | Semantics |
|---|---|---|
| `positions` | `tuple[BodyPosition, ...]` | canonical `BodyId` order |
| `ephemeris_mode` | `EphemerisMode` | **actual** mode used (SWIEPH or fallback MOSEPH) |
| `ephemeris_files` | `tuple[str, ...]` | files used; `()` for MOSEPH |

## 6. `EphemerisResult` (frozen dataclass) — service envelope

| Field | Type | Semantics |
|---|---|---|
| `request_snapshot` | `EphemerisRequest` | exact echo of the validated input |
| `timestamp_utc_iso` | `str` | ISO 8601 `Z`, the instant computed |
| `timestamp_local_iso` | `str` | ISO 8601 with numeric offset |
| `julian_day_ut` | `float` | exact JD (UT) used for calculation |
| `positions` | `tuple[BodyPosition, ...]` | all requested bodies, canonical order |
| `provider` | `ProviderMetadata` | provider-stable metadata |
| `provider_run` | `ProviderRun` | per-call mode/files |
| `config` | `CalculationConfig` | config actually applied |

> Note: `EphemerisResult` includes `provider_run` (per-call mode/files) in
> addition to `provider` (stable metadata). This resolves the request's
> "Ephemeris provider" output into its stable + per-call parts.

## 7. `EphemerisRequest` (frozen dataclass) — input

| Field | Type | Constraint |
|---|---|---|
| `date` | `datetime.date` | civil local date |
| `time` | `datetime.time` | civil local time; ≥ 1 s precision, sub-second preserved exactly |
| `timezone` | `str` | IANA zone name (reject abbreviations) |
| `latitude` | `float` | `[-90, 90]`, finite |
| `longitude` | `float` | `[-180, 180]`, finite |
| `bodies` | `tuple[BodyId, ...] \| None` | `None` ⇒ all nine, canonical order |
| `config` | `CalculationConfig` | overridable defaults |
| `provider_id` | `str \| None` | registry key; `None` ⇒ default provider |

JSON shape (used by `request_from_dict`):

```json
{
  "date": "1990-06-15",
  "time": "10:00:00",
  "timezone": "Asia/Kolkata",
  "latitude": 28.6139,
  "longitude": 77.2090,
  "bodies": null,
  "config": { "ayanamsa": "LAHIRI", "ephemeris_mode": "SWIEPH" },
  "provider_id": null
}
```

Validation rules (all raised at the service boundary, before any provider call):

| Input | Rule | Error |
|---|---|---|
| timezone | resolves in IANA DB; not an abbreviation | `InvalidTimestampError` |
| local time | must exist (DST gap ⇒ error) | `InvalidTimestampError` |
| ambiguous time | resolved `fold=0` (never an error) | — |
| latitude | `-90 ≤ lat ≤ 90`, finite | `InvalidCoordinatesError` |
| longitude | `-180 ≤ lon ≤ 180`, finite | `InvalidCoordinatesError` |
| date | ≥ 1582-10-15 (proleptic Gregorian; Julian-era dates are out of scope, Specialist Spec §9.5) | `InvalidTimestampError` |
| bodies | non-empty subset of `BodyId`; `()` rejected | `EphemerisError` (message: `"bodies must not be empty"`) |
| provider_id | registered in registry | `UnsupportedProviderError` |

> Notes: the empty tuple `bodies=()` is rejected with `EphemerisError`
> (`"bodies must not be empty"`). Dates before 1582-10-15 are rejected with
> `InvalidTimestampError` because the pure JD formula is proleptic-Gregorian
> only (Specialist Spec §9.5); Julian-era support is a deferred extension.

## 8. JSON Schema — `EphemerisResult`

The schema below is normative. Every object definition sets
`additionalProperties: false` — unknown fields are rejected, so the contract
stays strict.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EphemerisResult",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "request_snapshot", "timestamp_utc_iso", "timestamp_local_iso",
    "julian_day_ut", "positions", "provider", "provider_run", "config"
  ],
  "properties": {
    "request_snapshot": { "$ref": "#/$defs/EphemerisRequest" },
    "timestamp_utc_iso": { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d{1,6})?Z$" },
    "timestamp_local_iso": { "type": "string" },
    "julian_day_ut": { "type": "number" },
    "positions": { "type": "array", "items": { "$ref": "#/$defs/BodyPosition" } },
    "provider": { "$ref": "#/$defs/ProviderMetadata" },
    "provider_run": { "$ref": "#/$defs/ProviderRun" },
    "config": { "$ref": "#/$defs/CalculationConfig" }
  },
  "$defs": {
    "BodyId": { "enum": ["SUN","MOON","MARS","MERCURY","JUPITER","VENUS","SATURN","RAHU","KETU"] },
    "RetrogradeState": { "enum": ["DIRECT","RETROGRADE","STATIONARY"] },
    "Ayanamsa": { "enum": ["LAHIRI","RAMAN","FAGAN_BRADLEY"] },
    "EphemerisMode": { "enum": ["SWIEPH","MOSEPH"] },
    "PositionType": { "enum": ["APPARENT","TRUE"] },
    "NodeType": { "enum": ["MEAN","TRUE"] },
    "CalculationConfig": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "ayanamsa": { "oneOf": [{ "$ref": "#/$defs/Ayanamsa" }, { "type": "null" }] },
        "ayanamsa_override": { "oneOf": [{ "type": "array", "items": { "type": "number" }, "minItems": 2, "maxItems": 2 }, { "type": "null" }] },
        "ephemeris_mode": { "$ref": "#/$defs/EphemerisMode" },
        "position_type": { "$ref": "#/$defs/PositionType" },
        "node_type": { "$ref": "#/$defs/NodeType" },
        "ephemeris_path": { "oneOf": [{ "type": "string" }, { "type": "null" }] },
        "allow_fallback": { "type": "boolean" }
      },
      "required": ["ayanamsa","ayanamsa_override","ephemeris_mode","position_type","node_type","ephemeris_path","allow_fallback"]
    },
    "BodyPosition": {
      "type": "object",
      "additionalProperties": false,
      "required": ["body","longitude_tropical","longitude_sidereal","latitude","distance_au","speed_longitude","speed_latitude","speed_distance","retrograde","position_type","ayanamsa_value"],
      "properties": {
        "body": { "$ref": "#/$defs/BodyId" },
        "longitude_tropical": { "type": "number" },
        "longitude_sidereal": { "oneOf": [{ "type": "number" }, { "type": "null" }] },
        "latitude": { "type": "number" },
        "distance_au": { "type": "number" },
        "speed_longitude": { "type": "number" },
        "speed_latitude": { "type": "number" },
        "speed_distance": { "type": "number" },
        "retrograde": { "$ref": "#/$defs/RetrogradeState" },
        "position_type": { "$ref": "#/$defs/PositionType" },
        "ayanamsa_value": { "oneOf": [{ "type": "number" }, { "type": "null" }] }
      }
    },
    "ProviderMetadata": {
      "type": "object",
      "additionalProperties": false,
      "required": ["provider_id","library_name","library_version","ephemeris_version"],
      "properties": {
        "provider_id": { "type": "string" },
        "library_name": { "type": "string" },
        "library_version": { "type": "string" },
        "ephemeris_version": { "type": "string" }
      }
    },
    "ProviderRun": {
      "type": "object",
      "additionalProperties": false,
      "required": ["positions","ephemeris_mode","ephemeris_files"],
      "properties": {
        "positions": { "type": "array", "items": { "$ref": "#/$defs/BodyPosition" } },
        "ephemeris_mode": { "$ref": "#/$defs/EphemerisMode" },
        "ephemeris_files": { "type": "array", "items": { "type": "string" } }
      }
    },
    "EphemerisRequest": {
      "type": "object",
      "additionalProperties": false,
      "required": ["date","time","timezone","latitude","longitude","bodies","config","provider_id"],
      "properties": {
        "date": { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
        "time": { "type": "string", "pattern": "^\\d{2}:\\d{2}:\\d{2}(?:\\.\\d{1,6})?$" },
        "timezone": { "type": "string" },
        "latitude": { "type": "number" },
        "longitude": { "type": "number" },
        "bodies": { "oneOf": [{ "type": "array", "items": { "$ref": "#/$defs/BodyId" } }, { "type": "null" }] },
        "config": { "$ref": "#/$defs/CalculationConfig" },
        "provider_id": { "oneOf": [{ "type": "string" }, { "type": "null" }] }
      }
    }
  }
}
```

## 9. Example payload

Request: `1990-06-15 10:00:00 Asia/Kolkata, 28.6139 N, 77.2090 E, all bodies,
Lahiri, SWIEPH`.

```json
{
  "request_snapshot": {
    "date": "1990-06-15",
    "time": "10:00:00",
    "timezone": "Asia/Kolkata",
    "latitude": 28.6139,
    "longitude": 77.209,
    "bodies": null,
    "config": {
      "ayanamsa": "LAHIRI",
      "ayanamsa_override": null,
      "ephemeris_mode": "SWIEPH",
      "position_type": "APPARENT",
      "node_type": "MEAN",
      "ephemeris_path": null,
      "allow_fallback": true
    },
    "provider_id": null
  },
  "timestamp_utc_iso": "1990-06-15T04:30:00Z",
  "timestamp_local_iso": "1990-06-15T10:00:00+05:30",
  "julian_day_ut": 2448057.6875,
  "positions": [
    {
      "body": "SUN",
      "longitude_tropical": 84.123456789,
      "longitude_sidereal": 60.123456889,
      "latitude": 0.0000123,
      "distance_au": 1.0162,
      "speed_longitude": 0.9535,
      "speed_latitude": 0.0001,
      "speed_distance": 0.0001,
      "retrograde": "DIRECT",
      "position_type": "APPARENT",
      "ayanamsa_value": 23.9999999
    }
  ],
  "provider": {
    "provider_id": "swisseph.pysweph",
    "library_name": "pysweph",
    "library_version": "2.10.3.6",
    "ephemeris_version": "18"
  },
  "provider_run": {
    "positions": [
      {
        "body": "SUN",
        "longitude_tropical": 84.123456789,
        "longitude_sidereal": 60.123456889,
        "latitude": 0.0000123,
        "distance_au": 1.0162,
        "speed_longitude": 0.9535,
        "speed_latitude": 0.0001,
        "speed_distance": 0.0001,
        "retrograde": "DIRECT",
        "position_type": "APPARENT",
        "ayanamsa_value": 23.9999999
      }
    ],
    "ephemeris_mode": "SWIEPH",
    "ephemeris_files": ["se_18.se1", "sepl_18.se1", "semo_18.se1"]
  },
  "config": {
    "ayanamsa": "LAHIRI",
    "ayanamsa_override": null,
    "ephemeris_mode": "SWIEPH",
    "position_type": "APPARENT",
    "node_type": "MEAN",
    "ephemeris_path": null,
    "allow_fallback": true
  }
}
```

> `provider_run.positions` duplicates the top-level `positions` (both are
> abbreviated to the SUN entry for readability — a real result carries all
> nine bodies). The service guarantees the two arrays are equal (tested).
> The example numbers are internally consistent: tropical − ayanamsa =
> sidereal (`84.123456789 − 23.9999999 = 60.123456889`).

## 10. Round-trip guarantees

- `json.loads(result_to_json(r))` → identical doubles for every numeric field.
- `request_from_dict(json.loads(json.dumps(req.to_dict())))` equals `req`.
- Tests cover both (TEST-PLAN §6).

# JRE-006 — Gochar / Continuous Transit Engine: Data Contract

- Version: 0.2.0 (SPECIALIST)
- Date: 2026-08-14
- Status: SPECIALIST-COMPLETE (**normative at CODING**; supersedes the
  v0.1.0 architect draft where they conflict)
- Related: [specialist spec](JRE-006-SPECIALIST-SPEC.md),
  [architecture core](JRE-006-GOCHAR-TRANSIT-ENGINE.md),
  [test plan](JRE-006-TEST-PLAN.md),
  [ADR-022](../decisions/ADR-022-GOCHAR-LAYER-BOUNDARY.md) …
  [ADR-029](../decisions/ADR-029-ASPECT-STATE-ECHO-EVENTS-DEFERRED.md)

## 1. Design rules

1. **Echo, never redefine.** JRE-006 reuses JRE-003/JRE-005 public
   types verbatim (`PlanetState`, `TransitEvent`, `TransitEventKind`,
   `TransitReferencePoint`, `TransitThroughHouses`, `PairGeometry`,
   `AspectKind`, `ApplyingSeparating`, `Bhava`, `RashiId`,
   `NakshatraId`, `Pada`, `BodyId`, `RetrogradeState`,
   `TransitHouseAnalysis`, `TransitHouseFact`, `FactFrame`, `BirthData`,
   `HouseSystem`). JRE-006 result models **contain** these echoed
   values; they never re-declare them and define **zero new enums**.
2. **Deterministic serialization.** Enums as `.value` strings, tuples
   as lists, floats as JSON numbers, `None` as `null`; canonical key
   order (declaration order); byte-identical JSON across processes.
3. **Provenance everywhere.** Every result carries `GocharProvenance`.
4. **No hidden defaults.** Every `GocharConfig` default is declared in
   `config/gochar.toml`.

## 2. `GocharConfig`

| Field | Type | Default | Validation |
|---|---|---|---|
| `reference_point` | `str` | `"LAGNA"` | one of `LAGNA`, `MOON`, `SUN`, `ASC` |
| `house_system` | `str` | `"WHOLE_SIGN"` | a `jyotish.HouseSystem` value supported by JRE-003 |
| `sample_step_hours` | `float` | `24.0` | `0 < sample_step_hours <= 720` |
| `aspect_echo` | `bool` | `true` | — |
| `natal_house_series` | `bool` | `false` | when `true`, requests must supply a natal anchor |
| `tradition_profile` | `string \| null` | `null` | non-empty when present (passthrough echo only) |
| `version` | `string` | `"0.2.0"` | pinned |

TOML authority: `config/gochar.toml` declares every default; a config
missing any declared field is a load error (`InvalidGocharConfigError`).
Immutable `GocharConfig`, validated at construction.

## 3. Errors (`gochar.errors`)

| Error | Parent | Raised when |
|---|---|---|
| `GocharError` | `Exception` | base class |
| `InvalidGocharConfigError` | `GocharError` | config validation failure |
| `InvalidGocharRequestError` | `GocharError` | malformed request (bad instant/interval, start > end, empty bodies, unknown reference/house system, `natal_house_series` without anchor) |
| `GocharComputationError` | `GocharError` | a delegated JRE-003/JRE-005 computation failed and cannot be echoed (message includes the wrapped error class name) |

No raw `ValueError`/`KeyError`/`AttributeError` escapes the public
surface.

## 4. Result models

### 4.1 `GocharProvenance`

| Field | Type | Notes |
|---|---|---|
| `derivation_id` | `string` | `"gochar.instant.v1"` / `"gochar.natal.v1"` / `"gochar.interval.v1"` |
| `derivation_version` | `string` | pinned |
| `source_layers` | `list[string]` | ordered: `["JRE-002","JRE-003"]`, `["JRE-002","JRE-003","JRE-005"]`, or with `JRE-005` for natal-anchored intervals |
| `jyotish_version` | `string` | package version echo |
| `bhava_version` | `string` | package version echo |
| `gochar_version` | `string` | package version echo |
| `ephemeris_version` | `string` | echoed from JRE-003 provider metadata |
| `catalog_versions` | `object` | `{"rashi": …, "nakshatra": …}` echoes |
| `input_echo` | `object` | interval bounds / bodies / reference point / house system / sample step / aspect flag |
| `algorithm` | `string` | e.g. `"echo-jre003-events-bisection"`, `"echo-jre003-state-series"`, `"derive-transit-houses-jre005"`, `"echo-jre003-pair-geometry"` |

No timestamps of the derivation run, random values, process IDs, or
environment data (ADR-028).

### 4.2 `GocharInstantResult` (GENERIC — no birth data)

| Field | Type | Notes |
|---|---|---|
| `instant_utc_iso` | `string` | ISO-8601 UTC |
| `planet_states` | `list[PlanetState]` | echo of JRE-003 states; canonical body order |
| `pair_geometry` | `list[PairGeometry] \| null` | echo of `jyotish.all_pairs`; `null` when `aspect_echo=false` |
| `config_echo` | `object` | `reference_point`, `house_system`, `aspect_echo` |
| `provenance` | `GocharProvenance` | derivation `"gochar.instant.v1"` |

### 4.3 `GocharNatalResult` (INDIVIDUAL)

| Field | Type | Notes |
|---|---|---|
| `instant_utc_iso` | `string` | transit instant |
| `birth_snapshot` | `BirthData` | echo (request input; never engine state) |
| `transit_house_analysis` | `TransitHouseAnalysis` | echo of `bhava.derive_transit_analysis` |
| `transit_to_natal_aspects` | `list[PairGeometry] \| null` | echo of `jyotish.pair_geometry` per transit-body × natal-planet pair; `null` when `aspect_echo=false` |
| `reference_point` | `string` | echo |
| `provenance` | `GocharProvenance` | derivation `"gochar.natal.v1"` |

### 4.4 `GocharIntervalResult`

| Field | Type | Notes |
|---|---|---|
| `start_utc_iso` | `string` | interval start |
| `end_utc_iso` | `string` | interval end |
| `bodies` | `list[string]` | echo |
| `events` | `list[TransitEvent]` | **verbatim echo** of `jyotish.events_between`, re-asserted pinned order `(event_julian_day_ut, body.value, kind.value)` stable sort. Event identity = echoed `TransitEvent` + ordinal (position) in this sorted tuple |
| `state_samples` | `list[PlanetState]` | echo of `jyotish.state_series` at config step, ascending JD |
| `natal_house_series` | `list[TransitHouseAnalysis] \| null` | per-sample natal-frame house facts (JRE-005 echo); only when `natal_house_series=true` and a natal anchor is supplied |
| `natal_anchor` | `BirthData \| null` | echo when present |
| `provenance` | `GocharProvenance` | derivation `"gochar.interval.v1"` |

**Interval endpoint semantics (corrected, empirically verified):**
events crossing a boundary **exactly at `start_utc_iso` are included**;
events crossing **exactly at `end_utc_iso` are not guaranteed**
(upstream JRE-003 detection limitation — the final sample is only ever
an `f1` value). JRE-006 echoes verbatim and does not compensate. The
interval is documented as "`[start, end]` by contract, with
exact-`end`-crossing events not guaranteed".

**Deterministic ordering summary** (pinned everywhere):

- events: `(event_julian_day_ut, body.value, kind.value)` stable sort;
- bodies: JRE-003 canonical order (SUN, MOON, MARS, MERCURY, JUPITER,
  VENUS, SATURN, RAHU, KETU);
- reference points: `jyotish.TransitReferencePoint` declaration order
  (LAGNA, MOON, SUN, ASC);
- `state_samples`: ascending JD order;
- `natal_house_series`: ascending sample-JD order, canonical bodies per
  sample;
- transit-to-natal aspect pairs: canonical body order (transit body
  outer, natal body inner).

## 5. Request models

| Request | Fields | Validation |
|---|---|---|
| `GocharInstantRequest` | `instant_utc_iso`, `bodies`, config overrides | ISO-UTC instant; non-empty bodies |
| `GocharNatalRequest` | `birth`, `instant_utc_iso`, `bodies`, `reference_point`, config overrides | ISO-UTC instant; non-empty bodies; pinned reference |
| `GocharIntervalRequest` | `start_utc_iso`, `end_utc_iso`, `bodies`, `natal_anchor` (optional), config overrides | start <= end; non-empty bodies; `natal_house_series=true` requires `natal_anchor` |

## 6. JSON shapes

```jsonc
// GocharInstantResult (canonical key order)
{
  "instant_utc_iso": "2026-08-14T12:00:00.000000Z",
  "planet_states": [ /* PlanetState echo */ ],
  "pair_geometry": [ /* PairGeometry echo, null when aspect_echo=false */ ],
  "config_echo": { "reference_point": "LAGNA", "house_system": "WHOLE_SIGN", "aspect_echo": true },
  "provenance": { "derivation_id": "gochar.instant.v1", /* §4.1 */ }
}
```

```jsonc
// GocharIntervalResult (canonical key order)
{
  "start_utc_iso": "2026-08-01T00:00:00.000000Z",
  "end_utc_iso": "2026-08-31T00:00:00.000000Z",
  "bodies": ["SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN", "RAHU", "KETU"],
  "events": [ /* TransitEvent echoes, pinned order */ ],
  "state_samples": [ /* PlanetState echoes */ ],
  "natal_house_series": null,
  "natal_anchor": null,
  "provenance": { "derivation_id": "gochar.interval.v1", /* §4.1 */ }
}
```

JSON Schema (draft 2020-12) for every request/result type with
`additionalProperties=false` at every object level; enums constrained
to the pinned string sets; timestamps constrained to the ISO-8601 UTC
pattern (microsecond).

## 7. Round-trip guarantees

- `result_to_dict` → `result_to_json` → `result_to_dict`:
  value-identical (hex-float pinning for the golden fixture).
- Dict → JSON → dict round-trip lossless for all result types.
- Requests round-trip through `*_request_from_dict` with the same
  validation as construction.
- Malformed input (unknown enum string, extra key, wrong type) →
  `InvalidGocharRequestError` / `InvalidGocharConfigError`, never a
  raw exception.

## 8. Serialization helpers (public)

- `result_to_json`, `result_to_dict` (all three result families)
- `instant_request_from_dict`, `natal_request_from_dict`,
  `interval_request_from_dict`
- `config_from_dict`, `load_config` (TOML authority)

## 9. Cross-layer equality invariants (hard gates)

1. JRE-006 `events` == JRE-003 `events_between` output, byte-identical
   after the re-asserted stable sort (echo policy; incl. endpoint
   semantics §4.4).
2. JRE-006 `transit_house_analysis` == JRE-005
   `derive_transit_analysis(TransitThroughHouses, natal_chart)`
   output for the same inputs.
3. ASC ≡ LAGNA absolute-house anchor: natal-frame facts for
   `reference_point=ASC` and `reference_point=LAGNA` agree on
   whole-sign frames.
4. No eclipse vocabulary in any JRE-006 result (ADR-027).

## 10. Example payloads

See the test plan golden fixture section (JRE-006-TEST-PLAN.md §7) for
committed example payloads with real transit data.

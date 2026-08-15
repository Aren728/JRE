# JRE-006 — Gochar / Continuous Transit Engine: Specialist Specification

- Version: 0.2.0 (SPECIALIST)
- Date: 2026-08-14
- Status: SPECIALIST-COMPLETE (this document is **normative at CODING**;
  it supersedes design-level detail in the architecture core
  [JRE-006-GOCHAR-TRANSIT-ENGINE.md](JRE-006-GOCHAR-TRANSIT-ENGINE.md)
  where they conflict)
- Related: [data contract](JRE-006-DATA-CONTRACT.md),
  [test plan](JRE-006-TEST-PLAN.md),
  [queue item](../../orchestration/queue/JRE-006-GOCHAR-TRANSIT-ENGINE.md),
  [ADR-022](../decisions/ADR-022-GOCHAR-LAYER-BOUNDARY.md) …
  [ADR-029](../decisions/ADR-029-ASPECT-STATE-ECHO-EVENTS-DEFERRED.md)

## 1. Purpose

JRE-006 is the deterministic **gochar / continuous transit state layer**.
It consumes JRE-003 transit primitives and JRE-005 house facts through
their **public APIs only** and produces structured, machine-readable
transit facts: instant gochar state (GENERIC), transit-to-natal
relationship facts (INDIVIDUAL), and deterministic interval facts
(echoed event stream + sampled state series + optional natal-frame
house series), all with full provenance and deterministic serialization.

This specification is the implementation-ready contract. It pins every
field, enum, error, derivation rule, precision rule, and static gate.
Where it conflicts with the architecture core (v0.1.0), this document
wins (v0.2.0).

## 2. Layer boundary

### 2.1 Imports allowed in `src/gochar/`

- Public `jyotish` root (per `jyotish.__all__`).
- Public `bhava` root (per `bhava.__all__`).
- Python standard library.

### 2.2 Imports forbidden in `src/gochar/`

- `astronomy.*`, `jyotish.models`, `jyotish.swisseph`,
  `jyotish.service`, `jyotish.transit`, `jyotish.geometry`,
  `jyotish.houses`, `jyotish.lagna`, `jyotish.position`,
  `jyotish.rashi`, `jyotish.nakshatra`, `jyotish.eclipse`,
  `knowledge.*`, `bhava.models`, `bhava.derive`, `bhava.service`,
  and any direct Swiss Ephemeris module.
- **No `TYPE_CHECKING` bypass**: `TYPE_CHECKING` blocks in
  `src/gochar/` must not import forbidden modules.

### 2.3 Echo, never recompute

JRE-006 performs **no** planetary-position, cusp, house-span, lagna,
geometry, aspect, or event-search computation. All such computation is
delegated to JRE-003/JRE-005 and **echoed verbatim**. JRE-006's own
arithmetic is limited to: event re-sorting (pinned key), provenance
assembly, request validation, and result assembly.

### 2.4 No interpretation

JRE-006 contains no dasha, prediction, yoga, benefic/malefic,
auspiciousness, gochar judgement, drishti doctrine, classical rule
resolution, or confidence logic (static vocabulary gate, §26).

## 3. Public API dependency matrix

### 3.1 Required and AVAILABLE (verified against current public surfaces)

| # | Capability | Symbol | Layer |
|---|---|---|---|
| 1 | Instant transit states | `JyotishService.planetary_state`, `JyotishService.position_at`, `PlanetState` | JRE-003 |
| 2 | Sampled interval states | `JyotishService.state_series` | JRE-003 |
| 3 | Deterministic event search | `JyotishService.events_between` | JRE-003 |
| 4 | Event types (echoed) | `TransitEvent`, `TransitEventKind`, `SearchMetadata` | JRE-003 |
| 5 | Instant geometry | `jyotish.pair_geometry`, `jyotish.all_pairs`, `PairGeometry`, `AspectRelationship`, `AspectKind`, `ApplyingSeparating` | JRE-003 |
| 6 | Natal chart | `JyotishService.chart` → `NatalChart` | JRE-003 |
| 7 | Transit-through-houses | `JyotishService.transit_through_houses` → `TransitThroughHouses`, `HouseTransitEntry` | JRE-003 |
| 8 | Reference points | `TransitReferencePoint` (LAGNA/MOON/SUN/ASC) | JRE-003 |
| 9 | Time conversion | `jyotish.iso_utc_to_jd`, `jyotish.jd_to_iso_utc` | JRE-003 |
| 10 | Config + errors | `JyotishConfig`, `load_config`, `TransitSearchError`, `UnsupportedReferencePointError`, `JyotishError` | JRE-003 |
| 11 | Natal-frame transit house facts | `bhava.derive_transit_analysis` → `TransitHouseAnalysis`, `TransitHouseFact` | JRE-005 |
| 12 | Relative-house arithmetic | `bhava.relative_house` | JRE-005 |
| 13 | Frame constant | `bhava.FactFrame` | JRE-005 |
| 14 | Serialization helpers | `bhava.result_to_dict` / `result_to_json` | JRE-005 |

All 14 verified present in `jyotish.__all__` / `bhava.__all__` at
baseline `92085ff`. **No JRE-002 additive API is required for v0.1.**

### 3.2 Deferred (MISSING_PUBLIC_API — v0.2+, ADR-026)

| Capability | Missing symbol | Internal capability | Minimal additive API | Owning layer | Blocks v0.1? |
|---|---|---|---|---|---|
| Generic natal-free transit chart | none public for houses/lagna at an instant without `BirthData` | `JyotishService._house_cusps` + `compute_bhavas` + `derive_lagna` | `JyotishService.instant_chart(date, time, timezone, latitude, longitude, config) -> InstantChart` | JRE-003 | No (deferred) |
| Cusp-based house-ingress events | `events_between` accepts `TransitEventKind` only (fixed arcs) | ADR-005 bisection over arbitrary boundaries | `JyotishService.crossings_between(start, end, bodies, boundaries_deg, config)` | JRE-003 | No (deferred) |
| Continuous aspect events | no public separation root-finding | instant `pair_geometry` | `JyotishService.aspect_events_between(...)` (Specialist-recommended JRE-003 additive) | JRE-003 | No (deferred) |

No FORBIDDEN_WORKAROUND is required for v0.1; the static gate rejects
any attempt.

## 4. Module layout

```
src/gochar/
  __init__.py     — public surface (__all__ pinned), __version__ = "0.2.0"
  config.py       — GocharConfig validation + load_config (TOML authority)
  errors.py       — error taxonomy (§7)
  models.py       — GocharProvenance + result/request models (§9)
  derive.py       — pure helpers: sort_events, build_provenance,
                    natal_house_series sampling composition (§11-§12)
  service.py      — GocharService facade (§10-§12)
  serialize.py    — result_to_json/result_to_dict, request_from_dict,
                    config_from_dict, JSON Schema, golden helpers
config/gochar.toml   — declares every default (§5)
tests/unit/gochar/   — config, models, errors, derive, serialize, static
tests/integration/gochar/ — JRE-003 echo identity, JRE-005 equality,
                    determinism (in-process + cross-process), golden, perf
tests/fixtures/gochar/ — golden + request fixtures
```

Test-file basenames that already exist elsewhere in `tests/` are
prefixed `test_gochar_*` (repo convention, cf. `test_jyotish_*`,
`test_bhava_*`).

## 5. `GocharConfig` (TOML authority, no hidden defaults)

| Field | Type | Default | Validation |
|---|---|---|---|
| `reference_point` | `str` | `"LAGNA"` | one of `LAGNA`, `MOON`, `SUN`, `ASC` |
| `house_system` | `str` | `"WHOLE_SIGN"` | a `jyotish.HouseSystem` value supported by JRE-003 |
| `sample_step_hours` | `float` | `24.0` | `0 < sample_step_hours <= 720` |
| `aspect_echo` | `bool` | `true` | — |
| `natal_house_series` | `bool` | `false` | when `true`, requests must supply a natal anchor |
| `tradition_profile` | `str \| null` | `null` | non-empty when present (passthrough echo only) |
| `version` | `str` | `"0.2.0"` | pinned |

- `config/gochar.toml` declares every default; a config missing any
  declared field is a load error (`InvalidGocharConfigError`).
- `GocharConfig` is immutable (frozen dataclass), validated at
  construction.
- `reference_point`/`house_system` accept only the pinned string values;
  unknown values are rejected at validation, never at runtime.

## 6. Enums

**JRE-006 defines zero new enums.** It reuses, by import:

- `jyotish.TransitReferencePoint` (reference points)
- `jyotish.TransitEventKind` (event kinds, echoed)
- `jyotish.HouseSystem` (house systems, passthrough)
- `bhava.FactFrame` (frame tagging on house facts)
- `jyotish.ApplyingSeparating`, `jyotish.AspectKind` (aspect state, echoed)

Serialization renders all enum values as their string `.value`.

## 7. Error taxonomy (`gochar.errors`)

| Error | Parent | Raised when |
|---|---|---|
| `GocharError` | `Exception` | base |
| `InvalidGocharConfigError` | `GocharError` | config validation failure |
| `InvalidGocharRequestError` | `GocharError` | malformed request (§8) |
| `GocharComputationError` | `GocharError` | delegated JRE-003/JRE-005 computation fails; wraps the underlying typed error (message includes the wrapped error class name) |

No raw `ValueError`/`KeyError`/`AttributeError` escapes the public
surface.

## 8. Input invariants

- `instant_utc_iso` / `start_utc_iso` / `end_utc_iso`: valid ISO-8601
  UTC strings (parsable by `datetime.fromisoformat` after normalizing
  `Z`→`+00:00`); date-only strings are rejected.
- Interval: `start_utc_iso <= end_utc_iso` (string compare on
  normalized UTC is well-ordered; additionally compare JDs via
  `jyotish.iso_utc_to_jd`).
- `bodies`: non-empty tuple of `jyotish.BodyId` values.
- `reference_point`: pinned string; unknown → `InvalidGocharRequestError`.
- `house_system`: pinned string; unsupported → `InvalidGocharRequestError`.
- `natal_house_series=true` without a natal anchor → `InvalidGocharRequestError`.
- Natal anchor: `jyotish.BirthData` (validated by JRE-003 on use).

## 9. Result models (field-level)

### 9.1 `GocharProvenance`

`derivation_id: str`, `derivation_version: str`,
`source_layers: tuple[str, ...]`, `jyotish_version: str`,
`bhava_version: str`, `gochar_version: str`,
`ephemeris_version: str`, `catalog_versions: dict[str, str]`
(`rashi`, `nakshatra` keys), `input_echo: dict[str, Any]`,
`algorithm: str`.

Determinism rule: provenance contains only pinned versions, constants,
and input echoes — no wall-clock timestamps, randomness, PIDs, or
environment data (ADR-028; static hygiene scan §26).

### 9.2 `GocharInstantResult` (GENERIC — no birth data anywhere)

- `instant_utc_iso: str`
- `planet_states: tuple[PlanetState, ...]` — echo of
  `JyotishService.planetary_state`; body order = canonical JRE-003
  order (SUN, MOON, MARS, MERCURY, JUPITER, VENUS, SATURN, RAHU, KETU)
  filtered to requested bodies, which is the JRE-003 output order.
- `pair_geometry: tuple[PairGeometry, ...] | None` — echo of
  `jyotish.all_pairs(states)` when `aspect_echo=true`, else `None`.
- `config_echo: dict[str, Any]` — `reference_point`, `house_system`,
  `aspect_echo`.
- `provenance: GocharProvenance` — derivation `"gochar.instant.v1"`,
  `source_layers=("JRE-002", "JRE-003")`.

### 9.3 `GocharNatalResult` (INDIVIDUAL)

- `instant_utc_iso: str`
- `birth_snapshot: BirthData` — echo (privacy: request input, echoed,
  never engine state).
- `transit_house_analysis: TransitHouseAnalysis` — echo of
  `bhava.derive_transit_analysis(jyotish.transit_through_houses(...))`.
- `transit_to_natal_aspects: tuple[PairGeometry, ...] | None` — echo
  of `jyotish.pair_geometry(transit_state, natal_state)` per
  transit-body × natal-planet pair, canonical pair order (JRE-003),
  when `aspect_echo=true`, else `None`.
- `reference_point: str`
- `provenance: GocharProvenance` — derivation `"gochar.natal.v1"`,
  `source_layers=("JRE-002", "JRE-003", "JRE-005")`.

### 9.4 `GocharIntervalResult`

- `start_utc_iso: str`, `end_utc_iso: str`
- `bodies: tuple[str, ...]`
- `events: tuple[TransitEvent, ...]` — verbatim echo of
  `jyotish.events_between`, re-asserted pinned order (§13.6).
- `state_samples: tuple[PlanetState, ...]` — echo of
  `jyotish.state_series` at the config step, ascending JD.
- `natal_house_series: tuple[TransitHouseAnalysis, ...] | None` — when
  `natal_house_series=true` and a natal anchor is supplied (§12.3),
  else `None`.
- `natal_anchor: BirthData | None`
- `provenance: GocharProvenance` — derivation `"gochar.interval.v1"`;
  `algorithm` reflects whether the interval was natal-anchored.

### 9.5 Request models

- `GocharInstantRequest`: `instant_utc_iso`, `bodies`, optional config
  overrides.
- `GocharNatalRequest`: `birth`, `instant_utc_iso`, `bodies`,
  `reference_point`, optional config overrides.
- `GocharIntervalRequest`: `start_utc_iso`, `end_utc_iso`, `bodies`,
  `natal_anchor` (optional), optional config overrides.

## 10. Instant generic derivation (GENERIC)

1. Validate request (§8).
2. Split `instant_utc_iso` into civil date/time (stdlib
   `datetime.fromisoformat`); call
   `JyotishService.planetary_state(date, time, "UTC", 0.0, 0.0,
   bodies, jyotish_config)` — location-independent state facts
   (rashi/nakshatra/pada/retrograde do not depend on location; JRE-003
   computes them from longitude). The returned states are echoed
   verbatim. (Equivalently `position_at(iso_utc_to_jd(iso))`; the
   civil-UTC path is pinned for provenance clarity.)
3. If `aspect_echo=true`, call `jyotish.all_pairs(states,
   jyotish_config)` and echo.
4. Assemble `GocharInstantResult` + provenance.

## 11. Instant natal derivation (INDIVIDUAL)

1. Validate request (§8).
2. Call `JyotishService.transit_through_houses(birth,
   transit_date, transit_time, "UTC", reference, jyotish_config)` with
   the civil-UTC split of the instant.
3. Call `bhava.derive_transit_analysis(transit_through_houses,
   natal_chart=None, config=bhava_config)` — **natal chart required
   input**: pass `JyotishService.chart(birth, jyotish_config)`
   (computed once; the same chart used by
   `transit_through_houses` internally, but JRE-006 supplies it
   explicitly per the JRE-005 contract so the derivation is auditable).
   Echo the resulting `TransitHouseAnalysis` verbatim.
4. If `aspect_echo=true`: for each transit state × each natal planet
   state (canonical body order), call
   `jyotish.pair_geometry(transit_state, natal_state,
   jyotish_config)` and echo the aspects-bearing `PairGeometry`
   results. (This is JRE-003 geometry composed by JRE-006 — the full
   transit-to-natal aspect echo, distinct from
   `HouseTransitEntry.aspects_to_natal` which covers natal-house
   occupants only.)
5. Assemble `GocharNatalResult` + provenance.

## 12. Interval derivation

### 12.1 Event stream

1. Call `JyotishService.events_between(start_utc_iso, end_utc_iso,
   bodies, kinds=None, jyotish_config)` — `kinds=None` requests all
   `TransitEventKind` values (JRE-003 semantics).
2. Echo the returned tuple **verbatim**, then re-assert the pinned
   ordering (§13.6) with a stable sort. The re-sort is
   identity-preserving for JRE-003 output.

### 12.2 State series

Call `JyotishService.state_series(start_utc_iso, end_utc_iso,
step_days=config.sample_step_hours/24, bodies, jyotish_config)` and
echo verbatim (ascending JD).

### 12.3 Natal-frame house series (config-gated)

When `natal_house_series=true` and a natal anchor is supplied:

1. Compute the natal chart once: `chart(birth, jyotish_config)`.
2. Convert each sample JD in the `state_series` echo to civil UTC
   (`datetime.fromisoformat` on `jyotish.jd_to_iso_utc(jd)`).
3. For each sample, call `jyotish.transit_through_houses(birth,
   sample_date, sample_time, "UTC", reference, jyotish_config)` then
   `bhava.derive_transit_analysis(..., natal_chart=chart, ...)`;
   append the `TransitHouseAnalysis`.
4. Known v0.1 cost: the natal chart is computed inside each
   `transit_through_houses` call in addition to the one JRE-006
   computes — accepted (delegated computation; excluded from the JRE-006
   performance budget, §23). A JRE-003 additive API (precomputed-chart
   reuse) is a documented v0.2 candidate (ADR-026).
5. Sample order = ascending JD; per-sample body order = canonical.

## 13. Event semantics (inherited from JRE-003, pinned here)

JRE-006 **adopts JRE-003's ADR-005 event semantics verbatim** and
documents them as its own contract (ADR-023):

### 13.1 Detection method

Fixed sampling step → longitude unwrap → sign-change isolation of
`f(t) = λ*(t) − boundary` → bisection to
`transit_tolerance_jd` (default 1e-5 d ≈ 0.86 s) with a fixed iteration
cap (60). **An event is generated only on a sign change of `f` (or an
exact sample landing on the boundary); a mere change in sampled
position is never an event.**

### 13.2 False-event exclusion

Between two samples, an odd number of crossings produces exactly one
bisected event; an even number (double crossing, e.g. a fast retrograde
re-crossing within one step) produces **no** event — a documented
upstream miss bound, not a false positive. JRE-006 inherits this
bound and echoes the sample step in provenance so consumers can reason
about it.

### 13.3 Exact-boundary samples

A sample landing exactly on a boundary (`f0 == 0.0`) produces an event
at that sample with `SearchMetadata.iterations == 0` and no bisection.

### 13.4 Interval endpoints (CORRECTED vs architecture v0.1)

Empirically verified against the JRE-003 engine
(`ContinuousTransitEngine`, linear provider):

- crossing exactly at `start_jd`: **event included** (start is an `f0`
  sample);
- crossing exactly at `end_jd`: **event NOT included** (the final
  sample is only ever `f1`; `f0*f1 < 0` excludes zero).

JRE-006's interval is therefore documented as
**"`[start, end]` by contract, with exact-`end`-crossing events not
guaranteed"** (inherited upstream limitation; JRE-006 does **not**
compensate — echo policy). The test plan asserts start-exact and
interior-exact inclusion and the documented end-exact limitation.

### 13.5 Retrograde re-crossings

Each sign change is an independent event; a retrograde crossing of the
same boundary produces its own ingress/egress pair (JRE-003 unwrap
handles monotonicity within a step).

### 13.6 Deterministic ordering (total)

Pinned sort key `(event_julian_day_ut, body.value, kind.value)` with a
**stable** sort. Ties at identical `(jd, body, kind)` retain
source-stream relative order (deterministic). Event identity for
consumers = the echoed `TransitEvent` plus its **ordinal** (position)
in the sorted tuple — a deterministic sequence key; JRE-006 never
modifies `TransitEvent` fields.

### 13.7 Simultaneous events

Multiple kinds at one instant (e.g. a rashi and nakshatra boundary both
at 0°) sort by `body.value` then `kind.value`; total, pinned.

### 13.8 0°/360°

`boundary_deg` normalized to `[0, 360)` with `0.0` for a 360°→0°
crossing (JRE-003 `% 360` with `0.0 if 0`); `reached` bucket from the
JRE-003 catalogs. JRE-006 echoes; no re-normalization.

## 14. Retrograde / station semantics (inherited)

- A station is detected on a **sign change of apparent longitudinal
  velocity** (`v0*v1 < 0`), bisected on the speed function to
  `transit_tolerance_jd`; an exact zero-speed sample is a station with
  `iterations == 0`.
- **Near-zero, non-crossing velocities are not stations** — a true
  station requires a sign change; numerical noise near zero without a
  sign change produces nothing.
- Station events carry `direction=RetrogradeState.STATIONARY`;
  `STATION_RETROGRADE` (direct→retrograde) vs `STATION_DIRECT`
  (retrograde→direct) per the sign of the following sample's speed.
- JRE-006 echoes; it performs no station computation (§2.3).

## 15. Aspect semantics

- **Echo**: JRE-006 echoes JRE-003 `PairGeometry` results, which carry
  `AspectKind` (7 kinds, `ASPECT_IDEAL_ANGLES`) and
  `ApplyingSeparating` state at the instant (closed-form
  `applying_separating`: APPLYING when the distance to exactness is
  decreasing, SEPARATING when increasing, NONE at exactness or below
  the station epsilon). **Applying/separating is state, not an event.**
- **Events deferred**: exact-aspect **event timestamps** (aspect
  perfection) are NOT in v0.1 (ADR-029; ADR-026 §3); the v0.1
  limitation is machine-testable (`GocharIntervalResult` contains no
  aspect-event kind; instant results carry aspect state only).
- **Orb**: JRE-003 aspect detection is pinned (`pair_geometry`); JRE-006
  adds no orb of its own.
- **No interpretation**: aspect facts are geometric only.

## 16. Reference-frame semantics

- Reuse `jyotish.TransitReferencePoint`; `reference_point` is echoed on
  natal results.
- LAGNA ≡ ASC absolute-house anchor (house 1); MOON/SUN anchor on natal
  Moon/Sun rashi (JRE-003 `_natal_house_for` semantics, consumed via
  `transit_through_houses`).
- **Hard cross-layer invariants**:
  1. `GocharNatalResult.transit_house_analysis` equals
     `bhava.derive_transit_analysis` output for the same inputs.
  2. Whole-sign natal-frame facts agree for `reference_point=ASC` and
     `reference_point=LAGNA`.
- JRE-006 never computes house numbers directly; it consumes the
  JRE-003/JRE-005 derived values (ADR-025).

## 17. Transit / natal separation

- `GocharInstantResult` contains no birth data (structural).
- `GocharNatalResult` contains the transit state + natal **echo**
  (`birth_snapshot`) + relationship facts; natal state is never merged
  into transit facts (relationship facts *reference* the natal echo).
- `GocharIntervalResult.natal_anchor` echoes the anchor birth data when
  present; a generic interval has `natal_anchor=None` and no house
  series.
- No result type mixes GENERIC and INDIVIDUAL content.

## 18. Precision & time

- **Timestamps**: ISO-8601 UTC `Z`, microsecond precision — the exact
  strings produced by `jyotish.jd_to_iso_utc` (echoed values keep
  JRE-003's strings; JRE-006-generated values use the same format).
- **Time conversion**: only `jyotish.iso_utc_to_jd` /
  `jyotish.jd_to_iso_utc` and stdlib `datetime.fromisoformat` (civil
  UTC split). No new conversion code.
- **Timezone**: interval and JRE-006-derived instant queries are
  ISO-UTC; IANA timezone handling exists only where JRE-003 accepts it
  (JRE-006 always passes `"UTC"`). DST is handled by JRE-003's
  timezone conversion (stdlib `zoneinfo`); leap days by the proleptic
  Gregorian calendar — both delegated.
- **Angles**: degrees as floats, no rounding; JRE-003
  `transit_tolerance_jd` and `transit_sample_step_hours` are echoed in
  provenance.
- **Wraparound**: §13.8.

## 19. Determinism

- Every result is a pure function of (request, config, pinned catalog
  and ephemeris versions). In-process and cross-process serialized
  output are byte-identical.
- All ordering pinned (§13.6, §9 body/sample/reference order); no
  set/dict iteration in ordering paths (static scan).
- Provenance contains no environment-dependent data (§9.1).

## 20. Performance (p95, informational; delegated computation excluded)

Mirroring JRE-005 SPEC §30: the timed JRE-006 budget covers only
JRE-006's own work (validation, echo assembly, re-sort, provenance).
Delegated JRE-003/JRE-005 computation (position/geometry/event-search/
chart/transit-house calls) is excluded.

| Scenario | Budget (p95) |
|---|---|
| Instant generic analysis | < 5 ms |
| Instant natal analysis | < 5 ms |
| Interval (30 d, daily, 9 bodies): events + series echoes + re-sort | < 10 ms |
| Interval + natal_house_series (30 samples) | < 10 ms (series derivation excluded) |
| Event re-sort, 1-year stream | O(n log n), measured informational |

Worst case (all bodies, 1 year, dense events): the delegated
`events_between` dominates (JRE-003-owned); JRE-006's re-sort of the
resulting stream is the only own-cost term. No unbounded caches in
`src/gochar`; JRE-003's bounded process-scoped LRU is the only cache.

## 21. Serialization

- `result_to_json` / `result_to_dict` for all three result types;
  `instant_request_from_dict` / `natal_request_from_dict` /
  `interval_request_from_dict`; `config_from_dict`.
- Rules: enums → `.value` strings; tuples → JSON lists; floats → JSON
  numbers; `None` → `null`; canonical key order (declaration order);
  microsecond ISO-8601 `Z` timestamps.
- JSON Schema (draft 2020-12) per type with `additionalProperties=false`
  at every object level; golden fixture pinned with hex-float
  serialization (JRE-003/JRE-005 convention).
- Round-trip: dict ↔ JSON value-identical; requests round-trip with
  full validation; malformed input → typed errors (§7).

## 22. Configuration authority

`config/gochar.toml` is the single source of defaults (§5); explicit
per-request config overrides win; everything else is the TOML value.
No hidden defaults, no environment-variable configuration.

## 23. Eclipse / JRE-007 boundary

- JRE-006 performs no eclipse detection and consumes none of
  `jyotish.eclipses` output (ADR-027).
- Sun/Moon/node **positions** may be echoed as ordinary `PlanetState`
  values.
- Static gate: no eclipse vocabulary in `src/gochar`.

## 24. Interpretation boundary

Forbidden vocabulary in `src/gochar` production code: `dasha`,
`prediction`, `yoga`, `benefic`, `malefic`, `auspicious`, `forecast`,
`eclipse`. (The identifier `gochar` itself is the layer name; only
interpretive compounds are rejected.) Static scan enforced.

## 25. Deferred capabilities — machine-testable limitations (v0.2)

1. Generic natal-free transit chart: not available in v0.1; any request
   for it is an invalid request (no such request shape exists).
2. Cusp-based house-ingress **events**: absent in v0.1; natal-frame
   house **state at sample instants** is provided instead
   (`natal_house_series`), and the `events` stream contains only the
   `TransitEventKind` set.
3. Aspect **events** (perfection timestamps): absent in v0.1; instant
   aspect **state** (incl. `ApplyingSeparating`) is provided.

## 26. Static gates (CODING exit criteria)

1. Forbidden-import AST scan of `src/gochar` (§2.2), including
   `TYPE_CHECKING` blocks.
2. Interpretation + eclipse vocabulary scan (§23-§24).
3. Provenance-hygiene scan: no `time(`, `random`, `getpid`,
   `environ` in `src/gochar` provenance construction.
4. Public-surface pinning: `gochar.__all__` matches the spec and is
   enforced by a test.
5. No `set(`/`dict(` iteration in ordering paths (determinism).

## 27. Test strategy

Full matrix in the [test plan](JRE-006-TEST-PLAN.md) (v0.2.0). Hard
gates: JRE-003 event-stream echo byte-identity (incl. endpoint
semantics §13.4), JRE-005 house-series equality, ASC ≡ LAGNA,
cross-process byte determinism, serialization round-trip, static
boundary, performance smoke, golden fixture.

## 28. CODING handoff checklist

1. `GocharConfig` + TOML authority (§5).
2. Error taxonomy (§7); input invariants (§8).
3. Result/request models (§9) — reuse `jyotish`/`bhava` types only.
4. Derivation paths (§10-§12) with verbatim echoes.
5. Event ordering + endpoint semantics (§13).
6. Provenance (§9.1, ADR-028).
7. Serialization + Schema + golden (§21).
8. Static gates (§26); full regression (existing suite stays green).
9. No JRE-002/003/004/005 modification; no FORBIDDEN_WORKAROUND.
10. Advance queue to CODING-COMPLETE only on explicit authorization.

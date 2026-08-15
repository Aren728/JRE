# JRE-006 — Gochar / Continuous Transit Engine: Architecture and Refined Specification

- Version: 0.1.0 (ARCHITECT)
- Date: 2026-08-14
- Status: ARCHITECT-COMPLETE (this document is the design authority; the
  Specialist stage refines it into the implementable spec)
- Related: [queue item](../../orchestration/queue/JRE-006-GOCHAR-TRANSIT-ENGINE.md),
  [data contract](JRE-006-DATA-CONTRACT.md),
  [test plan](JRE-006-TEST-PLAN.md),
  [ADR-022](../decisions/ADR-022-GOCHAR-LAYER-BOUNDARY.md),
  [ADR-023](../decisions/ADR-023-TRANSIT-EVENT-ECHO-POLICY.md),
  [ADR-024](../decisions/ADR-024-INSTANT-INTERVAL-STATE-MODEL.md),
  [ADR-025](../decisions/ADR-025-TRANSIT-NATAL-REFERENCE-FRAME.md),
  [ADR-026](../decisions/ADR-026-DEFERRED-GOCHAR-CAPABILITIES.md),
  [ADR-027](../decisions/ADR-027-ECLIPSE-BOUNDARY.md),
  [ADR-028](../decisions/ADR-028-GOCHAR-PROVENANCE-ECHO.md)

## 1. Purpose

JRE-006 is the deterministic **gochar / continuous transit state layer**.
It consumes JRE-003 transit primitives (instant positions, sampled state
series, deterministic event search) and JRE-005 derived house facts, and
produces structured, machine-readable **transit state and interval
facts**: instant gochar state, transit-to-natal relationship facts, and
deterministic event streams over date ranges — all with full provenance
and deterministic serialization.

The layer answers computational questions only:

- Where is each transiting body at an instant (longitude, rashi,
  nakshatra, pada, retrograde/direct state)?
- What are the deterministic transit events (sign/nakshatra/pada
  ingress and egress, retrograde/direct stations) in a date range, and
  in what exact order?
- Through which natal houses does each transit body pass (per an
  explicit reference point), and which natal planets does it aspect at
  an instant?
- What is the transit-transit geometry among transiting bodies at an
  instant?
- What is the provenance of each transit fact (source layers, catalog
  and ephemeris versions, input echo)?

JRE-006 never answers interpretive questions (what the facts "mean").
Those belong to JRE-004 rules and future synthesis layers.

## 2. Scope

### 2.1 In scope (v0.1)

- **Instant gochar state (GENERIC mode)** — transit planet states
  echoed from JRE-003 `planetary_state` / `position_at`, including the
  rashi/nakshatra/pada/retrograde classification already carried by
  `PlanetState`; optional transit-transit pair-geometry echo from
  `pair_geometry`.
- **Transit-to-natal facts (INDIVIDUAL mode)** — for a transit instant
  against a natal chart: natal-frame house number/rashi per transit
  body via JRE-005 `derive_transit_analysis`, aspect echoes against
  natal planets via `pair_geometry`, reference-point echo.
- **Interval facts** — deterministic event stream over a closed
  ISO-UTC interval (echo of JRE-003 `events_between`, re-asserted
  pinned ordering), sampled transit state series (echo of
  `state_series`), and an optional config-gated natal-frame house
  series.
- **Reference-point model** — reuse of `jyotish.TransitReferencePoint`
  (LAGNA, MOON, SUN, ASC); ASC ≡ LAGNA absolute-house anchor
  equivalence (ADR-019/ADR-025).
- **Deterministic event ordering** — pinned sort key
  `(event_julian_day_ut, body.value, kind.value)` re-asserted by
  JRE-006.
- **Timezone handling** — interval queries in ISO-8601 UTC; instant
  queries accept IANA timezone names (delegated to JRE-003).
- **Date-range queries, boundary handling** — closed interval
  `[start, end]` echo semantics.
- **Provenance** — `GocharProvenance` on every externally observable
  result.
- **Deterministic serialization** — JSON round-trip, JSON Schema with
  `additionalProperties=false`, typed malformed-input errors.
- **Configuration authority** — `GocharConfig` from `config/gochar.toml`,
  no hidden defaults.

### 2.2 Deferred (v0.2+, with additive JRE-003 API proposals)

1. **Generic (natal-free) transit chart** — transit lagna and transit
   houses at an instant + location without birth data. JRE-003's public
   API computes houses/lagna only inside `chart()` (birth-anchored);
   `JyotishService._house_cusps` is private. v0.1 does not include a
   generic transit *chart* — only generic transit *state* (positions +
   classification + events), which is fully available.
2. **Cusp-based house-ingress events over time** — `events_between`
   searches fixed arcs only (rashi 30°, nakshatra 13°20′, pada
   3°20′); natal cusp longitudes are arbitrary fixed boundaries and are
   not addressable by the current public event API. v0.1 provides
   natal-frame house **state at sample instants** (via JRE-005), not
   cusp-crossing **events**.
3. **Continuous transit aspect events** (applying / exact / separating
   over time) — requires root-finding over the angular-separation
   function of two bodies. JRE-003 provides instant `pair_geometry`
   only. v0.1 provides instant aspect **echoes**; aspect **events** are
   deferred.

Each deferred capability has a minimal additive public API proposal in
§6.4. They are **not** v0.1 blockers.

### 2.3 Forbidden (never)

- Eclipse detection (JRE-007 owns it — ADR-027).
- Interpretation/prediction: no dasha, no yoga detection, no
  benefic/malefic, no auspiciousness, no gochar judgements, no drishti
  doctrine, no classical rule resolution, no confidence.
- Recomputation of anything JRE-003/JRE-005 already compute: planetary
  positions, cusps, house spans, lagna, geometry, aspects, event
  search, transit house facts.
- Direct imports of `astronomy.*`, `jyotish.models`, `jyotish.swisseph`,
  `knowledge.*`, or the Swiss Ephemeris binding.
- Recreating any JRE-003/JRE-005 type.

## 3. Layer boundary and separation

| Layer | Owns |
|---|---|
| JRE-002 | astronomy: exact planetary positions (raw, provider-mediated) |
| JRE-003 | Jyotish coordinate/state: classification, houses/lagna, geometry, continuous event search, eclipse facts, transit-through-houses |
| JRE-005 | derived bhava/house facts (natal and transit instants) |
| **JRE-006** | **gochar/transit state facts: instant state, transit-to-natal relationships, interval event/state facts, reference-point model, deterministic ordering, provenance, serialization** |
| JRE-004 | classical knowledge/rules/provenance/conflict/resolution |
| JRE-007 (future) | eclipse engine (detection, contacts, visibility) |
| Future synthesis | interpretation/prediction |

JRE-006 is a **composition layer with derivation**: it composes
JRE-003 primitives (which already perform all astronomical/astrological
computation) and JRE-005 house facts, adds the deterministic
state/interval/relationship model, provenance, and serialization — and
nothing else.

## 4. Dependencies

### 4.1 JRE-002 dependency matrix (via JRE-003 public API only)

JRE-006 does **not** import `astronomy` directly. All JRE-002-derived
values are consumed through `jyotish` public exports.

| Capability | Public symbol | Availability |
|---|---|---|
| Planet states (longitude, classification) | `jyotish.PlanetState`, `jyotish.derive_planet_state` | AVAILABLE |
| Body identity / retrograde state | `jyotish.BodyId`, `jyotish.RetrogradeState` | AVAILABLE |
| Catalog/version pins | `jyotish.RASHI_CATALOG_VERSION`, `jyotish.NAKSHATRA_CATALOG_VERSION` | AVAILABLE |
| Ephemeris version pin | `NatalChart.provider_metadata` / `EphemerisResult.provider` echo | AVAILABLE |

### 4.2 JRE-003 dependency matrix

| Capability | Public symbol | Availability |
|---|---|---|
| Instant transit states | `JyotishService.planetary_state` / `position_at` | AVAILABLE |
| Sampled interval states | `JyotishService.state_series` | AVAILABLE |
| Deterministic event search | `JyotishService.events_between` | AVAILABLE |
| Transit events (echoed type) | `jyotish.TransitEvent`, `jyotish.TransitEventKind`, `jyotish.SearchMetadata` | AVAILABLE |
| Instant geometry | `JyotishService.pair_geometry`, `jyotish.pair_geometry`, `jyotish.all_pairs`, `jyotish.PairGeometry` | AVAILABLE |
| Natal chart | `JyotishService.chart` → `jyotish.NatalChart` | AVAILABLE |
| Instant transit-through-houses | `JyotishService.transit_through_houses` → `jyotish.TransitThroughHouses`, `jyotish.HouseTransitEntry` | AVAILABLE |
| Reference points | `jyotish.TransitReferencePoint` (LAGNA/MOON/SUN/ASC) | AVAILABLE |
| Time conversion | `jyotish.iso_utc_to_jd`, `jyotish.jd_to_iso_utc` | AVAILABLE |
| Sign lordship (for natal-house-lord echoes) | `jyotish.sign_lord_of` | AVAILABLE |
| Configuration | `jyotish.JyotishConfig`, `jyotish.load_config` | AVAILABLE |
| Errors | `jyotish.TransitSearchError`, `jyotish.UnsupportedReferencePointError`, `jyotish.JyotishError` | AVAILABLE |

### 4.3 JRE-005 dependency matrix

| Capability | Public symbol | Availability |
|---|---|---|
| Natal-frame transit house facts | `bhava.derive_transit_analysis` → `bhava.TransitHouseAnalysis`, `bhava.TransitHouseFact` | AVAILABLE |
| Relative-house arithmetic | `bhava.relative_house` | AVAILABLE |
| Frame constants | `bhava.FactFrame` | AVAILABLE |
| Serialization helpers | `bhava.result_to_dict`, `bhava.result_to_json` | AVAILABLE |

### 4.4 Public API readiness audit (v0.1)

| Dependency | Classification | Evidence |
|---|---|---|
| Instant states, series, events, geometry, natal chart, transit-through-houses, reference points, time conversion, sign lordship, config, errors | AVAILABLE | §4.2 public exports (`jyotish.__all__`) |
| JRE-005 transit derivation, relative house | AVAILABLE | `bhava.__all__` |
| Generic natal-free transit chart | MISSING_PUBLIC_API (deferred v0.2) | `chart()` requires `BirthData`; `_house_cusps` private. Proposal: `JyotishService.instant_chart(date, time, timezone, latitude, longitude, config) -> InstantChart` reusing the existing house/lagna computation — JRE-003 additive correction |
| Cusp-based house-ingress events over time | MISSING_PUBLIC_API (deferred v0.2) | `events_between` accepts `TransitEventKind` only (fixed arcs). Proposal: additive `JyotishService.crossings_between(start, end, bodies, boundaries_deg, ...)` or a `HOUSE_INGRESS` kind with boundary set — JRE-003 additive correction |
| Continuous aspect events (applying/exact/separating) | MISSING_PUBLIC_API (deferred v0.2) | instant `pair_geometry` only. Proposal: additive `JyotishService.aspect_events_between(...)` (separation root-finding) or documented JRE-006-internal search over `state_series` echoes — requires Specialist decision |
| Direct astronomy/swisseph/knowledge access | FORBIDDEN_WORKAROUND (not used) | static gate will reject |

**Verdict: v0.1 is CODING-READY on the current public API. No
FORBIDDEN_WORKAROUND is required.**

## 5. Continuous transit model

JRE-006 models transit movement at three granularities, all derived
from JRE-003 public outputs:

1. **Instant state** — a single transit instant: planet states (each
   carrying longitude, rashi, nakshatra, pada, retrograde state, speed)
   + optional pair geometry echo + optional transit-to-natal facts.
2. **Sampled interval state** — a deterministic sequence of instant
   states over a closed interval (echo of `state_series` at a pinned
   step).
3. **Event stream** — discrete events (ingress/egress/stations) with
   exact timestamps (echo of `events_between`).

**Event boundaries.** JRE-003's engine (ADR-005) defines the event
semantics: fixed sampling step, unwrapped longitude, sign-change
isolation, bisection to `transit_tolerance_jd` with a fixed iteration
cap, retrograde re-crossings as separate events, and exact-boundary
handling when a sample lands on a boundary (`f0 == 0.0`). JRE-006
**adopts these semantics verbatim** (ADR-023) — it re-asserts ordering
but never re-derives events.

**Forward/retrograde/direct motion.** Stations are events
(`STATION_RETROGRADE`/`STATION_DIRECT`); each transit state echoes
`PlanetState.retrograde`. JRE-006 treats apparent-motion direction as
state carried by the echo, never recomputed.

**House boundaries.** Natal-frame house *state* at sample instants is
derived via JRE-005 (whole-sign and cusp systems, per the pinned
JRE-005 semantics). Natal *cusp-crossing events* over time are deferred
(§2.2.2).

**Aspect boundaries.** Instant aspect *echoes* only in v0.1
(§7). Aspect *events* (exact-angle crossings) are deferred (§2.2.3).

## 6. Event model

JRE-006's interval result contains an **echoed event stream**: the
`TransitEvent` objects returned by `jyotish.events_between`, wrapped
with a provenance block. JRE-006 does not define a competing event
type (ADR-023).

Event identity (echoed): `body`, `kind`, `event_julian_day_ut`,
`event_utc_iso`, `boundary_deg`, `reached` (Rashi/Nakshatra/Pada),
`direction`, `search_metadata` (algorithm, sample step, tolerance,
iterations, position calls).

**Deterministic ordering.** JRE-003 already sorts events by
`(event_julian_day_ut, body.value, kind.value)`. JRE-006 re-asserts the
same pinned sort key on the echoed stream (a stable re-sort is
identity-preserving for JRE-003 output and guarantees the contract even
if the upstream stream is ever unsorted). Ties at identical
`(jd, body, kind)` are ordered by their source-stream position (stable
sort), which is deterministic because the source stream is
deterministic.

**Simultaneous events.** Multiple events at the same timestamp sort by
`body.value` then `kind.value`; the ordering is total and pinned.

## 7. Aspect model

- **Geometric fact only.** JRE-006 echoes JRE-003 aspect geometry
  (`PairGeometry`, `AspectRelationship`, `AspectKind`,
  `ApplyingSeparating`) for (a) transit-transit pairs at an instant and
  (b) transit-to-natal pairs at an instant. No aspect doctrine, no
  classical meaning, no interpretation.
- **Tradition variation.** If a future consumer needs tradition-specific
  aspect rules, that belongs to JRE-004 knowledge configuration — JRE-006
  echoes the pinned JRE-003 geometric aspects only and records the
  geometry provenance.
- **Continuous aspect events are deferred** to v0.2 (§2.2.3); v0.1
  exposes instant echoes.

## 8. Retrograde / station model

- Stations are events from JRE-003 (`STATION_RETROGRADE`,
  `STATION_DIRECT`) with exact bisection timestamps — echoed, never
  recomputed.
- Stationary tolerance: JRE-003's speed-sign-change bisection is the
  pinned definition (no coarse "daily sign" approximation); JRE-006
  documents `SearchMetadata.iterations`/`position_calls` as the
  determinism echo.
- Longitude monotonicity/wraparound: JRE-003's unwrapping handles 0°/360°;
  JRE-006 echoes `boundary_deg` normalized to `[0, 360)` with `0.0` for
  360°→0° crossings.

## 9. Reference-frame model

- **Reuse `jyotish.TransitReferencePoint`** (LAGNA, MOON, SUN, ASC) —
  no redefinition (ADR-025).
- **Anchor semantics identical to JRE-003/JRE-005**: LAGNA and ASC are
  the same absolute-house anchor (house 1); MOON and SUN anchor on the
  natal Moon/Sun rashi; natal-frame house number is
  `((transit_rashi_index − anchor_rashi_index) mod 12) + 1` for
  whole-sign frames, or JRE-005's cusp-aware derivation for cusp
  systems.
- **JRE-005 cross-layer equality**: JRE-006 natal-frame house facts
  must equal JRE-005 `derive_transit_analysis` output for the same
  `TransitThroughHouses` input (hard cross-layer invariant, tested).
- Transit frame vs natal frame: transit state facts and natal facts are
  structurally separated (ADR-021 semantics); a transit-to-natal fact
  references the natal echo but never merges natal facts into transit
  state.

## 10. Precision / time model

- **Time representation**: ISO-8601 UTC `Z` strings (microsecond
  precision) for externally observable timestamps; internal Julian Day
  (UT) floats are carried only inside echoed JRE-003 values.
- **Time conversion**: `jyotish.iso_utc_to_jd` / `jyotish.jd_to_iso_utc`
  (Meeus ch. 7, identical to JRE-002/JRE-003) — no new conversion code.
- **Timezone normalization**: interval queries are ISO-UTC only;
  instant queries accept IANA timezone names and are normalized to UTC
  by JRE-003.
- **Angular precision**: degrees as floats, no premature rounding;
  classification is whatever `PlanetState` carries (JRE-003 pinned).
- **Comparison tolerance**: no new JRE-006 tolerance; the JRE-003
  `transit_tolerance_jd` is echoed in provenance.
- **Boundary inclusivity**: closed interval `[start, end]` for event
  queries (JRE-003 semantics); JRE-006 documents and tests the
  inclusive behavior.
- **Wraparound**: 0°/360° handled by JRE-003 unwrapping; JRE-006 adds no
  re-normalization of echoed values.
- **No floating-point ambiguity in ordering**: the sort key uses raw
  float JD plus integer-valued enum/body discriminants; equal JDs are
  ties broken by the pinned stable sort.

## 11. Transit / natal separation

- `GocharInstantResult` (GENERIC) contains transit state only — no
  birth data anywhere.
- `GocharNatalResult` (INDIVIDUAL) contains transit state **plus** the
  natal echo (`birth_snapshot` — the same privacy convention as
  JRE-003/JRE-005: personal data is request input, echoed, never engine
  state) and transit-to-natal facts.
- The two result types are never merged; interval results carry a flag
  indicating whether they are natal-anchored.
- A transit event may reference natal data (e.g., "transit body entered
  the natal 7th house") but never mutates or merges natal facts into
  transit state (ADR-021/ADR-023).

## 12. Provenance model

Every externally observable JRE-006 result carries a `GocharProvenance`:

- `derivation_id` — stable identity, e.g. `"gochar.instant.v1"`,
  `"gochar.natal.v1"`, `"gochar.interval.v1"`.
- `derivation_version` — pinned derivation version.
- `source_layers` — ordered tuple of layers actually consumed
  (e.g. `("JRE-002", "JRE-003", "JRE-005")`).
- `jyotish_version`, `bhava_version`, `gochar_version` — the pinned
  package versions at derivation time.
- `ephemeris_version` — echoed from JRE-003 provider metadata.
- `catalog_versions` — rashi/nakshatra catalog versions echoed.
- `input_echo` — interval bounds, bodies, reference point, house
  system, sample step, aspect-echo flag.
- `algorithm` — e.g. `"echo-jre003-events-bisection"`,
  `"derive-transit-houses-jre005"`.

**Determinism rule**: provenance contains only pinned versions,
constants, and input echoes — **no wall-clock timestamps, random
values, process IDs, or environment-dependent data** (ADR-028).

## 13. Serialization model

- Deterministic JSON: enums as their string values, tuples as lists,
  floats as JSON numbers, `None` as `null`.
- Canonical key ordering (pinned in the data contract) so byte
  equality holds across processes.
- JSON Schema with `additionalProperties=false` for every result and
  request type.
- Dict ↔ JSON round-trip guaranteed (float hex-pinning where the
  golden fixture requires bit identity, following the JRE-003/JRE-005
  golden convention).
- Malformed input → typed `GocharError` family, never raw exceptions.

## 14. Configuration model

`GocharConfig` (immutable, TOML authority at `config/gochar.toml`, no
hidden defaults):

- `reference_point` — default `LAGNA` (one of
  `jyotish.TransitReferencePoint` values).
- `house_system` — default `WHOLE_SIGN` (pass-through to JRE-003/JRE-005).
- `sample_step_hours` — default `24.0` (interval house-series sampling;
  validated `> 0`).
- `aspect_echo` — default `True` (instant pair-geometry echo).
- `natal_house_series` — default `False` (interval natal-frame house
  series; config-gated sampling).
- `tradition_profile` — `str | None` passthrough echo only (JRE-005
  pattern; no JRE-004 lookup).
- `version` — `"0.1.0"`.

Every default is declared in the TOML file (no hidden defaults),
mirroring JRE-003/JRE-005.

## 15. Performance model

Targets are p95, informational (mirroring JRE-005 SPEC §30: **delegated
JRE-003/JRE-005 computation is excluded** from the budget — the chart,
position, event-search, and house-derivation calls are the delegated
computations):

- Instant generic analysis (echo assembly): **< 5 ms** excluding the
  delegated JRE-003 position/geometry computation.
- Instant natal analysis: **< 5 ms** excluding the delegated JRE-003
  chart + transit computation and the JRE-005 house derivation.
- Interval analysis (e.g. 30 days, daily samples, 9 bodies): **< 50 ms**
  excluding the delegated JRE-003 `events_between` / `state_series`
  computation.
- Event ordering re-assertion: O(n log n) in the echoed event count.
- No unbounded memoization; JRE-003's bounded process-scoped LRU is
  the only cache, and it is JRE-003-owned.

## 16. Eclipse / JRE-007 boundary

- JRE-006 performs **no eclipse detection** — eclipse events, contacts,
  classification, and visibility belong to the future JRE-007 Eclipse
  Engine (ADR-027).
- JRE-006 may echo the **positions** of the Sun, Moon, and nodes
  (already present in ordinary transit state series) — these are
  planetary positions, not eclipse facts.
- JRE-006 consumes none of `jyotish.eclipses` output; the boundary is
  documented and machine-tested (no eclipse vocabulary in JRE-006).

## 17. Determinism

- Every result is a pure function of (query inputs, pinned
  catalog/ephemeris versions, pinned config). Repeated in-process and
  cross-process runs are byte-identical after serialization.
- All ordering is pinned: events (`(jd, body, kind)` stable sort),
  bodies (canonical JRE-003 body order), reference points (declaration
  order), house facts (JRE-005 pinned order), pair geometry (JRE-003
  pinned order).
- No set/dict iteration leaks into externally observable ordering.
- Provenance contains no environment-dependent data (§12).

## 18. Test strategy

Full strategy in the [test plan](JRE-006-TEST-PLAN.md). Highlights:

- Boundary tests: 0°/360° wraparound, exact-on-boundary events, sign /
  nakshatra / pada ingress/egress, retrograde/direct stations,
  timezone conversion, leap days, closed-interval endpoints,
  duplicate/simultaneous events, deterministic ordering.
- Cross-layer tests: JRE-003 event echo byte-identity; JRE-005
  transit-house equality; ASC ≡ LAGNA; reference-point matrix; golden
  fixture (byte identity).
- Determinism: in-process repetition + cross-process byte identity
  (subprocess).
- Static boundary: forbidden-import scan (no `astronomy`,
  `jyotish.models`, `jyotish.swisseph`, `knowledge`, network), no
  interpretation vocabulary (no dasha/prediction/yoga/benefic/malefic
  identifiers in production code), public-surface pinning.
- Performance smoke (informational) per §15.
- Serialization: round-trip, schema conformance
  (`additionalProperties=false`), malformed-input error taxonomy.

## 19. Future compatibility

- **Dasha** (future JRE): consumes JRE-003 `position_at`/`state_series`
  and JRE-006 interval facts; JRE-006's deterministic event streams and
  provenance are the input contract.
- **Gochar interpretation** (future synthesis): consumes JRE-006
  transit-to-natal facts; JRE-006 stops at facts.
- **Drishti** (JRE-004 rules / future): consumes JRE-006 instant aspect
  echoes (geometric) + JRE-004 doctrine — separated by design.
- **Yoga** (JRE-004 rules): consumes JRE-005 house facts and JRE-003
  geometry; JRE-006 transit events feed transit-yoga evaluation later.
- **Varga** (future): independent layer; JRE-006 unaffected.
- **Synthesis/prediction** (future): consumes all layers' facts;
  JRE-006 provides no confidence, no interpretation.

## 20. Risk register

| Risk | Mitigation |
|---|---|
| JRE-006 drifts into reimplementation of JRE-003 event search | Hard echo policy (ADR-023) + static boundary tests + provenance `source_layers` |
| Interval house series cost (repeated natal chart computation) | Config-gated (`natal_house_series=False` default); documented v0.2 JRE-003 additive API (reuse precomputed natal chart) |
| Aspect-event demand before v0.2 | Explicit deferral (ADR-026); instant echoes available in v0.1 |
| Simultaneous-event ordering drift | Pinned total sort key + stable tie-break + ordering tests |
| Provenance leaking environment data | ADR-028 rule + static scan for `time()/random/os.environ` in `src/gochar` |
| Eclipse scope creep | ADR-027 boundary + no eclipse vocabulary + JRE-007 handoff note |

## 21. Specialist handoff checklist

1. Pin `GocharConfig` schema, enums, error taxonomy, TOML authority.
2. Pin exact result models (`GocharInstantResult`, `GocharNatalResult`,
   `GocharIntervalResult`, `GocharProvenance`) and field-level contract.
3. Pin event-echo policy (verbatim echo + re-asserted sort).
4. Pin natal-frame house-series sampling semantics and the JRE-005
   equality invariant.
5. Pin precision/time rules (closed interval, ISO-UTC, no new
   tolerance).
6. Resolve (or explicitly defer) the three v0.2 capabilities with
   machine-testable limitations.
7. Complete test plan (boundary matrix, cross-layer, determinism,
   static, performance, golden).
8. Verify JRE-002/JRE-003/JRE-004/JRE-005 untouched; verify no
   FORBIDDEN_WORKAROUND.
9. Advance queue to SPECIALIST only on explicit authorization.

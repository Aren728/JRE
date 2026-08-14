# JRE-005 — Bhava / House Engine: Architecture and Refined Specification

- Version: 0.2.0 (SPECIALIST-refined)
- Date: 2026-08-14
- Status: SPECIALIST-COMPLETE (this document is the design authority; the
  Specialist stage refined it into the implementable spec — see the
  [specialist spec](JRE-005-SPECIALIST-SPEC.md), which is normative at
  SPECIALIST and supersedes design-level detail below where they
  conflict)
- Related: [queue item](../../orchestration/queue/JRE-005-BHAVA-ENGINE.md),
  [data contract](JRE-005-DATA-CONTRACT.md),
  [specialist draft](JRE-005-SPECIALIST-SPEC.md),
  [test plan](JRE-005-TEST-PLAN.md),
  [ADR-013](../decisions/ADR-013-BHAVA-LAYER-BOUNDARY.md),
  [ADR-014](../decisions/ADR-014-RELATIVE-HOUSE-CANONICAL.md),
  [ADR-015](../decisions/ADR-015-MULTI-HOUSE-SYSTEM-VIEWS.md),
  [ADR-016](../decisions/ADR-016-DERIVED-FACT-PROVENANCE.md)

## 1. Purpose

JRE-005 is the deterministic **bhava/house analytical layer**. It consumes
JRE-003 Jyotish state (`NatalChart`, `TransitThroughHouses`, catalog
versions) and produces structured, machine-readable **derived house-level
facts** for downstream JRE-004 knowledge/rule synthesis and later
prediction layers.

The layer answers computational questions only:

- Which house does each planet occupy, under which house system?
- What is a planet's house number relative to the lagna, the Moon, the
  Sun, or the ascendant?
- Which houses are empty, which are occupied, and by whom?
- Who lords each house and each sign; which houses does each planet lord?
- Is a planet in its own sign / own house?
- Which computational house categories (kendra, trikona, dusthana,
  upachaya) does each house belong to?
- Which geometric aspects does each house receive, from which planets?
- Which bodies sit within orb of a house cusp?
- Which house system was used for each fact, and what is the fact's
  derivation provenance?

JRE-005 never answers interpretive questions (what the facts "mean").
Those belong to JRE-004 rules and future synthesis.

## 2. Scope

In scope:

- One derived-fact engine over JRE-003 `NatalChart` inputs (natal frame).
- Derived facts per house, per planet, per reference point, and per
  house system (explicitly tagged).
- Relative-house calculations compatible with JRE-004's
  `relative_house(<BODY>, <REF>)` fact vocabulary.
- House ownership/lordship tables derived from JRE-003's pinned rashi
  catalog (echo, never re-authored).
- Empty-house facts, cusp/boundary facts, cusp-proximate bodies.
- Geometric aspect-to-house aggregation (echo of JRE-003 geometry).
- Retrograde/node state echo within house facts.
- Multi-house-system comparative analysis via per-system JRE-003 charts.
- Deterministic serialization with round-trip guarantees.
- Provenance on every derived fact (derivation id, version, input echo,
  JRE-003 catalog versions).
- Gochar-compatible derived house facts from `TransitThroughHouses`
  (transit frame) — the same derivation functions applied to transit
  planet states against a natal chart.

Out of scope (mandatory separation):

- Recomputing planetary positions, rashi/nakshatra/pada classification,
  cusps, spans, lagna, or geometry — JRE-003 owns all of these.
- Classical interpretation: benefic/malefic, yoga declaration, dasha
  results, gochar judgement, muhurta, prediction, confidence.
- Sign-based drishti (aspect) doctrine tables — future Drishti engine.
- Varga (divisional chart) computation — future engine (see §28).
- Evaluating JRE-004 rules or resolving rule conflicts — JRE-004 owns
  this; JRE-005 only *supplies facts* to it.
- Storing or embedding birth data.

## 3. Non-goals (mandatory separation)

The following are explicitly NOT JRE-005:

1. **No astronomy.** No positions, no ayanamsa, no ephemeris access, no
   `swisseph` imports anywhere in `bhava`.
2. **No geometry recomputation.** No cusps, no spans, no aspect-angle
   computation. JRE-005 reads `Bhava.start_deg/end_deg`,
   `AspectRelationship`, `PairGeometry` from JRE-003.
3. **No classical-rule interpretation.** No benefic/malefic, no
   "auspicious/inauspicious", no house significations (bhava karakatva),
   no yoga definitions, no dasha weights, no prediction.
4. **No drishti doctrine.** Sign-based aspect rules (e.g. "7th from
   every sign", special aspects of Mars/Jupiter/Saturn) are classical
   *rules* and belong to the future Drishti engine. JRE-005 aggregates
   only JRE-003's exact-degree geometric aspects.
5. **No varga.** Divisional charts are coordinate computations on
   JRE-003 positions — a separate future engine (interface reserved, §28).
6. **No rule evaluation.** JRE-005 does not know JRE-004 catalogs, rule
   schemas, or conflict resolution. It exposes facts only.
7. **No personal-data persistence.** Birth data is request input; it is
   echoed as `birth_snapshot` exactly as JRE-003 does, never stored.
8. **No network, no clocks, no randomness.** Determinism contract §25.

## 4. Layer boundary (the four-way split)

| Layer | Owns | Consumes | Produces |
|---|---|---|---|
| JRE-002 | astronomical core | ephemeris files | `BodyPosition`, `EphemerisResult` |
| JRE-003 | Jyotish coordinate/state | JRE-002 public API | `PlanetState`, `Bhava`, `LagnaState`, `NatalChart`, `TransitThroughHouses`, geometry, transit events, eclipse facts |
| **JRE-005** | **derived bhava/house computational state** | **JRE-003 public API** | **`HouseAnalysisResult`: per-house/per-planet/ownership/relative-house/aspect-to-house derived facts with provenance** |
| JRE-004 | classical knowledge/rules/provenance/conflict/resolution | JRE-003 outputs (+ optionally JRE-005 facts later) | `ResolvedRule` sets, synthesis |
| Future synthesis | interpretation/prediction | JRE-004 resolution + JRE-005 facts | interpretation |

The boundary rule (ADR-013): **JRE-005 composes JRE-003 results; it never
recomputes anything JRE-003 emits, and it never emits anything that is a
JRE-003 fact** (it re-emits JRE-003 values only as provenance echoes with
explicit `echoed_from` markers).

## 5. Design principles

1. **Composition over duplication** — every JRE-003 value used by
   JRE-005 is read from the input chart. The only arithmetic JRE-005
   performs is on *house numbers, sets, and comparisons*.
2. **Pure derivations** — every derived fact is a pure function of its
   inputs (chart + `BhavaConfig` + reference points). No state.
3. **Explicit over implicit** — house system, reference point, and
   tradition-variable definitions are explicit fields/parameters, never
   silently chosen defaults (except the documented default reference
   LAGNA, which is pinned and echoed).
4. **Facts, not meanings** — derived facts carry zero interpretation.
   Category membership is emitted as a set because the classical
   categories overlap; the *use* of categories is the rules layer's job.
5. **Provenance everywhere** — each fact records how it was derived and
   from which catalog versions (ADR-016).
6. **Determinism as a contract** — identical inputs ⇒ byte-identical
   output, in-process and cross-process (§25).
7. **Compatibility with JRE-004** — `relative_house` values must match
   JRE-004's snapshot semantics exactly (ADR-014); JRE-004 is not
   modified, and JRE-005's richer anchors are additive-only.

## 6. Module layout (proposed)

```
src/bhava/
    __init__.py        # public API surface (mirror jyotish pattern)
    models.py          # pure data models + enums (stdlib + jyotish public API only)
    errors.py          # error taxonomy (BhavaError family)
    config.py          # BhavaConfig validation + config/bhava.toml authority
    derive.py          # pure derivation functions (house/planet/ownership/relative facts)
    service.py         # BhavaService facade (consumes JyotishService)
    serialize.py       # result_to_json/result_to_dict + input parsers
```

`src/bhava/` imports **only** `jyotish` public API (JRE-003) and the
standard library. No `astronomy` imports (go through `jyotish`), no
`knowledge` imports, no `swisseph` imports, no network. Static gates
enforce this (TEST-PLAN §8).

## 7. Inputs consumed from JRE-003 (public API only)

| Input | Source | Used for |
|---|---|---|
| `NatalChart` | `JyotishService.chart` | primary analysis input: `lagna`, `bhavas`, `planet_states`, `config`, `provider_metadata`, `birth_snapshot` |
| `Bhava` | `NatalChart.bhavas` | house identity, spans, rashi, lord, occupants, occupant states, cusp nakshatra |
| `LagnaState` | `NatalChart.lagna` | lagna rashi/classification; LAGNA anchor |
| `PlanetState` | `NatalChart.planet_states` | per-body rashi/degree/retrograde; body identity |
| `AspectRelationship` | `Bhava.aspects`, `PairGeometry.aspects` | aspect-to-house aggregation (echo) |
| `HouseSystem` | `NatalChart.config.house_system` | fact tagging; per-system analysis |
| `RASHI_CATALOG_VERSION`, `NAKSHATRA_CATALOG_VERSION` | `jyotish` public exports | provenance pins (ADR-016) |
| `RASHI_ORDER`, `sign_lord_of(rashi)` | `jyotish` public exports | sign-lordship tables (echo of JRE-003 catalog) |
| `TransitThroughHouses` | `JyotishService.transit_through_houses` | gochar-frame derived house facts |
| `TransitReferencePoint` | `jyotish` public exports | reference-point enum (reused, not redefined) |

JRE-005 never calls `AstronomicalService`, never imports
`astronomy.models` directly, and never touches `jyotish.swisseph`.

## 8. House/bhava identity semantics

- A **house** is identified by `(house_system, house_number)` where
  `house_number ∈ {1..12}` and `house_system` is the JRE-003
  `HouseSystem` used to compute the chart. Identity is **per chart
  config** — the same number under two systems are two different facts.
- Every derived house fact echoes JRE-003's `Bhava.house_number`,
  `start_deg`, `end_deg`, `rashi`, `house_lord`, `occupants`, and
  `nakshatra` (with an `echoed_from: "bhava"` provenance marker).
- The lagna anchors house 1 in every system JRE-003 supports: for
  WHOLE_SIGN the lagna rashi is house 1; for cusp systems the ascendant
  cusp opens house 1 (JRE-003 semantics; ADR-002/003).
- JRE-005 defines no house identity of its own; it classifies and
  aggregates JRE-003's.

## 9. Whole-sign vs bhava-cusp semantics; multiple house systems

- JRE-003 already computes bhavas for any configured system
  (WHOLE_SIGN derived in pure code; EQUAL/PLACIDUS/KOCH/REGIOMONTANUS/
  CAMPANUS via the cusp provider). JRE-005 **does not recompute cusps**.
- **Whole-sign bhava**: house n = n-th sign from the lagna sign; the
  cusp is the sign boundary. **Cusp bhava**: house n is bounded by
  computed cusps (may split signs); `Bhava.rashi` is the sign containing
  the cusp point (JRE-003 echo).
- JRE-005 exposes `BoundaryKind` per house: `SIGN_BOUNDARY` for
  whole-sign cusps, `COMPUTED_CUSP` for provider cusps — a pure echo
  classification of `Bhava.start_deg` against the sign grid.
- **Multi-house-system views** (ADR-015): `BhavaConfig.house_systems`
  is a tuple of `HouseSystem`; JRE-005 requests one JRE-003 `NatalChart`
  per system (same birth data) and produces a per-system
  `HouseAnalysis`. Results from different systems are **never combined
  into one fact set** — each `HouseAnalysis` carries exactly one
  `house_system`, and every derived fact is tagged with it. The
  top-level `HouseAnalysisResult` may carry several analyses keyed by
  system for comparison, never merged.
- Default `house_systems = (WHOLE_SIGN,)` — pinned, echoed, no hidden
  behavior (whole-sign is the JRE-003 default and the classical
  Parashari norm; cusp systems are explicit opt-in).

## 10. House occupancy

- Occupancy is **echoed** from `Bhava.occupants` / `Bhava.occupant_states`
  (JRE-003 already assigns bodies by `longitude_used` span, wrap-aware).
- JRE-005 derives:
  - `OccupancyStatus` per house: `OCCUPIED` / `EMPTY` (occupants empty).
  - `occupied_house_numbers`, `empty_house_numbers`, and the count —
    computational summaries.
  - Per-occupant echo rows (body, retrograde state, node flag) with
    provenance.
- JRE-005 does not re-derive spans or re-place bodies.

## 11. Planet-to-house relationships

- The **house of a planet** is `house_number` of the `Bhava` whose
  `occupants` contains the body, in the chart's house system. This is
  JRE-003's occupancy fact, promoted to a first-class per-planet fact
  (`PlanetHouseFact.house_number`).
- **Fallback rule (pinned, JRE-004-compatible)**: if a body is not an
  occupant of any bhava (possible only in cusp systems where a body can
  fall outside cusp-bounded spans — JRE-003's `Bhava` always covers the
  ecliptic, but the rule is pinned for robustness), fall back to its
  **whole-sign house from the lagna rashi**:
  `((rashi_index(body) − rashi_index(lagna)) mod 12) + 1`. This exactly
  matches JRE-004's snapshot fallback (ADR-014), so the two layers can
  never disagree.
- Every `PlanetHouseFact` carries `house_system`, the derivation rule id
  (`PLANET_HOUSE_OCCUPANCY` or `PLANET_HOUSE_WHOLE_SIGN_FALLBACK`), and
  the echoed JRE-003 values used.

## 12. House lord identification

- The **lord of a house** = the classical rashi lord of the house's
  rashi — already computed by JRE-003 (`Bhava.house_lord`, pinned
  catalog `RASHI_LORDS`). JRE-005 echoes it.
- JRE-005 derives the **reverse direction**: `HouseOwnershipFact` —
  for each body, the list of houses it lords in the chart's system
  (`lorded_houses`), computed by scanning the 12 `Bhava` rows and
  matching `house_lord`. This is a pure aggregation of JRE-003 echoes.
- No interpretive "strong/weak lord" statements — strength rules are
  JRE-004/future.

## 13. Sign lord identification

- Sign lordship is JRE-003's pinned rashi catalog
  (`jyotish.sign_lord_of`). JRE-005 exposes a **derived sign-lordship
  table** (`sign_lords: dict[RashiId, BodyId]`) as an echo with
  `source_catalog: RASHI_CATALOG_VERSION` provenance. It is a
  convenience projection for consumers and rule conditions, not a new
  catalog.
- Tradition note: `RASHI_LORDS` is the classical Parasari assignment
  (BPHS ch. 4; Brihat Jataka ch. 1) as pinned by JRE-003; JRE-005 does
  not re-litigate it. Alternative lordship schemes (e.g. some regional
  variants) are out of scope and would be a versioned JRE-003 catalog
  change.

## 14. Bhava lord/occupancy relationships

Derived relationships (all computational comparisons):

- `lord_in_own_house(body, house)`: the house's `house_lord` occupies
  the house.
- `planet_in_own_house(body)`: body occupies a house it lords.
- `planet_in_own_sign(body)`: body occupies a sign it lords
  (comparison of `PlanetState.rashi` with the catalog lordship).
- `house_lord_placement(house)`: the house where the house's lord is
  placed (occupancy echo), `None` when the lord is not placed in any
  house (cusp systems) — then the whole-sign fallback house is used with
  the rule id recorded.
- `lord_and_occupant_overlap(house)`: whether the lord is also an
  occupant.

All are pure lookups over `PlanetHouseFact` / `Bhava` echoes. None
assign meaning.

## 15. Relative-house calculations (ADR-014)

Canonical definition, pinned and JRE-004-compatible (v0.2.0):

- **Anchor frame (`HOUSE_OCCUPANCY`)** — absolute house of body B
  (`house_of[B]`): occupancy house from the chart's bhavas (the chart's
  house system); whole-sign fallback only under the explicit
  `WHOLE_SIGN_FALLBACK` mode (§18/ADR-018), never silently. In cusp
  systems this is genuinely cusp-anchored (house numbers come from the
  cusp bhavas, not the sign grid). The lagna's own house is 1 by
  construction (house 1 = ascendant-anchored in every system).
- **Relative house of B from reference R**:
  `relative_house(B, R) = ((house_of[B] − house_of[R]) mod 12) + 1`,
  where `house_of[R]` uses the same map (the reference body's absolute
  house; for `LAGNA`/`ASC`, `house_of = 1`).
- Reference set: `LAGNA`, `MOON`, `SUN`, `ASC` (reusing JRE-003's
  `TransitReferencePoint`). `ASC` ≡ `LAGNA` — both are "the chart's
  house-1 (ascendant) house" (JRE-004-compatible pin).
- **Deferred capability (machine-testable)**: sign-grid anchoring
  (relative house counted by sign from a reference rashi, independent
  of house occupancy — a classical counting convention) is NOT
  supported in v0.2.0: `SIGN_GRID_FRAME_SUPPORTED = False` constant,
  `ChartEcho.sign_grid_frame_supported: false`, `RelativeHouseFrame`
  enum with sole member `HOUSE_OCCUPANCY` (any other frame →
  `InvalidBhavaConfigError`). Extending is additive and versioned
  (ADR-019).
- **Compatibility requirement**: for every body B and every reference
  R in {LAGNA, MOON, SUN, ASC}, JRE-005's `relative_house(B, R)` equals
  JRE-004's snapshot-normalized value for the same `NatalChart`. This is
  enforced by a cross-layer regression test at VALIDATOR time (JRE-004
  is a read-only oracle; not modified).
- Output forms: per-planet `relative_house_by_reference` map, plus a
  chart-level `relative_house_table: {ref: {body: house}}` mirroring
  JRE-004's snapshot `relative_houses` section shape.
- JRE-005 additionally emits the **absolute house of each reference
  body** so consumers can see the anchor (provenance echo).

## 16. House/sign/planet ownership relationships

The ownership model is a three-way derived table:

- **Sign ownership**: planet → signs it lords (from `RASHI_LORDS` echo).
- **House ownership**: planet → houses it lords in the chart's system
  (from `Bhava.house_lord` echo, §12).
- **Placement ownership**: planet → the sign/house it currently occupies
  (occupancy echo) and the lord of that sign/house.

JRE-005 emits `HouseOwnershipFact` (planet, `lorded_signs`,
`lorded_houses`) per system and per chart, plus the derived boolean
facts of §14. No karaka (significator) assignments — bhava karakatva is
interpretive and deferred.

## 17. Empty-house semantics

- **Empty house** = `occupants == ()` (computational, per system).
- JRE-005 emits `empty_house_numbers: tuple[int, ...]`,
  `occupied_house_numbers: tuple[int, ...]`, `empty_house_count`, and
  per-house `OccupancyStatus`.
- No interpretive meaning is attached (e.g. "empty house is weak") —
  that is a rules-layer judgement. The derived facts exist so rules can
  *express* such conditions if authored.
- `include_empty_houses` config flag (default true) controls whether the
  EMPTY/occupied summary rows are materialized; the per-house status is
  always present (it is part of `DerivedHouseFact`).

## 18. Cusp/boundary semantics

- Cusps are echoed from `Bhava.start_deg` / `Bhava.end_deg`
  (`longitude_used` frame, `[0, 360)`).
- `BoundaryKind`: `SIGN_BOUNDARY` (whole-sign: cusp ≡ sign start, modulo
  30°) or `COMPUTED_CUSP` (provider cusp). Classification is a pure
  comparison of `start_deg` against `rashi_span(rashi)[0]`.
- **Cusp-proximate bodies** (v0.2.0, ADR-017): a body whose
  `longitude_used` is within `BhavaConfig.cusp_proximity_orb_deg` of
  either cusp of its house, by **wrap-aware shortest arc**
  (`min(|a−b|, 360−|a−b|)`), boundary **inclusive** at exactly the orb.
  This is a geometric distance fact — classical "near the cusp" (bhava
  sandhi) notions are interpretive and deferred.
- The orb is **one configuration value per analysis** (system-
  independent: it measures distance to cusp points regardless of their
  source; house-system-specific cusp positions come from JRE-003),
  declared in `config/bhava.toml` (no hidden default), validated
  `0 < orb < 30.0`, default `3.0°`, documented as a **modern
  computational convention** — no classical verse pins a numeric orb
  (no fabricated citation).

## 19. Retrograde/node handling

- Retrograde/stationary state is **echoed** from `PlanetState.retrograde`
  into each `PlanetHouseFact` and house-occupant row.
- Node identity: `is_node = body in {RAHU, KETU}` (computational body
  identity, from the JRE-003 `BodyId` set). Nodes participate in all
  derived house facts exactly like grahas (they are bodies in JRE-003);
  no node-specific doctrine (e.g. "Rahu acts like Saturn") is applied.
- Stationary (`RetrogradeState.STATIONARY`) is preserved as-is.

## 20. Aspect-to-house relationships (geometric only)

- JRE-003 already computes exact-degree `AspectRelationship` facts
  (ADR-004): planet-to-planet and cusp-to-occupant. JRE-005 **aggregates
  them per house**:
  - `aspects_received` per house: every `AspectRelationship` whose
    target is an occupant of the house or the house cusp point, echoed
    with kind, exact angle, distance from exact, orb, within-orb,
    applying/separating, and source body.
  - Chart-level `aspects_to_houses` table: house → list of
    (source body, kind, target) with exact values.
- JRE-005 adds **no aspect kinds and no aspect rules**. Sign-based
  drishti doctrine (special aspects, sign-based aspect tables) is
  explicitly out of scope (future Drishti engine); JRE-005 documents
  this boundary so the Drishti engine can consume `aspects_to_houses`
  as its geometric input later.

## 21. Deterministic serialization

- Same conventions as JRE-003/JRE-004 (DATA-CONTRACT §0): snake_case
  keys, enums → string values, `Pada`-style int enums → ints, tuples →
  arrays, `None` → `null`, floats via Python's round-trip repr
  (identical double on decode), `-0.0 → 0.0`.
- `result_to_json` / `result_to_dict` for `HouseAnalysisResult` and
  every fact model; input parser `analysis_request_from_dict` validates
  on construction (typed errors).
- Round-trip guarantees: `json.loads(result_to_json(r))` preserves every
  double; `analysis_request_from_dict(json.loads(json.dumps(req)))`
  equals the input. JSON Schema with `additionalProperties: false`
  (DATA-CONTRACT §10).
- `GOLDEN_VERSION` pins the producing environment (same policy as
  JRE-002/JRE-003/JRE-004) for golden fixtures.

## 22. Provenance of derived facts (ADR-016)

Every derived fact carries a `derivation` block:

```json
{
  "id": "RELATIVE_HOUSE",
  "derivation_version": "0.1.0",
  "inputs": ["chart.bhavas", "chart.lagna", "planet_states"],
  "source_catalog_versions": { "rashi": "1.0.0", "nakshatra": "1.0.0" },
  "house_system": "WHOLE_SIGN"
}
```

- `source_catalog_versions` is read from JRE-003's public exports
  (`RASHI_CATALOG_VERSION`, `NAKSHATRA_CATALOG_VERSION`).
- Echoed JRE-003 values are marked `echoed_from` (e.g.
  `echoed_from: "bhava.house_lord"`) so consumers can distinguish
  JRE-003 facts from JRE-005 derivations.
- Derivation ids are stable string constants (not free text) —
  enumerated in the specialist spec §8.
- Provenance is data, never prediction; it enables auditability and
  cross-layer consistency checks (e.g. the JRE-004 compatibility test).

## 23. Error taxonomy

| Error | Raised when |
|---|---|
| `BhavaError` | base class |
| `InvalidAnalysisRequestError` | request malformed (empty bodies set, unknown reference, bad config) |
| `InvalidBhavaConfigError` | config field invalid (unknown house system, orb ≤ 0, bad category set) |
| `InconsistentChartError` | input `NatalChart` violates invariants (fewer than 12 bhavas, missing lagna, missing body states) |
| `UnsupportedReferenceError` | reference point not in the supported set (JRE-003's `UnsupportedReferencePointError` propagates where reused) |

- JRE-003 errors (`JyotishError` family, e.g. `UnsupportedHouseSystemError`
  for an unregistered system) **propagate unchanged** from the JRE-003
  calls JRE-005 makes — JRE-005 never swallows a provider error into a
  fact (same policy as JRE-003 §20).
- All errors expose the offending value in `__str__`.

## 24. Configuration authority

- `config/bhava.toml` declares **every** default (no hidden defaults;
  v0.2.0 — `reference_default` removed; the API `references` parameter
  defaults to all four references):

```toml
[bhava]
cusp_proximity_orb_deg = 3.0        # ADR-017; 0 < orb < 30.0
house_systems = ["WHOLE_SIGN"]      # multi-system views (ADR-015)
include_empty_houses = true         # materialize empty/occupied summaries
unplaced_body_behavior = "RAISE"    # ADR-018; no silent fallback
anchor_frame = "HOUSE_OCCUPANCY"    # ADR-019; sole supported frame
derivation_version = "0.2.0"        # provenance pin (ADR-016)
# tradition_profile intentionally omitted (TOML has no null) — None default (ADR-020)
```

- `BhavaConfig` is a frozen dataclass, immutable, echoed on every
  result. `load_config` reads the TOML (authoritative; unknown enum
  values → `InvalidBhavaConfigError`). No environment-variable
  overrides (determinism).
- Validation at load: `0 < cusp_proximity_orb_deg < 30.0`,
  `house_systems` non-empty, all known, no duplicates,
  `unplaced_body_behavior`/`anchor_frame` enum members,
  `tradition_profile` None or non-empty string, `include_empty_houses`
  bool.

## 25. Determinism requirements

- Every derivation is a pure function of `(NatalChart, BhavaConfig,
  references)`. No clocks, random, network, or global mutable state.
- Identical inputs ⇒ identical output, **bit-for-bit** in-process and
  **byte-for-byte** across processes (JSON). Cross-process harness
  mirrors JRE-002/JRE-003 (§TEST-PLAN 7).
- Catalog versions are pinned and echoed; a JRE-003 catalog change is a
  versioned decision (ADR-003) that JRE-005 observes, never adapts to
  implicitly.
- Ordering is canonical everywhere: houses 1–12, bodies in JRE-003
  canonical order, references in enum order, categories sorted.

## 26. Performance requirements

- JRE-005 adds pure arithmetic over one `NatalChart`; the dominant cost
  is the JRE-003 chart computation it delegates to. Budget:
  - House analysis over one chart (one system): **p95 < 5 ms** on the
    reference hardware (informational; chart computation excluded and
    documented).
  - No I/O at analysis time; catalogs are imported constants.
  - Multi-system analysis scales linearly in the number of systems
    (each is a separate JRE-003 chart call).
- Performance smoke tests (TEST-PLAN §13) assert order-of-magnitude
  bounds, matching the JRE-003/JRE-004 precedent.

## 27. Isolation requirements

- `src/bhava/` imports only `jyotish` public API + stdlib. Static gates
  (TEST-PLAN §8): no `astronomy` imports, no `knowledge` imports, no
  `swisseph` imports, no network imports, no personal-data writes, no
  interpretation vocabulary.
- JRE-002/JRE-003/JRE-004 remain byte-for-byte unchanged (git-diff
  isolation verified at every stage, as with JRE-003/JRE-004).
- `pyproject.toml` gains `bhava` + `tests/*/bhava` entries at CODING
  time only (build metadata; no dependency changes).

## 28. Future compatibility

| Future engine | JRE-005 interface it consumes | Notes |
|---|---|---|
| **Dasha** | `PlanetHouseFact` (house placement), ownership tables, `relative_house` from Moon/lagna, nakshatra lords (via JRE-003) | Vimshottari needs nakshatra lords (JRE-003) + house context; JRE-005 supplies the house layer |
| **Gochar** | `TransitThroughHouses`-frame derived facts (`transit_house_analysis`): transiting planet's house from natal lagna/Moon/Sun | Same derivation functions applied to a transit instant; no new engine semantics |
| **Drishti** | `aspects_to_houses` (geometric echo) as the input fact surface | Sign-based drishti doctrine is added by the Drishti engine, consuming JRE-005's geometric aggregation |
| **Yoga** | `relative_house`, categories, occupancy, lordship facts as condition inputs | JRE-004 rules already reference `relative_house`; JRE-005 extends the available fact surface (additive) |
| **Varga** | (interface reserved) per-house placement of divisional bodies | Varga coordinates are computed elsewhere from JRE-003 positions; JRE-005's house-context projections can be applied to varga charts later |
| **Synthesis/prediction** | `HouseAnalysisResult` facts + JRE-004 `ResolvedRule`s | JRE-005 facts carry no confidence/interpretation; prediction layers combine them |

Additivity rule: future needs add **new derived-fact kinds and new
reference anchors**, never change existing fact semantics (JRE-004's
additive-vocabulary policy, mirrored).

## 29. Classical concepts and tradition variation (research references)

Computational definitions JRE-005 encodes (all pinned, all echoed, none
interpretive):

- **Bhava vs rashi**: sign vs house distinction (BPHS bhava chapters;
  JRE-003 whole-sign vs cusp systems).
- **House lords**: classical rashi lordship (Parashari, BPHS ch. 4;
  Brihat Jataka ch. 1) — pinned in JRE-003's `RASHI_LORDS`.
- **Kendra/trikona/dusthana/upachaya** — house-number arithmetic
  (kendra 1/4/7/10; trikona 1/5/9; dusthana 6/8/12; upachaya 3/6/10/11).
  JRE-005 emits **membership sets** because these schemes overlap (6, 10).
- **Relative house counting** — "nth from the lagna / from the Moon
  (Chandra lagna) / from the Sun (Surya lagna)" conventions; represented
  explicitly as reference points, never silently chosen.
- **Cusp proximity** — the notion of a planet "near the cusp" is
  tradition-variable (orb size); JRE-005 exposes the orb as an explicit
  parameter with a pinned default.

Explicitly NOT encoded (interpretive/rules):

- Bhava karakatva (house significations: wealth, marriage, …).
- Strength/bala computations and judgements.
- Special/drishti aspect doctrine, yoga definitions, dasha systems.
- Jaimini's chara-karaka/pada bhava system (a distinct tradition with
  its own computational rules — noted for future work, not adopted
  silently).

Tradition-variation policy: where a definition varies by tradition, the
variation is represented **explicitly** (a parameter, an enum member, a
pinned set) rather than a silent choice. JRE-005's defaults follow the
Parashari norm already pinned by JRE-003/JRE-004.

## 30. Specialist resolutions (v0.2.0)

The Specialist resolved the six open questions; the resolutions are
normative in the [specialist spec](JRE-005-SPECIALIST-SPEC.md) (v0.2.0)
and recorded as ADR-017..021. Summary:

1. **Cusp-proximity orb** → pinned `3.0°` default, **one config value
   per analysis** (system-independent), wrap-aware shortest-arc math,
   inclusive boundary, validation `0 < orb < 30.0`, documented as a
   modern computational convention (no classical verse pins a numeric
   orb) — [ADR-017](../decisions/ADR-017-CUSP-PROXIMITY-ORB.md).
2. **Category representation** → sorted membership **set** (canonical
   enum order), overlaps preserved (1 → KENDRA+TRIKONA, 6 →
   DUSTHANA+UPACHAYA, 10 → KENDRA+UPACHAYA), no primary label — spec §17.
3. **Cusp-frame `ASC` anchor** → pinned **`HOUSE_OCCUPANCY` anchor
   frame**: relative houses are counted in the chart's house occupancy
   (cusp-anchored in cusp systems, never silently whole-sign); `ASC ≡
   LAGNA` is the JRE-004-compatible pin; sign-grid anchoring is a
   machine-testable deferred capability (`SIGN_GRID_FRAME_SUPPORTED =
   False` constant + `ChartEcho.sign_grid_frame_supported` + enum
   error) — [ADR-019](../decisions/ADR-019-ANCHOR-FRAMES-RELATIVE-HOUSE.md).
4. **Gochar v0.2.0 scope** → `TransitHouseFact` (frame TRANSIT): echo
   of `TransitThroughHouses` entries + natal-frame relative house;
   requires the natal chart input; no transit events, no
   interpretation — [ADR-021](../decisions/ADR-021-GOCHAR-DERIVED-FACTS-SCOPE.md).
5. **Tradition-profile hooks** → `tradition_profile: str | None`
   validated **passthrough**, echo + provenance only, **no computation
   change** in v0.2.0 — [ADR-020](../decisions/ADR-020-TRADITION-PROFILE-PASSTHROUGH.md).
6. **Unplaced-body semantics** → **no silent fallback**:
   `unplaced_body_behavior` config, `RAISE` default
   (`UnplacedBodyError`), explicit `WHOLE_SIGN_FALLBACK` opt-in,
   provenance-labeled per body — [ADR-018](../decisions/ADR-018-UNPLACED-BODY-SEMANTICS.md).

Additional pinning: `reference_default` config field removed (the API
`references` parameter defaults to all four references LAGNA/MOON/SUN/ASC
— no hidden default); category/deterministic ordering canonicalized
(spec §27); full `ChartEcho`, `TransitHouseAnalysis`, and schema pinned
(spec §24/§22, DATA-CONTRACT v0.2.0).

## 31. Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-08-14 | Architect architecture + refined specification (Status: ARCHITECT-COMPLETE) |
| 0.2.0 | 2026-08-14 | Specialist resolutions (six open questions → ADR-017..021), supersession table, refined §15/§18/§24/§28, CHANGE-history (Status: SPECIALIST-COMPLETE) |

# JRE-005 — Bhava / House Engine

Status: VALIDATOR-COMPLETE
Priority: HIGH

## Objective

Create the deterministic bhava/house analytical layer that consumes
JRE-003 Jyotish state (natal charts and transit-through-houses outputs)
and produces structured, machine-readable, **derived** house-level facts
for downstream JRE-004 knowledge/rule synthesis and later prediction
layers. JRE-005 is a computational derivation layer: it never recomputes
positions, cusps, or geometry, and it never interprets.

## Repository baseline

- JRE-002 — `78aff38` (MERGED)
- JRE-003 — `e568a64` (MERGED)
- JRE-004 — `04bbaf9` (MERGED)
- Working tree must remain clean before starting any stage.

## Required Inputs (all consumed from JRE-003 public API)

- `NatalChart` (birth snapshot echo, lagna, 12 `Bhava`, planet states,
  config echo, provider metadata) — primary input.
- `PlanetState` / `LagnaState` / `Bhava` fields (rashi, degree,
  nakshatra/pada, retrograde, spans, occupants, lords).
- `TransitThroughHouses` / `HouseTransitEntry` — for Gochar-compatible
  derived house facts.
- `RASHI_CATALOG_VERSION`, `NAKSHATRA_CATALOG_VERSION` — provenance pins.
- Optionally multiple `NatalChart` computations (one per house system)
  for comparative multi-system analysis.

## Required Outputs (derived facts)

For a chart (one or more explicit house systems):

- Per-house derived facts: identity, rashi, lord (echo), occupancy
  status, occupants (echo), house categories (computational set
  membership), cusp/boundary facts, cusp-proximate bodies, geometric
  aspects received (echo/aggregate).
- Per-planet house facts: house number, relative house per reference
  (LAGNA/MOON/SUN/ASC), own-sign / own-house flags, retrograde/node echo.
- Ownership tables: planet → lorded signs, planet → lorded houses.
- Empty-house facts: empty house numbers + count (computational).
- Relative-house table: `relative_house(<BODY>, <REF>)` for every body
  and reference — canonically derived, compatible with JRE-004's
  fact-vocabulary semantics (ADR-012/014).
- Aspect-to-house aggregation (geometric only; no drishti doctrine).
- Deterministic serialization (round-trip guaranteed), provenance on
  every derived fact.

## Separation Requirement

- **JRE-003** = astronomical/Jyotish coordinate state (positions,
  classification, cusps, geometry, transit events, eclipses).
- **JRE-005** = derived bhava/house computational state (the facts
  above). JRE-005 consumes JRE-003 outputs and never recomputes them.
- **JRE-004** = classical knowledge/rules/provenance/conflict/resolution.
- **Future synthesis** = interpretation/prediction.

JRE-005 MUST NOT perform interpretation: no benefic/malefic, no yoga
declarations, no dasha results, no gochar judgements, no drishti rule
tables, no prediction, no confidence. Classical *definitions* that are
computational (kendra/trikona/dusthana/upachaya membership, lordship,
occupancy, relative house) are derived facts; classical *interpretive
rules* are deferred to JRE-004/future layers.

## Determinism

Identical JRE-003 input (chart/config) + identical `BhavaConfig` must
produce identical derived output, byte-for-byte across processes. Pure
functions only; no clocks/random/network; pinned catalog versions.

## Deliverables

- Architecture and refined specification
- Data contract
- ADRs for architectural decisions
- Test strategy
- Python implementation (CODING stage, later)
- Automated tests (later)
- Validation report (later)

## Restrictions

- Architecture/specification only in this phase. NO implementation, NO
  code changes under `src/`, NO tests yet.
- Do NOT modify JRE-002/JRE-003/JRE-004 (all MERGED; must remain
  byte-for-byte unchanged).
- Do NOT begin prediction logic or generic AI/LLM interpretation.
- Do NOT encode classical predictive rules; separate computational
  definitions from interpretive rules; represent tradition variation
  explicitly rather than silently choosing one.

---

## Architect Decision (2026-08-14) — Status: ARCHITECT-COMPLETE

The Architect has reviewed this request. Design decisions and the
refined specification are authoritative; the original requirements above
remain in force.

### Decisions

1. **New package `bhava`** (import name) under `src/` — the derived
   bhava/house analytical layer. It consumes JRE-003's public API
   (`JyotishService`, `NatalChart`, `Bhava`, `LagnaState`,
   `PlanetState`, `TransitThroughHouses`, catalog versions) and stdlib
   only — see
   [ADR-013](../../docs/decisions/ADR-013-BHAVA-LAYER-BOUNDARY.md).
2. **Composition, never duplication**: JRE-005 consumes `NatalChart`
   and derives; it never recomputes positions, cusps, spans, or
   geometry. `Bhava` occupancy/lords/spans are echoed, not re-derived.
3. **Canonical `relative_house`** — JRE-005 makes
   `relative_house(<BODY>, <REF>)` a first-class derived fact with an
   explicit, pinned formula (occupancy-first with whole-sign fallback,
   exactly matching JRE-004's snapshot semantics; `LAGNA`/`ASC` equal in
   the whole-sign frame; additional anchors are additive) — see
   [ADR-014](../../docs/decisions/ADR-014-RELATIVE-HOUSE-CANONICAL.md).
4. **Multi-house-system views** — a `BhavaConfig.house_systems` tuple
   requests one JRE-003 `NatalChart` per system; every derived fact is
   tagged with its `house_system`; results from different systems are
   never mixed within one analysis — see
   [ADR-015](../../docs/decisions/ADR-015-MULTI-HOUSE-SYSTEM-VIEWS.md).
5. **Provenance on every derived fact** — each fact carries its
   derivation id, derivation version, input echo, and the JRE-003
   catalog versions it derives from — see
   [ADR-016](../../docs/decisions/ADR-016-DERIVED-FACT-PROVENANCE.md).
6. **House categories as a set, not a single label** — kendra/trikona/
   dusthana/upachaya membership is pure house-number arithmetic and
   overlaps (e.g. house 6 is both dusthana and upachaya); JRE-005 emits
   the full membership set rather than silently choosing one label.
7. **Aspect-to-house is geometric echo only** — JRE-005 aggregates
   JRE-003 `AspectRelationship` facts per house; sign-based drishti
   doctrine is explicitly deferred to the future Drishti engine.
8. **No new runtime dependencies** — `jyotish` (JRE-003) + stdlib.
   `pyproject.toml` gains `bhava` package/testpaths at CODING time
   (build metadata only).
9. **Configuration authority** — `config/bhava.toml` declares every
   default (no hidden defaults): reference default, cusp-proximity orb,
   house-system set, derivation-version pin. `BhavaConfig` immutable and
   echoed on every result.

### Refined specification

The full design — responsibility boundary, inputs, outputs, identity
semantics, whole-sign vs bhava-cusp, occupancy, lordship, relative
house, ownership, empty-house, cusp/boundary, retrograde/node,
aspect-to-house, serialization, provenance, error taxonomy, config
authority, determinism, performance, isolation, and future
compatibility — is in
[docs/architecture/JRE-005-BHAVA-CORE.md](../../docs/architecture/JRE-005-BHAVA-CORE.md)
(version 0.1.0), with the field-level contract in
[JRE-005-DATA-CONTRACT.md](../../docs/architecture/JRE-005-DATA-CONTRACT.md),
the implementable specialist draft in
[JRE-005-SPECIALIST-SPEC.md](../../docs/architecture/JRE-005-SPECIALIST-SPEC.md),
and the test strategy in
[JRE-005-TEST-PLAN.md](../../docs/architecture/JRE-005-TEST-PLAN.md).

### Handoff to SPECIALIST

Proceed to the SPECIALIST stage with the refined specification as input
when separately authorized. The Specialist must resolve the unresolved
questions in section 29 of the architecture document (cusp-proximity
orb default, category-set vs primary-label representation, ASC cusp
anchor, tradition-profile hooks, gochar-scope depth). Do NOT advance
this queue item to SPECIALIZED by any agent other than SPECIALIST.

---

## Specialist Decision (2026-08-14) — Status: SPECIALIST-COMPLETE (superseded by CODING)

The Specialist has converted the architecture into a fully pinned,
implementation-ready contract (v0.2.0). The specialist spec is now
normative for CODING.

### Resolutions of the six open questions

1. **Cusp-proximity orb** → pinned `3.0°` default, one config value per
   analysis (system-independent), wrap-aware shortest-arc math,
   inclusive boundary, validation `0 < orb < 30.0`, documented modern
   convention ([ADR-017](../../docs/decisions/ADR-017-CUSP-PROXIMITY-ORB.md)).
2. **House-category representation** → sorted membership set in
   canonical enum order, overlaps preserved, no primary label (spec §17).
3. **Cusp-frame ASC anchor** → pinned `HOUSE_OCCUPANCY` anchor frame:
   relative houses counted in the chart's house occupancy (cusp-anchored
   in cusp systems); `ASC ≡ LAGNA` (JRE-004 pin); sign-grid anchoring
   explicitly deferred and machine-testable (`SIGN_GRID_FRAME_SUPPORTED
   = False`, `ChartEcho.sign_grid_frame_supported`, enum error)
   ([ADR-019](../../docs/decisions/ADR-019-ANCHOR-FRAMES-RELATIVE-HOUSE.md)).
4. **Gochar v0.2.0 scope** → `TransitHouseFact` (frame TRANSIT): echo of
   `TransitThroughHouses` entries + natal-frame relative house; natal
   chart required input; no transit events, no interpretation
   ([ADR-021](../../docs/decisions/ADR-021-GOCHAR-DERIVED-FACTS-SCOPE.md)).
5. **Tradition-profile passthrough** → `tradition_profile: str | None`
   validated passthrough, echo + provenance only, no computation change
   ([ADR-020](../../docs/decisions/ADR-020-TRADITION-PROFILE-PASSTHROUGH.md)).
6. **Unplaced-body semantics** → no silent fallback:
   `unplaced_body_behavior` config (`RAISE` default →
   `UnplacedBodyError`; explicit `WHOLE_SIGN_FALLBACK` opt-in,
   provenance-labeled) ([ADR-018](../../docs/decisions/ADR-018-UNPLACED-BODY-SEMANTICS.md)).

### Pinning summary

Complete `BhavaConfig` schema (§7), all enums (§6), error taxonomy
(§29), house-number/house-system/whole-sign/cusp semantics (§9–§11),
occupancy (§12), planet-house derivation (§13), house/sign lordship
(§14–§15), ownership (§16), relative-house formula + reference semantics
(§11), aspect-to-house geometric echo (§20), category membership (§17),
cusp proximity (§19), unplaced-body behavior (§18), transit-house
behavior (§22), `DerivationBlock`/`ChartEcho` (§23–§24), catalog/version
handling (§25), serialization + JSON Schema (§26), deterministic ordering
(§27), config authority (§28), validation rules (§7–§8), performance
(§30), isolation (§31), and the CODING handoff contract (§34).

### Handoff to CODING

Proceed to CODING with the v0.2.0 specialist spec, data contract, and
only when separately authorized. Do NOT advance this queue item to
CODING by any agent other than CODING.

## CODING Decision (2026-08-14) — Status: CODING-COMPLETE

Implemented the full v0.2.0 contract in `src/bhava/` (models, errors,
config authority via `config/bhava.toml`, pure derivations, `BhavaService`
facade, serialization + JSON Schema, `__init__` public surface). Consumes
ONLY the `jyotish` public API + stdlib (ADR-013) — including the two
JRE-003 additive APIs (`sign_lord_of`, `BodyId`/`RetrogradeState`).

Verification (all green):

- `pytest tests/unit/bhava tests/integration/bhava` — **123 passed**
  (full v0.2.0 matrix: config/TOML authority, errors, identity, occupancy,
  planet-house, lordship, ownership, relative-house incl. LAGNA/ASC anchor
  equality, cusps/cusp-proximity orb, aspects, transit/gochar, serialization
  round-trip, provenance, determinism in-process, static gates, JRE-004
  `relative_house` oracle equality, golden fixtures, JSON Schema
  conformance, config echo, cross-process byte determinism, performance).
- `ruff check src tests` — clean; `mypy` strict over `src/bhava` — clean.
- Performance smoke: JRE-005 derivation p95 well under the 5 ms budget
  with the delegated JRE-003 computations (chart + pair geometry)
  computed once per SPEC §30 exclusion.
- JRE-002 / JRE-003 / JRE-004 implementation, tests, datasets untouched
  (empty diffs vs their commits); no `src/astronomy`/`jyotish`/`knowledge`
  changes from this stage.

Doc cleanup within this stage: stale `lord_of` → `sign_lord_of`
references in the JRE-005 docs (rashi/sign lordship only) and the two
non-normative `jyotish.models` CORE references aligned with the
public-API boundary.

### Handoff to QA

QA status is reserved for QA. Do NOT advance this queue item beyond
CODING-COMPLETE by any agent other than QA (when authorized).

## QA Decision (2026-08-14) — Status: QA-PASS

Independent QA verification (separate from CODING): contract/ADR-013..021
alignment, public-API boundary audit (no forbidden imports, no
TYPE_CHECKING bypass), JRE-003 composition (no recomputation), 108-cell
JRE-004 `relative_house` oracle equality across WHOLE_SIGN/PLACIDUS/KOCH,
multi-system isolation, transit/natal separation, unplaced-body RAISE +
labeled fallback (natal and transit), 1,213 complete `DerivationBlock`s,
exact serialization round-trip, in-process + cross-process byte
determinism, performance p95 ≈ 3.27 ms (budget 5 ms), interpretation
boundary clean, full suite 1049 passed, ruff/mypy clean, JRE-002/003/004
byte-identical. **Result: QA-PASS.**

## Validator Decision (2026-08-14) — Status: VALIDATOR-COMPLETE

Independent Validator (challenged, not rubber-stamped): requirement
matrix (41 rows, all PASS or documented), 576-cell oracle equality across
4 different births × 4 house systems (0 mismatches), cusp-proximity
boundary + wrap-around probes, category overlaps, classical sign-lord
table (BPHS ch. 4), ownership partition, exact double serialization
round-trip, cross-process determinism, performance p95 ≈ 3.23 ms (50
samples). Two non-blocking doc inconsistencies found and resolved as
bounded documentation corrections (SPEC §13 `PlanetHouseFact` field list
→ DATA-CONTRACT §4 alignment; SPEC §4 `jyotish.models` → `jyotish public
API`). JRE-002/003/004 byte-identical. **Result: VALIDATOR-PASS —
MERGE-ELIGIBLE.**

### Handoff to MERGE

Merge authorization granted 2026-08-14: one local JRE-005 commit.

### Change history

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-08-14 | Request created; Architect review complete (Status: ARCHITECT-COMPLETE) |
| 0.2.0 | 2026-08-14 | Specialist pinning complete: six resolutions (ADR-017..021), implementation-ready spec v0.2.0 (Status: SPECIALIST-COMPLETE) |
| 0.3.0 | 2026-08-14 | CODING complete per v0.2.0 contract: `src/bhava/` implemented (models, errors, config authority, pure derivations, `BhavaService`, serialization), `config/bhava.toml`, pyproject metadata, full unit+integration suite (123 bhava tests), golden fixtures, cross-process determinism, JRE-004 `relative_house` oracle equality, isolation/static gates, performance smoke (Status: CODING-COMPLETE) |
| 0.4.0 | 2026-08-14 | QA-PASS (independent verification: contract/ADR alignment, public-API boundary, 108-cell oracle equality, provenance, serialization, determinism, perf p95 ≈ 3.2 ms) then VALIDATOR-PASS (independent: 576-cell oracle equality across 4 births × 4 systems, requirement matrix 41 rows, integrity confirmed). Two bounded doc corrections applied: SPEC §13 `PlanetHouseFact` field list aligned with DATA-CONTRACT §4; SPEC §4 `jyotish.models re-exports` → `jyotish public API re-exports` (Status: VALIDATOR-COMPLETE) |

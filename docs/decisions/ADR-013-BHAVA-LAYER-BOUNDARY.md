# ADR-013 — JRE-005 Is a Derived-Fact Layer Consuming JRE-003, Never Recomputing It

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: nothing (extends the JRE-002/JRE-003/JRE-004 layer discipline)
- Decision maker: Architect

## Context

JRE-003 already computes everything geometric about houses: cusps for
six house systems, `Bhava` spans/occupants/lords, lagna, exact-degree
aspects, and transit-through-houses. The JRE-005 objective is a
"bhava/house analytical layer" — but JRE-003's `jyotish.houses` already
exists and is validated. The risk is either (a) duplicating JRE-003
geometry in a new layer, or (b) drawing the new layer so thin it adds no
value. The correct boundary must be explicit.

## Decision

1. **JRE-005 is a derived-fact layer.** It consumes JRE-003 public
   outputs (`NatalChart`, `TransitThroughHouses`, `Bhava`, `LagnaState`,
   `PlanetState`, `AspectRelationship`, catalog versions) and produces
   *derived* house-level facts (relative house, categories, ownership,
   occupancy status, cusp proximity, aspect-to-house aggregation,
   empty-house summaries, provenance blocks).
2. **JRE-005 never recomputes anything JRE-003 emits**: no positions,
   no cusps, no spans, no lagna, no aspect angles, no classification.
   JRE-003 values appear in JRE-005 output only as echoes marked
   `echoed_from` (ADR-016).
3. **New package `src/bhava/`**, importing only the `jyotish` public API
   and stdlib. No `astronomy`, no `knowledge`, no `swisseph`, no network.
4. **JRE-004 compatibility is a testable contract**: the
   `relative_house(<BODY>, <REF>)` fact JRE-005 derives must equal
   JRE-004's snapshot-normalized value for the same chart (ADR-014),
   verified by a cross-layer test using JRE-004 as a read-only oracle.
5. JRE-005 performs **no interpretation** — house categories are emitted
   as membership sets, aspects are geometric echoes, and classical
   interpretive rules (drishti doctrine, bhava karakatva, bala, yogas)
   are explicitly deferred.

Rationale:

- Composition over duplication keeps a single source of truth for all
  astronomical/geometric truth (JRE-003) and a single source for rules
  (JRE-004). Duplicating cusp/geometry math would fork validated,
  deterministic behavior — exactly what the merge discipline forbids.
- A separate `bhava` package (rather than extending `jyotish.houses`)
  preserves JRE-003's validated surface unchanged and gives future
  layers (Dasha/Gochar/Drishti/Yoga/Varga/Synthesis) one stable,
  interpretation-free fact surface.
- The derived facts JRE-005 adds (relative house, categories, ownership,
  empty-house, cusp proximity, aspect-to-house) are exactly the inputs
  classical rules and future engines need, and they are pure arithmetic
  over JRE-003 echoes.

Rejected alternatives:

- **Extend `jyotish.houses` with analytical functions** — modifies the
  merged, validated JRE-003 surface; mixes coordinate state with derived
  analysis; breaks the four-way layer split (JRE-003 = coordinate state,
  JRE-005 = derived state).
- **Recompute houses independently in `bhava`** — duplicates cusp math,
  forks validated behavior, adds a second source of truth.
- **Fold JRE-005 into JRE-004** — JRE-004 is the knowledge/rules layer;
  deriving computational house facts there would couple rules to
  derivation internals and duplicate JRE-003 consumption.

## Consequences

- JRE-002/JRE-003/JRE-004 remain byte-for-byte unchanged; their gates
  and tests are unaffected.
- `pyproject.toml` gains `bhava` + `tests/*/bhava` entries at CODING
  time (build metadata only; no new dependencies).
- Static gates enforce the import boundary (no astronomy/knowledge/
  swisseph/network in `src/bhava`).
- Future engines consume `HouseAnalysisResult` facts; the fact surface
  is extensible only additively.

## References

- [JRE-003 architecture §9 (bhava relationships)](../architecture/JRE-003-JYOTISH-CORE.md)
- [JRE-003 data contract §7 (Bhava/NatalChart)](../architecture/JRE-003-DATA-CONTRACT.md)
- [ADR-002 (adapter placement)](ADR-002-HOUSE-ECLIPSE-ADAPTER-PLACEMENT.md)

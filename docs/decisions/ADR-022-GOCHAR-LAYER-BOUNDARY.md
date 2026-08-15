# ADR-022 — JRE-006 Gochar Layer Boundary: Composition of JRE-003 Transit Primitives and JRE-005 House Facts

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: nothing (extends the JRE-005 ADR-013 boundary discipline to the gochar layer)
- Decision maker: Architect

## Context

Future interpretation layers (dasha, drishti, yoga, synthesis) need
deterministic **gochar facts**: where transiting bodies are, which
deterministic transit events occur in a date range, and how transits
relate to a natal chart. JRE-003 already owns the continuous-transit
event search (ADR-005) and transit-through-houses; JRE-005 already owns
natal-frame transit house facts (ADR-021). Without an explicit
boundary, a "gochar engine" could easily reimplement JRE-003's event
search or drift into interpretation.

## Decision

1. **JRE-006 owns gochar *state facts***: instant gochar state
   (GENERIC), transit-to-natal relationship facts (INDIVIDUAL), and
   deterministic interval facts (echoed event streams + sampled state
   series), plus the reference-point model, pinned event ordering,
   provenance, serialization, and configuration authority.
2. **JRE-006 composes; it never recomputes.** It consumes only the
   public `jyotish` and `bhava` roots plus the standard library. It
   performs no planetary-position, cusp, lagna, geometry, aspect, or
   event-search computation — all are delegated to JRE-003/JRE-005 and
   echoed verbatim.
3. **No type redefinition.** `TransitEvent`, `TransitEventKind`,
   `TransitReferencePoint`, `TransitThroughHouses`, `PlanetState`,
   `PairGeometry`, `TransitHouseFact`, `FactFrame`, etc. are imported
   and reused, never re-declared.
4. **No interpretation.** JRE-006 contains no dasha, prediction, yoga,
   benefic/malefic, auspiciousness, gochar judgement, drishti doctrine,
   rule resolution, or confidence logic. The word "transit" denotes
   structural transit-state handling only.
5. **Forbidden imports.** `astronomy.*`, `jyotish.models`,
   `jyotish.swisseph`, `knowledge.*`, and the Swiss Ephemeris binding
   are rejected, including via `TYPE_CHECKING`.

Rationale:

- Single source of truth per fact (echo discipline proven by ADR-013
  and ADR-021); correctness of all astronomy/Jyotish math remains owned
  by the validated JRE-002/JRE-003 layers.
- The layer adds exactly what is missing: deterministic
  state/interval/relationship facts with provenance — the input
  contract future layers need.

Rejected alternatives:

- **JRE-006 reimplements event search** — duplicates validated,
  ADR-005-pinned computation; rejected.
- **JRE-006 performs interpretation** — that is the future synthesis
  layer's role; rejected.

## Consequences

- `src/gochar/` is a pure composition layer; static boundary tests
  enforce the import and vocabulary rules.
- Provenance must record the actual source layers consumed
  (ADR-028).
- Deferred capabilities that would require non-public JRE-003
  internals are explicitly out of v0.1 scope (ADR-026).

## References

- [JRE-006 architecture core §2–§4](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- [ADR-013](../decisions/ADR-013-BHAVA-LAYER-BOUNDARY.md),
  [ADR-005](../decisions/ADR-005-CONTINUOUS-TRANSIT-ENGINE.md)

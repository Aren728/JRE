# ADR-027 — JRE-006 Eclipse Boundary: Detection Belongs to JRE-007

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: nothing (records the JRE-006/JRE-007 boundary)
- Decision maker: Architect

## Context

The roadmap reserves a future JRE-007 Eclipse Engine. JRE-006's
investigate-list included "eclipses" as a candidate capability; the
boundary must be explicit so JRE-006 neither duplicates eclipse
detection nor silently omits a capability consumers assume it has.

## Decision

1. **JRE-007 (future) owns eclipse detection**: eclipse events,
   contacts (partial/total), classification, and geographic visibility.
2. **JRE-006 performs no eclipse detection** and consumes none of
   `jyotish.eclipses` output in v0.1.
3. **JRE-006 may echo Sun/Moon/node positions** — these are ordinary
   planetary states already present in transit state series and
   `PlanetState`; they are positions, not eclipse facts.
4. **Machine-testable boundary**: JRE-006 production code contains no
   eclipse vocabulary identifiers (`eclipse`, `EclipseKind`,
   `EclipseEvent`, `EclipseContact`, `GeographicVisibility`), enforced
   by the static vocabulary scan.

Rationale:

- Eclipse detection is a distinct, specialized computation (JRE-003
  ADR-006 interface, future JRE-007 provider work); folding it into
  JRE-006 would blur two layers and duplicate future work.
- Sun/Moon/node positions are already first-class transit state; no
  special handling is needed.

Rejected alternatives:

- **JRE-006 echoes `jyotish.eclipses` results** — couples v0.1 to a
  capability whose owning layer is not yet built; rejected.
- **Silent omission** — the boundary is documented and tested instead of
  assumed.

## Consequences

- TEST-PLAN vocabulary scan (row 19) rejects eclipse identifiers in
  `src/gochar`.
- The JRE-007 architecture phase will document consumption of JRE-006
  Sun/Moon/node position echoes.

## References

- [JRE-006 architecture core §16](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- [JRE-006 test plan §2, §6](../architecture/JRE-006-TEST-PLAN.md)
- [ADR-006](../decisions/ADR-006-ECLIPSE-ENGINE-INTERFACE.md)

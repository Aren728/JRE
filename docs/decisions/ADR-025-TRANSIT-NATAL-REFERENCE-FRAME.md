# ADR-025 — Transit-to-Natal Reference Frame: Reuse JRE-003 Reference Points, ASC ≡ LAGNA

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: nothing (extends ADR-019 anchor-frame semantics to the gochar layer)
- Decision maker: Architect

## Context

Transit-to-natal house facts are relative to an anchor. JRE-003 already
defines `TransitReferencePoint` (LAGNA, MOON, SUN, ASC) with pinned
anchor semantics in `transit_through_houses`, and JRE-005 pins the
natal-frame relative-house arithmetic (ADR-014/ADR-019). JRE-006 must
reuse these rather than create competing definitions.

## Decision

1. **Reuse `jyotish.TransitReferencePoint`** — JRE-006 defines no
   reference-point enum of its own; `GocharConfig.reference_point` is a
   `TransitReferencePoint` value.
2. **Anchor semantics identical to JRE-003/JRE-005.** LAGNA and ASC are
   the same absolute-house anchor (house 1); MOON and SUN anchor on the
   natal Moon/Sun rashi. Whole-sign natal-frame house number is
   `((transit_rashi_index − anchor_rashi_index) mod 12) + 1`; cusp-aware
   derivation is JRE-005's, unchanged.
3. **ASC ≡ LAGNA is a hard cross-layer invariant.** For whole-sign
   frames, transit-to-natal facts computed with `reference_point=ASC`
   and `reference_point=LAGNA` agree. Tested in the reference matrix.
4. **JRE-005 equality is a hard cross-layer invariant.**
   `GocharNatalResult.transit_house_analysis` must equal
   `bhava.derive_transit_analysis` output for the same
   `TransitThroughHouses` input.
5. **Unknown reference values** raise the typed
   `UnsupportedReferencePointError` (wrapped as
   `GocharComputationError`), mirroring JRE-003's robust handling.

Rationale:

- One canonical anchor model across layers avoids silent drift between
  JRE-003, JRE-005, and JRE-006 outputs that downstream consumers
  compare.

Rejected alternatives:

- **JRE-006-defined reference enum** — duplicate vocabulary, drift
  risk; rejected.
- **Silently reusing Lagna semantics for cusp frames** — JRE-005
  already resolved this distinction (ADR-019); JRE-006 inherits it.

## Consequences

- Reference-matrix tests pin all four anchors and the ASC ≡ LAGNA
  equality.
- The JRE-005 oracle-equality test pattern (JRE-005 TEST-PLAN) extends
  to JRE-006.

## References

- [JRE-006 architecture core §9](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- [JRE-006 data contract §9](../architecture/JRE-006-DATA-CONTRACT.md)
- [ADR-014](../decisions/ADR-014-RELATIVE-HOUSE-CANONICAL.md),
  [ADR-019](../decisions/ADR-019-ANCHOR-FRAMES-RELATIVE-HOUSE.md)

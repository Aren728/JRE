# ADR-024 — Instant vs Interval Gochar State Model

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: nothing
- Decision maker: Architect

## Context

Gochar consumers query both a single instant ("where is Mars today
against my chart?") and a date range ("which ingresses and stations
occur this year?"). The two shapes must be distinct, deterministic, and
clearly separated, with pinned boundary semantics.

## Decision

1. **Three result shapes.** `GocharInstantResult` (GENERIC: transit
   state ± geometry echo, no birth data), `GocharNatalResult`
   (INDIVIDUAL: transit state + natal echo + transit-to-natal facts),
   and `GocharIntervalResult` (echoed event stream + sampled state
   series + optional natal-frame house series).
2. **Closed-interval semantics.** Interval queries are closed
   `[start_utc_iso, end_utc_iso]`; events at either endpoint are
   included (JRE-003 `events_between` semantics adopted verbatim,
   ADR-023).
3. **Sampling is echo-based.** The interval state series is the JRE-003
   `state_series` echo at a pinned step; JRE-006 performs no
   interpolation.
4. **Natal-frame house series is config-gated.** `natal_house_series`
   defaults `false`; when enabled, JRE-006 samples the natal-frame
   house facts per instant through the public
   `jyotish.transit_through_houses` + `bhava.derive_transit_analysis`
   path. The known cost (natal chart recomputed per sample) is accepted
   in v0.1 and documented as a v0.2 JRE-003 additive-API candidate
   (precomputed-chart reuse).
5. **Instant results never contain interval data and vice versa.** The
   shapes are distinct; mixed queries are invalid requests.

Rationale:

- Distinct shapes keep the no-birth-data guarantee of GENERIC results
  structurally enforceable.
- Echo-based sampling inherits JRE-003's validated determinism and
  avoids inventing interpolation semantics.
- Gating the expensive house series keeps v0.1's performance contract
  honest.

Rejected alternatives:

- **Single universal result with nullable fields** — weakens the
  GENERIC no-birth-data guarantee; rejected.
- **Interval house series always on** — unbounded cost; rejected.

## Consequences

- Data contract pins the three shapes with `additionalProperties=false`
  (DATA-CONTRACT §4).
- Performance smoke excludes the delegated JRE-003/JRE-005 computation
  (CORE §15).

## References

- [JRE-006 architecture core §5, §11](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- [JRE-006 data contract §4](../architecture/JRE-006-DATA-CONTRACT.md)

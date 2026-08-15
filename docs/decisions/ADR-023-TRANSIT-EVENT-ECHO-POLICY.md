# ADR-023 — Transit Event Echo Policy: Verbatim Echo, Re-asserted Pinned Ordering

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: nothing
- Decision maker: Architect

## Context

JRE-003's `events_between` already returns a deterministic, sorted
event tuple (`TransitEvent` with `SearchMetadata`), produced by the
ADR-005 bisection engine. JRE-006's interval result must expose these
events without duplicating the search and without silently changing
their semantics or ordering.

## Decision

1. **Verbatim echo.** JRE-006's interval `events` field is the
   `TransitEvent` tuple returned by `jyotish.events_between`, copied
   value-for-value. No re-derivation, no re-timestamping, no
   re-classification.
2. **Re-asserted pinned ordering.** JRE-006 applies the pinned sort key
   `(event_julian_day_ut, body.value, kind.value)` with a stable sort.
   For JRE-003 output this is identity-preserving; it guarantees the
   ordering contract even if the upstream stream were ever unsorted.
   Ties at identical `(jd, body, kind)` keep their source-stream
   relative order (stable), which is deterministic because the source
   stream is deterministic.
3. **Event identity is the echoed tuple.** JRE-006 defines no competing
   event type; consumers read `TransitEvent` fields directly.
4. **Boundary semantics adopted verbatim** (closed interval,
   exact-on-boundary `f0 == 0.0` handling, retrograde re-crossings as
   separate events, `boundary_deg` normalized `[0, 360)` with `0.0` for
   360°→0°).
5. **Provenance.** Each echoed stream carries a `GocharProvenance`
   whose `algorithm` documents `"echo-jre003-events-bisection"` and
   whose `input_echo` records the queried interval, bodies, and config.

Rationale:

- JRE-003 is the validated owner of event semantics (ADR-005); any
  re-derivation risks divergence and defeats the single-source-of-truth
  discipline.
- The pinned sort re-assertion makes the ordering contract explicit and
  machine-testable without changing behavior.

Rejected alternatives:

- **JRE-006 event type mirroring `TransitEvent`** — duplicate type,
  drift risk; rejected.
- **Trusting upstream order without re-assertion** — the contract would
  silently depend on an implementation detail; rejected.

## Consequences

- Cross-layer echo identity is a hard validator gate
  (DATA-CONTRACT §9.1): JRE-006 serialized events byte-equal JRE-003's.
- Ordering tests cover simultaneous events and exact-boundary events.

## References

- [JRE-006 architecture core §5–§6](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- [JRE-006 data contract §4.4, §9](../architecture/JRE-006-DATA-CONTRACT.md)
- [ADR-005](../decisions/ADR-005-CONTINUOUS-TRANSIT-ENGINE.md)

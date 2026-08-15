# ADR-026 — Deferred Gochar Capabilities and Their Additive JRE-003 API Proposals

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: nothing
- Decision maker: Architect

## Context

Three gochar capabilities are natural extensions of v0.1 but cannot be
built **correctly** from the current public JRE-003/JRE-005 APIs without
either reaching into private internals (FORBIDDEN_WORKAROUND) or
duplicating validated computation. Per the architecture principle
"do not work around a missing API; record it", they are deferred to
v0.2 with additive-API proposals, and the limitations are made explicit
and machine-testable.

## Decision

1. **Generic (natal-free) transit chart — deferred to v0.2.**
   - Requirement: transit lagna and transit houses at an instant +
     location without birth data (a "today's gochar chart").
   - Missing: JRE-003 computes houses/lagna only inside
     `chart()` (birth-anchored); `JyotishService._house_cusps` and the
     lagna/house assembly are internal.
   - Proposal: additive public
     `JyotishService.instant_chart(date, time, timezone, latitude,
     longitude, config) -> InstantChart` (or an `InstantChart` reuse of
     the existing `_house_cusps` + `compute_bhavas` + `derive_lagna`
     path) — a JRE-003 additive correction, no behavior change.
   - v0.1 limitation (machine-testable): GENERIC gochar covers state
     (positions + classification + events) only; any request for a
     natal-free transit *chart* is an invalid request.
2. **Cusp-based house-ingress events over time — deferred to v0.2.**
   - Requirement: "transit body crosses a natal cusp" events.
   - Missing: `events_between` searches fixed arcs only (rashi 30°,
     nakshatra 13°20′, pada 3°20′); natal cusp longitudes are arbitrary
     fixed boundaries not addressable by the public API.
   - Proposal: additive
     `JyotishService.crossings_between(start, end, bodies,
     boundaries_deg, config)` (generalizes the ADR-005 bisection to
     caller-supplied boundaries) or a `HOUSE_INGRESS` kind with a
     boundary set — a JRE-003 additive correction.
   - v0.1 limitation (machine-testable): natal-frame house facts are
     **state at sample instants** (via JRE-005), never cusp-crossing
     events.
3. **Continuous transit aspect events (applying/exact/separating) —
   deferred to v0.2.**
   - Requirement: exact timestamps when a transit–transit or
     transit–natal angular separation crosses an aspect angle.
   - Missing: JRE-003 provides instant `pair_geometry` only; no public
     root-finding over the separation function.
   - Proposal: additive `JyotishService.aspect_events_between(...)`
     (separation root-finding on JRE-003-owned geometry), or a
     documented JRE-006-internal search over `state_series` echoes —
     Specialist decision required.
   - v0.1 limitation (machine-testable): only instant aspect echoes are
     exposed; `aspect_echo=false` disables them.

No v0.1 requirement depends on a deferred capability; v0.1 is
CODING-READY on the current public API (CORE §4.4).

Rationale:

- Correctness and the public-API boundary outrank completeness: an
  approximate or internal-import implementation would violate ADR-013
  discipline and risk divergence from JRE-003's validated semantics.
- Deferral is recorded, not forgotten: each proposal is a bounded,
  additive JRE-003 correction that a later authorization can approve
  (the JRE-005 `sign_lord_of` / `BodyId` precedent).

Rejected alternatives:

- **Reaching into JRE-003 internals for v0.1** — FORBIDDEN_WORKAROUND;
  rejected.
- **Approximate event semantics** — the architecture forbids inventing
  approximate event semantics for convenience; rejected.

## Consequences

- TEST-PLAN rows assert the v0.1 limitations are machine-testable
  (invalid-request behavior, state-not-events, echo-only aspects).
- The JRE-006 Specialist spec must pin the exact limitation messages.

## References

- [JRE-006 architecture core §2.2, §4.4](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- [JRE-006 test plan §2](../architecture/JRE-006-TEST-PLAN.md)

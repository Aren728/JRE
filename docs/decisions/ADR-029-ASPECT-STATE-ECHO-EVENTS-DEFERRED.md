# ADR-029 — Aspect State Is Echoed; Aspect Perfection Events Are Deferred to v0.2

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-006 Gochar / Continuous Transit Engine](../architecture/JRE-006-GOCHAR-TRANSIT-ENGINE.md)
- Supersedes: refines [ADR-026](../decisions/ADR-026-DEFERRED-GOCHAR-CAPABILITIES.md) item 3
- Decision maker: Specialist

## Context

The JRE-006 architecture deferred "continuous aspect events
(applying/exact/separating)". The Specialist review established that
JRE-003's public `pair_geometry` already provides instant **aspect
state** including `ApplyingSeparating` (APPLYING / SEPARATING / NONE,
closed-form from ecliptic-arc separation and longitude speeds). The
boundary between what JRE-006 echoes (state) and what it defers
(perfection **event timestamps**) must be pinned so consumers know
exactly what v0.1 delivers.

## Decision

1. **Aspect state is echoed in v0.1.** `GocharNatalResult.transit_to_natal_aspects`
   (and `GocharInstantResult.pair_geometry` for transit-transit) carry
   the full JRE-003 `PairGeometry` echo, including `AspectKind` and
   `ApplyingSeparating`. "Applying/separating" in v0.1 means the
   **instantaneous state** JRE-003 computes — never an event.
2. **Aspect perfection events are deferred to v0.2.** Exact timestamps
   of entering an orb, perfecting an aspect, or leaving it require
   root-finding over the angular-separation function of two bodies,
   which no current public API provides. The v0.1 limitation is
   machine-testable: `GocharIntervalResult` contains no aspect-event
   kind, and instant results carry aspect state only.
3. **No orb of JRE-006's own.** Aspect detection orb is JRE-003's
   pinned `pair_geometry` semantics; JRE-006 adds none.
4. **Recommended v0.2 additive API** (refines ADR-026 item 3):
   `JyotishService.aspect_events_between(start, end, body_a, body_b,
   aspect_kinds, config)` — JRE-003-owned separation root-finding over
   its own geometry, so JRE-006 never implements root-finding itself.

Rationale:

- JRE-003 owns aspect geometry (ADR-004); echoing its state preserves a
  single source of truth, and deferring event timestamps avoids
  implementing unowned numerical search.
- The distinction (state vs event) is exactly the boundary consumers
  need: v0.1 answers "is this aspect applying now?", v0.2 answers
  "when does it perfect?".

Rejected alternatives:

- **JRE-006 implements separation root-finding in v0.1** — new,
  unowned numerical code with tolerance decisions; violates the
  echo-don't-recompute discipline; rejected.
- **Treating applying/separating as an event in v0.1** — the
  `ApplyingSeparating` value is instant state, not a timestamped
  crossing; conflating them would mislead consumers; rejected.

## Consequences

- SPEC §15 pins aspect-state echo; TEST-PLAN §2 rows 17-18 assert the
  state echo and the deferral.
- The data contract §4.3 documents `transit_to_natal_aspects` as state
  echo.

## References

- [JRE-006 specialist spec §15](../architecture/JRE-006-SPECIALIST-SPEC.md)
- [JRE-006 data contract §4.3](../architecture/JRE-006-DATA-CONTRACT.md)
- [ADR-026](../decisions/ADR-026-DEFERRED-GOCHAR-CAPABILITIES.md),
  [ADR-004](../decisions/ADR-004-CONJUNCTION-ASPECT-SEMANTICS.md)

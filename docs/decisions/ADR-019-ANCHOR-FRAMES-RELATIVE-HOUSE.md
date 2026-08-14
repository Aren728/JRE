# ADR-019 — Relative-House Anchor Frames: `HOUSE_OCCUPANCY` Now, Sign-Grid Explicitly Deferred

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: architecture draft §15 ASC wording ("cusp-frame ASC anchor
  is a future additive vocabulary addition" — now pinned precisely)
- Decision maker: Specialist

## Context

The question: how is `relative_house` anchored in cusp-based systems,
and does JRE-005 silently reuse whole-sign/lagna semantics? JRE-004
pins `ASC == LAGNA` in its snapshot. JRE-005 must anchor precisely,
preserve the JRE-004 equality contract, and make any deferred capability
explicit and machine-testable.

## Decision

1. **Anchor frame = `HOUSE_OCCUPANCY`** (sole supported frame in
   v0.2.0): absolute house numbers come from the chart's bhava
   occupancy in the chart's house system. In cusp systems this is
   genuinely cusp-anchored — the numbers come from the cusp bhavas, not
   from the sign grid. There is **no silent reuse of whole-sign
   counting** for placed bodies; the only whole-sign arithmetic is the
   explicit, config-gated fallback (ADR-018).
2. **References resolve in that frame**: `LAGNA` → 1 (house 1 is
   ascendant-anchored in every system); `MOON`/`SUN` → the body's
   absolute house; `ASC` → 1. `ASC ≡ LAGNA` is the JRE-004-compatible
   pin (both mean "the chart's house-1/ascendant house").
3. **Sign-grid anchoring is explicitly deferred and machine-testable**:
   - `RelativeHouseFrame` enum has only `HOUSE_OCCUPANCY`; any other
     value → `InvalidBhavaConfigError`;
   - public constant `SIGN_GRID_FRAME_SUPPORTED = False`;
   - `ChartEcho.anchor_frame == "HOUSE_OCCUPANCY"` and
     `ChartEcho.sign_grid_frame_supported == false` on every result;
   - tests pin the constant, the echo, and the enum error.
   Enabling it later is an additive, versioned change (enum member +
   derivation + `derivation_version` bump); it never alters the
   `HOUSE_OCCUPANCY` contract or JRE-004 equality.
4. **JRE-004 equality preserved** for the supported frame: for every
   body/reference in {LAGNA, MOON, SUN, ASC} and every house system,
   JRE-005 equals JRE-004's `normalize_snapshot` oracle (ADR-014).

Rationale:

- Occupancy anchoring is the only frame consistent with JRE-004's
  validated snapshot semantics; anything else would fork rule outcomes.
- Explicit deferral (flag + frame echo + enum error) makes the
  limitation a machine-checkable fact rather than prose.
- The classical sign-counting convention remains available as a
  future additive frame without disturbing the JRE-004 contract.

Rejected alternatives:

- **Silently treat ASC as sign-counting from the ascendant rashi** —
  would break JRE-004 equality and hide the semantic choice.
- **Pre-declare an unused `SIGN_GRID` enum member now** — a phantom
  value with no derivation invites misuse; the capability flag is
  sufficient and honest.
- **Make cusp systems use sign-grid anchoring** — forks the layers and
  contradicts the occupancy echo discipline (ADR-013).

## Consequences

- `ChartEcho` carries `anchor_frame` + `sign_grid_frame_supported`;
  tests pin the limitation (TEST-PLAN §5a).
- Future work: sign-grid frame, and possibly per-reference custom
  frames — additive and versioned.

## References

- [ADR-014 (JRE-004 oracle)](ADR-014-RELATIVE-HOUSE-CANONICAL.md)
- [JRE-005 architecture §15, §30.3](../architecture/JRE-005-BHAVA-CORE.md)
- [JRE-005 specialist spec §11](../architecture/JRE-005-SPECIALIST-SPEC.md)

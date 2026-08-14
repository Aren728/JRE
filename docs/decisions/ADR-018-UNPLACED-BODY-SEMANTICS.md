# ADR-018 — Unplaced-Body Semantics: No Silent Fallback

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: architecture draft §11 fallback phrasing ("robustness pin")
- Decision maker: Specialist

## Context

A body may not fall inside any bhava span of a provider cusp system
(e.g. extreme-latitude Placidus pathologies or inconsistent input
charts). JRE-004's snapshot normalization has a robustness path
(whole-sign fallback) that is pinned for its own layer. JRE-005 must
define exact behavior — silent fallback would hide a genuine
computational anomaly and could disagree with JRE-004's semantics in
subtle ways.

## Decision

1. **No silent fallback.** `BhavaConfig.unplaced_body_behavior`
   (enum, default `RAISE`):
   - `RAISE` (default): an unplaced body raises `UnplacedBodyError`
     (message includes body id, `longitude_used`, house system).
     Serialization never produces a fabricated house.
   - `WHOLE_SIGN_FALLBACK` (explicit opt-in): the whole-sign house from
     the lagna rashi is used **and labeled**: `house_rule ==
     "PLANET_HOUSE_WHOLE_SIGN_FALLBACK"` on the fact, with the fallback
     inputs recorded in `derivation.inputs`. Never silent.
2. **The two behaviors produce different, documented outputs**; the
   active behavior is echoed in `ChartEcho.unplaced_body_behavior` and
   in every `DerivationBlock`.
3. **JRE-004 oracle equality** holds in both modes for real JRE-003
   charts (spans partition the ecliptic → no unplaced bodies); for
   synthetic unplaced cases the oracle test runs with
   `WHOLE_SIGN_FALLBACK` (matching JRE-004's robustness path).
4. The unplaced condition is detected only by **occupancy echo**
   (no bhava contains the body); it is never inferred from geometry.

Rationale:

- Silent fallback hides anomalies and forks fact provenance; raising
  makes inconsistency loud and auditable.
- The explicit opt-in preserves JRE-004 parity for the synthetic cases
  where JRE-004's robustness path would engage, with full labeling.

Rejected alternatives:

- **Always fallback silently** — hides anomalies; contradicts the
  explicit-variation/provenance discipline (ADR-016).
- **Always raise** — breaks the JRE-004 oracle-parity path for synthetic
  charts; the opt-in knob is the middle ground.
- **Infer the "correct" span from adjacent cusps** — recomputes geometry
  (forbidden, ADR-013).

## Consequences

- `UnplacedBodyError` added to the taxonomy; TEST-PLAN §5a covers both
  modes.
- Real JRE-003 charts never trigger the path (documented invariant).

## References

- [JRE-005 architecture §18, §30.6](../architecture/JRE-005-BHAVA-CORE.md)
- [JRE-005 specialist spec §18](../architecture/JRE-005-SPECIALIST-SPEC.md)
- [ADR-014 (JRE-004 oracle)](ADR-014-RELATIVE-HOUSE-CANONICAL.md)

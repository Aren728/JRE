# ADR-004 — Conjunction and Aspect Semantics: Exact Angular Geometry

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-003 Jyotish Coordinate and State Layer](../architecture/JRE-003-JYOTISH-CORE.md)
- Decision maker: Architect

## Context

JRE-003 requirement B mandates planet-to-planet geometry and explicitly warns:
**"Do NOT define conjunction merely as 'same house'. Preserve exact angular
separation."** This forces a design decision about what "conjunction" and
"aspect" mean at the fact layer, and where the classical sign-based drishti
rules belong.

## Decision

1. **The primitive is exact angular separation.**
   - `separation_deg`: great-circle separation on the ecliptic sphere
     (latitude included): `acos(sinβ1·sinβ2 + cosβ1·cosβ2·cos(λ1−λ2))`, in
     `[0, 180]`.
   - `normalized_separation_deg`: ecliptic arc `(λ2 − λ1) mod 360`, `[0, 360)`.
2. **Conjunction is an orb decision on exact separation**, not a bucket test:
   `conjunction = (separation_deg ≤ conjunction_orb_deg)`. The exact distance
   is always preserved (`conjunction_distance_deg == separation_deg`).
   `same_rashi` and `same_bhava` are separate boolean facts — two bodies in
   the same house with a 25° gap are **not** conjunct, and two bodies 2°
   apart in different houses **are**.
3. **Aspects are exact-degree kinds with per-kind orbs.** Each pair is
   checked against the ideal angles (0/60/90/120/150/180) with explicit
   per-kind orbs from `JyotishConfig.aspect_orbs_deg`;
   `distance_from_exact_deg` records the exact angular distance from the
   ideal, `within_orb` records the orb decision, and the orb used is echoed.
   No orb is hidden (requirement J).
4. **Applying/separating is derived from relative motion** (sign of the
   time-derivative of the separation, computed deterministically from the two
   bodies' `speed_longitude`), not from house or rashi progression.
5. **Classical sign-based drishti rule tables (e.g. Jupiter's 5/7/9,
   Mars 4/8, Saturn 3/10) are NOT computed in JRE-003.** They are rules for
   the future Rules layer, which will operate on the exact-angular facts
   JRE-003 provides. Computing them here would conflate the fact layer with
   the rule layer (requirement I).

Rationale:

- The request's explicit warning makes exact separation the non-negotiable
  primitive; bucketing it away would break the continuous model (E).
- Degree-based aspects with explicit orbs are deterministic, independently
  verifiable geometry — the right content for a fact layer.
- Sign-based drishti embeds interpretation-layered rule choices; deferring it
  keeps JRE-003 interpretation-free and keeps the Rules layer free to version
  drishti tables independently.

Rejected alternatives:

- **Conjunction = same house / same rashi** — explicitly prohibited by the
  request and scientifically wrong (loses angular information).
- **Rashi-count aspects only** (e.g. "7th from each other") — this is the
  drishti rule system, deferred per above.
- **Single global orb for all aspects** — hides per-aspect configuration;
  violates J (no hidden defaults).

## Consequences

- `PairGeometry` always carries both the exact separation and the
  classification flags; consumers can never observe a "conjunction" without
  its exact distance.
- Default orbs (conjunction 8.0°, per-aspect table in `config/jyotish.toml`)
  are proposed values; the Specialist confirms against Jyotish convention and
  records them as versioned config (architecture §25.2). Changing an orb
  never changes the separation facts — only the boolean decisions — so
  geometry remains stable across orb policy changes.
- Validation of geometry is pure math (round-trip spherical identity) plus
  cross-checks with an independent implementation (TEST-PLAN §12).
- Future Drishti layer consumes `PairGeometry` unchanged.

## References

- [JRE-003 Architecture §8, §15](../architecture/JRE-003-JYOTISH-CORE.md)
- [JRE-003 Data Contract §5–§6](../architecture/JRE-003-DATA-CONTRACT.md)

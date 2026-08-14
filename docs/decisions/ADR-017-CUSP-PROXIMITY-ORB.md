# ADR-017 — Cusp-Proximity Orb: Wrap-Aware Arc, Inclusive Boundary, One Config Value

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: nothing (resolution of architecture §30.1)
- Decision maker: Specialist

## Context

JRE-005 emits which bodies sit "near a house cusp" (classical bhava
sandhi). The classical tradition describes the concept of a planet at
the junction of two bhavas but does **not** pin a numeric orb — no verse
is cited here (no fabricated citations). The orb therefore needs an
explicit computational definition: exact math, boundary behavior, and
whether the value is configuration, house-system-specific, or
tradition-specific.

## Decision

1. **Exact math** (normative): shortest angular arc, wrap-aware —
   `arc(a, b) = min(|a−b|, 360 − |a−b|)`. A body is cusp-proximate to a
   house when `arc(longitude_used(body), start) ≤ orb` or
   `arc(longitude_used(body), end) ≤ orb`.
2. **Boundary behavior**: inclusive at exactly `orb`; a body exactly on
   a cusp (`arc == 0`) is cusp-proximate (it is an occupant of the house
   opening there under the half-open `[start, end)` span rule).
3. **Configuration, not house-system-specific**: one
   `cusp_proximity_orb_deg` value per analysis applies to every house
   system in `house_systems`. The orb measures distance to a cusp point;
   the *positions* of cusp points are system-specific (from JRE-003),
   the orb is not. House-system-specific orbs are a possible future
   additive extension, not a v0.2.0 feature.
4. **Tradition-variable in practice, pinned default**: different schools
   use different orbs; JRE-005 pins `3.0°` as the default, declared in
   `config/bhava.toml` (no hidden default), validated `0 < orb < 30.0`.
   An orb ≥ 30° would make every body cusp-proximate to some cusp in
   whole-sign bhavas — degenerate and rejected.
5. The fact is **computational** (a distance measurement); "near the
   cusp ⇒ strong/weak" is interpretive and deferred.

Rationale:

- Wrap-aware shortest arc is the only rotation-invariant distance on the
  ecliptic; naive `|a−b|` breaks at 0°/360°.
- A single config value keeps the semantics auditable and deterministic;
  per-system orbs would multiply knobs without a classical basis.
- Explicit default + range validation satisfies the no-hidden-default
  rule and bounds degenerate configurations.

Rejected alternatives:

- **5.0° default** (a common modern convention) — arbitrary; 3.0° is
  pinned and the knob is exposed; both are modern conventions, the
  pinned default is a versioned decision.
- **Per-house-system orbs** — no classical basis; more knobs, same
  concept; deferred as additive.
- **No proximity fact** — rules and future engines need the distance
  fact; omitting it would push geometry into the rules layer.

## Consequences

- `DerivedHouseFact.cusp_proximate_bodies` per §19 of the specialist
  spec; `arc` is a pure function with boundary tests (TEST-PLAN §5a).
- `ChartEcho.cusp_proximity_orb_deg` echoes the value used.

## References

- [JRE-005 architecture §18, §30.1](../architecture/JRE-005-BHAVA-CORE.md)
- [JRE-005 specialist spec §19](../architecture/JRE-005-SPECIALIST-SPEC.md)

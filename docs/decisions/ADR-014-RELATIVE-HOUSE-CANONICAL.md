# ADR-014 — Canonical `relative_house` Derivation in JRE-005 (JRE-004-Compatible)

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: nothing (JRE-004's FACT_VOCABULARY v1.1.0
  `relative_house(<BODY>, <REF>)` semantics remain normative; JRE-005
  makes the derivation canonical and additive)
- Decision maker: Architect

## Context

JRE-004's fact vocabulary exposes `relative_house(<BODY>, <REF>)` with
`<REF> ∈ {LAGNA, MOON, SUN, ASC}` (SPEC §6.2, ADR-012). JRE-004's
snapshot normalization (`synthesis.normalize_snapshot`) computes the
value ad hoc: absolute house from chart occupancy with a whole-sign
fallback from the lagna rashi, then `((house − anchor) mod 12) + 1` per
reference; `ASC` is pinned equal to `LAGNA` in the whole-sign frame.

JRE-005's mandate is derived house facts — relative house is the most
important one. Two layers computing the same fact must never disagree.

## Decision

1. **JRE-005 is the canonical provider of `relative_house`** for its
   chart inputs, with the exact pinned formula:

   ```
   whole_sign_house(b) = ((rashi_index(planet(b).rashi)
                           − rashi_index(chart.lagna.rashi)) mod 12) + 1
   house_of[b]  = occupancy house from chart.bhavas, else whole_sign_house(b)
   house_of[LAGNA] = 1
   relative_house(B, R) = ((house_of[B] − house_of[R]) mod 12) + 1
   ```

2. **Equality with JRE-004 is a hard contract**: for every body B and
   reference R ∈ {LAGNA, MOON, SUN, ASC}, JRE-005's value equals JRE-004's
   `normalize_snapshot` value for the same `NatalChart`. A cross-layer
   regression test asserts this using JRE-004 as a read-only oracle
   (JRE-004 is NOT modified).
3. **`ASC` equals `LAGNA`** in the whole-sign frame (JRE-004's pin).
   A cusp-frame `ASC` anchor is a **future additive** vocabulary
   addition: extend the reference enum, add the derivation, bump
   `FACT_VOCABULARY_VERSION` / `derivation_version`; existing facts and
   rules are unaffected.
4. **The absolute house of the reference body is emitted** alongside each
   relative value (provenance echo), so consumers can audit the anchor.
5. **No silent counting convention**: the reference is an explicit
   parameter everywhere (LAGNA default is pinned and echoed, never
   inferred).

Rationale:

- The occupancy-first/whole-sign-fallback rule matches the validated
  JRE-004 semantics exactly; a different convention (e.g. pure
  whole-sign counting, or cusp-bhava counting) would fork the layers and
  silently change rule outcomes for identical conditions.
- Pinning the formula prevents drift: both layers derive from the same
  JRE-003 chart and the same arithmetic, so any JRE-003 change is
  observed identically by both.
- Additivity preserves the JRE-004 rule-authoring contract (existing
  catalogs keep their semantics).

Rejected alternatives:

- **Pure whole-sign counting for JRE-005** — disagrees with JRE-004's
  occupancy-based snapshot for cusp systems; would break rule
  equivalence.
- **Cusp-bhava counting as the default** — changes `ASC` semantics vs
  JRE-004's pin; cusp-frame anchors are additive, not a silent default.
- **Keep the derivation only in JRE-004** — JRE-005's mandate is derived
  house facts; leaving relative house in JRE-004's ad-hoc normalization
  denies downstream layers (Dasha/Gochar/Yoga) a stable fact surface.

## Consequences

- `HouseAnalysis.relative_house_table` mirrors JRE-004's
  `relative_houses` snapshot shape exactly.
- A cross-layer regression test ships with JRE-005 (TEST-PLAN §10).
- Future reference anchors (e.g. ARUDHA, Ghati, cusp-frame ASC) are
  additive enum extensions with their own derivation rules.

## References

- [JRE-004 specialist spec §6.2/§6.3](../architecture/JRE-004-SPECIALIST-SPEC.md)
- [ADR-012 (fact vocabulary derived facts)](ADR-012-FACT-VOCABULARY-DERIVED-FACTS.md)
- [JRE-005 architecture §15](../architecture/JRE-005-BHAVA-CORE.md)

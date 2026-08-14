# ADR-021 — Gochar Scope v0.2.0: Derived House Facts for Transiting Bodies, No Interpretation

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: nothing (resolution of architecture §30.4)
- Decision maker: Specialist

## Context

Gochar (transit) analysis needs house-level facts about transiting
planets relative to a natal chart. JRE-003 already provides
`TransitThroughHouses` (per-transit-body natal house, rashi, lord,
occupants, aspects) and transit *events* (ingress/egress/stations).
JRE-005 must define exactly what it consumes and derives without
becoming a transit interpretation engine.

## Decision

1. **Consumed from JRE-003 `TransitThroughHouses`** (echoed, never
   recomputed): `reference`, `transit_instant_utc_iso`, `entries`
   (`natal_house_number`, `natal_house_rashi`, `natal_house_lord`,
   `natal_occupants`, `aspects_to_natal`), `planet_states` (only `body`
   and `longitude_used` are read for anchoring), `birth_snapshot`,
   `config`.
2. **Derived**: `TransitHouseFact` per transiting body (frame `TRANSIT`)
   — echoed entry fields plus `relative_house_by_reference` computed in
   the **natal frame** (absolute house of the transiting longitude via
   `bhava_containing_longitude` on the natal chart's bhavas, JRE-003
   public API; same §18 fallback gating; relative house per the §11.2
   formula). The **natal chart is a required input** to
   `analyze_transit` (the `TransitThroughHouses` result does not embed
   the natal bhavas); missing it → `InvalidAnalysisRequestError`.
3. **Separation**: transit facts (`frame: TRANSIT`) and natal facts
   (`frame: NATAL`) are distinct fact sets, never merged. Both carry
   full provenance (`TRANSIT_HOUSE_ECHO` / `TRANSIT_RELATIVE_HOUSE`).
4. **Explicitly NOT in scope**: transit *events* (ingress/egress/
   stations are JRE-003 facts — JRE-005 does not compute or aggregate
   them), any statement about what a transit "means", dasha/gochar
   effects, or predictions. JRE-005 produces facts only; interpretation
   belongs to JRE-004 rules / future synthesis.

Rationale:

- Echoing JRE-003's entries keeps a single source of truth (ADR-013);
  the only derivation added is the natal-frame relative house, which is
  the fact future Gochar interpretation needs.
- Requiring the natal chart makes the derivation explicit and auditable
  rather than partially derived from an opaque transit result.

Rejected alternatives:

- **Full mirror of the natal fact set for transits** — larger surface
  with no validated consumer in v0.2.0; the echo+relative-house scope is
  the minimal correct slice; extending is additive.
- **Deriving house numbers from transit events** — events are instants,
  not placement facts; would duplicate JRE-003 transit logic.
- **No transit support** — Gochar is a mandated future consumer
  (architecture §28); the interface must exist now.

## Consequences

- `TransitHouseAnalysis` + `TransitHouseFact` added to the data contract
  (§7a); `transit_request_from_dict` validates on construction.
- TEST-PLAN §5a/§12 cover echo fidelity, natal-frame derivation, and
  frame separation.

## References

- [JRE-005 architecture §28, §30.4](../architecture/JRE-005-BHAVA-CORE.md)
- [JRE-005 specialist spec §22](../architecture/JRE-005-SPECIALIST-SPEC.md)
- [JRE-003 transit-through-houses contract](../architecture/JRE-003-DATA-CONTRACT.md)

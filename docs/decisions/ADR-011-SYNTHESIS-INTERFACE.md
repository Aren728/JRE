# ADR-011 — Synthesis Interface

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-004 Classical Knowledge & Rule Engine](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- Decision maker: Architect

## Context

JRE-004's output is consumed by future engines (Drishti, Yoga, Dasha,
Gochar/Nakshatra interpretation, multi-layer synthesis, prediction/
confidence). Those engines do not exist yet, so the interface they will build
against must be defined now, be deterministic, and expose everything a
consumer needs to audit a result — the rules, their order, their provenance,
and any conflicts — while hiding catalog internals.

## Decision

1. **One public facade: `KnowledgeService`** with `synthesize(query) ->
   `SynthesisResult`` plus registry queries (`sources()`, `profiles()`,
   `get_profile()`, `rule_catalog_versions()`). This is the only surface
   future engines import; no other module reads catalog files.

2. **`SynthesisResult` is a complete, self-describing envelope:**

   - `query` — exact echo of the `RuleQuery` (including `fact_snapshot`);
   - `profile` — the resolved `TraditionProfile` (identity + version +
     priority order + policy);
   - `matched_rules` — ordered by precedence (ADR-010);
   - `suppressed_rules` — present when `FIRST_WINS` suppressed any rule;
   - `conflicts` — every `ConflictRecord`, never silently elided;
   - `provenance_index` — rule_id → canonical provenance strings (ADR-008);
   - `config` + `search_metadata` — config snapshot and determinism echo
     (catalog versions, rule counts, algorithm name).

3. **Determinism is a contract.** Identical `(query, profile version,
   source catalog version, rule catalog versions, config)` ⇒ byte-identical
   JSON. Cross-process determinism is tested (TEST-PLAN §4).

4. **The interface never interprets.** `SynthesisResult` returns rules and
   metadata; it contains no verdict, score, or recommendation. Future engines
   add interpretation by consuming this contract — no JRE-004 change.

5. **Catalog loading is internal.** Catalogs load once at construction,
   checksum-verified, immutable; version pins are echoed so a consumer can
   reproduce the exact catalog set.

Rationale:

- A complete, self-describing result means the future engines can be written
  and validated against a stable contract before they exist, and every
  consumer can audit *which* rule, *from where*, *in which tradition*, and
  *against what it lost*.
- "No interpretation in the interface" preserves the hard boundary while
  still shipping the rule content interpretation engines need.

Rejected alternatives:

- **Exposing catalog readers to consumers** — couples engines to file
  layout and versioning internals.
- **Minimal result (rules only)** — hides precedence rationale, conflicts,
  and provenance, making results unauditable.

## Consequences

- Consumers code against `SynthesisResult` only; catalogs may be reorganized
  without breaking them.
- QA validates schema conformance of the envelope (JSON Schema per
  DATA-CONTRACT §10–§11).
- VALIDATOR can audit provenance cross-references offline.

## References

- [JRE-004 Architecture §13](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- [JRE-004 Data Contract §7–§8](../architecture/JRE-004-DATA-CONTRACT.md)
- [JSP-001 Layers 3 and 5](../../specifications/core/JSP-001.md)

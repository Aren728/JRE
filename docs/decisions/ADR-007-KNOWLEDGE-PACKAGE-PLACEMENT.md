# ADR-007 — Knowledge Package Placement and Boundary

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-004 Classical Knowledge & Rule Engine](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- Decision maker: Architect

## Context

JRE-004 (Classical Knowledge & Rule Engine) must sit above JRE-002
(astronomy) and JRE-003 (jyotish facts) and below future interpretation
engines, without modifying the astronomical core. The repository's static
gates already reserve the names `knowledge`, `rules`, `inference`,
`calculations`, `transits`, `dasha`, `astrology` as forbidden imports from
`astronomy` and `jyotish` — anticipating exactly this layer. JSP-001 layers 3
(Knowledge) and 5 (Rules) both belong to this task. The question: where does
the code live, and what may it import?

## Decision

1. **One new package `src/knowledge/`** (import name `knowledge`) implements
   both the Knowledge (source registry, provenance, rule schema) and Rules
   (profiles, precedence, conflict, synthesis) capabilities of this task.
   They share catalogs, configuration, and the facade; separating them into
   two packages now would add boundary ceremony without a consumer.
2. **Dependency direction is strictly downward:**
   - `knowledge` may import **only** stdlib and `jyotish`'s **public API**
     (models/enums used by the fact vocabulary and result types).
   - `knowledge` must **never** import `astronomy`, `swisseph`,
     `astronomy.swisseph`, `inference`, `astrology`, `transits`, `dasha`,
     `calculations`, or `gochar`.
   - `jyotish` and `astronomy` never import `knowledge` (already enforced by
     their existing static gates; unchanged).
3. **Rules are data, not code.** Rule catalogs live under
   `datasets/knowledge/rules/` and are validated by the schema; the engine
   never contains per-domain logic.
4. **No text ingestion.** `datasets/knowledge/sources/` holds bibliographic
   provenance (source/edition metadata), not prose corpora.
5. No new runtime dependencies; `pyproject.toml` gains `knowledge` package +
   testpaths at CODING time (build metadata only).

Rationale:

- The layer numbering note in the JRE-003 spec's future-compatibility section
  is superseded (see the JRE-004 architecture header); the engine numbering
  belongs to REQUEST-time decisions, and this task is next in line.
- Keeping the boundary at "public API of the layer below" mirrors JRE-003's
  proven relationship to JRE-002 and makes the static gates mechanical.

Rejected alternatives:

- **`src/rules/` split from `src/knowledge/`** — two packages with no
  independent consumers; the catalogs and facade are shared.
- **Importing `astronomy` directly** for fact types — facts must arrive
  through `jyotish` output so the vocabulary is pinned to the classification
  layer, not raw positions.

## Consequences

- Static tests enforce the import boundary (`test_forbidden_imports.py`).
- Future engines import `knowledge`'s public API only.
- JRE-002 and JRE-003 remain byte-for-byte untouched (guarded by
  `test_astronomy_unmodified.py` / the JRE-003 equivalent).

## References

- [JRE-004 Architecture §5](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- [JRE-003 Architecture §5 conventions](../architecture/JRE-003-JYOTISH-CORE.md)

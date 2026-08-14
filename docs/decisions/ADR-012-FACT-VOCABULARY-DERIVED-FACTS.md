# ADR-012 — Fact Vocabulary v1.1.0 and the Derived-Facts Layer

- Status: ACCEPTED
- Date: 2026-08-13
- Related task: [JRE-004 Classical Knowledge & Rule Engine — recovery](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- Decision maker: Architect (recovery), per the approved architecture analysis

## Context

The VALIDATOR failed the original JRE-004 authored rule data: 14/16 rule
citations did not match the cited edition texts. The recovery reconciliation
kept/rewrote the rules that are supported by verified classical statements.
Several of those verified statements require facts that `FACT_VOCABULARY`
v1.0.0 cannot express:

- **benefic/malefic nature** — the corrected BPHS Gaja-Kesari requires
  "conjunct or aspected by (another) benefic" (BPHS ch. 36 v. 3-4);
- **dignity** — the same verse requires Jupiter to be free of debilitation and
  inimical signs;
- **combustion** — the verse requires Jupiter not be combust; the Jātaka
  Pārijāta second form requires the Moon not be "obscured by the Sun";
- **aspect strength (¼/½/¾/full)** — the classical drishti doctrine
  (BPHS ch. 26 v. 2-5, Phaladīpikā ch. 2 v. 23) used by the Gaja-Kesari
  "aspected by" arms;
- **all-body `relative_house` references** — the Phaladīpikā Sakata and Kesari
  rules count houses *from Jupiter* (`relative_house(MOON, JUPITER)`), which
  v1.0.0's `RELATIVE_HOUSE_REFS = (LAGNA, ASC, …)` rejected.

The vocabulary is part of the calculation identity (SPEC §16) and conditions
"bind only to these paths" (SPEC §6.2), so adding paths requires a versioned
bump — a parallel "v1.0.0 + side layer" would break schema validation and the
identity contract. The Specialist specification already prescribes the exact
mechanism (SPEC §6.2 supersession #10): *append to the `<REF>` enum → extend
snapshot normalization → bump `FACT_VOCABULARY_VERSION`*.

## Decision

1. **`FACT_VOCABULARY_VERSION` bumps 1.0.0 → 1.1.0** (additive only: no
   existing path, value set, or op is removed or re-typed).

2. **`relative_house(<BODY>, <REF>)` extends its reference set to all nine
   grahas** (`RELATIVE_HOUSE_REFS = LAGNA, ASC, SUN…KETU`). The 1-arg form
   still defaults `REF` to `LAGNA`. Snapshot normalization
   (`synthesis._relative_houses`) now emits a house map for every placed body
   as a reference.

3. **A JRE-004 derived-facts layer is added** (`src/knowledge/facts.py`),
   shipping four new paths with pinned value sets:

   | Path | Value set | Source |
   |---|---|---|
   | `planet(<BODY>).nature` | BENEFIC / MALEFIC / NEUTRAL | BPHS ch. 3 v. 11 |
   | `planet(<BODY>).dignity` | EXALTED / MULATRIKONA / OWN / FRIEND / NEUTRAL / ENEMY / DEBILITATED | BPHS ch. 3 v. 49-55, ch. 4 |
   | `planet(<BODY>).combusted` | bool | BPHS ch. 7 v. 28-29 |
   | `pair(<A>,<B>).aspect_strength` | QUARTER / HALF / THREE_QUARTER / FULL | BPHS ch. 26 v. 2-5; Phaladīpikā ch. 2 v. 23 |

   The tables (nature, exaltation/debilitation, own signs, moolatrikona,
   combustion degrees, natural friendship, rashi lords, aspect doctrine) are
   **authored data** in `datasets/knowledge/facts/facts.json` — versioned,
   checksummed, and provenance-pinned per fact entry — and are loaded through
   `FactsRegistry`/`load_facts()`.

4. **Derived facts are computed by JRE-004 in snapshot normalization**, never
   by JRE-003. `normalize_snapshot(chart, pairs=…, facts=registry)` enriches
   the canonical snapshot in place, deterministically, from JRE-003 public
   outputs already present (planet rashis, Sun-separation pairs, relative
   houses). A missing input leaves the derived field absent and the consuming
   rule atom evaluates **False** — never an exception, never a wrongly-fired
   rule.

5. **Aspect-strength doctrine is pinned in two places that are asserted equal
   by a conformance test:** the facts catalog table and the schema constants
   `ASPECT_POSITION_STRENGTHS`/`SPECIAL_ASPECT_POSITIONS`. The evaluator
   resolves `pair(A,B).aspect_strength` **directionally** (A's glance on B)
   from `relative_houses`, so the order-insensitive `pairs` entries never
   carry it.

6. **JRE-003 remains unchanged.** All v1.1.0 facts are derived *from* JRE-003
   outputs; JRE-003's `__init__` forbids benefic/malefic, dignity, combustion
   and classical-drishti computation, and ADR-004 point 5 reserves sign-based
   drishti tables for the Rules layer. No JRE-003 modification is required —
   this is the whole point of the additive design.

## Why these facts are knowledge facts, not Jyotish state

JRE-003 computes *positional/geometric state*: where a planet is, what it
conjuncts, its separation in degrees. Benefic/malefic classification, dignity,
combustion thresholds, and classical aspect strength are **interpretive
tables with provenance** — the same geometry yields different classical
readings in different traditions, and each reading must carry its source. They
therefore belong in JRE-004 as versioned, provenance-carrying data plus a pure
derivation step, and future engines can disagree with a table by shipping a
different (versioned, sourced) facts catalog — never by changing JRE-003.

## Determinism and versioning

- The derivation is a pure function of (snapshot dict, immutable
  `FactsRegistry`); identical inputs give bit-identical snapshots (SPEC §16).
- `SearchMetadata.catalogs` echoes `fact_vocabulary` (1.1.0) **and** `facts`
  (the facts catalog version), so a consumer can reproduce the exact
  vocabulary + tables used for a result.
- `config/knowledge.toml` carries a `facts_catalog_version` pin key
  (unpinned by default); a non-empty pin enforces exact-match at load and a
  mismatch raises `CatalogIntegrityError` at construction (same policy as the
  other catalogs).

## Compatibility implications

- **Additive only:** every v1.0.0 condition (path/op/value) is still valid and
  evaluates identically; no rule catalog needed a path change for v1.0.0
  semantics.
- Rule catalogs that consume the new paths are re-validated at load against
  v1.1.0 (`validate_condition`), so a rule referencing a v1.2.0 path fails
  fast at load — never silently.
- `derive_*` helpers are pure and public (exported from `knowledge`), so the
  facts layer is independently unit-testable without a full synthesis.

Rejected alternatives:

- **Leave v1.0.0 and encode the rules with approximations** — weakens the
  classical statements to fit the vocabulary, explicitly forbidden by the
  recovery mandate ("do not weaken the classical rules merely to fit
  v1.0.0").
- **Add the facts to JRE-003** — violates the JRE-003 boundary ("no
  benefic/malefic, yogas, dashas"), drags interpretive tables into a state
  layer, and would require a JRE-003 spec change.
- **Unversioned "side layer" of paths** — breaks schema validation, the
  calculation identity, and the deterministic-version contract.

## Consequences

- JRE-004 ships the classical facts it needs to represent the verified rules
  with correct provenance; the rules agent can extend tables via the same
  additive mechanism (new fact entries or a catalog version bump).
- QA and VALIDATOR can audit every derived fact back to a committed short
  evidence excerpt (`datasets/validation/knowledge/`).
- JRE-002 and JRE-003 remain untouched by this recovery.

## References

- [JRE-004 Specialist SPEC §6.2, §6.3, §16](../architecture/JRE-004-SPECIALIST-SPEC.md)
- [ADR-004 Conjunction/Aspect Semantics](../decisions/ADR-004-CONJUNCTION-ASPECT-SEMANTICS.md)
- [ADR-007 Knowledge Package Placement](../decisions/ADR-007-KNOWLEDGE-PACKAGE-PLACEMENT.md)
- [JRE-004 Validation Report](../validation/JRE-004-VALIDATION-REPORT.md)
- [JSP-001 Layers 3 and 5](../../specifications/core/JSP-001.md)

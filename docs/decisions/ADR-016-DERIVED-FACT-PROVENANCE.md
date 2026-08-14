# ADR-016 — Provenance on Every JRE-005 Derived Fact

- Status: ACCEPTED
- Date: 2026-08-14
- Related task: [JRE-005 Bhava / House Engine](../architecture/JRE-005-BHAVA-CORE.md)
- Supersedes: nothing (extends the JRE-003 echo/config-echo and JRE-004
  provenance discipline to the derived layer)
- Decision maker: Architect

## Context

JRE-005 produces facts that are *derived* from JRE-003 facts. Consumers
(JRE-004 rules, future Dasha/Gochar/Drishti/Yoga/Synthesis engines) need
to know, for every fact: which derivation produced it, from which
version, from which input facts, and from which pinned catalogs. Without
this, a derived fact is indistinguishable from a JRE-003 fact, and a
catalog or derivation change becomes an undetectable silent change.
JRE-003/JRE-004 already established checksummed, versioned catalogs and
config echoes; JRE-005 extends the same discipline to derivations.

## Decision

1. **Every derived fact carries a `DerivationBlock`** with stable fields:
   `id` (stable derivation id string, e.g. `RELATIVE_HOUSE`), `derivation_version`
   (from `BhavaConfig.derivation_version`), `inputs` (the JRE-003 input
   fact ids consumed), `source_catalog_versions`
   (`{"rashi": ..., "nakshatra": ...}` read from JRE-003's public
   `RASHI_CATALOG_VERSION`/`NAKSHATRA_CATALOG_VERSION` exports), and
   `house_system`.
2. **JRE-003 echoes are marked**: any JRE-003 value re-emitted in
   JRE-005 output carries an `echoed_from` marker (e.g.
   `"bhava.house_lord"`). Derived values never masquerade as JRE-003
   facts, and JRE-003 facts are never silently recomputed.
3. **Derivation ids are stable constants** (enumerated in the specialist
   spec §8): new derivations append; existing ids never change meaning.
   Changing a derivation's formula requires a new id or a
   `derivation_version` bump — never silent mutation.
4. **Provenance is data, not prediction**: it enables auditability and
   cross-layer consistency (e.g. the ADR-014 JRE-004 equality test), and
   it carries no confidence or interpretation.
5. **Golden fixtures pin the environment** (`GOLDEN_VERSION`), so a
   provenance/determinism regression fails loudly.

Rationale:

- Auditability across four layers requires knowing *which* layer produced
  a fact and from what — the alternative (trusting field names) breaks
  as soon as a field name collides between layers.
- Catalog versions are already part of JRE-003's calculation identity
  (ADR-003); echoing them in derivations makes JRE-005 observe JRE-003
  catalog changes explicitly rather than implicitly.
- Stable ids + version bumps make the additivity policy (architecture
  §28) enforceable: future engines extend, never silently reinterpret.

Rejected alternatives:

- **No provenance blocks** — derived facts indistinguishable from
  JRE-003 echoes; silent drift undetectable.
- **Free-text provenance** — unverifiable; stable ids are testable.
- **Recompute catalog versions inside `bhava`** — JRE-005 must not
  re-derive JRE-003 metadata; it reads the public exports (ADR-013).

## Consequences

- `DerivationBlock` is part of the JSON Schema (DATA-CONTRACT §9/§11)
  with `additionalProperties: false`.
- Static/provenance tests assert: every derived fact has a block; every
  echo has `echoed_from`; ids come from the pinned constant set.
- The JRE-004 cross-layer equality test consumes provenance to confirm
  both layers derived from the same catalog versions.

## References

- [JRE-003 architecture §17 (reproducibility)](../architecture/JRE-003-JYOTISH-CORE.md)
- [ADR-003 (catalog versioning)](ADR-003-ZODIAC-MODE-CATALOG-VERSIONING.md)
- [JRE-004 provenance system (source registry)](ADR-008-SOURCE-REGISTRY-PROVENANCE.md)
- [JRE-005 architecture §22](../architecture/JRE-005-BHAVA-CORE.md)

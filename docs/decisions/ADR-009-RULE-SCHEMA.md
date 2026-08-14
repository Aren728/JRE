# ADR-009 — Rule Schema

- Status: ACCEPTED
- Date: 2026-08-12
- Related task: [JRE-004 Classical Knowledge & Rule Engine](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- Decision maker: Architect

## Context

JRE-004 must represent classical Jyotish rules machine-readably so future
engines (Drishti, Yoga, Dasha, Gochar, Nakshatra interpretation, synthesis,
prediction/confidence) can consume them deterministically. The request
forbids implementing predictions, so the schema must carry *rule content*
while the engine evaluates only *conditions*. Rules must bind to the facts
JRE-003 already produces (Rashi, Nakshatra, Pada, Bhava, aspects, transit
events, eclipses).

## Decision

1. **A rule is a versioned data record with six parts:**

   | Part | Type | Purpose |
   |---|---|---|
   | identity | `rule_id`, `rule_version`, `status` | stable, versioned, ACTIVE/DEPRECATED/SUPERSEDED |
   | scope | `domain` (`RuleDomain`), `tradition_tags` | which future engine group consumes it |
   | condition | `RuleCondition` tree | predicate over the fact vocabulary |
   | conclusion | `RuleConclusion` | structured, machine-readable content |
   | provenance | primary `ProvenanceRef` + supporting refs | mandatory attribution (ADR-008) |
   | authority | `authority_tier` 1–5 | authored strength used by precedence (ADR-010) |

2. **Conditions are a typed recursive grammar.** `RuleCondition` is either an
   atom (`op` + `path` + `value`) or a combiner (`ALL`/`ANY`/`NOT` +
   children). Atoms bind to a **pinned fact vocabulary**
   (`planet(BODY).rashi`, `lagna.nakshatra`, `bhava(N).occupants`,
   `pair(A,B).conjunction`, `transit(BODY).kind`, `eclipse.kind`, …). A path
   outside the vocabulary, a wrong literal type, or a malformed tree fails
   schema validation — it never silently "matches nothing".

3. **Conclusions are opaque data, not executable logic.** `RuleConclusion`
   has a `kind` label, a canonical `statement` string, and a `structured`
   dict. The engine stores, orders, and echoes conclusions; it has **no**
   evaluator that converts them into outcomes, scores, or recommendations.
   Whether a conclusion is "interpretive" is a content-authoring matter for
   the Rules agent, not engine behavior.

4. **No code generation.** Rules are never compiled into functions; they are
   data validated against the schema and evaluated by the single pure
   condition evaluator.

Rationale:

- A data-driven schema with a pinned vocabulary keeps rule catalogs stable
  across engine versions (a rule that worked on JRE-003 v0.3 output keeps
  working) and lets future engines validate their inputs.
- Keeping conclusions opaque preserves the hard "no predictions in the
  engine" boundary: JRE-004 can ship `YOGA_DEFINITION` rules without any
  code path that "predicts".

Rejected alternatives:

- **Rules as Python callables** — code-in-data; breaks versioning,
  serialization, static analysis, and the no-interpretation gate.
- **Free-form text conditions** — non-deterministic and unverifiable.
- **A conclusion evaluator** — that is the future interpretation engine's
  job, deferred by the request.

## Consequences

- Schema validation is a hard gate at catalog load (`RuleSchemaError`).
- CODING ships ≥ 3 example catalogs covering `YOGA_DEFINITION`, `DRISHTI`,
  and `KARAKA`/`BHAVA_MEANING` to prove the grammar and the no-evaluator
  boundary.
- Golden catalogs make precedence/conflict tests deterministic.

## References

- [JRE-004 Architecture §6, §9](../architecture/JRE-004-KNOWLEDGE-RULES-CORE.md)
- [JRE-004 Data Contract §2–§4](../architecture/JRE-004-DATA-CONTRACT.md)
- [ADR-004 Conjunction/Aspect Semantics](../decisions/ADR-004-CONJUNCTION-ASPECT-SEMANTICS.md)

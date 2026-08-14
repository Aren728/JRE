# JRE — Jyotish Reasoning Engine

A modular computational reasoning framework for Jyotisha.

## Architecture

JRE separates:

1. Astronomical calculations
2. Astrological classification
3. Knowledge representation
4. Rule execution
5. Dynamic state calculation
6. Evidence aggregation
7. Inference
8. Explanation

## Orchestration status

- JRE-002 — Astronomical Core: MERGED
- JRE-003 — Jyotish Coordinate and State Layer: QA-COMPLETE
- JRE-004 — Classical Knowledge & Rule Engine (layers 3 + 5):
  VALIDATOR-COMPLETE (recovery, second pass) — the original FAIL (14/16
  citations incorrect) was corrected via FACT_VOCABULARY v1.1.0 + a
  derived-facts layer ([ADR-012](docs/decisions/ADR-012-FACT-VOCABULARY-DERIVED-FACTS.md)),
  re-authored rule catalogs, committed validation evidence, and a second
  correction of the `natural_friendship` table to the verified verse-55
  reading
  ([recovery validation report](docs/validation/JRE-004-RECOVERY-VALIDATION-REPORT.md);
  original [validation report](docs/validation/JRE-004-VALIDATION-REPORT.md);
  [queue item](orchestration/queue/JRE-004-CLASSICAL-KNOWLEDGE.md),
  [architecture](docs/architecture/JRE-004-KNOWLEDGE-RULES-CORE.md),
  [specialist spec](docs/architecture/JRE-004-SPECIALIST-SPEC.md))

- JRE-005 — Bhava / House Engine (derived bhava/house computational
  state): VALIDATOR-COMPLETE — `src/bhava/` implements the v0.2.0
  contract (occupancy, planet-house, lordship/ownership,
  relative-house, categories, cusp proximity, aspect echo,
  transit-house facts, provenance, deterministic serialization) over
  the JRE-003 public API only (ADR-013); 123 tests green, QA-PASS,
  VALIDATOR-PASS (cross-layer `relative_house` oracle equality
  verified)
  ([queue item](orchestration/queue/JRE-005-BHAVA-ENGINE.md),
  [architecture](docs/architecture/JRE-005-BHAVA-CORE.md),
  [specialist spec](docs/architecture/JRE-005-SPECIALIST-SPEC.md),
  [data contract](docs/architecture/JRE-005-DATA-CONTRACT.md),
  [test plan](docs/architecture/JRE-005-TEST-PLAN.md))

Future interpretation engines (Yoga, Dasha, Drishti, Gochar/Nakshatra
interpretation, multi-layer synthesis, prediction/confidence) will be
numbered at REQUEST time starting at JRE-006+ and consume JRE-004's
`KnowledgeService.synthesize` output and JRE-005's `HouseAnalysisResult`
facts.

## Hardware Target

Designed initially for low-resource systems:

- 2 CPU cores
- ~4 GB RAM
- Linux
- Python 3.12

Heavy AI inference is not required for the core engine.

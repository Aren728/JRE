# JRS Architecture — Data Flow & Pipeline Design

## Overview

JRS (Jyotish Research System) implements a deterministic, traceable pipeline that transforms raw birth data into structured astrological assessments. Every step is auditable, reproducible, and backed by classical source citations.

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BIRTH DATA INPUT                           │
│  Date, Time, Timezone, Latitude, Longitude                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    JRE ENGINE LAYER (JRE-002→006)                   │
│                                                                     │
│  JRE-002  Astronomical Core     → planetary positions, cusps       │
│  JRE-003  Coordinate/State      → rashi, nakshatra, bhava state    │
│  JRE-004  Classical Knowledge   → rule catalogs, fact vocabulary   │
│  JRE-005  Bhava Engine          → house occupancy, lordship        │
│  JRE-006  Gochar/Transit Engine → transit facts, event windows     │
│                                                                     │
│  Output: Raw natal facts dictionary                                │
│  e.g., {"sun_strong": true, "10th_lord_in_kendra": true, ...}     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   JRS EVIDENCE LAYER (JRS-031→033)                  │
│                                                                     │
│  Domain Service.evaluate_*_facts(natal_facts)                       │
│                                                                     │
│  1. Load domain rules from TOML config                             │
│     (e.g., config/domains/wealth.toml)                              │
│  2. Evaluate each rule's condition_facts against natal_facts        │
│  3. Produce EvidenceRecord objects:                                 │
│     {rule_id, outcome_taxonomy, direction, strength, source_id}    │
│                                                                     │
│  Output: tuple[EvidenceRecord, ...]                                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  TEMPORAL WINDOWS LAYER (JRS-028)                   │
│                                                                     │
│  EventWindow construction from Dasha + Transit data                │
│                                                                     │
│  - Dasha periods (planetary periods)                               │
│  - Transit activations (current planetary movements)               │
│  - Convergence level (NONE → LOW → MODERATE → HIGH → VERY_HIGH)   │
│                                                                     │
│  Output: tuple[EventWindow, ...]                                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 CONVERGENCE ENGINE (JRS-029)                        │
│                                                                     │
│  ConvergenceService.assess_domain(                                 │
│      outcome_taxonomy,                                              │
│      evidence_records,                                              │
│      event_windows,                                                 │
│  )                                                                  │
│                                                                     │
│  1. Count supporting/contradicting/mitigating records              │
│  2. Calculate independent channels (source × group)                │
│  3. Classify assessment status:                                     │
│     STRONGLY_SUPPORTED → SUPPORTED → WEAKLY_SUPPORTED              │
│     → NEUTRAL → CONTRADICTED → STRONGLY_CONTRADICTED              │
│  4. Classify timing status: CONVERGENT / DIVERGENT / INACTIVE      │
│  5. Classify overall strength: STRONG / MODERATE / WEAK            │
│                                                                     │
│  Output: DomainAssessment                                           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              RESEARCH CITATIONS (JRS-046)                           │
│                                                                     │
│  ResearchService.get_citations_for_domain(domain)                   │
│                                                                     │
│  Resolves rule IDs to human-readable classical source citations:    │
│  - Brihat Parashara Hora Shastra, Chapter X, Verse Y              │
│  - Phaladeepika (Mantreshwara), Chapter X, Verse Y                │
│                                                                     │
│  Strictly read-only; does not alter calculations.                   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              CLI OUTPUT (JRS-045)                                   │
│                                                                     │
│  Traceable report with:                                             │
│  - Birth data                                                       │
│  - Assessment status & evidence dimensions                          │
│  - Key factors (triggered rules)                                   │
│  - Classical source citations                                       │
│  - Timing analysis                                                  │
│  - Limitations                                                      │
│                                                                     │
│  Formats: Text (default) or JSON (--json flag)                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### Determinism
- Byte-identical output for identical inputs
- No randomness, no external state, no time-dependent behavior
- All functions are pure (same input → same output)

### Traceability
- Every EvidenceRecord traces back to a classical source (rule_id → source, location, verse)
- Every DomainAssessment shows exactly which evidence produced the verdict
- CLI output exposes internal state for audit

### Separation of Concerns
- **Research layer** structures knowledge (citations, claims)
- **Domain layer** evaluates rules (condition_facts → EvidenceRecords)
- **Convergence layer** aggregates evidence (records → assessment)
- **CLI layer** formats output (assessment → report)
- No layer modifies another's logic

### Domain Independence
Each domain has its own:
- TOML config (rules)
- Domain service (rule loader + fact evaluator)
- Outcome taxonomy (domain-specific enums)
- Validation dataset (reference charts with known outcomes)

Domains share:
- EvidenceRecord model (from `jrs.evidence.models`)
- ConvergenceService (from `jrs.convergence.service`)
- EventWindow model (from `jrs.temporal.models`)

## Configuration

| Config File | Purpose |
|------------|---------|
| `config/domains/wealth.toml` | Wealth domain rules |
| `config/domains/career.toml` | Career domain rules |
| `config/domains/marriage.toml` | Marriage domain rules |
| `config/domains/progeny.toml` | Progeny domain rules |
| `config/domains/migration.toml` | Migration domain rules |
| `config/domains/education.toml` | Education domain rules |
| `config/domains/property.toml` | Property domain rules |
| `config/domains/transitions.toml` | Transitions domain rules |
| `config/convergence.toml` | Convergence thresholds & source weights |
| `config/research_sources.toml` | Classical source citations |
| `config/jrs.toml` | Orchestrator routing matrix |

## Testing Strategy

- **Unit tests**: Models, config loading, rule evaluation, condition parsing
- **Integration tests**: Full pipeline execution against reference charts
- **Validation tests**: Domain-specific fixtures with known ground truth
- **Determinism tests**: Byte-identical output verification
- **Cross-chart tests**: Consistency across all reference charts

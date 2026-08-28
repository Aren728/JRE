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

## Yoga Evaluation Pipeline (RI-010)

The RI-010 engine implements a multi-layered yoga evaluation pipeline that separates D1 formation, deep modifiers, transit activation, and divisional chart confirmation into distinct, auditable stages.

```
┌─────────────────────────────────────────────────────────────────────┐
│              YOGA EVALUATION PIPELINE (RI-010)                     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Layer 1: Structural Detection                           │     │
│  │  (RelationshipGraphService + YogaEvaluatorService)       │     │
│  │                                                           │     │
│  │  • Conjunction (same rashi)                               │     │
│  │  • Aspect (Parashari + special: Mars 4/7/8, Jupiter 5/7/9│     │
│  │    Saturn 3/7/10)                                         │     │
│  │  • Exchange (Parivartana: reciprocal sign ownership)      │     │
│  │  • Dispositorship (A in B's sign → directed edge)         │     │
│  │  • Chain truncation when terminal lord is combust         │     │
│  │                                                           │     │
│  │  Output: list[PlanetRelationship]                         │     │
│  └──────────────────────────┬────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Layer 2: Deep Modifiers (5-Tier Pipeline)                │     │
│  │  (ModifierEvaluationService)                              │     │
│  │                                                           │     │
│  │  Tier 1: Combustion Check                                 │     │
│  │    → CANCELLED (unless exalted/own-sign → WEAKENED 0.5×) │     │
│  │  Tier 2: Debilitation / Neecha Bhanga                     │     │
│  │    → CANCELLED unless deb-lord in Kendra (→ 0.7×)        │     │
│  │  Tier 3: Graha Yuddha (Planetary War)                    │     │
│  │    → 1.0° longitude threshold; victor dominates           │     │
│  │    → Loser suppressed (0.3×); winner maintained           │     │
│  │  Tier 4: Cheshta Bala (Retrograde)                        │     │
│  │    → Strength boost (1.2×) for retrograde planets         │     │
│  │  Tier 5: Node Taint (Rahu/Ketu)                           │     │
│  │    → Conjunction: 0.7× (30% reduction)                    │     │
│  │    → 7th aspect: 0.85× (15% reduction)                    │     │
│  │    → Pseudo-aspects (5th/9th): rejected (Parashari)       │     │
│  │                                                           │     │
│  │  Output: ModifierReport (status, strength, modifier_chain)│     │
│  └──────────────────────────┬────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Layer 3: Transit Activation                              │     │
│  │  (TransitActivationService + VedhaService + TaraBalaSvc)  │     │
│  │                                                           │     │
│  │  • Dasha-first hierarchy (Dasha > Antardasha > Transit)   │     │
│  │  • Vedha obstruction masks (Phaladeepika Ch 26)           │     │
│  │  • Tara Bala strength (Nakshatra-based: even=tara favorable│     │
│  │                                                           │     │
│  │  Output: ActivationResult (activated, source, strength)   │     │
│  └──────────────────────────┬────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Layer 4: Varga Confirmation (Divisional Charts)          │     │
│  │  (VargaConfirmationService + SaptavargajaBalaService)     │     │
│  │                                                           │     │
│  │  • D9 (Navamsha) confirmation                             │     │
│  │    → Kendra/Trikona: STRONG (1.5×) / MODERATE (1.0×) /   │     │
│  │      WEAK (0.7×)                                          │     │
│  │    → Debilitation in D9: binary CANCELLED                 │     │
│  │    → Vargottama (D1 sign == D9 sign): 2.0× multiplier    │     │
│  │  • D10 (Dashamsha) career confirmation                    │     │
│  │  • D7 (Saptamamsha) progeny confirmation                  │     │
│  │  • Saptavargaja Bala (7-Varga composite score)            │     │
│  │    → ≥25: Very Strong | 18–24: Moderate | <18: Weak       │     │
│  │                                                           │     │
│  │  Output: VargaConfirmationResult (status, strength,       │     │
│  │          multiplier, vargottama_planets)                   │     │
│  └──────────────────────────┬────────────────────────────────┘     │
│                             │                                       │
│                             ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │  Layer 5: Evidence Convergence                            │     │
│  │  (ConvergenceService)                                     │     │
│  │                                                           │     │
│  │  • Aggregate evidence from all layers                     │     │
│  │  • Classify: STRONGLY_SUPPORTED → CONTRADICTED            │     │
│  │  • Timing: CONVERGENT / DIVERGENT / INACTIVE              │     │
│  │  • Strength: STRONG / MODERATE / WEAK                     │     │
│  │                                                           │     │
│  │  Output: DomainAssessment                                 │     │
│  └───────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
```

### Frozen Data Structures

The following data structures are frozen (immutable) and form the stable API contracts between pipeline layers:

| Model | Package | Fields |
|-------|---------|--------|
| `PlanetRelationship` | `jrs.structural.models` | planet_a, planet_b, relationship_type, is_directed, strength_modifier, node_involvement, is_active |
| `RelationshipType` | `jrs.structural.models` | CONJUNCTION, ASPECT, EXCHANGE, DISPOSITOR, TRANSIT_ASPECT, TRANSIT_CONJUNCTION |
| `ModifierResult` | `jrs.yoga_evaluator.modifier_service` | planet, status, modifier_chain, net_strength, cancellation_reason, war_victor, node_taint_type |
| `ModifierReport` | `jrs.yoga_evaluator.modifier_service` | planet_results, overall_status, overall_strength, cancellation_reason |
| `YogaEvaluation` | `jrs.yoga_evaluator.models` | yoga_name, status, cancellation_reason, is_manifesting, activation_source, modifier_report |
| `VargaConfirmationResult` | `jrs.varga.confirmation_service` | confirmation_status, strength, kendra_trikona_count, vargottama_planets, net_strength_multiplier |
| `SaptavargajaScore` | `jrs.varga.saptavargaja_service` | planet, total_score, dignity_level, varga_scores, moolatrikona_count |
| `ActivationResult` | `jrs.temporal.activation_service` | is_activated, activation_source, dasha_support, transit_trigger, vedha_obstructed |

### Scoring Matrices

#### Graha Yuddha (Planetary War) — Saravali Ch 24

| Condition | Threshold | Effect |
|-----------|-----------|--------|
| War detection | ≤ 1.0° longitude difference | Victor dominates |
| War eligibility | Non-luminary planets only | Mars, Mercury, Jupiter, Venus, Saturn |
| Victor | Higher longitude wins | Strength maintained (1.0×) |
| Defeated | Lower longitude | Suppressed (0.3×) |

#### Nodal Interception Severity — BPHS Ch 9, RI-010C MY-025–030

| Taint Type | Multiplier | Status |
|------------|------------|--------|
| Rahu/Ketu conjunction (0°–10°) | 0.7× (30% reduction) | WEAKENED |
| Rahu/Ketu 7th aspect | 0.85× (15% reduction) | WEAKENED |
| Rahu/Ketu 5th/9th pseudo-aspect | Rejected (Parashari) | No effect |

#### Saptavargaja Bala Point Matrix — BPHS Ch 3, Ch 45

| Dignity | Points | Description |
|---------|--------|-------------|
| Moolatrikona | 5.0 | Highest dignity (0°20'–sign start) |
| Own sign | 4.0 | Planet in its own rashi |
| Great Friend | 3.5 | Sign lord is great friend |
| Friend | 3.0 | Sign lord is friend |
| Neutral | 2.0 | Sign lord is neutral |
| Enemy | 1.0 | Sign lord is enemy |
| Great Enemy | 0.5 | Sign lord is great enemy |
| Debilitated | 0.0 | Planet in debilitation sign |

| Total Score | Classification |
|-------------|----------------|
| ≥ 25 | Very Strong |
| 18–24 | Moderate |
| < 18 | Weak |

---

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

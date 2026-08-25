# JRE/JRS Architecture Gap Analysis

> **Date:** 2026-08-25
> **Sources:** RI-010A (Kendra-Trikona Doctrine), RI-010B (Multi-Planet Relationships)
> **Status:** Analysis — Awaiting prioritization decisions

---

## Executive Summary

This document consolidates all architectural gaps identified in RI-010A and RI-010B research reports, cross-references them against the existing codebase, and provides a prioritized implementation roadmap.

**Key Insight:** The knowledge layer (`src/knowledge/`) already computes `derive_dignity`, `derive_nature`, `derive_combusted`, and `derive_aspect_strength` — these are available as fact-vocabulary paths in rule evaluation. The primary gaps are in the **JRE-012 (Drik)** and **JRE-013 (Yoga)** engines, which do not consume these derived facts.

---

## Tier 1: HIGH PRIORITY — Core Yoga Strength Gaps

These gaps prevent accurate yoga strength assessment and are required for any meaningful yoga evaluation.

### Gap 1: Parivartana Classification (Maha/Kahala/Dainya)

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010B Section C.2 |
| **Current State** | JRE-013 detects exchange (`ConnectionType.EXCHANGE`) but does not classify type |
| **Classical Basis** | BPHS Ch.26: Maha (Kendra-Trikona), Kahala (auspicious houses), Dainya (Dusthana) |
| **Impact** | Cannot distinguish beneficial exchanges from harmful ones |
| **Proposed Location** | `src/yoga/service.py` — extend `_detect_connection` or add classification method |
| **New Fact Vocabulary** | `pair(<A>,<B>).exchange_type` → `"MAHA"` / `"KAHALA"` / `"DAINYA"` |
| **Effort** | LOW — Pure classification logic using existing SIGN_LORDS and house numbering |
| **Dependencies** | None |

### Gap 2: Neecha Bhanga Detection (7 Conditions)

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010B Section E.3 |
| **Current State** | No debilitation cancellation detection anywhere |
| **Classical Basis** | Phaladeepika Ch.7: 7 conditions for debilitation cancellation |
| **Impact** | Debilitated planets incorrectly treated as permanently weak |
| **Proposed Location** | `src/knowledge/facts.py` — add `derive_neecha_bhanga` function |
| **New Fact Vocabulary** | `planet(<BODY>).neecha_bhanga` → `bool` |
| **Effort** | MEDIUM — 7 conditional checks requiring multiple fact lookups |
| **Dependencies** | Requires `derive_dignity`, `derive_aspect_strength`, relative house computation |

### Gap 3: Combustion Detection in JRE-013

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section A.7, RI-010B Section B.9 |
| **Current State** | `derive_combusted` exists in knowledge layer but JRE-013 Yoga engine does not use it |
| **Classical Basis** | BPHS Ch.3: Planet within combustion threshold of Sun loses capacity |
| **Impact** | Yoga planets incorrectly treated as fully functional when combust |
| **Proposed Location** | `src/yoga/service.py` — consume `combusted` fact in `_compute_strength` |
| **New Fact Vocabulary** | Already exists: `planet(<BODY>).combusted` → `bool` |
| **Effort** | LOW — Modify `_compute_strength` to check combustion fact |
| **Dependencies** | Knowledge layer already provides the fact |

### Gap 4: Yoga Strength Based on Dignity

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section C.7, RI-010B Section E.7 |
| **Current State** | JRE-013 uses Shadbala ratio only; does not check exaltation/debilitation/own sign |
| **Classical Basis** | BPHS Ch.3: Exaltation strengthens, debilitation weakens, own sign empowers |
| **Impact** | Yoga strength not accurately reflecting planetary dignity |
| **Proposed Location** | `src/yoga/service.py` — extend `_compute_strength` to include dignity |
| **New Fact Vocabulary** | Already exists: `planet(<BODY>).dignity` → `"EXALTED"` / `"DEBILITATED"` / etc. |
| **Effort** | LOW — Modify `_compute_strength` to weight dignity |
| **Dependencies** | Knowledge layer already provides the fact |

### Gap 5: Dusthana Placement Penalty

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section E.2, RI-010B Section F.3 |
| **Current State** | JRE-013 does not check if yoga conjunction occurs in 6th/8th/12th |
| **Classical Basis** | BPHS Ch.33: Conjunction in Dusthana dims the yoga |
| **Impact** | Raja/Dhana yogas in Dusthana treated same as in Kendra/Trikona |
| **Proposed Location** | `src/yoga/service.py` — add house-of-conjunction check |
| **New Fact Vocabulary** | `pair(<A>,<B>).conjunction_house` → `int` (house number) |
| **Effort** | LOW — Check conjunction planet's house against DUSTHANA_HOUSES |
| **Dependencies** | Requires lagna_num (already available) |

---

## Tier 2: MEDIUM PRIORITY — Aspect System Enhancements

These gaps enhance the aspect computation system but are not blocking basic yoga evaluation.

### Gap 6: Aspect Strength in DrikResult

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010B Section B.3 |
| **Current State** | `DrikResult` stores aspects but not their strength (1/4, 1/2, 3/4, full) |
| **Classical Basis** | BPHS Ch.26 v.2-5: Aspect strength varies by house position |
| **Impact** | Aspect strength only computed at rule evaluation time, not in aspect graph |
| **Proposed Location** | `src/drik/models.py` — add `strength` field to `AspectApplication` |
| **New Fact Vocabulary** | Already exists: `pair(<A>,<B>).aspect_strength` → `"QUARTER"` / `"HALF"` / etc. |
| **Effort** | MEDIUM — Modify AspectApplication dataclass and DrikResult computation |
| **Dependencies** | Requires relative house computation |

### Gap 7: Aspect Direction Asymmetry

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010B Section B.5 |
| **Current State** | JRE-012 treats aspects as symmetric (A→B = B→A) |
| **Classical Basis** | BPHS Ch.26: Mars in Aries aspects Capricorn at 4th (full) but Saturn in Capricorn aspects Aries at 3rd (full for Saturn's special) |
| **Impact** | Asymmetric aspects not captured |
| **Proposed Location** | `src/drik/service.py` — compute directional aspects |
| **Effort** | HIGH — Requires rethinking aspect computation model |
| **Dependencies** | Significant architectural change |

### Gap 8: Dispositor Chain Computation

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010B Section D.2 |
| **Current State** | No dispositor chain tracing anywhere |
| **Classical Basis** | BPHS Ch.3: Follow sign lords to trace influence chains |
| **Impact** | Cannot identify final dispositor or chain strength |
| **Proposed Location** | New module: `src/jre/dispositor/` or extend `src/yoga/service.py` |
| **New Fact Vocabulary** | `planet(<BODY>).dispositor` → `body`, `planet(<BODY>).dispositor_chain` → `list[body]` |
| **Effort** | MEDIUM — Graph traversal algorithm |
| **Dependencies** | Requires SIGN_LORDS (existing) |

### Gap 9: Multi-Planet Conjunction Hierarchy

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section E.2 |
| **Current State** | JRE-013 does not determine which planet dominates in 3+ conjunction |
| **Classical Basis** | BPHS Ch.3: Planet in exaltation/own sign dominates |
| **Impact** | Multi-planet conjunctions treated as flat set |
| **Proposed Location** | `src/yoga/service.py` — add conjunction dominance logic |
| **Effort** | LOW — Simple priority ranking by dignity |
| **Dependencies** | Requires `derive_dignity` (existing) |

### Gap 10: Retrograde Modification of Yoga Results

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section C.9, RI-010B Section B.9 |
| **Current State** | JRE-013 does not modify yoga results based on retrograde status |
| **Classical Basis** | BPHS Ch.3: Retrograde planet acts as if exalted |
| **Impact** | Retrograde planets incorrectly treated as direct |
| **Proposed Location** | `src/yoga/service.py` — check `retrograde` field in strength computation |
| **Effort** | LOW — Check existing `PlanetState.retrograde` field |
| **Dependencies** | None (field already exists) |

---

## Tier 3: LOW PRIORITY — Advanced Features

These gaps are real but can be addressed in future iterations.

### Gap 11: Aspect Chain Validity

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010B Section F |
| **Current State** | No logic to validate A→B→C chains |
| **Classical Basis** | BPHS Ch.26: Chain valid if intermediate planet dignified and not combust |
| **Impact** | Cannot determine if multi-planet chains are meaningful |
| **Effort** | HIGH — Requires relationship graph data structure |
| **Dependencies** | Requires Gap 8 (dispositor chains) |

### Gap 12: Yoga Cancellation Detection

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section D.4 |
| **Current State** | JRE-013 does not detect when yoga conditions are cancelled |
| **Classical Basis** | BPHS Ch.33: Yoga cancelled if key planet debilitated, combust, or in Dusthana |
| **Impact** | Cancelled yogas incorrectly reported as active |
| **Effort** | MEDIUM — Requires combining multiple fact checks |
| **Dependencies** | Requires Gap 3 (combustion), Gap 4 (dignity), Gap 5 (Dusthana) |

### Gap 13: Multiple Yoga Accumulation

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section D.5 |
| **Current State** | JRE-013 reports each yoga independently |
| **Classical Basis** | BPHS Ch.33: Multiple yogas = cumulative effect |
| **Impact** | Cannot determine combined yoga strength |
| **Effort** | MEDIUM — Requires yoga interaction logic |
| **Dependencies** | Requires all Tier 1 gaps |

### Gap 14: Pancha Mahapurusha Yoga Detection

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010B Section E.5 |
| **Current State** | JRE-013 does not detect Pancha Mahapurusha yogas |
| **Classical Basis** | BPHS Ch.33: Planet in own sign/exaltation in Kendra |
| **Impact** | Five major planetary yogas not detected |
| **Effort** | LOW — Simple condition check |
| **Dependencies** | Requires `derive_dignity` (existing) |

### Gap 15: Kendradhipati Dosha Detection

| Attribute | Value |
|-----------|-------|
| **Source** | RI-010A Section A.4 |
| **Current State** | No detection of benefic Kendra lordship modification |
| **Classical Basis** | BPHS Ch.33: Benefics ruling Kendras lose beneficence |
| **Impact** | Functional malefic/benefic classification incomplete |
| **Effort** | LOW — Simple condition check |
| **Dependencies** | Requires `derive_nature` (existing) |

---

## Implementation Roadmap

### Phase 1: Quick Wins (Effort: LOW, Impact: HIGH)

| # | Gap | Files Modified | Tests |
|---|-----|----------------|-------|
| 1 | Parivartana Classification | `src/yoga/service.py` | Unit tests for Maha/Kahala/Dainya |
| 3 | Combustion in JRE-013 | `src/yoga/service.py` | Unit tests for combust yoga planets |
| 4 | Dignity-based yoga strength | `src/yoga/service.py` | Unit tests for exalted/debilitated |
| 5 | Dusthana placement penalty | `src/yoga/service.py` | Unit tests for 6th/8th/12th conjunction |
| 9 | Multi-planet conjunction hierarchy | `src/yoga/service.py` | Unit tests for 3+ conjunctions |
| 10 | Retrograde modification | `src/yoga/service.py` | Unit tests for retrograde planets |

### Phase 2: Knowledge Layer Integration (Effort: MEDIUM, Impact: HIGH)

| # | Gap | Files Modified | Tests |
|---|-----|----------------|-------|
| 2 | Neecha Bhanga detection | `src/knowledge/facts.py` | Unit tests for 7 conditions |
| 6 | Aspect strength in DrikResult | `src/drik/models.py`, `src/drik/service.py` | Unit tests for strength field |
| 8 | Dispositor chain computation | New module or `src/yoga/service.py` | Unit tests for chain tracing |

### Phase 3: Advanced Features (Effort: HIGH, Impact: MEDIUM)

| # | Gap | Files Modified | Tests |
|---|-----|----------------|-------|
| 7 | Aspect direction asymmetry | `src/drik/service.py` | Unit tests for directional aspects |
| 11 | Aspect chain validity | New relationship graph module | Unit tests for chain validation |
| 12 | Yoga cancellation detection | `src/yoga/service.py` | Integration tests |
| 13 | Multiple yoga accumulation | `src/yoga/service.py` | Integration tests |

### Phase 4: Named Yoga Expansion (Effort: LOW, Impact: MEDIUM)

| # | Gap | Files Modified | Tests |
|---|-----|----------------|-------|
| 14 | Pancha Mahapurusha detection | `src/yoga/service.py` + `src/yoga/models.py` | Unit tests for 5 yogas |
| 15 | Kendradhipati Dosha detection | `src/yoga/service.py` | Unit tests for functional malefic |

---

## Dependency Graph

```
Phase 1 (Quick Wins):
  Gap 1 (Parivartana) ─────────────────────────┐
  Gap 3 (Combustion in JRE-013) ────────────────┤
  Gap 4 (Dignity-based strength) ───────────────┤
  Gap 5 (Dusthana penalty) ─────────────────────┤
  Gap 9 (Multi-planet hierarchy) ───────────────┤──→ Phase 2
  Gap 10 (Retrograde modification) ─────────────┘

Phase 2 (Knowledge Integration):
  Gap 2 (Neecha Bhanga) ────────────────────────┐
  Gap 6 (Aspect strength in DrikResult) ────────┤
  Gap 8 (Dispositor chain) ─────────────────────┤──→ Phase 3

Phase 3 (Advanced):
  Gap 7 (Aspect asymmetry) ─────────────────────┤
  Gap 11 (Chain validity) ──────────────────────┤
  Gap 12 (Yoga cancellation) ───────────────────┤──→ Phase 4
  Gap 13 (Yoga accumulation) ───────────────────┘

Phase 4 (Named Yogas):
  Gap 14 (Pancha Mahapurusha) ──────────────────┤
  Gap 15 (Kendradhipati Dosha) ─────────────────┘
```

---

## Validation Strategy

For each gap implementation:

1. **Unit tests** — Verify the specific fact/condition detection
2. **Integration tests** — Verify yoga evaluation with new facts
3. **Regression tests** — Verify existing tests still pass
4. **mypy --strict** — Verify type safety
5. **ruff check** — Verify code quality

### Existing Test Coverage

| Module | Test File | Current Coverage |
|--------|-----------|------------------|
| JRE-012 (Drik) | `tests/unit/drik/` | Aspect computation |
| JRE-013 (Yoga) | `tests/unit/yoga/` | Basic yoga detection |
| Knowledge layer | `tests/unit/knowledge/` | Fact derivation |
| JRS Western | `tests/unit/jrs/western/` | Western interpretation |

---

## Open Questions

1. **Should dispositor chains be a new JRE engine or extend JRE-013?**
   - Pro: Dispositorship is a structural fact, not interpretation
   - Con: Adds complexity to an already complex Yoga engine

2. **Should aspect asymmetry be implemented in JRE-012 or deferred?**
   - Pro: Classical texts support asymmetry
   - Con: Significant architectural change; most practitioners use symmetric aspects

3. **Should Pancha Mahapurusha be a separate YogaId or extend existing detection?**
   - Pro: Separate enum value is cleaner
   - Con: More enum values to maintain

4. **What is the priority of Phase 3 vs Phase 4?**
   - Phase 3 has higher impact but higher effort
   - Phase 4 has lower effort but lower impact

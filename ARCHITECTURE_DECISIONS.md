# Architecture Decisions: Open Questions Resolution

> **Date:** 2026-08-25
> **Status:** Decisions Made — Ready for Implementation
> **Related:** ARCHITECTURE_GAP_ANALYSIS.md, RI-010C_SPEC.md

---

## Decision 1: Dispositor Chains — New Engine vs Extend JRE-013

### Question
Should dispositor chains be a new JRE engine or extend JRE-013?

### Options

| Option | Pros | Cons |
|--------|------|------|
| **A: New JRE engine** | Clean separation; structural fact not interpretation; reusable | More code; more tests; new module to maintain |
| **B: Extend JRE-013** | Less code; leverages existing infrastructure | Mixes structural facts with yoga detection; violates separation |

### Analysis

**Dispositorship IS a structural fact, not interpretation.** Per ADR-012 and the knowledge layer boundary:
- JRE-003 computes planetary positions
- JRE-005 computes house analysis
- JRE-012 computes aspects
- JRE-013 detects yoga structures
- Knowledge layer derives benefic/malefic, dignity, combustion

Dispositorship (which planet rules the sign another planet occupies) is a **deterministic structural fact** derived from JRE-003 positions + SIGN_LORDS. It is NOT yoga interpretation.

**However**, the Yoga engine (JRE-013) already consumes structural facts (connections, house lords) to detect yoga patterns. Adding dispositor chains to JRE-013 would be **extending the pattern detection**, not adding interpretation.

### Decision

**Option B: Extend JRE-013** — but with a clean internal separation.

**Rationale:**
1. Dispositor chains are consumed BY yoga detection (e.g., "Raja Yoga where both planets share the same dispositor")
2. Creating a new JRE engine for a single fact type is over-engineering
3. The existing `_build_connection_map` pattern naturally extends to dispositor chains
4. We can add a `_build_dispositor_map` method to YogaService that is conceptually separate from yoga evaluation

**Implementation approach:**
- Add `_build_dispositor_map` to `YogaService` (private method)
- Add `dispositor_chains: dict[BodyId, tuple[BodyId, ...]]` parameter to `_evaluate_yoga`
- Expose via `identify_yogas(planet_states, lagna_sign, ..., include_dispositor_chains=True)`
- Default `include_dispositor_chains=False` for backward compatibility

**Confidence:** HIGH — This aligns with how JRE-013 already works (consumes structural facts, produces yoga patterns).

---

## Decision 2: Aspect Asymmetry — Implement or Defer

### Question
Should aspect asymmetry be implemented in JRE-012 or deferred?

### Options

| Option | Pros | Cons |
|--------|------|------|
| **A: Implement in JRE-012** | Classical accuracy; captures directional differences | Architectural change to DrikResult; doubles aspect count |
| **B: Defer** | No architectural change; simpler | Inaccurate for some classical rules |
| **C: Implement in knowledge layer only** | No JRE-012 change; asymmetry computed at rule evaluation | Computation repeated for each rule |

### Analysis

**Classical texts ARE asymmetric.** Per BPHS Ch.26:
- Mars in Aries aspects Capricorn at 4th house (FULL for Mars' special aspect)
- Saturn in Capricorn aspects Aries at 3rd house (FULL for Saturn's special aspect)
- These are DIFFERENT strengths despite being the same pair

**However**, the asymmetry matters primarily for:
1. Aspect strength gradation (1/4, 1/2, 3/4, full) — already handled by knowledge layer
2. Special aspects (Mars 4/8, Jupiter 5/9, Saturn 3/10) — already handled by JRE-012

**The key insight:** JRE-012 already stores `source_planet` and `target_planet` as separate fields. The asymmetry is captured in the DIRECTION (A→B vs B→A), not in the aspect detection itself.

**Current JRE-012 behavior:**
- Detects A aspects B (e.g., Mars aspects Saturn at 4th)
- Does NOT detect B aspects A (e.g., Saturn aspects Mars at 3rd)
- This IS asymmetric — it only stores one direction

**The real issue:** JRE-012 stores each aspect ONCE (A→B), not twice (A→B and B→A). So the asymmetry IS captured — we just need to ensure the knowledge layer computes strength correctly for each direction.

### Decision

**Option C: Implement in knowledge layer only** — no JRE-012 change needed.

**Rationale:**
1. JRE-012 already stores directional aspects (source→target)
2. The knowledge layer already computes `pair(<A>,<B>).aspect_strength` using relative houses
3. The asymmetry is a STRENGTH property, not a DETECTION property
4. No architectural change to JRE-012 required
5. The `derive_aspect_strength` function in `src/knowledge/facts.py` already handles directionality

**What needs to change:**
- Ensure `pair(<A>,<B>).aspect_strength` is directional (A aspects B, not B aspects A)
- Verify the knowledge layer computes strength based on A's house from B, not B's house from A
- This is already the case (confirmed in code review)

**Confidence:** HIGH — The asymmetry is already captured in the data model; we just need to verify the strength computation is directional.

---

## Decision 3: Pancha Mahapurusha — Separate YogaId or Extend Detection

### Question
Should Pancha Mahapurusha be a separate YogaId or extend existing detection?

### Options

| Option | Pros | Cons |
|--------|------|------|
| **A: Separate YogaId** | Clean enumeration; explicit detection; testable | More enum values; more methods |
| **B: Extend existing detection** | Less code; leverages existing patterns | Ambiguous which yoga is detected; harder to query |

### Analysis

**Pancha Mahapurusha is fundamentally different from existing yogas:**
- Gajakesari: Jupiter in Kendra from Moon (two planets, relative position)
- Raja Yoga: Kendra lord connected to Trikona lord (two lords, connection type)
- Dhana Yoga: 2nd lord connected to 11th lord (two lords, connection type)
- Viparita Raja: Dusthana lords exchange/conjoin (two lords, connection type)
- **Pancha Mahapurusha: ONE planet in own sign/exaltation in Kendra** (single planet, dignity + house)

**Pancha Mahapurusha has 5 distinct sub-types:**
- Ruchaka (Mars)
- Bhadra (Mercury)
- Hamsa (Jupiter)
- Malavya (Venus)
- Sasa (Saturn)

**Query pattern:** Users will ask "Does this chart have Pancha Mahapurusha?" and "Which one?" — requiring explicit enumeration.

### Decision

**Option A: Separate YogaId** — but with a single enum value and sub-type reporting.

**Rationale:**
1. Pancha Mahapurusha is a named classical yoga with explicit definition
2. Users need to query it specifically (not buried in general detection)
3. The 5 sub-types can be reported as details, not separate enum values
4. Cleaner API: `result.result_for(YogaId.PANCHA_MAHA PURUSHA_YOGA)`

**Implementation:**
- Single enum value: `PANCHA_MAHA PURUSHA_YOGA = "PANCHA_MAHA PURUSHA_YOGA"`
- In `YogaCondition.details`, report which specific yoga: `"Ruchaka Yoga: Mars in Aries (own sign) in 1st house (Kendra)"`
- This keeps the enum small while providing full information

**Confidence:** HIGH — This matches how classical texts treat it (one yoga category, five manifestations).

---

## Decision 4: Phase 3 vs Phase 4 Priority

### Question
What is the priority of Phase 3 (Advanced Features) vs Phase 4 (Named Yoga Expansion)?

### Phase 3 Items

| Gap | Effort | Impact | Dependencies |
|-----|--------|--------|--------------|
| Gap 7: Aspect asymmetry | HIGH | MEDIUM | None (decision: defer JRE-012 change) |
| Gap 11: Aspect chain validity | HIGH | MEDIUM | Gap 8 (dispositor chains) |
| Gap 12: Yoga cancellation | MEDIUM | HIGH | Gaps 3, 4, 5 (done in Phase 1) |
| Gap 13: Yoga accumulation | MEDIUM | LOW | All Phase 1 gaps |

### Phase 4 Items

| Gap | Effort | Impact | Dependencies |
|-----|--------|--------|--------------|
| Gap 14: Pancha Mahapurusha | LOW | MEDIUM | None (decision: separate YogaId) |
| Gap 15: Kendradhipati Dosha | LOW | LOW | None |

### Analysis

**Phase 3 has:**
- 1 HIGH effort item (aspect asymmetry — now deferred to knowledge layer)
- 1 HIGH effort item (aspect chain validity — requires dispositor chains)
- 1 MEDIUM effort item (yoga cancellation — ready to implement)
- 1 MEDIUM effort item (yoga accumulation — complex logic)

**Phase 4 has:**
- 2 LOW effort items (Pancha Mahapurusha, Kendradhipati Dosha)

**Impact comparison:**
- Phase 3 Gap 12 (yoga cancellation) has HIGH impact — currently yogas are reported as active even when cancelled
- Phase 3 Gap 13 (yoga accumulation) has LOW impact — edge case
- Phase 4 items have MEDIUM/LOW impact but are quick wins

### Decision

**Implement Phase 4 first, then Phase 3 Gap 12, then defer remaining Phase 3 items.**

**Rationale:**
1. **Phase 4 first:** Pancha Mahapurusha and Kendradhipati Dosha are LOW effort, MEDIUM/LOW impact — quick wins that add value
2. **Phase 3 Gap 12 second:** Yoga cancellation is MEDIUM effort, HIGH impact — important for accuracy
3. **Defer Phase 3 Gaps 7, 11, 13:** HIGH effort items that can wait for RI-010D

**Revised implementation order:**

```
Phase 1 (DONE): Parivartana, combustion, dignity, Dusthana, retrograde, connection hierarchy
    ↓
Phase 2 (RI-010C): Aspect strength in DrikResult, Neecha Bhanga
    ↓
Phase 4 (RI-010C): Pancha Mahapurusha, Kendradhipati Dosha
    ↓
Phase 3 Gap 12 (RI-010C): Yoga cancellation detection
    ↓
Phase 3 Gaps 7, 11, 13 (RI-010D): Aspect asymmetry, chain validity, accumulation
```

**Confidence:** HIGH — This optimizes for maximum value with minimum effort.

---

## Summary

| Question | Decision | Confidence |
|----------|----------|------------|
| Dispositor chains | Extend JRE-013 (not new engine) | HIGH |
| Aspect asymmetry | Implement in knowledge layer only (no JRE-012 change) | HIGH |
| Pancha Mahapurusha | Separate YogaId with sub-type reporting | HIGH |
| Phase 3 vs 4 priority | Phase 4 first, then Phase 3 Gap 12, defer rest | HIGH |

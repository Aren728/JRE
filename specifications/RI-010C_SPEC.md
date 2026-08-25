# RI-010C: YOGA ENGINE STRENGTH AND RELATIONSHIP ENHANCEMENTS

> **Status:** Specification — Updated with Architecture Decisions
> **Date:** 2026-08-25
> **Depends on:** RI-010A (Kendra-Trikona Research), RI-010B (Multi-Planet Research), Phase 1 Implementation (Complete)
> **Decisions:** ARCHITECTURE_DECISIONS.md (2026-08-25)

---

## 1. Objective

Enhance the JRE-012 (Drik) and JRE-013 (Yoga) engines to correctly incorporate classical yoga strength factors, named yogas, and relationship chain validation. This builds on Phase 1 (which added Parivartana classification, dignity-based strength, combustion penalty, Dusthana placement penalty, retrograde modification, and connection type hierarchy to JRE-013).

## 2. Architecture Decisions (from ARCHITECTURE_DECISIONS.md)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Dispositor chains | Extend JRE-013 (not new engine) | Dispositorship is consumed BY yoga detection; extending `_build_connection_map` pattern is natural |
| Aspect asymmetry | Knowledge layer only (no JRE-012 change) | JRE-012 already stores directional aspects; asymmetry is a STRENGTH property, not DETECTION |
| Pancha Mahapurusha | Separate YogaId with sub-type reporting | Named classical yoga; users need explicit query; 5 sub-types reported in details |
| Phase 3 vs 4 priority | Phase 4 first, then Phase 3 Gap 12, defer rest | Quick wins first, then high-impact cancellation detection |

## 3. STRICT CONSTRAINTS

- **NO modifications to src/jyotish/ (JRE-003) core models**
- **NO modifications to src/astronomy/ core models**
- **NO new JRE engines** — extend existing JRE-012 and JRE-013 only
- **NO new systems or CLI changes**
- **Backward compatible** — existing tests must continue to pass
- **No interpretation terms** in JRE modules (enforced by test_yoga_static.py)

## 4. Scope

### 4.1 Files to Modify

| File | Changes |
|------|---------|
| `src/drik/models.py` | Add `strength` field to `AspectApplication` (optional, backwards-compatible) |
| `src/drik/service.py` | Verify aspect strength computation is directional (no code change expected) |
| `src/yoga/models.py` | Add `YogaId.PANCHA_MAHA PURUSHA_YOGA`, `YogaId.KENDRADHIPATI_DOSHA`, `YogaResult.is_cancelled`, `YogaResult.cancellation_reasons` |
| `src/yoga/service.py` | Add Neecha Bhanga, Pancha Mahapurusha, Kendradhipati Dosha, yoga cancellation, dispositor chain detection |

### 4.2 Files to Create

| File | Purpose |
|------|---------|
| `tests/unit/drik/test_drik_aspect_strength.py` | Verify aspect strength in DrikResult is directional |
| `tests/unit/yoga/test_yoga_neecha_bhanga.py` | Tests for Neecha Bhanga detection |
| `tests/unit/yoga/test_yoga_pancha_mahapurusha.py` | Tests for Pancha Mahapurusha detection |
| `tests/unit/yoga/test_yoga_kendradhipati.py` | Tests for Kendradhipati Dosha detection |
| `tests/unit/yoga/test_yoga_cancellation.py` | Tests for yoga cancellation detection |
| `tests/unit/yoga/test_yoga_dispositor.py` | Tests for dispositor chain computation |

## 5. Implementation Tasks

**Execution order:** Tasks are ordered by the architecture decision: Phase 4 first (quick wins), then Phase 3 Gap 12, then remaining tasks.

---

### Task 1: Aspect Strength Verification (Gap 6 — Revised)

**Priority:** LOW (verification only)
**Effort:** LOW
**Decision:** No JRE-012 change; verify knowledge layer computes directional strength.

**Objective:** Verify that `pair(<A>,<B>).aspect_strength` in the knowledge layer is directional (A aspects B, not B aspects A).

**Classical Basis:** BPHS Ch.26 v.2-5 — Aspect strength varies by house position from the aspecter.

**Implementation:**

1. Read `src/knowledge/facts.py` — confirm `_aspect_strength_from_snapshot` uses `relative_houses[aspecter][aspected]` (directional)
2. Add test file `tests/unit/drik/test_drik_aspect_strength.py` with cases:
   - Mars in Aries aspects Saturn in Capricorn → Mars's 4th aspect = FULL
   - Saturn in Capricorn aspects Mars in Aries → Saturn's 3rd aspect = FULL
   - Same pair, different strengths depending on direction
3. If asymmetry is NOT captured, add directional logic to `derive_aspect_strength`

**Validation:**
- Tests verify directional strength computation
- No changes to JRE-012 models or service

---

### Task 2: Pancha Mahapurusha Yoga Detection (Gap 14)

**Priority:** HIGH (Phase 4 quick win)
**Effort:** LOW
**Decision:** Separate YogaId with sub-type reporting in details.

**Objective:** Detect the five Pancha Mahapurusha yogas (Ruchaka, Bhadra, Hamsa, Malavya, Sasa).

**Classical Basis:** BPHS Ch.33 — Planet in own sign or exaltation in Kendra:

| Yoga | Planet | Own Signs | Exaltation Sign | Condition |
|------|--------|-----------|-----------------|-----------|
| Ruchaka | Mars | Aries (1), Scorpio (8) | Capricorn (10) | In Kendra from Lagna |
| Bhadra | Mercury | Gemini (3), Virgo (6) | — | In Kendra from Lagna |
| Hamsa | Jupiter | Sagittarius (9), Pisces (12) | Cancer (4) | In Kendra from Lagna |
| Malavya | Venus | Taurus (2), Libra (7) | Pisces (12) | In Kendra from Lagna |
| Sasa | Saturn | Capricorn (10), Aquarius (11) | Libra (7) | In Kendra from Lagna |

**Implementation:**

1. Add `PANCHA_MAHA PURUSHA_YOGA = "PANCHA_MAHA PURUSHA_YOGA"` to `YogaId` enum
2. Add `_eval_pancha_mahapurusha` method to `YogaService`
3. Logic:
   - For each of the 5 planets (Mars, Mercury, Jupiter, Venus, Saturn):
     - Check if planet is in own sign or exaltation (use `_get_dignity`)
     - Check if planet's sign is Kendra from Lagna (use `house_from_lagna`)
     - If both conditions met → yoga present
4. Report in `YogaCondition.details`: `"Ruchaka: Mars in Aries (own) in 1st (Kendra)"`

**Validation:**
- 5 positive tests (one per yoga type)
- 5 negative tests (planet in own sign but not Kendra)
- 1 test for exaltation variant
- 1 test for absent when no conditions met

---

### Task 3: Kendradhipati Dosha Detection (Gap 15)

**Priority:** HIGH (Phase 4 quick win)
**Effort:** LOW
**Decision:** Separate YogaId.

**Objective:** Detect when natural benefics ruling Kendra houses lose beneficence.

**Classical Basis:** BPHS Ch.33 — Natural benefics (Jupiter, Venus, Mercury, Moon) ruling Kendras become functionally neutral.

**Implementation:**

1. Add `KENDRADHIPATI_DOSHA = "KENDRADHIPATI_DOSHA"` to `YogaId` enum
2. Add `_eval_kendradhipati_dosha` method to `YogaService`
3. Logic:
   - For each natural benefic (Jupiter, Venus, Mercury, Moon):
     - Check if planet rules any Kendra house (1, 4, 7, 10) from Lagna
     - If yes → Dosha present
4. Report in `YogaCondition.details`: `"Jupiter rules 7th (Kendra) — Kendradhipati Dosha"`

**Validation:**
- Tests for each natural benefic ruling Kendra
- Tests for natural malefics NOT triggering Dosha
- Tests for benefics NOT ruling Kendra

---

### Task 4: Yoga Cancellation Detection (Gap 12)

**Priority:** HIGH (Phase 3 Gap 12 — high impact)
**Effort:** MEDIUM
**Decision:** Add cancellation fields to YogaResult.

**Objective:** Detect when yoga conditions are cancelled by debilitation, combustion, or Dusthana placement.

**Classical Basis:** BPHS Ch.33 — Yoga cancelled if:
- Key planet debilitated (without Neecha Bhanga)
- Key planet combust
- Key planet in Dusthana (6/8/12)
- Malefic aspect on yoga planets

**Implementation:**

1. Add to `YogaResult`:
   - `is_cancelled: bool = False`
   - `cancellation_reasons: tuple[str, ...] = ()`
2. In each `_eval_*` method (after detecting yoga presence):
   - Check each yoga planet for cancellation conditions
   - If any planet triggers cancellation → set `is_cancelled = True`
   - Populate `cancellation_reasons` with specific reasons
3. Cancellation conditions (checked per planet):
   - Debilitated AND no Neecha Bhanga → `"Planet X debilitated in Y"`
   - Combust → `"Planet X combust (within Z° of Sun)"`
   - In Dusthana → `"Planet X in house Y (Dusthana)"`
   - Malefic aspect → `"Planet X aspected by malefic Y"`

**Validation:**
- Tests for each cancellation condition independently
- Tests for partial cancellation (some planets cancelled, others not)
- Tests for no cancellation when all planets strong
- Tests that `is_cancelled` does not change `is_present` (yoga exists but is weakened)

---

### Task 5: Neecha Bhanga Detection (Gap 2)

**Priority:** MEDIUM
**Effort:** MEDIUM
**Decision:** Integrate with Task 4 (cancellation detection).

**Objective:** Detect debilitation cancellation conditions that restore partial strength.

**Classical Basis:** Phaladeepika Ch.7 — 7 conditions for debilitation cancellation:

| # | Condition | Classical Source |
|---|-----------|------------------|
| 1 | Planet in exaltation aspects debilitated planet | Phaladeepika 7.1 |
| 2 | Planet in own sign aspects debilitated planet | Phaladeepika 7.1 |
| 3 | Debilitated planet's dispositor in Kendra from Lagna/Moon | Phaladeepika 7.2 |
| 4 | Debilitated planet in Kendra from Lagna/Moon | Phaladeepika 7.2 |
| 5 | Debilitated planet's dispositor aspects it | Phaladeepika 7.2 |
| 6 | Planet exalted in Navamsa (D9) | Phaladeepika 7.3 |
| 7 | Retrograde debilitated planet | BPHS Ch.3 |

**Implementation:**

1. Add `_check_neecha_bhanga` method to `YogaService`
2. Input: debilitated planet's BodyId, state_map, drik_result, lagna_num
3. Check each of the 7 conditions (skip condition 6 — D9 not yet available)
4. Return `tuple[str, ...]` of satisfied conditions
5. In `_compute_strength`: if Neecha Bhanga detected, increase dignity_factor from 0.1 toward 0.6
6. In yoga cancellation: if Neecha Bhanga detected, do NOT cancel for debilitation

**Validation:**
- Tests for conditions 1-5, 7 (skip 6)
- Tests for no Neecha Bhanga when no conditions met
- Tests that Neecha Bhanga restores partial strength
- Tests that Neecha Bhanga prevents cancellation

---

### Task 6: Dispositor Chain Computation (Gap 8)

**Priority:** MEDIUM
**Effort:** MEDIUM
**Decision:** Extend JRE-013 (not new engine).

**Objective:** Trace sign lord chains to identify final dispositor and chain strength.

**Classical Basis:** BPHS Ch.3 — Follow sign lords to trace influence chains.

**Implementation:**

1. Add `_build_dispositor_map` method to `YogaService`:
   - Input: `state_map: dict[BodyId, PlanetState]`
   - For each planet, find its dispositor (sign lord of occupied sign)
   - Trace chains until termination (planet in own sign = final dispositor)
   - Return `dict[BodyId, tuple[BodyId, ...]]` (planet → chain ending with final dispositor)
2. Add `include_dispositor_chains: bool = False` parameter to `identify_yogas`
3. When enabled, store dispositor chains in `YogaReport` (new field)
4. Expose final dispositor identification

**New YogaReport field:**
```python
dispositor_chains: dict[BodyId, tuple[BodyId, ...]] = field(default_factory=dict)
final_dispositor: BodyId | None = None
```

**Validation:**
- Tests for simple chain (A in B's sign, B in own sign)
- Tests for circular chain (A in B's sign, B in A's sign — mutual reception)
- Tests for final dispositor identification
- Tests for chain strength computation

---

## 6. Validation Criteria

- **pytest must pass 100%** (existing + new tests)
- **mypy --strict must pass** on src/drik/ and src/yoga/
- **ruff check must pass** on all modified files
- **test_yoga_static.py must pass** (no interpretation terms in JRE modules)
- **No regressions** in existing test suites

## 7. Out of Scope (Deferred to RI-010D)

| Gap | Reason for Deferral |
|-----|---------------------|
| Gap 7: Aspect direction asymmetry (JRE-012 change) | Knowledge layer already handles; no JRE-012 change needed |
| Gap 11: Aspect chain validity | Requires relationship graph; depends on dispositor chains (Task 6) |
| Gap 13: Multiple yoga accumulation | Complex logic; low impact; can wait |
| Gap 15: Dispositor chain strength weighting | Depends on Task 6; can be added incrementally |

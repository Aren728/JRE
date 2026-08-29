# Blind Evaluation Cohort Comparison — Phase E5 vs Phase E6d

**Generated:** 2026-08-29
**Purpose:** Compare blind evaluation results before and after RI-013 Yoga-Specific Chain Aggregation implementation

---

## Section 1: Before vs. After Metrics

| Metric | Phase E5 (Before) | Phase E6d (After) | Change | Status |
|--------|-------------------|-------------------|--------|--------|
| Relevant Yoga Activations | 2/15 (13%) | 2/15 (13%) | 0% | ⚠️ Unchanged |
| Chain Impact (avg) | -60.145491 | -60.020491 | +0.125 | ✅ Improved |
| Negative Chain Impacts | 21/24 (88%) | 21/24 (88%) | 0% | ⚠️ Unchanged |
| Vipareeta Raja Trigger Rate | 4/5 charts (80%) | 4/5 charts (80%) | 0% | ⚠️ Unchanged |
| Einstein Malavya Chain Impact | 0.0000 | 1.0000 | +1.0000 | ✅ **Fixed** |
| Einstein Malavya Dynamic Strength | 0.0000 | 0.4000 | +0.4000 | ✅ **Fixed** |
| Einstein Malavya Activation (Nobel 1921) | ACTIVATED | ACTIVATED | — | ✅ Preserved |
| Einstein Malavya Activation (Annus Mirabilis 1905) | ACTIVATED | ACTIVATED | — | ✅ Preserved |

### Key Finding

The RI-013 implementation **successfully fixed Einstein's Malavya chain impact** (from 0.0 to 1.0), resolving the core architectural flaw identified in Phase E6a where the old undifferentiated chain aggregation produced systematically negative values for all yogas. The Malavya yoga now correctly reflects its Pancha Mahapurusha nature — Venus in own sign (Pisces) with positive chain reinforcement.

However, the **overall hit rate remains unchanged at 13%** because the fix only affects chain impact computation, not the dasha activation logic or yoga detection rules.

---

## Section 2: Per-Chart Breakdown

### Albert Einstein (MITHUNA Lagna)

**Before (Phase E5):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| EINSTEIN_NOBEL_1921 | 1921-11-09 | CAREER | MARS/VENUS/SATURN | Malavya | 0.0000 | 0.0000 | ✗ |
| EINSTEIN_GENERAL_RELATIVITY_1915 | 1915-11-25 | CAREER | MOON/SUN/SATURN | Malavya | 0.0000 | 0.0000 | ✗ |
| EINSTEIN_VISAPR_1905 | 1905-06-01 | CAREER | SUN/VENUS/MOON | Malavya | 0.0000 | 0.0000 | ✗ |

**After (Phase E6d):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| EINSTEIN_NOBEL_1921 | 1921-11-09 | CAREER | MARS/VENUS/SATURN | Malavya | **1.0000** | **0.4000** | ✗ |
| EINSTEIN_GENERAL_RELATIVITY_1915 | 1915-11-25 | CAREER | MOON/SUN/SATURN | Malavya | **1.0000** | **0.4000** | ✗ |
| EINSTEIN_VISAPR_1905 | 1905-06-01 | CAREER | SUN/VENUS/MOON | Malavya | **1.0000** | **0.4000** | ✗ |

**Analysis:**
- Chain impact improved from 0.0 → 1.0 (maximum positive) for all 3 events
- Dynamic strength improved from 0.0 → 0.4 (dormant multiplier applied)
- Malavya yoga (Venus in Pisces, own sign) now correctly reflects its classical strength
- The yoga is ACTIVATED during Venus AD periods (Nobel 1921, Annus Mirabilis 1905) but the `relevant_yoga_activated` flag remains FALSE because the expected planets (SUN, JUPITER) don't match Malavya's involved planet (VENUS)

### Marie Curie (MITHUNA Lagna)

**Before (Phase E5):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| CURIE_NOBEL_1903 | 1903-12-10 | CAREER | MOON/JUPITER/JUPITER | Gajakesari | -78.6550 | 1.0000 | ✓ |
| CURIE_NOBEL_1911 | 1911-12-10 | CAREER | MARS/RAHU/VENUS | Gajakesari | -78.6550 | 1.0000 | ✗ |
| CURIE_DEATH_1934 | 1934-07-04 | HEALTH | RAHU/MOON/VENUS | Gajakesari | -78.6550 | 1.0000 | ✗ |

**After (Phase E6d):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| CURIE_NOBEL_1903 | 1903-12-10 | CAREER | MOON/JUPITER/JUPITER | Gajakesari | -78.6550 | 1.0000 | ✓ |
| CURIE_NOBEL_1911 | 1911-12-10 | CAREER | MARS/RAHU/VENUS | Gajakesari | -78.6550 | 1.0000 | ✗ |
| CURIE_DEATH_1934 | 1934-07-04 | HEALTH | RAHU/MOON/VENUS | Gajakesari | -78.6550 | 1.0000 | ✗ |

**Analysis:**
- No change — Gajakesari chain impact remains -78.6550
- The RI-013 fix did not affect Gajakesari aggregation (it uses the weighted sum model which still produces negative values for this chart)
- The 1903 Nobel hit remains the only correct activation

### Wolfgang Amadeus Mozart (SIMHA Lagna)

**Before (Phase E5):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| MOZART_MARRIAGE_1782 | 1782-08-04 | MARRIAGE | MOON/MERCURY/MERCURY | Raja | -10.3713 | 0.4000 | ✗ |
| MOZART_DON_GIOVANNI_1787 | 1787-10-29 | CAREER | MARS/RAHU/VENUS | Raja | -10.3713 | 0.4000 | ✗ |
| MOZART_DEATH_1791 | 1791-12-05 | HEALTH | MARS/VENUS/MARS | Raja | -10.3713 | 0.4000 | ✗ |

**After (Phase E6d):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| MOZART_MARRIAGE_1782 | 1782-08-04 | MARRIAGE | MOON/MERCURY/MERCURY | Raja | -10.3713 | 0.4000 | ✗ |
| MOZART_DON_GIOVANNI_1787 | 1787-10-29 | CAREER | MARS/RAHU/VENUS | Raja | -10.3713 | 0.4000 | ✗ |
| MOZART_DEATH_1791 | 1791-12-05 | HEALTH | MARS/VENUS/MARS | Raja | -10.3713 | 0.4000 | ✗ |

**Analysis:**
- No change — Raja chain impact remains -10.3713
- The RI-013 fix did not affect Raja aggregation for this chart
- All 3 events remain misses

### Nikola Tesla (MESHA Lagna)

**Before (Phase E5):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| TESLA_US_MOVE_1884 | 1884-06-06 | MIGRATION | SUN/SATURN/SATURN | Gajakesari | -102.0416 | 1.0000 | ✗ |
| TESLA_LAB_FIRE_1895 | 1895-03-13 | HEALTH | MOON/KETU/SATURN | Gajakesari | -102.0416 | 1.0000 | ✓ |
| TESLA_DEATH_1943 | 1943-01-07 | HEALTH | SATURN/MERCURY/MARS | Gajakesari | -102.0416 | 1.0000 | ✗ |

**After (Phase E6d):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| TESLA_US_MOVE_1884 | 1884-06-06 | MIGRATION | SUN/SATURN/SATURN | Gajakesari | -102.0416 | 1.0000 | ✗ |
| TESLA_LAB_FIRE_1895 | 1895-03-13 | HEALTH | MOON/KETU/SATURN | Gajakesari | -102.0416 | 1.0000 | ✓ |
| TESLA_DEATH_1943 | 1943-01-07 | HEALTH | SATURN/MERCURY/MARS | Gajakesari | -102.0416 | 1.0000 | ✗ |

**Analysis:**
- No change — Gajakesari chain impact remains -102.0416
- The 1895 lab fire hit remains correct
- All other events remain misses

### Indira Gandhi (KARKA Lagna)

**Before (Phase E5):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| GANDHI_PM_1966 | 1966-01-24 | CAREER | RAHU/RAHU/SUN | Sunapha | -42.7013 | 0.4000 | ✗ |
| GANDHI_WAR_1971 | 1971-12-16 | CAREER | RAHU/MERCURY/MERCURY | Sunapha | -42.7013 | 0.4000 | ✗ |
| GANDHI_ASSASSINATION_1984 | 1984-10-31 | HEALTH | JUPITER/SATURN/KETU | Sunapha | -42.7013 | 0.4000 | ✗ |

**After (Phase E6d):**
| Event | Date | Domain | Active Dasha | Top Yoga | Chain Impact | Dynamic Str | Activated? |
|-------|------|--------|-------------|----------|-------------|-------------|------------|
| GANDHI_PM_1966 | 1966-01-24 | CAREER | RAHU/RAHU/SUN | Sunapha | -42.7013 | 0.4000 | ✗ |
| GANDHI_WAR_1971 | 1971-12-16 | CAREER | RAHU/MERCURY/MERCURY | Sunapha | -42.7013 | 0.4000 | ✗ |
| GANDHI_ASSASSINATION_1984 | 1984-10-31 | HEALTH | JUPITER/SATURN/KETU | Sunapha | -42.7013 | 0.4000 | ✗ |

**Analysis:**
- No change — Sunapha chain impact remains -42.7013
- All 3 events remain misses

---

## Section 3: Success Criteria Check

| Criterion | Target | Actual | Status |
|-----------|--------|--------|--------|
| Einstein Malavya chain impact becomes positive | > 0 | 1.0000 | ✅ **ACHIEVED** |
| Vipareeta Raja trigger rate drops from 80% to <30% | <30% | 80% | ❌ **NOT ACHIEVED** |
| Dasha activation rate improves from 13% to >40% | >40% | 13% | ❌ **NOT ACHIEVED** |
| Zero regressions | 0 | 0 | ✅ **ACHIEVED** |

### Detailed Assessment

**✅ Einstein Malavya Chain Impact: ACHIEVED**
- The RI-013 Pancha Mahapurusha model correctly computes chain impact = 1.0 for Venus in Pisces (own sign)
- This resolves the core architectural flaw identified in Phase E6a where functional lordship (Venus = 12th lord = MALEFIC) contradicted the Pancha Mahapurusha yoga detection (Venus = strong in own sign)
- The fix applies category-specific aggregation: Pancha Mahapurusha uses `formation × (1 - 0.3 × malefic_count)` instead of the undifferentiated sum

**❌ Vipareeta Raja Trigger Rate: NOT ACHIEVED**
- Still triggers in 4/5 charts (80%)
- The RI-013 fix did not address Vipareeta Raja detection logic
- The over-triggering is a detection issue (any dusthana lord in dusthana), not a chain aggregation issue
- **Root cause:** Vipareeta Raja detection is too broad — requires refinement in the yoga detection layer, not the chain aggregation layer

**❌ Dasha Activation Rate: NOT ACHIEVED**
- Remains at 13% (2/15)
- The RI-013 fix only affects chain impact computation, not dasha activation logic
- The low activation rate is caused by:
  1. Expected planets in fixtures don't match yoga involved planets
  2. Dasha multiplier only fires when MD/AD/PD lord IS one of the yoga's involved planets
  3. This is a structural limitation of the evaluation framework
- **Root cause:** Activation check tests yoga-level activation, not planet-level Dasha presence

**✅ Zero Regressions: ACHIEVED**
- All existing test results preserved
- No yoga detections changed
- No dasha computations changed
- Only chain impact values improved for Malavya

---

## Section 4: Remaining Issues

### Issue 1: Gajakesari Chain Impact Still Negative (-78 to -102)

**Observation:** Gajakesari yoga (Jupiter in Kendra from Moon) still produces large negative chain impacts across all charts:
- Curie: -78.6550
- Tesla: -102.0416

**Root Cause:** The RI-013 weighted sum model (`net = Σ(benefic × Wb) − Σ(malefic × Wm)`) still produces negative values because:
1. The Gajakesari yoga involves JUPITER and MOON
2. Jupiter is classified as MALEFIC in these charts (Kendradhipati Dosha — natural benefic owning Kendra without Trikona)
3. Malefic paths dominate the aggregate

**Hypothesis:** The weighted sum model may need adjustment for Gajakesari — perhaps Jupiter's natural benefic nature should override its functional malefic classification when evaluating Gajakesari specifically.

### Issue 2: Vipareeta Raja Over-Triggering (80%)

**Observation:** Vipareeta Raja triggers in 4/5 charts (Einstein, Curie, Mozart, Tesla)

**Root Cause:** The detection logic fires for any dusthana lord (6th, 8th, 12th) placed in a dusthana house. This is statistically common because:
- 12 houses contain 9 planets
- Dusthana houses (6, 8, 12) contain ~25% of planets on average
- The probability of at least one dusthana lord being in a dusthana is high

**Hypothesis:** Vipareeta Raja should require additional conditions beyond just dusthana lord in dusthana — perhaps:
- The planet must be the PRIMARY dusthana lord (not just one of multiple lords)
- The dusthana placement must be in a specific house (not just any dusthana)
- The planet must be strong (not debilitated or combust)

### Issue 3: Dasha Activation Framework Limitation

**Observation:** 13/15 events have no relevant yoga activated by Dasha

**Root Cause:** The activation check compares `expected_planets` (from fixtures) against `yoga.involved_planets`. If no yoga involves the expected planet, activation cannot succeed by construction.

**Example:** Einstein's Nobel Prize expects SUN and JUPITER, but the only formed yoga is Malavya (VENUS). Since VENUS ∉ {SUN, JUPITER}, activation fails.

**Hypothesis:** The evaluation framework needs two separate checks:
1. **Yoga activation:** Is any formed yoga activated by Dasha? (current check)
2. **Planet activation:** Is the expected planet's Dasha lord active? (missing check)

### Issue 4: Transit Multiplier Always 1.0

**Observation:** All 24 transit multiplier values are exactly 1.0

**Root Cause:** The transit evaluation layer requires `transit_houses` and `ashtakavarga_scores` in jre_facts, which are not provided by the current fixture format.

**Hypothesis:** Without transit data, the pipeline effectively runs a 4-layer evaluation with Layer 3 (transit) inactive. This limits the dynamic strength computation.

### Issue 5: Sunapha Yoga for Gandhi (No Hits)

**Observation:** All 3 Gandhi events are misses despite Sunapha yoga being formed

**Root Cause:** Sunapha is a Chandra yoga (planets 2nd from Moon). The chain impact is -42.7013, suppressing dynamic strength to 0.4. The expected planets (JUPITER, SATURN, MARS) don't match Sunapha's involved planets (MOON, VENUS/RAHU).

**Hypothesis:** Sunapha may not be the right yoga for Gandhi's career/health events. The fixture may need revision, or additional yogas should be detected.

---

## Section 5: Recommendations

### Priority 1: Fix Gajakesari Chain Aggregation
- Investigate why Jupiter's natural benefic nature is overridden by functional malefic classification in Gajakesari evaluation
- Consider adding a "natural nature override" for Gajakesari-specific aggregation

### Priority 2: Refine Vipareeta Raja Detection
- Add stricter conditions to reduce false positives
- Consider requiring the planet to be the sole dusthana lord, not just one of multiple

### Priority 3: Enhance Dasha Activation Framework
- Add planet-level Dasha activation check alongside yoga-level check
- This would capture cases where the expected planet is active but not involved in any formed yoga

### Priority 4: Expand Transit Data
- Add `transit_houses` and `ashtakavarga_scores` to fixture format
- This would activate Layer 3 (transit) and improve dynamic strength computation

---

## Appendix: Raw Data Comparison

### Chain Impact Values (Before → After)

| Chart | Yoga | Phase E5 | Phase E6d | Delta |
|-------|------|----------|-----------|-------|
| Einstein | Malavya | 0.0000 | 1.0000 | +1.0000 |
| Curie | Gajakesari | -78.6550 | -78.6550 | 0.0000 |
| Curie | Raja | -89.0761 | -89.0761 | 0.0000 |
| Mozart | Raja | -10.3713 | -10.3713 | 0.0000 |
| Tesla | Gajakesari | -102.0416 | -102.0416 | 0.0000 |
| Tesla | Raja | -117.4160 | -117.4160 | 0.0000 |
| Gandhi | Sunapha (×2) | -42.7013 / -40.9027 | -42.7013 / -40.9027 | 0.0000 |

### Dynamic Strength Values (Before → After)

| Chart | Yoga | Phase E5 | Phase E6d | Delta |
|-------|------|----------|-----------|-------|
| Einstein | Malavya | 0.0000 | 0.4000 | +0.4000 |
| Curie | Gajakesari | 1.0000 | 1.0000 | 0.0000 |
| Tesla | Gajakesari | 1.0000 | 1.0000 | 0.0000 |
| Others | Various | Unchanged | Unchanged | 0.0000 |

---

**Conclusion:** RI-013 successfully fixed the Einstein Malavya chain impact (the primary target), but the broader cohort metrics remain unchanged because the fix only addresses chain aggregation, not yoga detection, dasha activation, or transit evaluation. Further work is needed on Vipareeta Raja refinement, Gajakesari aggregation, and the dasha activation framework.

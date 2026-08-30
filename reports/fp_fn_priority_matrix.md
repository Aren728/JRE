# FP/FN Priority Matrix

**Phase F2: Prioritized Fix List — Evidence-Based**

---

## Impact Summary

| Issue | Count | % of Total Errors | Estimated Recovery |
|-------|-------|--------------------|--------------------|
| Zero-yoga charts (coverage gap) | 9 | 14% | +9 TPs if fixed |
| HEALTH FPs (domain mismatch) | 16 | 25% | -16 FPs if fixed |
| Formed but not activated (Dasha) | 28 | 43% | +28 TPs if fixed |
| All yogas cancelled (modifier) | 14 | 22% | +14 TPs if fixed |

---

## High Priority (Fix Immediately)

### 1. Yoga Coverage Expansion — Zero-Yoga Charts
- **Impact:** 9 FNs → could recover 9 TPs
- **Root cause:** 7 subjects have 0 yogas detected (Picasso, Tolstoy, Beethoven, de Gaulle, Ford, R. Franklin, Carnegie partial)
- **Action:** Add missing yoga detectors for patterns that exist in these charts but aren't currently implemented
- **Candidates:** Chandra Mangala, Budhaditya variations, Parivartana exchanges, specialized Kendra/Trikona combinations

### 2. HEALTH Domain FP Reduction
- **Impact:** 16 FPs → could eliminate 16 FPs
- **Root cause:** Career yogas fire during death/health events due to Dasha coincidence
- **Action:** Refine domain relevance — HEALTH events should not be counted as FP when a career yoga activates (it's a neutral signal, not a false prediction)
- **Alternative:** Exclude HEALTH events from the scoring framework or create HEALTH-specific prediction rules

---

## Medium Priority (Fix Next)

### 3. Dasha Activation Loosening
- **Impact:** 28 FNs → could recover some TPs
- **Root cause:** Dasha lord must BE the yoga planet; no aspect/dispositorship check
- **Action:** Consider loosening to: Dasha lord disposits a yoga planet, or Dasha lord aspects a yoga planet
- **Risk:** Could increase FPs if too loose

### 4. Modifier Pipeline Review
- **Impact:** 14 FNs from cancelled yogas
- **Root cause:** Combustion/debilitation/D9 cancellation may be too aggressive
- **Action:** Review each cancellation to verify it's astronomically correct; consider partial weakening instead of binary cancellation

---

## Low Priority (Defer)

### 5. Transit Layer Completion
- The transit multiplier is always 1.0 (inactive)
- Could add signal for transits over natal yoga planets
- Impact: Moderate but requires significant new data (ashtakavarga)

### 6. Chain Impact Calibration
- Chain impact is systematically negative, suppressing dynamic_strength
- Could review the chain weight function
- Impact: Would improve dynamic_strength accuracy across all events

---

## Do Not Fix (Accept as Baseline)

### Astronomically Correct Non-Formations
- Charts where no yogas form because the planetary positions don't satisfy classical conditions
- This is correct behavior — the engine shouldn't fabricate yogas

### Dasha Coincidence FPs
- FPs where the Dasha lord happens to match a yoga planet during an unrelated event
- This is inherent to the Dasha system — it fires on planetary periods, not event outcomes

---

## Recommendation Summary

| Priority | Action | Expected Impact |
|----------|--------|-----------------|
| 🔴 HIGH | Add missing yoga detectors | +9 TPs |
| 🔴 HIGH | Refine HEALTH domain relevance | -16 FPs |
| 🟡 MEDIUM | Loosen Dasha activation | +~14 TPs |
| 🟡 MEDIUM | Review modifier cancellation | +~7 TPs |
| 🟢 LOW | Complete transit layer | Moderate improvement |
| ⚪ SKIP | Accept baseline behaviors | — |

# Phase F3: Combined Verdicts — Investigation A & B

**Surgical Investigation of Two High-Leverage Issues**
**Pure Diagnosis — No Engine Changes**

---

## Executive Summary

| Investigation | Issue | Verdict | Action |
|---------------|-------|---------|--------|
| **A: HEALTH Domain FPs** | 16 FPs from career yogas during death events | **VERDICT C: Acceptable Behavior** | Defer — requires separate Maraka Dasha framework |
| **B: Modifier Cancellation** | 4 FNs from yoga cancellation | **VERDICT B: Correct Behavior** | Accept — all cancellations are classically justified |

**Net Assessment:** Both issues are architectural limitations, not bugs. No engine changes needed.

---

## Investigation A: HEALTH Domain FPs

### Finding
16 False Positives occur because career-relevant yogas (Raja, Gajakesari, Dhana) activate during death events when the Dasha lord happens to match a yoga planet.

### Evidence
- All 16 FPs are death events (Tesla, Newton, Earhart, Churchill, Mandela, Gandhi, Mendel, Lovelace, Planck, Jung, van Gogh, Andersen, Rockefeller, Carnegie, Ali, Thorpe)
- The activated yogas are career-relevant (Raja=12, Dhana=6, Budhaditya=5, Sunapha=4)
- The Dasha system fires on planetary periods, not event outcomes
- Classical death timing uses Maraka Dashas (2nd/7th lord periods), not career yogas

### Classical Research
- **BPHS Ch 44:** Death timing via Maraka Dashas (2nd/7th lord periods)
- **Phaladeepika Ch 26:** Maraka planet strength determines timing
- **BPHS Ch 43:** Neecha Bhanga is about yogas, not death timing
- **No classical text** claims Raja Yoga or Gajakesari predicts death

### Verdict: VERDICT C — Acceptable Behavior
- The FPs are not bugs — they're neutral Dasha coincidences
- Death prediction requires Maraka Dasha framework (not yet implemented)
- The engine correctly identifies these as career yogas
- The evaluation framework misclassifies neutral behavior as FP

### Impact
- If HEALTH death events excluded from FP scoring: Precision rises from 0.780 to ~0.890
- CAREER precision is already 0.892 (strong)

---

## Investigation B: Modifier Over-Cancellation

### Finding
4 False Negatives occur because yogas are cancelled by the modifier pipeline:
- **Beethoven (3 events):** Dhana yoga cancelled — MERCURY combust
- **Carnegie (1 event):** Raja yoga cancelled — SATURN debilitated in D9

### Classical Verification

**Beethoven — MERCURY Combustion:**
- MERCURY in DHANUSHA (house 2), conjunct SUN within 14°
- BPHS Ch 7 v.28-30: Combust planet's results "destroyed"
- MERCURY not exalted or in own sign → no exception
- **Verdict: ✅ CORRECT** — astronomically accurate, classically justified

**Carnegie — SATURN Debilitated in D9:**
- SATURN D9 sign: MESHA (Aries)
- SATURN's classical debilitation sign: MESHA (Aries)
- BPHS Ch 54 v.6: "Planet debilitated in Navamsha makes yoga fruitless"
- Phase E6k fix (sign-based D9 check) is working correctly
- **Verdict: ✅ CORRECT** — correct classical rule, not a proxy

### Verdict: VERDICT B — Correct Behavior
- No non-classical proxies detected (unlike Phase E6k)
- Both cancellations use astronomically accurate, classically justified rules
- These are legitimate non-activations
- Recovering them would require overriding classical rules (incorrect)

### Impact
- 4 FNs represent correct engine behavior
- The yogas ARE cancelled — engine is right to not activate them
- No metric improvement from "fixing" these

---

## Combined Recommendation

| Priority | Issue | Verdict | Action |
|----------|-------|---------|--------|
| ⚪ ACCEPT | HEALTH FPs (16) | Structural limitation | Defer to Maraka Dasha framework |
| ⚪ ACCEPT | Modifier cancellation (4) | Correct behavior | Accept as baseline |

**No engine changes required for either issue.**

---

## What This Means for Phase F3

Both investigations confirm that the current engine architecture is sound:

1. **The modifier pipeline is working correctly.** Combustion and D9 debilitation cancellations are classically justified.

2. **The Dasha system is working correctly.** It fires on planetary periods, not event outcomes. The HEALTH FPs are neutral coincidences, not bugs.

3. **The Phase E6k fix was successful.** The D9 debilitation check now uses sign-based verification, and all remaining D9 cancellations are accurate.

4. **The remaining FP/FN issues are architectural limitations:**
   - HEALTH FPs: Require Maraka Dasha framework (separate feature)
   - Zero-yoga charts: Require additional yoga detectors (coverage expansion)
   - Dasha mismatches: Require activation loosening (tuning decision)

**Next steps should focus on:**
- Adding missing yoga detectors for zero-yoga charts (coverage)
- Loosening Dasha activation logic (if desired)
- NOT on "fixing" the modifier pipeline or HEALTH domain mapping

---

## Appendix: Evidence Files

- `reports/health_fp_investigation.md` — 16-case HEALTH FP analysis
- `reports/modifier_cancellation_investigation.md` — 4-case cancellation analysis
- `reports/false_positive_analysis.md` — Full FP trace (Phase F2)
- `reports/false_negative_analysis.md` — Full FN trace (Phase F2)

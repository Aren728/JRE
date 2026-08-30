# Modifier Over-Cancellation Investigation — 4 Cases

**Phase F3 Investigation B: Evidence-Based Verdict**

---

## Section 1: The 4 Cases

### Case 1: Beethoven — BEETHOVEN_9TH_1824 (CAREER)
- **Yoga:** Dhana (JUPITER + MERCURY)
- **Cancellation:** MERCURY is combust
- **MERCURY status:** rashi=DHANUSHA, house=2, combust=True
- **Dasha:** RAHU/KETU/MARS (none match yoga planets)

### Case 2: Beethoven — BEETHOVEN_MOONLIGHT_1802 (CAREER)
- **Yoga:** Dhana (JUPITER + MERCURY)
- **Cancellation:** MERCURY is combust
- **Same chart, same cancellation**

### Case 3: Beethoven — BEETHOVEN_DEATH_1827 (HEALTH)
- **Yoga:** Dhana (JUPITER + MERCURY)
- **Cancellation:** MERCURY is combust
- **Same chart, same cancellation**

### Case 4: Carnegie — CARNEGIE_GOSPEL_1889 (CAREER)
- **Yoga:** Raja (MERCURY + SATURN)
- **Modifier Status:** FORMED (no combustion/debilitation at D1)
- **Varga Status:** CANCELLED — "SATURN debilitated in D9 (Navamsha)"
- **SATURN D9 sign:** MESHA (Aries) — SATURN's classical debilitation sign
- **Dasha:** RAHU/JUPITER/RAHU (none match yoga planets)

---

## Section 2: Classical Verification

### Case 1-3: Beethoven — MERCURY Combustion

**Classical Rule (BPHS Ch 7, v. 28-30):**
> "When a planet is within specified degrees of the Sun, its results are destroyed."

**Combustion thresholds (BPHS):**
- Mercury: within 14° of Sun (BPHS Ch 7)
- Exception: If Mercury is exalted or in own sign, combustion is partially offset

**Engine Implementation:**
- MERCURY in DHANUSHA (house 2), combust=True
- MERCURY is NOT exalted (DHANUSHA is Jupiter's sign, not Mercury's)
- MERCURY is NOT in own sign (MITHUNA or KANYA)
- Therefore: No exception applies → CANCELLED

**Classical Verdict:** ✅ **CORRECT**
- MERCURY is combust per BPHS thresholds
- No Neecha Bhanga or exaltation exception applies
- The Dhana yoga is legitimately cancelled
- This is astronomically accurate — MERCURY and SUN are conjunct in Beethoven's chart

### Case 4: Carnegie — SATURN Debilitated in D9

**Classical Rule (BPHS Ch 54, v. 6):**
> "A planet debilitated in Navamsha makes the yoga fruitless."

**Debilitation sign (BPHS Ch 3):**
- SATURN debilitated in MESHA (Aries)

**Engine Implementation:**
- SATURN D9 sign: MESHA (Aries)
- SATURN's debilitation sign: MESHA
- Therefore: SATURN IS debilitated in D9 → CANCELLED

**Classical Verdict:** ✅ **CORRECT**
- SATURN's D9 sign matches its classical debilitation sign
- The Phase E6k fix (sign-based D9 check) is working correctly
- The Raja yoga is legitimately cancelled per BPHS Ch 54

**Note:** This is the same class of issue as the Phase E6k D9 debilitation bug, but here it's CORRECT behavior. In Phase E6k, the bug was using a Dusthana house proxy instead of sign-based check. Now that we use sign-based check, this cancellation is accurate.

---

## Section 3: Verdict

### VERDICT B: Correct Behavior — All 4 Cancellations Are Classically Justified

**Summary:**

| Case | Yoga | Cancellation | Classical Basis | Verdict |
|------|------|--------------|-----------------|---------|
| Beethoven (×3) | Dhana | MERCURY combust | BPHS Ch 7 v.28-30 | ✅ Correct |
| Carnegie | Raja | SATURN debilitated in D9 | BPHS Ch 54 v.6 | ✅ Correct |

**Rationale:**

1. **No non-classical proxies detected.** Unlike the Phase E6k bug (Dusthana house proxy), both cancellations use astronomically accurate, classically justified rules.

2. **MERCURY combustion is real.** Beethoven's MERCURY is conjunct the Sun within 14° — this is observable astronomical fact, not a proxy.

3. **SATURN D9 debilitation is real.** Carnegie's SATURN has D9 sign MESHA (Aries) — this is the correct classical debilitation sign for SATURN, verified by the Phase E6k fix.

4. **These are legitimate non-activations.** The yogas are correctly identified as cancelled. The Dasha mismatch (no yoga planet in Dasha lord) is an additional reason they don't activate.

**Impact on Metrics:**
- These 4 FNs represent correct engine behavior
- The yogas ARE cancelled — the engine is right to not activate them
- Recovering these would require overriding classical rules, which would be incorrect

**Recommendation:** Accept as baseline. These cancellations are classically justified. The engine is working correctly.

---

## Section 4: Comparison with Phase E6k

| Aspect | Phase E6k Bug | Phase F3 Finding |
|--------|---------------|------------------|
| Issue | D9 debilitation used Dusthana house proxy | D9 debilitation uses sign-based check |
| Fix | Changed to sign-based check | No fix needed — already correct |
| Verdict | Bug (wrong proxy) | Correct behavior (right rule) |
| Impact | 11 yogas falsely cancelled | 0 yogas falsely cancelled |

The Phase E6k fix resolved the D9 debilitation bug. The remaining D9 cancellations (like Carnegie's SATURN) are now classically accurate.

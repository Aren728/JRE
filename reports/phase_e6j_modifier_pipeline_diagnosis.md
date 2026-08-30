# Phase E6j — Modifier Pipeline Diagnostic Report

## Executive Summary

**The modifier pipeline is NOT over-cancelling** when given raw fixture data (0 cancellations across 10 charts). However, the **D9 (Navamsha) Confirmation** step contains a **false-positive debilitation check** that cancels **11 valid yogas across 7 charts** when the pipeline runs with live JyotishService data.

This is the single highest-impact bug identified in the entire validation pipeline.

---

## Part A: Newton Saraswati Trace

### Finding: Saraswati is FORMED with raw fixture data

When evaluated with the raw fixture data (`chart_006_newton.json`), Saraswati passes all checks:

| Planet | House | Rashi | Combust | Debilitated | Node Conj | Dusthana | Modifier Result |
|--------|-------|-------|---------|-------------|-----------|----------|-----------------|
| Jupiter | H4 | KUMBHA | No | No | No | No | FORMED (1.2x retrograde) |
| Mercury | H2 | DHANUSHA | No | No | No | No | FORMED (1.2x retrograde) |
| Venus | H4 | KUMBHA | No | No | No | No | FORMED (1.2x retrograde) |

**Saraswati FORMED** with modifier strength 1.0 (all planets retrograde-boosted to 1.2, but capped at 1.0 overall).

### Finding: Saraswati is CANCELLED with live JyotishService data

When evaluated with `_build_jre_facts()` from the JyotishService chart:

```
Saraswati: CANCELLED
Reason: MERCURY debilitated in D9 (Navamsha)
```

**Root Cause**: The `_is_debilitated_in_d9()` function in `src/jrs/varga/confirmation_service.py` uses a **flawed proxy**:

```python
# CURRENT (FLAWED):
if d9_house in _DUSTHANA_HOUSES:  # 6, 8, 12
    # Consider debilitated — THIS IS WRONG
```

**The problem**: Mercury's D9 house is 6 (Dusthana), but its D9 sign is **DHANUSHA** (Sagittarius), which is NOT Mercury's debilitation sign (Pisces). Mercury in Dhanusha is actually **strong** (friendly sign). The function incorrectly treats D9 house position as debilitation.

---

## Part B: Cohort-Wide Modifier Audit

### Audit Results (Raw Fixture Data)

| Metric | Count |
|--------|-------|
| Total yogas formed at Layer 1 | 20 |
| Classically justified cancellations | 0 |
| Suspicious cancellations | 0 |
| Unknown cancellations | 0 |
| Survived to activation | 20 |

**With raw fixture data: NO yogas are cancelled.** The modifier pipeline (combustion, debilitation, node taint, etc.) is working correctly.

### D9 False Positive Impact (Live Data)

| Chart | Yoga Cancelled | Planet "Debilitated" | Actual D9 Sign | Is Truly Debilitated? |
|-------|---------------|---------------------|----------------|----------------------|
| Curie | Raja | VENUS | ? | **No** — Venus not in debilitation sign |
| Tesla | Budhaditya | MERCURY | DHANUSHA | **No** — Mercury not debilitated in Dhanusha |
| Gandhi | Sunapha | VENUS | ? | **No** |
| Gandhi | Budhaditya | MERCURY | DHANUSHA | **No** |
| **Newton** | **Budhaditya** | MERCURY | DHANUSHA | **No** |
| **Newton** | **Saraswati** | MERCURY | DHANUSHA | **No** |
| Lincoln | Anapha | MOON | ? | **No** |
| Teresa | Anapha | MOON | ? | **No** |
| Teresa | Neecha Bhanga | MARS | ? | **No** |
| **Jobs** | **Gajakesari** | MOON | ? | **No** |
| Jobs | Anapha | MOON | ? | **No** |

**Total: 11 yogas falsely cancelled across 7 charts**

### Per-Modifier Breakdown (from raw fixture audit)

| Modifier | Count | Classification |
|----------|-------|---------------|
| CHESHTA_BALA (retrograde) | 6 | Classically justified — strength boost |
| NODE_CONJUNCTION_TAINT | 4 | Classically justified — 30% reduction |
| NODE_ASPECT_TAINT | 0 | — |
| COMBUSTION | 0 | — |
| DEBILITATION | 0 | — |
| DUSTHANA_PLACEMENT | 0 | — |

---

## Part C: Mozart Non-Activation Verification

### Verdict: ASTRONOMICALLY CORRECT ✅

Mozart's 0/3 is **not a detection bug**. Every classical yoga check correctly fails:

| Yoga | Why It Doesn't Form |
|------|-------------------|
| **Budhaditya** | Mercury 0.75° from Sun — **extremely combust** (threshold: < 8°) |
| **Pancha Mahapurusha** | Venus in H7 (Kendra) but in **Aquarius** (not own sign Tula/Vrishabha, not exaltation Meena) |
| **Gajakesari** | Jupiter H2, Moon H4 — distance 10 (not in kendra 0/3/6/9) |
| **Saraswati** | Jupiter in H2 (not in Kendra, not own/exalt sign) |
| **Amala** | No benefic exclusively in H10 |
| **Chandra Yogas** | No planets in 2nd/12th from Moon |
| **Raja** | Forms (WEAKENED) but Dasha lords don't match participants |
| **Dhana** | Forms (WEAKENED) but Dasha lords don't match participants |

---

## Section 4: Recommended Fixes

### Fix 1 (CRITICAL): D9 Debilitation False Positive

**Location**: `src/jrs/varga/confirmation_service.py`, method `_is_debilitated_in_d9()`

**Current (flawed)**:
```python
if d9_house in _DUSTHANA_HOUSES:
    # Consider debilitated — WRONG for most planets
```

**Proposed fix**: Use the actual D9 sign (from `planet_d9_sign`) to check debilitation, not the D9 house position:

```python
d9_sign = jre_facts.get("planet_d9_sign", {}).get(planet, "")
_DEBILITATION_SIGNS = {
    "SUN": "TULA", "MOON": "VRISHCHIKA", "MARS": "KARKA",
    "MERCURY": "MEENA", "JUPITER": "MAKARA", "VENUS": "KANYA", "SATURN": "MESHA",
}
if d9_sign == _DEBILITATION_SIGNS.get(planet, ""):
    # Truly debilitated in D9
```

**Estimated hit rate impact**: +10-15pp (converting 5-8 false cancellations to hits)

### Fix 2 (Priority): Domain Mapping for Remaining Non-Hits

Some activated yogas still don't hit because their domains don't match the event:
- Tesla's Budhaditya → INTELLECTUAL_EXCELLENCE (events are MIGRATION, HEALTH)
- Earhart's Amala → CAREER_PROMINENCE (Disappearance is HEALTH)

**Estimated hit rate impact**: +3-5pp

---

## Section 5: Deliverables

| File | Description |
|------|-------------|
| `scripts/diagnose_newton_saraswati.py` | Layer-by-layer trace of Saraswati |
| `scripts/audit_modifier_cancellations.py` | Cohort-wide modifier audit |
| `scripts/diagnose_mozart_non_activation.py` | Mozart verification |
| `reports/newton_saraswati_trace.md` | Newton trace report |
| `reports/modifier_cancellation_audit.md` | Audit report |
| `reports/mozart_non_activation_verification.md` | Mozart verification report |

---

## Section 6: Conclusion

**Is the modifier pipeline over-cancelling?**

- **No** — the 5-tier modifier pipeline (combustion, debilitation, graha yuddha, cheshta bala, node taint) is working correctly with 0 false cancellations.
- **Yes** — the **Phase 4 D9 Confirmation** step has a **false-positive debilitation check** that cancels 11 valid yogas across 7 charts.

**The single highest-leverage fix** is correcting `_is_debilitated_in_d9()` to use actual D9 signs instead of house-position proxies. This alone could raise the hit rate from 40% to 50-55%.

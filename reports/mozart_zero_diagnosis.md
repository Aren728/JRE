# Mozart Zero-Hit Diagnosis — Phase E6h Track B

## Executive Summary

W.A. Mozart (1756-01-27, Simha Lagna) produces **0/3 yoga activations** in the engine.
This diagnosis traces every classical yoga that should or shouldn't form, and identifies
the exact root causes of the engine's failure to produce relevant activations.

## Section 1: Mozart Chart Summary

- **Lagna**: SIMHA
- **Moon**: Vrishchika (Jyeshta Nakshatra)
- **Key feature**: Sun, Mercury, Saturn in H6 (Makara) — dusthana concentration
- **Jupiter**: H2 (Kanya/Virgo) — debilitated, not in kendra from Moon
- **Venus**: H7 (Kumbha/Aquarius) — functional malefic (3rd/10th lord)

## Section 2: Engine Detection

Engine detects: []

**The engine returns 0 yogas for Mozart.** This is because:
1. `evaluate_classical_yogas()` requires `house` data in planet facts
2. The fixture may not include `house` field (computed from rashi+lagna)
3. Even with houses, only Gajakesari and Raja have detectors

## Section 3: Classical Yoga Checks

| Yoga | Status | Reason |
|------|--------|--------|
| Budhaditya | FORMED | SUN and MERCURY in house 6 (MAKARA) | Engine: ✗ |
| Gajakesari | NOT_FORMED | Jupiter H2 NOT in kenda from Moon H4 (diff=10) | Engine: ✗ |
| Hamsa | NOT_FORMED | Jupiter in KANYA H2 (not in kendra or own/exalted sign) | Engine: ✗ |
| Saraswati | NOT_FORMED | J=2 M=6 V=7 — not all in kendra, or Jupiter not strong | Engine: ✗ |
| Raja | FORMED | Kendra lord SATURN(H6) conjunct Trikona lord SUN(H6) | Engine: ✗ |
| Dhana | FORMED | MERCURY and MERCURY conjunct in H6 | Engine: ✗ |

## Section 4: Gap Analysis

### Yogas that SHOULD form but engine doesn't detect:

- **Budhaditya**: SUN and MERCURY in house 6 (MAKARA)
- **Raja**: Kendra lord SATURN(H6) conjunct Trikona lord SUN(H6)
- **Dhana**: MERCURY and MERCURY conjunct in H6

### Root Cause: Missing Yoga Detectors

The engine's `evaluate_classical_yogas()` only implements **4 yogas**:
1. Gajakesari (Jupiter kendra from Moon)
2. Raja (Kendra lord conjunct Trikona lord)
3. Vipareeta Raja (Dusthana lord in dusthana)
4. Dhana (2nd + 11th lord conjunct)

**Missing classical yoga detectors:**
- Budhaditya
- Raja
- Dhana

## Section 5: Recommended Fixes

### Priority 1: Implement Budhaditya Detector
Sun-Mercury conjunction is common and significant. Add to `evaluate_classical_yogas()`:
```python
# Budhaditya Yoga
if sun_house == merc_house:
    # Check Mercury not combust
    if not mercury_combust:
        results.append(evaluate_formation('Budhaditya', ['SUN', 'MERCURY'], facts))
```

### Priority 2: Implement Pancha Mahapurusha Detector
Five yogas based on Mars/Mercury/Jupiter/Venus/Saturn in own sign in Kendra.

### Priority 3: Implement Sunapha/Anapha Detector
Moon-centered yogas based on planets in 2nd/12th from Moon.

### Priority 4: Implement Saraswati Detector
Jupiter/Mercury/Venus all in Kendras with strong Jupiter.

### Note on Domain Mapping
Even if all yogas were detected, the domain mapping must include ARTISTIC_EXCELLENCE
for Budhaditya, Saraswati, and Bhadra to match Mozart's CAREER events.

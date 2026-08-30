# Phase F3 — Error Attribution Report

## Executive Summary

| Metric | DEV (30 charts) | VAL (10 charts) | Combined |
|--------|-----------------|-----------------|----------|
| Total Events | 90 | 30 | 120 |
| True Positives | 60 | 16 | 76 |
| False Positives | 11 | 2 | 13 |
| False Negatives | 19 | 12 | 31 |
| Precision | 0.854 | — | 0.854 |
| Recall | 0.710 | — | 0.710 |


## Layer-by-Layer Failure Distribution

### False Negatives (Root Cause)

| Category | Count | % | Description |
|----------|-------|---|-------------|
| Coverage Gap | 9 | 29.0% | No classical yoga detected for this domain |
| Formation Failed | 9 | 29.0% | Yoga cancelled by modifiers (combustion/D9/debilitation) |
| Dasha Mismatch | 13 | 41.9% | Yoga formed but MD/AD/PD didn't align with yoga planets |
| Transit Penalty | 0 | 0.0% | BAV transit multiplier dropped strength below threshold |
| Domain Mapping | 0 | 0.0% | Yoga activated but mapped domains don't include event domain |

### False Positives (Root Cause)

| Category | Count | % | Description |
|----------|-------|---|-------------|
| Domain Overlap | 5 | 38.5% | Yoga activated for different domain than event |
| Weak Activation | 0 | 0.0% | Dynamic strength < 0.3 but still triggered |
| Dasha Coincidence | 8 | 61.5% | Dasha aligned by chance, no causal link |
| Modifier Over-Cancellation | 0 | 0.0% | Yoga incorrectly cancelled by modifier pipeline |

### False Negatives by Domain

| Domain | Count | % |
|--------|-------|---|
| CAREER | 21 | 67.7% |
| HEALTH | 10 | 32.3% |

### False Positives by Domain

| Domain | Count | % |
|--------|-------|---|
| HEALTH | 8 | 61.5% |
| CAREER | 4 | 30.8% |
| MARRIAGE | 1 | 7.7% |

### False Negatives by Subject

| Subject | FN Count | Top Category |
|---------|----------|--------------|
| Charles de Gaulle | 3 | Dasha Mismatch |
| Rosalind Franklin | 3 | Dasha Mismatch |
| Ludwig van Beethoven | 3 | Coverage Gap |
| Pablo Picasso | 3 | Coverage Gap |
| Leo Tolstoy | 3 | Coverage Gap |
| Wolfgang Amadeus Mozart | 2 | Formation Failed |
| Steve Jobs | 2 | Dasha Mismatch |
| John F. Kennedy | 2 | Formation Failed |
| Albert Einstein | 1 | Dasha Mismatch |
| Indira Gandhi | 1 | Dasha Mismatch |
| Isaac Newton | 1 | Formation Failed |
| Winston Churchill | 1 | Dasha Mismatch |
| Margaret Thatcher | 1 | Formation Failed |
| Queen Victoria | 1 | Dasha Mismatch |
| Gregor Mendel | 1 | Formation Failed |
| Charlie Chaplin | 1 | Dasha Mismatch |
| Pyotr Tchaikovsky | 1 | Formation Failed |
| Anton Chekhov | 1 | Formation Failed |

### False Positives by Subject

| Subject | FP Count | Top Category |
|---------|----------|--------------|
| Mahatma Gandhi | 3 | Dasha Coincidence |
| Wolfgang Amadeus Mozart | 1 | Domain Overlap |
| Nikola Tesla | 1 | Dasha Coincidence |
| Isaac Newton | 1 | Domain Overlap |
| Amelia Earhart | 1 | Dasha Coincidence |
| Winston Churchill | 1 | Domain Overlap |
| Nelson Mandela | 1 | Dasha Coincidence |
| Gregor Mendel | 1 | Domain Overlap |
| Carl Jung | 1 | Dasha Coincidence |
| Hans Christian Andersen | 1 | Domain Overlap |
| Anton Chekhov | 1 | Dasha Coincidence |


## The Hit List — Prioritized Fixes for Phase F4

Based on the error attribution, here are the top 5 specific, actionable fixes
ordered by expected impact on F1 score:

### Priority 1: Add Missing Yoga Detectors for Zero-Yoga Charts

- **Impact:** 9 FNs across 3 subjects
- **Details:** Subjects: Leo Tolstoy, Ludwig van Beethoven, Pablo Picasso. These charts have no classical yogas detected. Need additional detectors (Vasumati, Neecha Bhang, etc.).
- **Expected Recovery:** +9 TPs

### Priority 2: Loosen Dasha Activation Logic (Add Dispositor/Aspect Matching)

- **Impact:** 13 FNs across 8 subjects
- **Details:** Yogas formed but MD/AD/PD lords don't match yoga planets. Adding dispositor chain or aspect-based matching could recover many.
- **Expected Recovery:** +6 to +13 TPs

### Priority 3: Review Modifier Pipeline Thresholds

- **Impact:** 9 FNs
- **Details:** Yogas cancelled by combustion/debilitation/D9. Review if thresholds are too aggressive.
- **Expected Recovery:** +4 TPs

### Priority 4: Refine Domain Mapping to Reduce False Positives

- **Impact:** 5 FPs
- **Details:** Yogas activated for wrong domain. Add death/health exclusion logic for career yogas.
- **Expected Recovery:** -5 FPs



## Appendix A: Detailed False Positive Traces

### FP #1: Wolfgang Amadeus Mozart — MOZART_MARRIAGE_1782

- **Domain:** MARRIAGE
- **Category:** Domain Overlap
- **Dasha:** MD=MOON / AD=MERCURY
- **Activated Yogas:**
  - Dhana (strength: N/A)

### FP #2: Nikola Tesla — TESLA_DEATH_1943

- **Domain:** HEALTH
- **Category:** Dasha Coincidence
- **Dasha:** MD=SATURN / AD=MERCURY
- **Activated Yogas:**
  - Raja (strength: N/A)
  - Dhana (strength: N/A)
  - Budhaditya (strength: N/A)

### FP #3: Isaac Newton — NEWTON_DEATH_1727

- **Domain:** HEALTH
- **Category:** Domain Overlap
- **Dasha:** MD=SATURN / AD=JUPITER
- **Activated Yogas:**
  - Raja (strength: N/A)
  - Saraswati (strength: N/A)

### FP #4: Amelia Earhart — EARHART_DISAPPEARANCE_1937

- **Domain:** HEALTH
- **Category:** Dasha Coincidence
- **Dasha:** MD=MARS / AD=RAHU
- **Activated Yogas:**
  - Raja (strength: N/A)

### FP #5: Winston Churchill — CHURCHILL_DEATH_1965

- **Domain:** HEALTH
- **Category:** Domain Overlap
- **Dasha:** MD=MERCURY / AD=VENUS
- **Activated Yogas:**
  - Raja (strength: N/A)
  - Dhana (strength: N/A)

### FP #6: Nelson Mandela — MANDELA_DEATH_2013

- **Domain:** HEALTH
- **Category:** Dasha Coincidence
- **Dasha:** MD=SATURN / AD=MARS
- **Activated Yogas:**
  - Sunapha (strength: N/A)
  - Dhudhara (strength: N/A)
  - Budhaditya (strength: N/A)

### FP #7: Mahatma Gandhi — GANDHI_SALT_1930

- **Domain:** CAREER
- **Category:** Dasha Coincidence
- **Dasha:** MD=RAHU / AD=VENUS
- **Activated Yogas:**
  - Gajakesari (strength: N/A)
  - Raja (strength: N/A)

### FP #8: Mahatma Gandhi — GANDHI_INDEPENDENCE_1947

- **Domain:** CAREER
- **Category:** Dasha Coincidence
- **Dasha:** MD=JUPITER / AD=MOON
- **Activated Yogas:**
  - Gajakesari (strength: N/A)

### FP #9: Mahatma Gandhi — GANDHI_ASSASSINATION_1948

- **Domain:** HEALTH
- **Category:** Dasha Coincidence
- **Dasha:** MD=JUPITER / AD=MOON
- **Activated Yogas:**
  - Gajakesari (strength: N/A)
  - Raja (strength: N/A)

### FP #10: Gregor Mendel — MENDEL_DEATH_1884

- **Domain:** HEALTH
- **Category:** Domain Overlap
- **Dasha:** MD=RAHU / AD=MOON
- **Activated Yogas:**
  - Sunapha (strength: N/A)

### FP #11: Carl Jung — JUNG_COLLECTIVE_1916

- **Domain:** CAREER
- **Category:** Dasha Coincidence
- **Dasha:** MD=MARS / AD=RAHU
- **Activated Yogas:**
  - Sunapha (strength: N/A)

### FP #12: Hans Christian Andersen — ANDERSEN_DEATH_1875

- **Domain:** HEALTH
- **Category:** Domain Overlap
- **Dasha:** MD=JUPITER / AD=SATURN
- **Activated Yogas:**
  - Neecha Bhanga (strength: N/A)

### FP #13: Anton Chekhov — CHEKHOV_CHERRY_1904

- **Domain:** CAREER
- **Category:** Dasha Coincidence
- **Dasha:** MD=MARS / AD=RAHU
- **Activated Yogas:**
  - Raja (strength: N/A)
  - Budhaditya (strength: N/A)


## Appendix B: Detailed False Negative Traces

### FN #1: Albert Einstein — EINSTEIN_GENERAL_RELATIVITY_1915

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=MOON / AD=SUN
- **Chart Yogas:**
  - Vipareeta Raja (status: FORMED, activation: DORMANT)
  - Malavya (status: FORMED, activation: DORMANT)

### FN #2: Wolfgang Amadeus Mozart — MOZART_DON_GIOVANNI_1787

- **Domain:** CAREER
- **Category:** Formation Failed
- **Dasha:** MD=MARS / AD=RAHU
- **Chart Yogas:**
  - Raja (status: WEAKENED, activation: DORMANT)
  - Dhana (status: CANCELLED, activation: DORMANT)

### FN #3: Wolfgang Amadeus Mozart — MOZART_DEATH_1791

- **Domain:** HEALTH
- **Category:** Formation Failed
- **Dasha:** MD=MARS / AD=VENUS
- **Chart Yogas:**
  - Raja (status: WEAKENED, activation: DORMANT)
  - Dhana (status: CANCELLED, activation: DORMANT)

### FN #4: Indira Gandhi — GANDHI_ASSASSINATION_1984

- **Domain:** HEALTH
- **Category:** Dasha Mismatch
- **Dasha:** MD=JUPITER / AD=SATURN
- **Chart Yogas:**
  - Sunapha (status: WEAKENED, activation: DORMANT)
  - Sunapha (status: WEAKENED, activation: DORMANT)
  - Budhaditya (status: FORMED, activation: DORMANT)

### FN #5: Isaac Newton — NEWTON_LUCASIAN_1669

- **Domain:** CAREER
- **Category:** Formation Failed
- **Dasha:** MD=MARS / AD=RAHU
- **Chart Yogas:**
  - Raja (status: CANCELLED, activation: DORMANT)
  - Budhaditya (status: FORMED, activation: DORMANT)
  - Saraswati (status: CANCELLED, activation: DORMANT)

### FN #6: Steve Jobs — JOBS_APPLE_1976

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=VENUS / AD=SATURN
- **Chart Yogas:**
  - Gajakesari (status: WEAKENED, activation: DORMANT)
  - Vipareeta Raja (status: FORMED, activation: DORMANT)
  - Dhana (status: WEAKENED, activation: DORMANT)
  - Anapha (status: WEAKENED, activation: DORMANT)

### FN #7: Steve Jobs — JOBS_OUSTED_1985

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=SUN / AD=SATURN
- **Chart Yogas:**
  - Gajakesari (status: WEAKENED, activation: DORMANT)
  - Vipareeta Raja (status: FORMED, activation: DORMANT)
  - Dhana (status: WEAKENED, activation: DORMANT)
  - Anapha (status: WEAKENED, activation: DORMANT)

### FN #8: Winston Churchill — CHURCHILL_PM_1940

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=JUPITER / AD=RAHU
- **Chart Yogas:**
  - Raja (status: FORMED, activation: DORMANT)
  - Dhana (status: WEAKENED, activation: DORMANT)
  - Anapha (status: FORMED, activation: DORMANT)

### FN #9: John F. Kennedy — JFK_CUBAN_MISSILE_1962

- **Domain:** CAREER
- **Category:** Formation Failed
- **Dasha:** MD=RAHU / AD=MERCURY
- **Chart Yogas:**
  - Gajakesari (status: WEAKENED, activation: DORMANT)
  - Raja (status: FORMED, activation: DORMANT)
  - Sunapha (status: CANCELLED, activation: DORMANT)

### FN #10: John F. Kennedy — JFK_ASSASSINATION_1963

- **Domain:** HEALTH
- **Category:** Formation Failed
- **Dasha:** MD=RAHU / AD=MERCURY
- **Chart Yogas:**
  - Gajakesari (status: WEAKENED, activation: DORMANT)
  - Raja (status: FORMED, activation: DORMANT)
  - Sunapha (status: CANCELLED, activation: DORMANT)

### FN #11: Margaret Thatcher — THATCHER_FALKLANDS_1982

- **Domain:** CAREER
- **Category:** Formation Failed
- **Dasha:** MD=JUPITER / AD=MERCURY
- **Chart Yogas:**
  - Dhana (status: CANCELLED, activation: DORMANT)
  - Sasa (status: FORMED, activation: DORMANT)
  - Sunapha (status: WEAKENED, activation: DORMANT)
  - Anapha (status: WEAKENED, activation: DORMANT)
  - Dhudhara (status: WEAKENED, activation: DORMANT)

### FN #12: Charles de Gaulle — DEGAULLE_LIBERATION_1944

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=RAHU / AD=JUPITER
- **Chart Yogas:**
  - Ruchaka (status: FORMED, activation: DORMANT)

### FN #13: Charles de Gaulle — DEGAULLE_PRESIDENT_1959

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=JUPITER / AD=JUPITER
- **Chart Yogas:**
  - Ruchaka (status: FORMED, activation: DORMANT)

### FN #14: Charles de Gaulle — DEGAULLE_DEATH_1970

- **Domain:** HEALTH
- **Category:** Dasha Mismatch
- **Dasha:** MD=JUPITER / AD=MOON
- **Chart Yogas:**
  - Ruchaka (status: FORMED, activation: DORMANT)

### FN #15: Queen Victoria — VICTORIA_DEATH_1901

- **Domain:** HEALTH
- **Category:** Dasha Mismatch
- **Dasha:** MD=SATURN / AD=SATURN
- **Chart Yogas:**
  - Raja (status: WEAKENED, activation: DORMANT)
  - Sunapha (status: WEAKENED, activation: DORMANT)
  - Sunapha (status: WEAKENED, activation: DORMANT)

### FN #16: Gregor Mendel — MENDEL_PUBLICATION_1866

- **Domain:** CAREER
- **Category:** Formation Failed
- **Dasha:** MD=MARS / AD=KETU
- **Chart Yogas:**
  - Dhana (status: FORMED, activation: DORMANT)
  - Sunapha (status: CANCELLED, activation: DORMANT)
  - Saraswati (status: FORMED, activation: DORMANT)
  - Amala (status: FORMED, activation: DORMANT)
  - Vasumati (status: FORMED, activation: DORMANT)

### FN #17: Rosalind Franklin — FRANKLIN_PHOTO51_1952

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=MARS / AD=MERCURY
- **Chart Yogas:**
  - Vipareeta Raja (status: FORMED, activation: DORMANT)

### FN #18: Rosalind Franklin — FRANKLIN_DNA_1953

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=MARS / AD=KETU
- **Chart Yogas:**
  - Vipareeta Raja (status: FORMED, activation: DORMANT)

### FN #19: Rosalind Franklin — FRANKLIN_DEATH_1958

- **Domain:** HEALTH
- **Category:** Dasha Mismatch
- **Dasha:** MD=RAHU / AD=RAHU
- **Chart Yogas:**
  - Vipareeta Raja (status: FORMED, activation: DORMANT)

### FN #20: Ludwig van Beethoven — BEETHOVEN_9TH_1824

- **Domain:** CAREER
- **Category:** Coverage Gap
- **Dasha:** MD=RAHU / AD=KETU
- **Chart Yogas:**
  - Dhana (status: CANCELLED, activation: DORMANT)

### FN #21: Ludwig van Beethoven — BEETHOVEN_MOONLIGHT_1802

- **Domain:** CAREER
- **Category:** Coverage Gap
- **Dasha:** MD=MOON / AD=SATURN
- **Chart Yogas:**
  - Dhana (status: CANCELLED, activation: DORMANT)

### FN #22: Ludwig van Beethoven — BEETHOVEN_DEATH_1827

- **Domain:** HEALTH
- **Category:** Coverage Gap
- **Dasha:** MD=RAHU / AD=VENUS
- **Chart Yogas:**
  - Dhana (status: CANCELLED, activation: DORMANT)

### FN #23: Pablo Picasso — PICASSO_GUERNICA_1937

- **Domain:** CAREER
- **Category:** Coverage Gap
- **Dasha:** MD=JUPITER / AD=JUPITER
- **Chart Yogas:**

### FN #24: Pablo Picasso — PICASSO_BLUE_1901

- **Domain:** CAREER
- **Category:** Coverage Gap
- **Dasha:** MD=MOON / AD=MOON
- **Chart Yogas:**

### FN #25: Pablo Picasso — PICASSO_DEATH_1973

- **Domain:** HEALTH
- **Category:** Coverage Gap
- **Dasha:** MD=MERCURY / AD=KETU
- **Chart Yogas:**

### FN #26: Leo Tolstoy — TOLSTOY_WAR_AND_PEACE_1869

- **Domain:** CAREER
- **Category:** Coverage Gap
- **Dasha:** MD=RAHU / AD=RAHU
- **Chart Yogas:**

### FN #27: Leo Tolstoy — TOLSTOY_ANNA_KARENINA_1877

- **Domain:** CAREER
- **Category:** Coverage Gap
- **Dasha:** MD=RAHU / AD=MERCURY
- **Chart Yogas:**

### FN #28: Leo Tolstoy — TOLSTOY_DEATH_1910

- **Domain:** HEALTH
- **Category:** Coverage Gap
- **Dasha:** MD=SATURN / AD=VENUS
- **Chart Yogas:**

### FN #29: Charlie Chaplin — CHAPLIN_GOLD_RUSH_1925

- **Domain:** CAREER
- **Category:** Dasha Mismatch
- **Dasha:** MD=MARS / AD=SUN
- **Chart Yogas:**
  - Raja (status: WEAKENED, activation: DORMANT)
  - Vipareeta Raja (status: FORMED, activation: DORMANT)

### FN #30: Pyotr Tchaikovsky — TCHAIKOVSKY_SWAN_1877

- **Domain:** CAREER
- **Category:** Formation Failed
- **Dasha:** MD=RAHU / AD=RAHU
- **Chart Yogas:**
  - Gajakesari (status: WEAKENED, activation: DORMANT)
  - Raja (status: WEAKENED, activation: DORMANT)
  - Dhana (status: CANCELLED, activation: DORMANT)
  - Anapha (status: WEAKENED, activation: DORMANT)

### FN #31: Anton Chekhov — CHEKHOV_DEATH_1904

- **Domain:** HEALTH
- **Category:** Formation Failed
- **Dasha:** MD=MARS / AD=RAHU
- **Chart Yogas:**
  - Gajakesari (status: FORMED, activation: DORMANT)
  - Raja (status: CANCELLED, activation: DORMANT)
  - Sunapha (status: FORMED, activation: DORMANT)
  - Budhaditya (status: CANCELLED, activation: DORMANT)



## HOLDOUT Readiness

- ✅ **No rules, weights, or engine logic were modified during this phase.**
- ✅ Error attribution is purely diagnostic — no calibration performed.
- ✅ The HOLDOUT set (10 charts, 30 events) remains locked and untouched.
- ✅ Engine is ready for Phase F4 calibration, after which the HOLDOUT set
  will be evaluated exactly once for final performance metrics.

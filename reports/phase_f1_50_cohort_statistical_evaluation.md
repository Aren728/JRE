# Phase F1: 50-Chart Cohort Statistical Evaluation

**Strictly Blind Evaluation — No Calibration or Tuning**

**Cohort Size:** 10 subjects | **Total Events:** 30

---

## Section 1: Core Statistical Metrics

| Metric | Value |
|--------|-------|
| **True Positives (TP)** | 19 |
| **False Positives (FP)** | 4 |
| **False Negatives (FN)** | 7 |
| **Precision** | 0.826 |
| **Recall** | 0.731 |
| **F1 Score** | 0.776 |
| **Hit Rate (TP/Total)** | 0.633 (19/30) |
| **95% Confidence Interval** | [0.461, 0.806] |

### Interpretation

- **Precision** (0.826): Of all events where the engine predicted a relevant yoga activation, 82.6% were actually relevant to the event domain.
- **Recall** (0.731): Of all events where a relevant yoga existed and was activated, the engine correctly identified 73.1%.
- **F1 Score** (0.776): Harmonic mean of precision and recall, balancing false positives and false negatives.
- **95% CI**: The true hit rate lies between 46.1% and 80.6% with 95% confidence (Wilson score interval).

---

## Section 2: Domain Breakdown

| Domain | Events | TP | FP | FN | Precision | Recall | F1 |
|--------|--------|----|----|-----|-----------|--------|-----|
| CAREER | 19 | 13 | 2 | 4 | 0.867 | 0.765 | 0.812 |
| HEALTH | 10 | 5 | 2 | 3 | 0.714 | 0.625 | 0.667 |
| MIGRATION | 1 | 1 | 0 | 0 | 1.000 | 1.000 | 1.000 |

---

## Section 3: Per-Subject Breakdown

| Subject | Events | TP | FP | FN | Precision | Recall | F1 |
|---------|--------|----|----|-----|-----------|--------|-----|
| Andrew Carnegie | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Babe Ruth | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Cornelius Vanderbilt | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Henry Ford | 3 | 0 | 0 | 3 | 0.000 | 0.000 | 0.000 |
| J.P. Morgan | 3 | 1 | 0 | 2 | 1.000 | 0.333 | 0.500 |
| Jackie Robinson | 3 | 2 | 0 | 1 | 1.000 | 0.667 | 0.800 |
| Jesse Owens | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| Jim Thorpe | 3 | 0 | 3 | 0 | 0.000 | 0.000 | 0.000 |
| John D. Rockefeller | 3 | 1 | 1 | 1 | 0.500 | 0.500 | 0.500 |
| Muhammad Ali | 3 | 3 | 0 | 0 | 1.000 | 1.000 | 1.000 |

---

## Section 4: False Positive Analysis

**Total FPs: 4**

| Subject | Event | Domain | Detail |
|---------|-------|--------|--------|
| John D. Rockefeller | ROCKEFELLER_DEATH_1937 | HEALTH | Yoga activated but not relevant to domain/event |
| Jim Thorpe | THORPE_OLYMPICS_1912 | CAREER | Yoga activated but not relevant to domain/event |
| Jim Thorpe | THORPE_NFL_1920 | CAREER | Yoga activated but not relevant to domain/event |
| Jim Thorpe | THORPE_DEATH_1953 | HEALTH | Yoga activated but not relevant to domain/event |

---

## Section 5: False Negative Analysis

**Total FNs: 7**

| Subject | Event | Domain | Detail |
|---------|-------|--------|--------|
| Henry Ford | FORD_MODEL_T_1908 | CAREER | No yoga activated during event |
| Henry Ford | FORD_ASSEMBLY_1913 | CAREER | No yoga activated during event |
| Henry Ford | FORD_DEATH_1947 | HEALTH | No yoga activated during event |
| John D. Rockefeller | ROCKEFELLER_STD_1870 | CAREER | No yoga activated during event |
| J.P. Morgan | MORGAN_PANIC_1907 | CAREER | No yoga activated during event |
| J.P. Morgan | MORGAN_DEATH_1913 | HEALTH | No yoga activated during event |
| Jackie Robinson | ROBINSON_DEATH_1972 | HEALTH | No yoga activated during event |

---

## Section 6: Methodology

### Evaluation Framework
- **Strictly blind**: The engine has no access to ground-truth event outcomes during prediction generation.
- **No calibration**: All weights, thresholds, and logic are frozen from the pre-F1 architecture.
- **No post-hoc adjustments**: Results are reported exactly as the pipeline produces them.

### Classification Rules
- **TP (True Positive)**: A relevant yoga was activated by the active Dasha during the event window.
- **FP (False Positive)**: A yoga was activated but was not relevant to the event domain or involved planets.
- **FN (False Negative)**: No yoga was activated despite a relevant yoga existing in the chart.

### Confidence Interval
- **Method**: Wilson score interval (normal approximation).
- **Coverage**: 95% confidence level.
- **Rationale**: Wilson score is preferred over Wald interval for binomial proportions, especially when p is near 0 or 1.

### Pipeline Layers
1. **Layer 1 — Relationship Graph**: Structural detection (conjunctions, aspects, dispositorship, exchanges)
2. **Layer 1.5 — Chain Evaluator**: Multi-hop Kendra-Trikona chain impact
3. **Layer 2 — Modifiers**: 5-tier priority (combustion, debilitation, graha yuddha, retrograde, node taint)
4. **Layer 3 — Temporal**: Vimshottari Dasha multiplier (transit inactive)
5. **Layer 4 — Varga**: D9 (Navamsha) confirmation

# RI-013 Validation Plan

## Objective

Validate the Yoga-specific chain aggregation models defined in RI-013 against:
1. The 5-chart cohort (Einstein, Curie, Mozart, Tesla, Gandhi) — known canonical facts
2. 12 synthetic test cases in the test matrix (TC001–TC012) — edge cases

The goal is to confirm that the new aggregation models resolve the three systemic failures identified in Phase E5/E6:
- 100% negative chain impacts
- 80% Vipareeta Raja over-trigger rate
- 13% Dasha activation rate

---

## Methodology

### Step 1: Synthetic Test Matrix Validation

Run each of the 12 test cases through the proposed aggregation models and confirm expected outcomes.

| Test Case | Yoga | Expected Status | Validation Method |
|---|---|---|---|
| TC001 | Gajakesari | FORMED, positive chain | Compute: W_benefic=0.8, W_malefic=0.5 |
| TC002 | Gajakesari | FORMED, weakened | Verify never-cancelled rule |
| TC003 | Budhaditya | FORMED, positive chain | Compute: W_benefic=1.0 |
| TC004 | Budhaditya | CANCELLED | Verify any-malefic-cancels rule |
| TC005 | Budhaditya | FORMED (immunity) | Verify own-sign immunity |
| TC006 | Malavya | FORMED (immunity) | Verify Pancha Mahapurusha immunity |
| TC007 | Vipareeta Raja | FORMED (legitimate) | Verify primary dusthana lordship |
| TC008 | Vipareeta Raja | NOT_FORMED (false positive fix) | Verify Kendra-lord exclusion |
| TC009 | Kemadruma | FORMED, HIGH | Verify isolation |
| TC010 | Kemadruma | CANCELLED | Verify benefic cancellation |
| TC011 | Raja | FORMED, positive chain | Compute: W_benefic=1.0, W_malefic=0.7 |
| TC012 | Ruchaka | FORMED, weakened | Verify Pancha Mahapurusha immunity |

### Step 2: Cohort Baseline Comparison

For each chart in the cohort, run the current engine (Phase E5 baseline) and record results:

#### Einstein (chart_001_pilot.json)
| Yoga | Phase E5 Chain Impact | RI-013 Expected |
|---|---|---|
| Malavya | −167.35 | Positive (>0) — Venus own-sign immunity |
| Vipareeta Raja | Formed, negative chain | Evaluate: Is Venus primarily a dusthana lord? (No — owns H5+H12, primary role is Kendra/Trikona) → Should be NOT_FORMED |
| Sunapha | Formed, negative chain | Should use Chandra model: W_benefic=0.6, W_malefic=0.8 |

#### Curie (chart_002_curie.json)
| Yoga | Phase E5 Chain Impact | RI-013 Expected |
|---|---|---|
| Gajakesari | Formed, negative chain | Should use Gajakesari model: W_benefic=0.8, W_malefic=0.5 |
| Sunapha | Formed, negative chain | Should use Chandra model |

#### Mozart (chart_003_mozart.json)
| Yoga | Phase E5 Chain Impact | RI-013 Expected |
|---|---|---|
| Raja | Formed, negative chain | Should use Raja model: W_benefic=1.0, W_malefic=0.7 |
| Vipareeta Raja | Formed, negative chain | Evaluate primary dusthana lordship |

#### Tesla (chart_004_tesla.json)
| Yoga | Phase E5 Chain Impact | RI-013 Expected |
|---|---|---|
| Gajakesari | Formed, negative chain | Should use Gajakesari model |
| Sunapha | Formed, negative chain | Should use Chandra model |

#### Gandhi (chart_005_gandhi.json)
| Yoga | Phase E5 Chain Impact | RI-013 Expected |
|---|---|---|
| Sunapha | Formed, negative chain | Should use Chandra model |
| Anapha | Formed, negative chain | Should use Chandra model |

### Step 3: Discrepancy Analysis

For each chart, compare Phase E5 results vs. RI-013 expected results:

| Discrepancy Type | Definition | Action |
|---|---|---|
| **Sign Mismatch** | Chain impact sign flips from negative to positive (or vice versa) | Verify formula correctness |
| **Magnitude Mismatch** | Chain impact magnitude differs by >50% from expected | Adjust category weights |
| **Status Mismatch** | Yoga status changes (FORMED → NOT_FORMED or CANCELLED) | Verify formation rules |
| **False Positive** | Yoga should NOT form but does (Vipareeta Raja) | Add exclusion rules |
| **False Negative** | Yoga should form but doesn't | Verify formation rules |

### Step 4: Root Cause Attribution

For each remaining discrepancy, attribute to one of:

| Root Cause | Description | Fix |
|---|---|---|
| **Formation Rule** | Yoga shouldn't have formed | Fix detection logic |
| **Aggregation Model** | Formula needs weight adjustment | Tune W_benefic/W_malefic |
| **Relevance Filter** | Wrong chains are being counted | Fix chain filtering |
| **Immunity Condition** | Missing or wrong immunity check | Add/fix immunity rules |
| **Functional Lordship** | Planet classification is wrong for this yoga | Add yoga-specific override |

### Step 5: Iterative Refinement

1. Apply fixes based on Step 4 analysis
2. Re-run Steps 1-3
3. Repeat until convergence (all 12 synthetic cases pass, all 5 cohort charts show expected improvements)

### Step 6: Statistical Validation

After convergence, measure:

| Metric | Phase E5 Baseline | Target | Measurement |
|---|---|---|---|
| **Chain Impact Sign** | 100% negative | >50% positive for classically strong yogas | Count positive vs. negative across all formed yogas |
| **Activation Rate** | 13% (2/15) | >50% (8/15) | Count events where relevant Yoga was activated |
| **Vipareeta Raja Rate** | 80% (4/5) | <30% (≤1/5) | Count charts where Vipareeta Raja triggers |
| **False Positive Rate** | Unknown | 0% | Count yogas that shouldn't form but do |
| **False Negative Rate** | Unknown | <10% | Count yogas that should form but don't |

---

## Execution Plan

### Phase A: Synthetic Validation (Day 1)

1. Implement `YogaSpecificChainAggregator` class with category-specific weights
2. Run TC001–TC012 through the new aggregator
3. Assert all 12 test cases pass
4. If any fail, debug and fix

### Phase B: Cohort Comparison (Days 2-3)

1. Run all 5 charts through the updated engine
2. Compare chain impact signs and magnitudes against Phase E5 baseline
3. Create discrepancy matrix
4. Identify root causes for each discrepancy

### Phase C: Refinement (Days 4-5)

1. Fix aggregation models based on discrepancy analysis
2. Re-run Phase A and B
3. Iterate until convergence

### Phase D: Statistical Validation (Day 6)

1. Run full blind evaluation (all 5 charts × 3 events = 15 events)
2. Measure activation rate, Vipareeta Raja rate, false positive/negative rates
3. Compare against Phase E5 baseline

### Phase E: Final Report (Day 7)

1. Document all changes and their rationale
2. Create before/after comparison table
3. Identify remaining gaps and future work items
4. Update RI-013 specification with final calibrated weights

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Aggregation models produce new false positives | Medium | High | Include false positive check in Phase D |
| Weight calibration requires many iterations | High | Medium | Start with conservative weights, adjust incrementally |
| Some yogas lack classical weight guidance | Medium | Low | Use default weights from RI-013 table |
| Cohort too small for statistical significance | High | Medium | Use synthetic test matrix as primary validation |

---

## Success Criteria

The validation is considered successful when:

1. ✅ All 12 synthetic test cases pass (TC001–TC012)
2. ✅ Einstein's Malavya chain impact becomes positive (>0)
3. ✅ Vipareeta Raja trigger rate drops from 80% to <30%
4. ✅ Dasha activation rate increases from 13% to >50%
5. ✅ No new false positives introduced
6. ✅ All existing Reconstruction Gate tests (585) still pass
7. ✅ Full test suite (1,726+) passes with zero regressions

# Yoga Engine Calibration Report

## Summary

- **Total charts tested:** 20
- **Total True Positives:** 10
- **Total False Positives:** 0
- **Total False Negatives:** 0
- **Total True Negatives:** 10
- **Overall Precision:** 1.0000
- **Overall Recall:** 1.0000
- **Overall F1 Score:** 1.0000

---

## Budhaditya Yoga Detection

| Metric | Value |
|--------|-------|
| Charts Tested | 10 |
| True Positives | 5 |
| False Positives | 0 |
| False Negatives | 0 |
| True Negatives | 5 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1 Score | 1.0000 |

## Gajakesari Yoga Detection

| Metric | Value |
|--------|-------|
| Charts Tested | 10 |
| True Positives | 5 |
| False Positives | 0 |
| False Negatives | 0 |
| True Negatives | 5 |
| Precision | 1.0000 |
| Recall | 1.0000 |
| F1 Score | 1.0000 |

---

## Methodology

- **Detection Logic:** Budhaditya = Sun and Mercury in the same house. 
  Gajakesari = Jupiter in kendra (1, 4, 7, 10) from Moon.
- **Dataset:** 20 synthetic charts (10 per yoga type: 5 positive, 5 negative).
- **Ground Truth:** Manually verified classical yoga formation conditions.
- **Engine:** `YogaEvaluatorService.evaluate_classical_yogas()` + detection helpers.

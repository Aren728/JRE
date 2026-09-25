# Phase 5C Specification — Transit / Gochara Integration

**Status:** Draft
**Predecessor:** Phase 5B (Ashtakavarga calculation engine, golden-state 6th stage, `ashta_scoring_enabled` flag)
**Baseline to protect:** Frozen benchmark Micro-F1 = 0.7435 (TP=71, FP=31, FN=18 over 120 events; gate threshold 0.7385)

---

## 1. Goal

Integrate the Phase 5B Ashtakavarga engine with the existing temporal
layer (`jrs.temporal`) so that predicted yoga activations are modulated
by transit (Gochara) quality: a yoga activating during a dasha window
while its lord transits a high-SAV sign scores higher; one activating
through a low-SAV sign is dampened. The integration must be:

- **Deterministic** — no wall-clock, randomness, or unordered iteration;
  byte-identical outputs for identical inputs (goldens must verify).
- **Flag-isolated** — all transit modulation sits behind a versioned
  feature flag (`gochara_scoring_enabled`, default **False**) so the
  frozen benchmark baseline cannot silently regress.
- **Provenance-complete** — every modulation emits `REL-GOCHARA-*` nodes
  linking the RULE node, the FACT-ASHTA-* evidence, and the TEMPORAL
  node, closing the Phase 5 exit criterion for REL-* vocabulary.
- **Benchmark-governed** — every rule adjustment runs the 40-chart
  corpus with side-by-side F1 comparison (flag off vs flag on).

## 2. Existing Surfaces (no duplication)

| Surface | Owner | Role in 5C |
|---------|-------|-----------|
| `jrs.temporal.ashtakavarga_service.AshtakavargaService.compute_profile` | JRE temporal | transit positions + per-planet `PlanetTransitInfo` at a reference instant |
| `jrs.calculations.ashtakavarga.compute_full_ashtakavarga` | Phase 5B | natal BAV/SAV/Shodhita rows (FACT-ASHTA-*) |
| `jrs.validation.golden_state.CANONICAL_STAGE_IDS` | Phase 2/5B | 6th stage `ashtakavarga`; 5C adds a 7th stage `gochara` |
| `jrs.prediction_engine.provenance` | Phase 3/5A/5B | DAG emission (FACT-*, RULE-*, TEMPORAL; 5C adds REL-*) |
| `scripts/error_attribution.py`, `jrs.validation.error_taxonomy` | F3/5A | DASHA_MISMATCH / timing attribution gets a transit-quality axis |

## 3. Core Calculation: Transit Quality Score (TQS)

For a predicted activation of yoga Y with involved planets P at target
instant T:

```
TQS(Y, T) = mean over p in P of sav_score(sign_of(p at T))
```

- `sav_score` is the natal Shodhita SAV of the sign p occupies at T
  (fallback: raw SAV when Shodhita is unavailable — must be recorded in
  the report under `tqs_basis`).
- `PlanetTransitInfo` from `compute_profile` supplies sign-of-planet at
  T; the reference instant is pinned (`GOLDEN_TRANSIT_DATE` semantics —
  never wall-clock) for any golden/hashed path.
- Normalized bands (aligning with the classical 337/12 ≈ 28 mean):
  - `TQS >= 30` → multiplier 1.08 (supportive gochara)
  - `25 <= TQS < 30` → 1.00 (neutral)
  - `18 <= TQS < 25` → 0.92 (mixed)
  - `TQS < 18` → 0.80 (afflicted gochara)
  Bands are frozen in `GOCHARA_BANDS` (a module constant, versioned
  with the stage) — not magic numbers inline.

## 4. Pipeline Wiring

1. `jrs.temporal.gochara_service` (new): `compute_tqs(jre_facts,
   yoga_evals, target_instant) -> GocharaReport` returning per-yoga TQS,
   band, multiplier, and `REL-GOCHARA-<YOGA_ID>` relation ids. Reads the
   Phase 5B report from `jre_facts["ashtakavarga"]` when
   `ashta_scoring_enabled` is on; computes raw SAV inline otherwise
   (read-only; no facts mutation).
2. `YogaEvaluatorService` gains an optional gochara modulation step in
   the dynamic-strength chain, gated by `gochara_scoring_enabled()`
   (default False, env `JRS_GOCHARA_SCORING`). Off-path is a no-op:
   byte-identical to current output.
3. Provenance: when the flag is on, `build_provenance_chain` emits
   `REL-*` edges/edges-attributes `TRANSIT_SUPPORTS` (TQS band ≥
   neutral) or `TRANSIT_DAMPENS` (below) from each RULE node to the
   relevant `FACT-ASHTA-SAV` node and the TEMPORAL node.

## 5. Golden-State & Benchmark Invariants

- New canonical stage `gochara` appended **after** `ashtakavarga`
  (`CANONICAL_STAGE_IDS` grows to 7). Schema version stays `1.0.0`
  (additive stage; manifests regenerate; all existing stage hashes must
  remain stable).
- The golden stage records the **flag-independent** TQS report at the
  pinned transit instant — mirroring the 5B pattern where the golden
  stage is hashable regardless of scoring flags.
- Benchmark gate: flag-off run must remain exactly
  TP=71/FP=31/FN=18, F1=0.7435. First flag-on run establishes the
  `BASELINE_*_GOCHARA` companion constants via the same
  recharacterization procedure used in Phase F4/5B.

## 6. Error-Attribution Extension (Phase 5A hook)

`ErrorKind.DASHA_MISMATCH` splits on transit quality in attributed
detail: failures whose timing window overlapped but whose TQS was
afflicted (< 18) gain detail suffix `transit_dampened=TQS <value>`.
This is diagnostic-only — it must not change verdicts or counts.

## 7. Acceptance Criteria

- [ ] `gochara` stage present in all 50 golden manifests; prior 6 stage
      hashes unchanged per fixture.
- [ ] Flag off: benchmark gate PASS with unchanged confusion matrix.
- [ ] Flag on: gate still PASS or the F1 delta is reported side-by-side
      in `reports/gochara_calibration_metrics.md` (no silent regressions).
- [ ] `REL-GOCHARA-*` nodes present in flag-on evidence graphs and
      absent from flag-off graphs (byte-identical to current goldens).
- [ ] Deterministic JSON fixture + unit tests for `compute_tqs`, band
      mapping, and REL emission; strict mypy clean.
- [ ] Diagnostic CLI (see `scripts/ashtakavarga_diagnostics.py`) gains a
      `--gochara <instant>` mode rendering the TQS table.

## 8. Out of Scope (5C)

- Interpretive text generation (forecast wording) — later phase.
- Transit-to-natal house linking beyond sign-level SAV lookup.
- Any change to the frozen corpus fixtures or manifest hashes.

# JRE-BENCH-002 — Pre-Registered Benchmark Corpus Expansion

- **Benchmark id:** `JRE-BENCH-002`
- **Status:** `PRE_REGISTERED` (analysis plan locked before any new data is scored)
- **Parent benchmark:** `JRE-BENCH-001` (frozen, immutable — 40 charts / 120 events / 30 closed-world + 10 open-world)
- **Seal target:** `benchmarks/JRE-BENCH-002.json` (sealed by `scripts/seal_benchmark.py` when the corpus completes; this document precedes it)
- **Power analysis:** `scripts/bench002_power.py` (exact binomial, dependency-free; numbers below are recomputed by `tests/unit/jrs/benchmarks/test_bench002_preregistration.py`)
- **Governing seal discipline:** immutable-in-place policy inherited from JRE-BENCH-001 — the corpus, labels, protocol, and thresholds are never mutated after sealing.

## 1. Motivation

The Phase 10 ablation matrix (JRE-ABLATION-001) found the multi-varga
D9/D10 rescue to be the only verdict-moving mechanism on
JRE-BENCH-001: its removal collapses Micro-F1 from the sealed companion
0.7565 to the gating baseline 0.7435, with **2 discordant pairs**
(b=2, c=0) over 120 scored events — exact two-sided McNemar
**p = 0.5**, verdict `INSIGNIFICANT_POSITIVE`.

The effect is directionally consistent but statistically
underpowered: the corpus yields a discordant density of
2/120 ≈ 0.0167 pairs per scored event, far below the 6-pair minimum
for significance at α = 0.05 under the observed one-directional
pattern. This pre-registration locks the expansion design and the
analysis before any new data is collected, so the resulting p-values
carry confirmatory (not exploratory) weight.

## 2. Locked Analysis Plan

### 2.1 Primary hypothesis (H1 — multi-varga rescue)

**H1:** The D9/D10 cross-varga rescue's contribution replicates on the
expanded corpus with sign consistency: in the paired
FULL-minus-VARGA ablation, more events regress than improve when the
mechanism is removed (b > c), and Micro-F1 (ablated) < Micro-F1 (full).

- **Test:** exact two-sided binomial McNemar on paired per-event
  decisions (identical methodology to JRE-ABLATION-001).
- **Significance:** p < 0.05 **and** b > c (directional requirement).
- **Power target:** ≥ 0.80 under the sign-flip model with per-pair
  regression probability π = 0.9 (the observed pattern was π = 1.0;
  π = 0.9 is the pre-registered conservative assumption).

### 2.2 Secondary hypotheses (confidence-pathway mechanisms)

The Phase 10 matrix showed A1 (SAV factor), A2 (Gochara/Vedha), and
A4 (Dasha gate) produce **zero verdict-level discordance**: they act
through the confidence-ordering pathway. On the expanded corpus these
mechanisms are evaluated with pre-registered secondary endpoints:

- **H2 (per mechanism):** the mean paired per-event confidence delta
  (FULL − ablated) over events whose evidence-chain payload differs
  between the two runs is non-zero by sign test, and the
  best-prediction *rank stability* (fraction of events whose selected
  best prediction changes) is reported.
- These are **exploratory-locked**: reported with exact p-values but
  explicitly labelled secondary; no confirmatory claim rests on them.

### 2.3 Estimands and endpoints

| Endpoint | Definition | Test |
|---|---|---|
| Primary | McNemar discordance (b, c) of the A3 ablation | exact binomial, two-sided, α=0.05 |
| Secondary | per-mechanism mean confidence delta | sign test |
| Descriptive | Micro-F1 / Macro-F1 / precision / recall per scenario | point estimates (sealed) |

Gate semantics are unchanged: JRE-BENCH-001's baseline remains the
non-degradation gate; JRE-BENCH-002 re-seals its own baseline counts
and becomes the gate for post-expansion work.

## 3. Locked Power Analysis

Computed exactly by `scripts/bench002_power.py` (α = 0.05,
target power = 0.80):

- Minimal all-one-direction discordant count for significance:
  **m = 6** (p = 2·0.5⁶ = 0.03125).
- Minimal discordant count reaching power ≥ 0.80 at π = 0.9:
  **m = 12** (power = 0.8891; at π = 0.95: m = 9 → 0.9288;
  at π = 0.8: m = 20 → 0.8042).
- Observed discordant density: 2 pairs / 120 events.

**Locked expansion target: ≥ 720 scored events (≥ 240 charts),
expected ≈ 12 discordant pairs, power = 0.889 under π = 0.9.**

Exact power table (probability that the exact McNemar test rejects,
b ~ Bin(m, π)):

| m | p(b=0) | π=0.80 | π=0.85 | π=0.90 | π=0.95 | π=1.0 |
|---|--------|--------|--------|--------|--------|-------|
| 6 | 0.03125 | 0.2622 | 0.3772 | 0.5314 | 0.7351 | 1.0000 |
| 8 | 0.00781 | 0.1678 | 0.2725 | 0.4305 | 0.6634 | 1.0000 |
| 9 | 0.00391 | 0.4362 | 0.5995 | 0.7748 | 0.9288 | 1.0000 |
| 12 | 0.00049 | 0.5584 | 0.7358 | 0.8891 | 0.9804 | 1.0000 |
| 16 | 0.00003 | 0.5981 | 0.7899 | 0.9316 | 0.9930 | 1.0000 |
| 20 | 0.00000 | 0.8042 | 0.9327 | 0.9887 | 0.9997 | 1.0000 |

(The non-monotonicity for π < 1 is genuine discrete-McNemar behaviour:
the exact rejection region's granularity changes with m.)

## 4. Locked Corpus-Construction Rules

1. **Block structure.** New subjects are added in whole 40-chart
   blocks (30 closed-world dev + 10 open-world validation), preserving
   the 3-events-per-chart scoring structure of JRE-BENCH-001.
2. **New subjects only.** No resampling, augmentation, or
   bootstrapping of existing charts; every chart is a new verifiable
   historical subject.
3. **Inclusion criteria.** Verified birth date/time/place; ≥ 3 dated
   life events with documented dates and windows; events map onto the
   existing `EventDomain` enum; ephemeris instant inside the
   Swiss-Ephemeris-validated range of the engine.
4. **Exclusion criteria.** Duplicate subjects, charts with contested
   birth times (no source), events with date uncertainty wider than
   the window schema, subjects whose event count would unbalance the
   per-domain macro-F1 cohort beyond the block plan.
5. **Label lock.** Event labels are frozen at block creation through
   the existing corpus-manifest hashing discipline
   (`input_sha256` / `computed_sha256` per fixture) before any
   evaluation is run against the block.
6. **No adaptive labeling.** Labels are produced without reference to
   engine output; any labelling run that touched the engine invalidates
   the block (logged as a deviation and discarded).
7. **Domain balance.** Each block maintains ≥ 6 of the locked event
   domains to keep macro-F1 defined over a comparable population.

## 5. Locked Execution Order (No-Peeking Protocol)

1. Collect block 1 (charts 041–080) → freeze labels via manifest →
   run the 6-scenario matrix → record.
2. Repeat per block until total scored events ≥ 720.
3. **Single confirmatory analysis** of H1 after the final block:
   `scripts/ablation_matrix.py` with the expanded pool; exact McNemar.
4. No interim analyses of H1. Interim looks are prohibited; if an
   interim look is unavoidably required for operational reasons it
   must be logged in §7 and the final alpha adjusted by the
   Pocock-style boundary recorded there (default: none planned).
5. Secondary endpoints are analysed in the same single pass.

## 6. Sealing & Deviation Policy

- On completion, `scripts/seal_benchmark.py` seals
  `benchmarks/JRE-BENCH-002.json` with the expanded corpus hashes, the
  observed baseline/companion counts, and a pointer to this document
  (`preregistration: docs/validation/phase_11a_bench002_preregistration.md`).
- Deviations from §4/§5 are appended to §7 with date and rationale
  **before** the confirmatory analysis runs; unlogged deviations
  invalidate the confirmatory claim (the analysis is then labelled
  exploratory in all outputs).
- The confirmatory analysis must be executed by a commit whose diff
  contains no changes under `src/jrs/` (analysis-only diff).

## 7. Deviation Log

_(empty at pre-registration)_

| Date | Deviation | Rationale | Impact |
|------|-----------|-----------|--------|

## 8. Success Criteria for Phase 11A

- [x] Power analysis tool committed and unit-tested against exact values
- [x] This document locked with the §3 numbers produced by the tool
- [ ] First expansion block (charts 041–080) collected and label-locked
- [ ] Confirmatory analysis executed per §5 and sealed as JRE-BENCH-002

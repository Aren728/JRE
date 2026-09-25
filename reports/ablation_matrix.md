# Phase 10 — Empirical Ablation Matrix & Analysis

Sealed reference: **JRE-BENCH-001** — gating baseline Micro-F1 **0.7435** (TP=71 / FP=31 / FN=18), companion (FULL, all flags on) **0.7565** (TP=73 / FP=32 / FN=15).

Method: paired per-event ablation over the frozen 120-event corpus; exact binomial McNemar test on discordant events; 
alpha = 0.05. 

## Headline results

| Exp | Mechanism removed | F1 (full) | F1 (ablated) | ΔF1 | TP/FP/FN shift | McNemar b/c | p (exact) | Verdict |
|-----|-------------------|-----------|--------------|-----|----------------|-------------|-----------|---------|
| A1 | Shodhita SAV TQS factor (ashtakavarga_scoring) | 0.7565 | 0.7565 | +0.0000 | TP+0 / FP+0 / FN+0 | 0/0 | 1.0000 | NEUTRAL |
| A2 | Gochara TQS bands + vedha dampening (gochara_scoring) | 0.7565 | 0.7565 | +0.0000 | TP+0 / FP+0 / FN+0 | 0/0 | 1.0000 | NEUTRAL |
| A3 | Multi-varga D9/D10 cross-evidence rescue (varga_scoring) | 0.7565 | 0.7435 | +0.0130 | TP-2 / FP-1 / FN+3 | 2/0 | 0.5000 | INSIGNIFICANT_POSITIVE |
| A4 | Dasha permissive gate (dasha_transit_scoring) | 0.7565 | 0.7565 | +0.0000 | TP+0 / FP+0 / FN+0 | 0/0 | 1.0000 | NEUTRAL |

ΔF1 = F1(full) − F1(ablated); positive values quantify the mechanism's contribution to the sealed companion baseline.

## A1 — Ashtakavarga Isolation

**Hypothesis.** Removing the Shodhita SAV factor isolates its contribution to prediction confidence ordering and TQS-basis selection.

**Result.** Removing Shodhita SAV TQS factor (ashtakavarga_scoring) moves Micro-F1 from 0.7565 to 0.7565 (Δ = +0.0000); counts shift TP+0 / FP+0 / FN+0. Of 0 discordant events, 0 regressed and 0 improved when the mechanism was removed (exact p = 1.0000).

Removal leaves every paired event unchanged: on this corpus the mechanism's contribution is absorbed by the confidence-ordering pathway without flipping any best-prediction selection (verdict: NEUTRAL).

## A2 — Gochara & Vedha Isolation

**Hypothesis.** Removing the transit factor measures classical gochara dampening/support multipliers and vedha obstruction.

**Result.** Removing Gochara TQS bands + vedha dampening (gochara_scoring) moves Micro-F1 from 0.7565 to 0.7565 (Δ = +0.0000); counts shift TP+0 / FP+0 / FN+0. Of 0 discordant events, 0 regressed and 0 improved when the mechanism was removed (exact p = 1.0000).

Removal leaves every paired event unchanged: on this corpus the mechanism's contribution is absorbed by the confidence-ordering pathway without flipping any best-prediction selection (verdict: NEUTRAL).

## A3 — Multi-Varga Rescue Isolation

**Hypothesis.** Removing the D9/D10 cross-varga rescue collapses to the sealed baseline behaviour (0.7435), quantifying the +0.0130 F1 lift attributable to cross-evidence.

**Result.** Removing Multi-varga D9/D10 cross-evidence rescue (varga_scoring) moves Micro-F1 from 0.7565 to 0.7435 (Δ = +0.0130); counts shift TP-2 / FP-1 / FN+3. Of 2 discordant events, 2 regressed and 0 improved when the mechanism was removed (exact p = 0.5000).

The ablated system sits within the non-degradation tolerance of the sealed gating baseline, consistent with the removal collapsing to baseline behaviour.

## A4 — Dasha Permissive Gate Isolation

**Hypothesis.** Removing the dasha gate measures FP shifts when transit activations are un-gated (confidence demotion disappears).

**Result.** Removing Dasha permissive gate (dasha_transit_scoring) moves Micro-F1 from 0.7565 to 0.7565 (Δ = +0.0000); counts shift TP+0 / FP+0 / FN+0. Of 0 discordant events, 0 regressed and 0 improved when the mechanism was removed (exact p = 1.0000).

Removal leaves every paired event unchanged: on this corpus the mechanism's contribution is absorbed by the confidence-ordering pathway without flipping any best-prediction selection (verdict: NEUTRAL).

## Threats to validity

- Single frozen corpus (40 charts / 120 events): p-values are exact for this corpus but generalization requires an expanded, pre-registered event set.
- Deterministic pipeline: no sampling variance; all variance is across paired events, which McNemar models.
- Confidence-ordering mechanisms (gochara, dasha) act through best-prediction selection; their effect is competitive rather than absolute.
- The Phase 5F hooks were tuned on this corpus's dev split; a held-out replication would strengthen causal claims.

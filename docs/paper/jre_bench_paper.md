# Classical Jyotish Mechanisms under Deterministic
# Historical-Event Benchmarks: An Ablation Study of the
# Jyotish Reasoning Engine (JRE 1.0)

*Engineering report — generated deterministically from sealed repository artifacts by `scripts/generate_paper.py`; do not edit by hand.*

---

## Abstract

We present the validation methodology and first empirical ablation study of the Jyotish Reasoning Engine (JRE), a fully deterministic implementation of classical Parashari astrology (BPHS). The engine is audited end-to-end by golden-state hash contracts over nine pipeline stages (50 fixture(s) verified, 0 mismatch(es)) and evaluated on a frozen 40-chart / 120-event historical corpus (**JRE-BENCH-001**) with an event-level scoring protocol. The sealed system reaches **Micro-F1 = 0.7435** (TP=71, FP=31, FN=18; precision 0.6961, recall 0.7978 on the flag-off baseline) and **Micro-F1 = 0.7565** with all Phase 5 scoring mechanisms enabled. A paired leave-one-out ablation over the identical 120 events, analysed with exact binomial McNemar tests, isolates the causal contribution of each classical mechanism: the D9/D10 cross-varga evidence rescue is the only verdict-moving component (2 regression / 0 improvement discordant events, exact p = 0.50), while the Ashtakavarga strength factor, Gochara/Vedha transits, and the Dasha permissive gate act exclusively through the confidence-ordering pathway on this corpus. A pre-registered corpus expansion (JRE-BENCH-002, ≥ 720 scored events) is locked to give the confirmatory analysis ≥ 0.80 power at the observed effect size.

**Keywords:** Jyotish, deterministic pipelines, golden-state hashing, historical validation, ablation, McNemar test

## 1. Introduction

Computational implementations of classical Jyotish typically fail on three engineering axes: determinism (identical inputs must reproduce identical outputs), auditability (every prediction must trace to its rules and raw data), and falsifiability (claims must be measured against fixed, verifiable ground truth). The JRE addresses all three: a pure calculation core (Swiss Ephemeris 2.10.03) feeds a fact-extraction layer; yoga formation, cancellation, and temporal activation are evaluated by deterministic services; every evaluation emits a provenance DAG (Prediction → Rules → Facts → Classical References) whose hash is part of the regression gate. The studied build is sealed as JRE 1.0.0-rc1 (commit `b6a37db78e9e`).

## 2. Benchmark Design (JRE-BENCH-001)

The corpus freezes **40 historical charts** (30 development, closed-world; 10 validation, open-world) with **120 dated life events** across 6 domains. Fixture inputs and canonical payloads are hash-locked per chart (`input_sha256` / `computed_sha256`); the corpus manifest hash `4e8eb130bab10c2a…` is sealed. Scoring is event-level: every real known event is scored exactly once (TP = matched, non-CANCELLED prediction; FP = unconfirmed activation incl. cancelled best-predictions; FN = silent miss); synthetic unmatched predictions are excluded. Micro-F1 pools the 120 decisions; Macro-F1 averages per-domain F1.

**Gating baseline (flag-off):** Micro-F1 = 0.7435 (TP=71 / FP=31 / FN=18), precision 0.6961, recall 0.7978, non-degradation tolerance ±0.005. **Companion (all mechanisms on):** Micro-F1 = 0.7565 (TP=73 / FP=32 / FN=15).

## 3. Determinism & Audit Infrastructure

- **Golden states:** nine canonical pipeline stages (chart, jre_facts, dasha, yogas, ashtakavarga, gochara, multi_varga, dasha_transit, evidence_graph) are hash-verified per fixture — reproduction claim: *50 fixture(s) verified, 0 mismatch(es)*.
- **Invariants:** the identity invariant (identical DAG and identical report bytes under re-evaluation) and the sensitivity invariant (single-variable perturbations are bounded to their dependency cone) are continuously tested.
- **Reproducibility:** a clean-room audit (`scripts/audit_clean_reproduce.py`) verifies pinned dependencies, Stage 1-9 hashes, and the bit-for-bit baseline in one command.
- **Lineage:** any prediction id resolves backward through Rule → Dasha Gate → Transit → Varga → Yoga → SAV → raw ephemeris floats via the lineage API.

## 4. Ablation Methodology

Each classical mechanism is isolated by leave-one-out feature-flag ablation from the full system (single-variable change). Scenarios are compared as **paired samples over the identical 120 events**; significance uses the exact two-sided binomial McNemar test on discordant pairs (b = events that regress on removal, c = events that improve). Effect direction: contribution = F1(full) − F1(ablated). The analysis (JRE-ABLATION-001) is anchored by bit-for-bit reproduction of both sealed reference rows.

## 5. Results

| Exp | Mechanism | F1 (full) | F1 (ablated) | ΔF1 | b/c | p (exact) | Verdict |
|-----|-----------|-----------|--------------|-----|-----|-----------|---------|
| A1 | Shodhita SAV TQS factor (ashtakavarga_scoring) | 0.7565 | 0.7565 | +0.0000 | 0/0 | 1.0000 | NEUTRAL |
| A2 | Gochara TQS bands + vedha dampening (gochara_scoring) | 0.7565 | 0.7565 | +0.0000 | 0/0 | 1.0000 | NEUTRAL |
| A3 | Multi-varga D9/D10 cross-evidence rescue (varga_scoring) | 0.7565 | 0.7435 | +0.0130 | 2/0 | 0.5000 | INSIGNIFICANT_POSITIVE |
| A4 | Dasha permissive gate (dasha_transit_scoring) | 0.7565 | 0.7565 | +0.0000 | 0/0 | 1.0000 | NEUTRAL |

Verdict distribution: {'NEUTRAL': 3, 'INSIGNIFICANT_POSITIVE': 1}. The multi-varga D9/D10 rescue removal collapses Micro-F1 exactly to the sealed gating baseline (0.7435), quantifying the cross-evidence lift at **+0.0130** with 2 discordant events — directionally consistent, not individually significant at this corpus size (exact p = 0.50). The remaining mechanisms produce zero discordance: their contribution flows through the confidence-ordering pathway (best-prediction selection, TQS-basis choice) rather than verdict flips.

## 6. Power & Pre-Registration (JRE-BENCH-002)

At the observed discordant density (2 pairs / 120 events), the confirmatory analysis requires a larger corpus. The pre-registered plan (locked in `docs/validation/phase_11a_bench002_preregistration.md`) fixes: exact McNemar at α = 0.05 with a directional requirement (b > c); power ≥ 0.80 under a π = 0.9 sign-flip model; and a minimum of **≥ 720 scored events (240 charts)** — the minimal m reaching the power target is 12 discordant pairs (power = 0.8891). The expansion proceeds in whole 40-chart blocks with label freezing before evaluation and a single confirmatory pass.

## 7. Threats to Validity

- **Corpus size and provenance.** 120 events from 40 historical subjects; birth-time precision and event dating are archival quality but not uniform.
- **Label subjectivity.** Event–domain mapping is curated; the closed-world scope bounds label noise but cannot eliminate it.
- **Multiple mechanisms, one corpus.** The ablation family is interpreted jointly; no multiplicity correction is applied to the four exact tests, and all are null on this corpus anyway.
- **Confidence-pathway opacity.** Mechanisms acting through ranking are invisible to verdict-level F1; the secondary endpoints in JRE-BENCH-002 address this.
- **Engineering culture.** All rules were implemented from classical sources before measurement, but the implementers and evaluators overlap — a fully independent replication remains future work.

## 8. Conclusion

A classical-astrology engine can be held to modern software and empirical standards: deterministic, hash-audited, provenance-complete, and measurable against frozen ground truth. On the sealed corpus the engine's scoring mechanisms are individually small and only the cross-varga evidence rescue moves verdicts; the pre-registered expansion will establish whether that contribution is confirmable. All artifacts — benchmark seal, ablation reports, lineage API, and reproducibility audit — are part of the release and re-executable from the repository.

## References

1. BPHS — Parashara, *Brihat Parashara Hora Shastra* (chapters referenced per rule in the evidence-graph citations: Ch. 28, 33, 34, 35, 37–42).
2. JRE-BENCH-001 — frozen benchmark seal, `benchmarks/JRE-BENCH-001.json` (sha256 8e8b831475f4c4f6…).
3. JRE-ABLATION-001 — ablation matrix, `reports/ablation_matrix.json`.
4. JRE-BENCH-002 — pre-registration, `docs/validation/phase_11a_bench002_preregistration.md`.
5. JRE 1.0.0-rc1 — release seal, `releases/v1.0.0-rc1.json`.
6. McNemar, Q. (1947). Note on the sampling error of the difference between correlated proportions or percentages. *Psychometrika* 12(2):153–157.

---

*Artifact integrity: bench seal sha256 8e8b831475f4c4f6… · ablation report sha256 b335c86a9e2bc7bd… · pre-registration sha256 c3dcafd4a0909c1d…*

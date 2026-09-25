#!/usr/bin/env python3
"""Phase 10: Empirical ablation matrix & analysis (JRE-BENCH-001).

Establishes the causal contribution of each Jyotish mechanism by
measuring per-event deltas against the sealed JRE-BENCH-001 baselines:

    gating baseline  : Micro-F1 = 0.7435 (TP=71 / FP=31 / FN=18), flags OFF
    companion        : Micro-F1 = 0.7565 (TP=73 / FP=32 / FN=15), ALL_ON

Experiments (one mechanism removed from the FULL system per run):

    A1  remove SAV multiplier        -> ALL_ON with JRS_ASHTA_SCORING=0
    A2  remove Gochara & Vedha      -> ALL_ON with JRS_GOCHARA_SCORING=0
    A3  remove Multi-Varga rescue    -> ALL_ON with JRS_VARGA_SCORING=0
    A4  remove Dasha permissive gate -> ALL_ON with JRS_DASHA_TRANSIT_SCORING=0

Methodology
-----------
Each scenario executes the frozen corpus through the real pipeline with
only the flag permutation differing (single-variable change — the
Phase 9B sensitivity discipline). Per-event TP/FP/FN decisions are
pooled across the 120 scored events, so experiments are compared as
**paired samples** over the identical event set, not as pooled counts
alone.

Significance: exact binomial McNemar test on the paired contingency
table (b = events that regress when the mechanism is removed, c =
events that improve). The exact two-sided p-value is computed from the
binomial tail summed to convergence (no scipy dependency):

    p = 2 * sum_{k<=min(b,c)} C(n,k) 0.5^n,  clipped to 1, with
    n = b + c, early-exit symmetry (p = 1 when b == c), and an
    escalation guard to ``math.comb``-based evaluation when the
    iterative accumulation converges slowly.

Effect direction: ``contribution = F1(full) - F1(ablated)``. Negative
values mean the mechanism is currently counter-productive on this
corpus. The threshold map (alpha = 0.05) classifies each mechanism as
SIGNIFICANT_CONTRIBUTOR / NEUTRAL / INSIGNIFICANT / DEGRADER.

Outputs (deterministic; pinned-instant pipeline):

- ``reports/ablation_matrix.json``     machine-readable full results
- ``reports/ablation_matrix.md``       empirical paper draft (markdown)

Usage::

    python scripts/ablation_matrix.py
    python scripts/ablation_matrix.py --json   # stdout JSON only
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from jrs.validation.benchmark import (  # noqa: E402
    BASELINE_MICRO_F1,
    F1_TOLERANCE,
    evaluate_corpus,
)

ABLATION_SCHEMA_VERSION = "1.0.0"
REPORT_JSON = REPO_ROOT / "reports" / "ablation_matrix.json"
REPORT_MD = REPO_ROOT / "reports" / "ablation_matrix.md"
ALPHA = 0.05

# ── Sealed references (JRE-BENCH-001) ──────────────────────────────────────
SEALED_BASELINE = {"micro_f1": 0.7435, "tp": 71, "fp": 31, "fn": 18}
SEALED_COMPANION = {"micro_f1": 0.7565, "tp": 73, "fp": 32, "fn": 15}

# Flag registry (canonical repo spellings; see jrs.api.dependencies).
FLAG_ENV_VARS: dict[str, str] = {
    "ASHTAKAVARGA": "JRS_ASHTA_SCORING",
    "GOCHARA": "JRS_GOCHARA_SCORING",
    "MULTI_VARGA": "JRS_VARGA_SCORING",
    "DASHA_TRANSIT": "JRS_DASHA_TRANSIT_SCORING",
}

# Experiment registry: id -> (title, hypothesis, flag->on/off map).
EXPERIMENTS: tuple[dict[str, Any], ...] = (
    {
        "id": "A1",
        "title": "Ashtakavarga Isolation",
        "hypothesis": (
            "Removing the Shodhita SAV factor isolates its contribution "
            "to prediction confidence ordering and TQS-basis selection."
        ),
        "flags": {
            "JRS_ASHTA_SCORING": False,
            "JRS_GOCHARA_SCORING": True,
            "JRS_VARGA_SCORING": True,
            "JRS_DASHA_TRANSIT_SCORING": True,
        },
        "mechanism": "Shodhita SAV TQS factor (ashtakavarga_scoring)",
    },
    {
        "id": "A2",
        "title": "Gochara & Vedha Isolation",
        "hypothesis": (
            "Removing the transit factor measures classical gochara "
            "dampening/support multipliers and vedha obstruction."
        ),
        "flags": {
            "JRS_ASHTA_SCORING": True,
            "JRS_GOCHARA_SCORING": False,
            "JRS_VARGA_SCORING": True,
            "JRS_DASHA_TRANSIT_SCORING": True,
        },
        "mechanism": "Gochara TQS bands + vedha dampening (gochara_scoring)",
    },
    {
        "id": "A3",
        "title": "Multi-Varga Rescue Isolation",
        "hypothesis": (
            "Removing the D9/D10 cross-varga rescue collapses to the "
            "sealed baseline behaviour (0.7435), quantifying the "
            "+0.0130 F1 lift attributable to cross-evidence."
        ),
        "flags": {
            "JRS_ASHTA_SCORING": True,
            "JRS_GOCHARA_SCORING": True,
            "JRS_VARGA_SCORING": False,
            "JRS_DASHA_TRANSIT_SCORING": True,
        },
        "mechanism": "Multi-varga D9/D10 cross-evidence rescue (varga_scoring)",
    },
    {
        "id": "A4",
        "title": "Dasha Permissive Gate Isolation",
        "hypothesis": (
            "Removing the dasha gate measures FP shifts when transit "
            "activations are un-gated (confidence demotion disappears)."
        ),
        "flags": {
            "JRS_ASHTA_SCORING": True,
            "JRS_GOCHARA_SCORING": True,
            "JRS_VARGA_SCORING": True,
            "JRS_DASHA_TRANSIT_SCORING": False,
        },
        "mechanism": "Dasha permissive gate (dasha_transit_scoring)",
    },
)

# ── Exact binomial McNemar ─────────────────────────────────────────────────


def _binom_tail_two_sided(k: int, n: int) -> float:
    """Exact two-sided binomial tail P(X <= k), X ~ Bin(n, 0.5), doubled.

    Uses an iterative accumulation with an escalation guard to
    ``math.comb`` evaluation when the iterative sum converges slowly.
    """
    if n == 0:
        return 1.0
    k = min(k, n)
    # Iterative accumulation (exact for the small n this corpus yields).
    prob = 0.5**n
    tail = prob
    for i in range(1, k + 1):
        prob *= (n - i + 1) / i
        tail += prob
    if tail > 1.0:
        # Escalation guard: recompute exactly via math.comb.
        tail = sum(math.comb(n, i) for i in range(0, k + 1)) * 0.5**n
    return min(1.0, 2.0 * tail)


def mcnemar_exact(b: int, c: int) -> dict[str, Any]:
    """Exact binomial McNemar test on paired counts (b regressions, c
    improvements). Returns n, statistic, exact p, and a verdict at
    alpha = 0.05.
    """
    n = b + c
    if n == 0:
        return {
            "b_regressed": b,
            "c_improved": c,
            "n_discordant": 0,
            "statistic": 0.0,
            "p_value": 1.0,
            "significant_at_alpha": False,
        }
    stat = min(b, c)
    p_value = _binom_tail_two_sided(stat, n)
    return {
        "b_regressed": b,
        "c_improved": c,
        "n_discordant": n,
        "statistic": stat,
        "p_value": p_value,
        "significant_at_alpha": p_value < ALPHA,
    }


# ── Scenario execution ──────────────────────────────────────────────────────

_FLAG_KEYS = tuple(FLAG_ENV_VARS.values())  # canonical env-var names


def _apply_flags(on: dict[str, bool]) -> None:
    for env_var in _FLAG_KEYS:
        if on.get(env_var):
            os.environ[env_var] = "1"
        else:
            os.environ.pop(env_var, None)


def _restore_flags() -> None:
    for env_var in _FLAG_KEYS:
        os.environ.pop(env_var, None)


def _run_scenario(name: str, flags: dict[str, bool]) -> dict[str, Any]:
    """Evaluate the corpus once under one flag permutation."""
    _apply_flags(flags)
    metrics = evaluate_corpus()
    per_chart = metrics.get("per_chart", {})
    event_decisions: dict[str, str] = {}
    for fid, payload in per_chart.items():
        for match in payload.get("matches", []):
            event_id = str(match.get("event_id", ""))
            if event_id.startswith("unmatched_"):
                continue  # F3 protocol: synthetic entries are excluded
            verdict = str(match.get("verdict", ""))
            if verdict == "TRUE_POSITIVE":
                event_decisions[event_id] = "tp"
            elif verdict == "FALSE_NEGATIVE":
                event_decisions[event_id] = "fn"
            else:  # FALSE_POSITIVE / TRUE_NEGATIVE
                event_decisions[event_id] = "fp"
    observed = {
        "tp": metrics["overall_metrics"]["true_positives"],
        "fp": metrics["overall_metrics"]["false_positives"],
        "fn": metrics["overall_metrics"]["false_negatives"],
    }
    return {
        "scenario": name,
        "flags": dict(flags),
        "observed": observed,
        "micro_f1": metrics["micro_f1"],
        "macro_f1": metrics["macro_f1"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "n_charts": metrics["n_charts"],
        "event_decisions": event_decisions,
    }


# ── Pairwise analysis ───────────────────────────────────────────────────────


def _pairwise(full: dict[str, Any], ablated: dict[str, Any]) -> dict[str, Any]:
    """Paired analysis of one ablation against the FULL system."""
    full_dec = full["event_decisions"]
    abl_dec = ablated["event_decisions"]
    shared = sorted(set(full_dec) & set(abl_dec))
    b = sum(  # events that regressed when the mechanism was removed
        1
        for eid in shared
        if full_dec[eid] == "tp" and abl_dec[eid] != "tp"
    )
    c = sum(  # events that improved when the mechanism was removed
        1
        for eid in shared
        if full_dec[eid] != "tp" and abl_dec[eid] == "tp"
    )
    stats = mcnemar_exact(b, c)
    f1_full = full["micro_f1"]
    f1_abl = ablated["micro_f1"]
    delta = f1_full - f1_abl  # positive = mechanism contributes

    if stats["significant_at_alpha"] and delta > 0:
        verdict = "SIGNIFICANT_CONTRIBUTOR"
    elif stats["significant_at_alpha"] and delta < 0:
        verdict = "SIGNIFICANT_DEGRADER"
    elif delta > 0:
        verdict = "INSIGNIFICANT_POSITIVE"
    elif delta < 0:
        verdict = "INSIGNIFICANT_NEGATIVE"
    else:
        verdict = "NEUTRAL"

    # Degradation gate: ablated F1 vs the sealed gating baseline.
    gate_breach = f1_abl < SEALED_BASELINE["micro_f1"] - F1_TOLERANCE

    return {
        "experiment": ablated["scenario"],
        "mechanism_removed": None,  # filled by caller
        "f1_full": f1_full,
        "f1_ablated": f1_abl,
        "f1_delta": round(delta, 6),
        "observed_full": full["observed"],
        "observed_ablated": ablated["observed"],
        "counts_delta": {
            key: ablated["observed"][key] - full["observed"][key]
            for key in ("tp", "fp", "fn")
        },
        "paired_events": len(shared),
        "mcnemar": stats,
        "verdict": verdict,
        "gate_breach": gate_breach,
        "within_tolerance_of_baseline": abs(
            f1_abl - SEALED_BASELINE["micro_f1"]
        ) <= F1_TOLERANCE,
    }


def _attach_experiment_metadata(rows: list[dict[str, Any]]) -> None:
    by_id = {exp["id"]: exp for exp in EXPERIMENTS}
    for row in rows:
        exp = by_id[row["experiment"]]
        row["experiment_id"] = exp["id"]
        row["mechanism_removed"] = exp["mechanism"]
        row["title"] = exp["title"]
        row["hypothesis"] = exp["hypothesis"]


# ── Report rendering ────────────────────────────────────────────────────────


def _render_markdown(report: dict[str, Any]) -> str:
    base = report["sealed_reference"]["gating_baseline"]
    companion = report["sealed_reference"]["companion"]
    lines: list[str] = []
    lines.append("# Phase 10 — Empirical Ablation Matrix & Analysis")
    lines.append("")
    lines.append(
        f"Sealed reference: **JRE-BENCH-001** — gating baseline "
        f"Micro-F1 **{base['micro_f1']}** (TP={base['tp']} / FP={base['fp']} / "
        f"FN={base['fn']}), companion (FULL, all flags on) "
        f"**{companion['micro_f1']}** (TP={companion['tp']} / FP={companion['fp']} / "
        f"FN={companion['fn']})."
    )
    lines.append("")
    lines.append(
        "Method: paired per-event ablation over the frozen 120-event corpus; "
        "exact binomial McNemar test on discordant events; "
    )
    lines.append(f"alpha = {report['analysis_config']['alpha']}. ")
    lines.append("")
    lines.append("## Headline results")
    lines.append("")
    lines.append(
        "| Exp | Mechanism removed | F1 (full) | F1 (ablated) | ΔF1 | TP/FP/FN shift | McNemar b/c | p (exact) | Verdict |"
    )
    lines.append(
        "|-----|-------------------|-----------|--------------|-----|----------------|-------------|-----------|---------|"
    )
    for row in report["experiments"]:
        m = row["mcnemar"]
        cd = row["counts_delta"]
        lines.append(
            f"| {row['experiment_id']} | {row['mechanism_removed']} "
            f"| {row['f1_full']:.4f} | {row['f1_ablated']:.4f} "
            f"| {row['f1_delta']:+.4f} "
            f"| TP{cd['tp']:+d} / FP{cd['fp']:+d} / FN{cd['fn']:+d} "
            f"| {m['b_regressed']}/{m['c_improved']} "
            f"| {m['p_value']:.4f} | {row['verdict']} |"
        )
    lines.append("")
    lines.append(
        "ΔF1 = F1(full) − F1(ablated); positive values quantify the "
        "mechanism's contribution to the sealed companion baseline."
    )
    lines.append("")

    # Per-experiment narrative sections.
    for row in report["experiments"]:
        lines.append(f"## {row['experiment_id']} — {row['title']}")
        lines.append("")
        lines.append(f"**Hypothesis.** {row['hypothesis']}")
        lines.append("")
        m = row["mcnemar"]
        cd = row["counts_delta"]
        lines.append(
            f"**Result.** Removing {row['mechanism_removed']} moves Micro-F1 "
            f"from {row['f1_full']:.4f} to {row['f1_ablated']:.4f} "
            f"(Δ = {row['f1_delta']:+.4f}); counts shift "
            f"TP{cd['tp']:+d} / FP{cd['fp']:+d} / FN{cd['fn']:+d}. "
            f"Of {m['n_discordant']} discordant events, "
            f"{m['b_regressed']} regressed and {m['c_improved']} improved when "
            f"the mechanism was removed (exact p = {m['p_value']:.4f})."
        )
        lines.append("")
        if row["f1_delta"] == 0:
            lines.append(
                "Removal leaves every paired event unchanged: on this corpus "
                "the mechanism's contribution is absorbed by the "
                "confidence-ordering pathway without flipping any "
                "best-prediction selection (verdict: "
                f"{row['verdict']})."
            )
        elif row["within_tolerance_of_baseline"]:
            lines.append(
                "The ablated system sits within the non-degradation tolerance "
                "of the sealed gating baseline, consistent with the removal "
                "collapsing to baseline behaviour."
            )
        else:
            lines.append(
                "The ablated system deviates from the sealed gating baseline "
                "beyond tolerance — the removed mechanism interacts with the "
                "other scoring factors rather than acting in isolation."
            )
        lines.append("")

    lines.append("## Threats to validity")
    lines.append("")
    lines.append(
        "- Single frozen corpus (40 charts / 120 events): p-values are "
        "exact for this corpus but generalization requires an expanded, "
        "pre-registered event set.\n"
        "- Deterministic pipeline: no sampling variance; all variance is "
        "across paired events, which McNemar models.\n"
        "- Confidence-ordering mechanisms (gochara, dasha) act through "
        "best-prediction selection; their effect is competitive rather "
        "than absolute.\n"
        "- The Phase 5F hooks were tuned on this corpus's dev split; a "
        "held-out replication would strengthen causal claims."
    )
    lines.append("")
    return "\n".join(lines)


def _build_report(
    baseline_run: dict[str, Any],
    full_run: dict[str, Any],
    ablated_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    rows = [_pairwise(full_run, abl) for abl in ablated_runs]
    _attach_experiment_metadata(rows)
    return {
        "schema_version": ABLATION_SCHEMA_VERSION,
        "analysis_id": "JRE-ABLATION-001",
        "sealed_reference": {
            "benchmark_id": "JRE-BENCH-001",
            "gating_baseline": SEALED_BASELINE,
            "companion": SEALED_COMPANION,
        },
        "analysis_config": {
            "alpha": ALPHA,
            "test": "exact binomial McNemar (two-sided, paired events)",
            "paired_event_pool": "120 scored known events (F3 protocol)",
            "n_charts": full_run["n_charts"],
        },
        "runs": {
            "baseline": {
                "scenario": baseline_run["scenario"],
                "flags": baseline_run["flags"],
                "observed": baseline_run["observed"],
                "micro_f1": baseline_run["micro_f1"],
            },
            "full": {
                "scenario": full_run["scenario"],
                "flags": full_run["flags"],
                "observed": full_run["observed"],
                "micro_f1": full_run["micro_f1"],
            },
            "ablations": [
                {
                    "scenario": run["scenario"],
                    "flags": run["flags"],
                    "observed": run["observed"],
                    "micro_f1": run["micro_f1"],
                }
                for run in ablated_runs
            ],
        },
        "experiments": rows,
        "baseline_match": (
            baseline_run["observed"]["tp"] == SEALED_BASELINE["tp"]
            and baseline_run["observed"]["fp"] == SEALED_BASELINE["fp"]
            and baseline_run["observed"]["fn"] == SEALED_BASELINE["fn"]
            and round(baseline_run["micro_f1"], 4) == SEALED_BASELINE["micro_f1"]
        ),
        "companion_match": (
            full_run["observed"]["tp"] == SEALED_COMPANION["tp"]
            and full_run["observed"]["fp"] == SEALED_COMPANION["fp"]
            and full_run["observed"]["fn"] == SEALED_COMPANION["fn"]
            and round(full_run["micro_f1"], 4) == SEALED_COMPANION["micro_f1"]
        ),
    }


def _print_summary(report: dict[str, Any]) -> None:
    print("PHASE 10 EMPIRICAL ABLATION MATRIX (JRE-BENCH-001)")
    print(
        f"baseline match: {report['baseline_match']} | companion match: "
        f"{report['companion_match']} | paired events: "
        f"{report['analysis_config']['paired_event_pool']}"
    )
    print()
    header = (
        f"{'exp':<4} {'mechanism':<44} {'F1(full)':>9} {'F1(abl)':>9} "
        f"{'dF1':>8} {'b/c':>6} {'p':>7} {'verdict':>24}"
    )
    print(header)
    print("-" * len(header))
    for row in report["experiments"]:
        m = row["mcnemar"]
        mechanism = row["mechanism_removed"]
        mechanism = mechanism[:42] + "…" if len(mechanism) > 44 else mechanism
        print(
            f"{row['experiment_id']:<4} {mechanism:<44} "
            f"{row['f1_full']:>9.4f} {row['f1_ablated']:>9.4f} "
            f"{row['f1_delta']:>+8.4f} "
            f"{m['b_regressed']}/{m['c_improved']:>3} "
            f"{m['p_value']:>7.4f} {row['verdict']:>24}"
        )
    print()
    gate_breaches = [r["experiment_id"] for r in report["experiments"] if r["gate_breach"]]
    if gate_breaches:
        print(
            "GATE: ablation(s) below baseline tolerance: " + ", ".join(gate_breaches)
        )
    else:
        print(
            "GATE: every ablated system within "
            f"{F1_TOLERANCE} of the sealed gating baseline"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 10 empirical ablation matrix (JRE-BENCH-001)."
    )
    parser.add_argument("--json", action="store_true", help="stdout JSON only")
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="do not write reports/ablation_matrix.{json,md}",
    )
    args = parser.parse_args(argv)

    pre_set = sorted(v for v in FLAG_ENV_VARS.values() if os.environ.get(v))
    if pre_set:
        print(
            "REFUSING TO RUN: scoring env vars already set in the parent "
            f"environment: {', '.join(pre_set)}",
            file=sys.stderr,
        )
        return 2

    try:
        # 1. Sealed baseline: all flags OFF.
        baseline_run = _run_scenario(
            "BASELINE", {env: False for env in _FLAG_KEYS}
        )
        # 2. FULL companion: all flags ON.
        full_run = _run_scenario("FULL", {env: True for env in _FLAG_KEYS})
        # 3. Leave-one-out ablations.
        ablated_runs: list[dict[str, Any]] = []
        for exp in EXPERIMENTS:
            ablated_runs.append(
                _run_scenario(exp["id"], dict(exp["flags"]))
            )
    finally:
        _restore_flags()

    report = _build_report(baseline_run, full_run, ablated_runs)

    if not args.no_write:
        REPORT_JSON.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        REPORT_MD.write_text(_render_markdown(report), encoding="utf-8")
        print(f"Wrote {REPORT_JSON}", file=sys.stderr)
        print(f"Wrote {REPORT_MD}", file=sys.stderr)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_summary(report)

    # Exit 1 when the seal reference itself fails to reproduce — the
    # ablation conclusions would be unfounded.
    return 0 if (report["baseline_match"] and report["companion_match"]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

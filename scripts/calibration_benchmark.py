#!/usr/bin/env python3
"""Phase 5E: Side-by-side A/B benchmark calibration bench.

Executes the frozen 40-chart benchmark corpus (30 dev + 10 validation)
once per feature-flag scenario and reports TP/FP/FN deltas, Micro-F1
companion baselines, and error-taxonomy movement against the frozen
Phase F3 baseline (Micro-F1 = 0.7435, TP=71 / FP=31 / FN=18).

Scenarios
---------
- BASELINE      : all scoring flags OFF (the frozen Phase F3 protocol).
- ASHTAKAVARGA  : JRS_ASHTA_SCORING=1 only (Phase 5B bindu/TQS facts).
- GOCHARA       : JRS_GOCHARA_SCORING=1 only (Phase 5C transit facts).
- MULTI_VARGA   : JRS_VARGA_SCORING=1 only (Phase 5D varga facts).
- DASHA_TRANSIT : JRS_DASHA_TRANSIT_SCORING=1 only (Phase 5E permissive
-                 dasha/transit gate facts).
- ALL_ON        : every scoring flag enabled simultaneously.

Each ``evaluate_corpus()`` call materializes charts and jre_facts from
scratch, so per-scenario flag state is read through
``jrs.api.dependencies.build_jre_facts`` exactly as the API layer would
(the flag predicates read ``os.environ`` at call time). The child
environment is restored after the run, and the tool refuses to start
when any scoring env var is already set in the parent environment.

A scenario whose Micro-F1 falls below ``BASELINE_MICRO_F1 - F1_TOLERANCE``
breaches the non-degradation gate. The BASELINE scenario itself must
reproduce the frozen Phase F3 confusion counts bit-for-bit; any drift
invalidates the companion baselines and fails the run.

Usage::
    python scripts/calibration_benchmark.py              # human-readable
    python scripts/calibration_benchmark.py --json       # machine-readable
    python scripts/calibration_benchmark.py --out reports/calibration_5e.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from jrs.validation.benchmark import (  # noqa: E402
    BASELINE_MICRO_F1,
    F1_TOLERANCE,
    evaluate_corpus,
)

CALIBRATION_SCHEMA_VERSION = "1.0.0"

# Frozen Phase F3 confusion counts the BASELINE scenario must reproduce
# (see BASELINE_* constants in jrs.validation.benchmark).
FROZEN_BASELINE_COUNTS = {"tp": 71, "fp": 31, "fn": 18}

# Scoring-flag registry: scenario key -> environment variable.
FLAG_ENV_VARS: dict[str, str] = {
    "ASHTAKAVARGA": "JRS_ASHTA_SCORING",
    "GOCHARA": "JRS_GOCHARA_SCORING",
    "MULTI_VARGA": "JRS_VARGA_SCORING",
    "DASHA_TRANSIT": "JRS_DASHA_TRANSIT_SCORING",
}

# Ordered scenario plan: name -> set of enabled flag keys.
SCENARIOS: tuple[tuple[str, frozenset[str]], ...] = (
    ("BASELINE", frozenset()),
    ("ASHTAKAVARGA", frozenset({"ASHTAKAVARGA"})),
    ("GOCHARA", frozenset({"GOCHARA"})),
    ("MULTI_VARGA", frozenset({"MULTI_VARGA"})),
    ("DASHA_TRANSIT", frozenset({"DASHA_TRANSIT"})),
    ("ALL_ON", frozenset(FLAG_ENV_VARS)),
)

TAXONOMY_KINDS: tuple[str, ...] = (
    "COVERAGE_GAP",
    "DASHA_MISMATCH",
    "DOMAIN_OVERLAP",
    "FORMATION_CANCELLED",
)

# Short column headers for the taxonomy table.
_KIND_HEADERS: dict[str, str] = {
    "COVERAGE_GAP": "COV_GAP",
    "DASHA_MISMATCH": "DASHA_MM",
    "DOMAIN_OVERLAP": "DOM_OVLP",
    "FORMATION_CANCELLED": "FORM_CXL",
}


def _apply_flags(enabled: frozenset[str]) -> None:
    """Set/unset every scoring env var for one scenario."""
    for key, env_var in FLAG_ENV_VARS.items():
        if key in enabled:
            os.environ[env_var] = "1"
        else:
            os.environ.pop(env_var, None)


def _restore_flags() -> None:
    """Leave the environment exactly as the tool found it."""
    for env_var in FLAG_ENV_VARS.values():
        os.environ.pop(env_var, None)


def _run_scenario(name: str, enabled: frozenset[str]) -> dict[str, Any]:
    """Evaluate the corpus once under one flag permutation."""
    _apply_flags(enabled)
    metrics = evaluate_corpus()
    by_kind: dict[str, int] = dict(
        metrics["error_attribution"].get("by_kind", {})
    )
    taxonomy = {
        kind: int(by_kind.get(kind, 0))
        for kind in sorted(set(by_kind) | set(TAXONOMY_KINDS))
    }
    return {
        "scenario": name,
        "flags": {FLAG_ENV_VARS[k]: (k in enabled) for k in sorted(FLAG_ENV_VARS)},
        "n_charts": metrics["n_charts"],
        "true_positives": metrics["overall_metrics"]["true_positives"],
        "false_positives": metrics["overall_metrics"]["false_positives"],
        "false_negatives": metrics["overall_metrics"]["false_negatives"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "micro_f1": metrics["micro_f1"],
        "macro_f1": metrics["macro_f1"],
        "delta_micro_f1": round(metrics["micro_f1"] - BASELINE_MICRO_F1, 6),
        "error_taxonomy_by_kind": taxonomy,
        "gate_breach": metrics["micro_f1"] < BASELINE_MICRO_F1 - F1_TOLERANCE,
    }


def _attach_deltas(results: list[dict[str, Any]]) -> None:
    """Fold in per-scenario movement relative to the measured BASELINE run."""
    base = next(r for r in results if r["scenario"] == "BASELINE")
    base_taxonomy = base["error_taxonomy_by_kind"]
    base_total = sum(base_taxonomy.values())
    for r in results:
        r["tp_delta"] = r["true_positives"] - base["true_positives"]
        r["fp_delta"] = r["false_positives"] - base["false_positives"]
        r["fn_delta"] = r["false_negatives"] - base["false_negatives"]
        r["delta_micro_f1_vs_measured"] = round(
            r["micro_f1"] - base["micro_f1"], 6
        )
        r["error_taxonomy_movement"] = {
            kind: r["error_taxonomy_by_kind"].get(kind, 0) - base_taxonomy.get(kind, 0)
            for kind in sorted(
                set(r["error_taxonomy_by_kind"]) | set(base_taxonomy)
            )
        }
        r["attributed_total"] = sum(r["error_taxonomy_by_kind"].values())
        r["attributed_total_delta"] = r["attributed_total"] - base_total
    base["baseline_match"] = (
        base["true_positives"] == FROZEN_BASELINE_COUNTS["tp"]
        and base["false_positives"] == FROZEN_BASELINE_COUNTS["fp"]
        and base["false_negatives"] == FROZEN_BASELINE_COUNTS["fn"]
    )


def _build_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    base = next(r for r in results if r["scenario"] == "BASELINE")
    breaches = [r["scenario"] for r in results if r["gate_breach"]]
    return {
        "schema_version": CALIBRATION_SCHEMA_VERSION,
        "frozen_baseline": {
            "micro_f1": BASELINE_MICRO_F1,
            **FROZEN_BASELINE_COUNTS,
            "non_degradation_margin": F1_TOLERANCE,
        },
        "baseline_match": base["baseline_match"],
        "gate_breaches": breaches,
        "scenarios": results,
    }


def _print_report(report: dict[str, Any]) -> None:
    results = report["scenarios"]
    print("PHASE 5E SIDE-BY-SIDE CALIBRATION BENCH")
    print(
        f"corpus={results[0]['n_charts']} charts | frozen baseline "
        f"Micro-F1={BASELINE_MICRO_F1} (TP={FROZEN_BASELINE_COUNTS['tp']} "
        f"FP={FROZEN_BASELINE_COUNTS['fp']} FN={FROZEN_BASELINE_COUNTS['fn']}) "
        f"| non-degradation margin={F1_TOLERANCE}"
    )
    if not report["baseline_match"]:
        print(
            "WARNING: BASELINE run drifted from the frozen Phase F3 counts "
            "(see baseline_match=false) - companion baselines are invalid",
            file=sys.stderr,
        )
    print()
    header = (
        f"{'scenario':<14} {'TP':>4} {'FP':>4} {'FN':>4} | "
        f"{'dTP':>4} {'dFP':>4} {'dFN':>4} | "
        f"{'precision':>9} {'recall':>7} {'micro-F1':>9} {'dF1':>8} {'macro-F1':>9} {'gate':>5}"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        verdict = "BREACH" if r["gate_breach"] else "PASS"
        print(
            f"{r['scenario']:<14} {r['true_positives']:>4} "
            f"{r['false_positives']:>4} {r['false_negatives']:>4} | "
            f"{r['tp_delta']:>4} {r['fp_delta']:>4} {r['fn_delta']:>4} | "
            f"{r['precision']:>9.4f} {r['recall']:>7.4f} "
            f"{r['micro_f1']:>9.4f} {r['delta_micro_f1_vs_measured']:>+8.4f} "
            f"{r['macro_f1']:>9.4f} {verdict:>5}"
        )

    print()
    print("error taxonomy (attributed FP/FN matches by ErrorKind; delta vs BASELINE)")
    kinds = sorted(
        {k for r in results for k in r["error_taxonomy_by_kind"]}
    )
    tax_header = f"{'scenario':<14} " + " ".join(
        f"{_KIND_HEADERS.get(k, k):>11}" for k in kinds
    ) + f" {'total':>11}"
    print(tax_header)
    print("-" * len(tax_header))
    for r in results:
        cells = []
        for k in kinds:
            count = r["error_taxonomy_by_kind"].get(k, 0)
            delta = r["error_taxonomy_movement"].get(k, 0)
            cells.append(f"{count:>5} ({delta:>+3})")
        print(
            f"{r['scenario']:<14} "
            + " ".join(cells)
            + f" {r['attributed_total']:>5} ({r['attributed_total_delta']:>+3})"
        )

    print()
    if report["gate_breaches"]:
        print(
            "CALIBRATION GATE: FAIL - non-degradation breach in: "
            + ", ".join(report["gate_breaches"])
        )
    else:
        print(
            "CALIBRATION GATE: PASS - every scenario within "
            f"{F1_TOLERANCE} of the frozen baseline"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Phase 5E side-by-side A/B calibration bench over the frozen "
            "40-chart benchmark corpus."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable JSON report instead of the table",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="also write the JSON report to this path",
    )
    args = parser.parse_args(argv)

    pre_set = sorted(v for v in FLAG_ENV_VARS.values() if os.environ.get(v))
    if pre_set:
        print(
            "REFUSING TO RUN: scoring env vars already set in the parent "
            f"environment: {', '.join(pre_set)}. Unset them first.",
            file=sys.stderr,
        )
        return 2

    results: list[dict[str, Any]] = []
    try:
        for name, enabled in SCENARIOS:
            results.append(_run_scenario(name, enabled))
    finally:
        _restore_flags()

    _attach_deltas(results)
    report = _build_report(results)

    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"Wrote calibration report: {args.out}", file=sys.stderr)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_report(report)

    return 1 if report["gate_breaches"] or not report["baseline_match"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

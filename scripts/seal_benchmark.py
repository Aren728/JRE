#!/usr/bin/env python3
"""Phase 9C: Seal the frozen benchmark manifest (JRE-BENCH-001).

Generates ``benchmarks/JRE-BENCH-001.json`` from live repository
state: the frozen 40-chart corpus (via ``corpus_manifest.json``), the
event/label schema, the evaluation protocol, the Phase F3 baseline
metrics with confusion counts, the Phase 5F flag-on companion
baselines, and the versioning policy.

JRE-BENCH-001 is the immutable baseline: every rule-tuning or ablation
experiment is measured against it. Amendments create a NEW benchmark
id (JRE-BENCH-002, ...) — the sealed file is never mutated in place.

Usage::

    python scripts/seal_benchmark.py            # (re)write the seal
    python scripts/seal_benchmark.py --check    # verify live == sealed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from jrs.validation.benchmark import (  # noqa: E402
    BASELINE_MACRO_F1,
    BASELINE_MICRO_F1,
    BASELINE_PRECISION,
    BASELINE_RECALL,
    F1_TOLERANCE,
    MANIFEST_PATH,
)

BENCH_ID = "JRE-BENCH-001"
BENCH_SCHEMA_VERSION = "1.0.0"
SEAL_PATH = REPO_ROOT / "benchmarks" / f"{BENCH_ID}.json"

# Phase 5F companion baselines (flag-on scenarios; non-gating — recorded
# from reports/calibration_phase_5f_hooks.json).
COMPANION_BASELINES: tuple[dict[str, Any], ...] = (
    {
        "scenario": "MULTI_VARGA",
        "flags": {"JRS_VARGA_SCORING": True},
        "tp": 73,
        "fp": 32,
        "fn": 15,
        "micro_f1": 0.7565,
        "delta_vs_baseline": 0.0130,
    },
    {
        "scenario": "ALL_ON",
        "flags": {
            "JRS_ASHTA_SCORING": True,
            "JRS_GOCHARA_SCORING": True,
            "JRS_VARGA_SCORING": True,
            "JRS_DASHA_TRANSIT_SCORING": True,
        },
        "tp": 73,
        "fp": 32,
        "fn": 15,
        "micro_f1": 0.7565,
        "delta_vs_baseline": 0.0130,
    },
)

EVENT_DOMAINS = (
    "CAREER",
    "WEALTH",
    "MARRIAGE",
    "HEALTH",
    "SPIRITUALITY",
    "GENERAL",
)

LABEL_SCHEMA_FIELDS: tuple[dict[str, str], ...] = (
    {"field": "event_id", "type": "string", "description": "Stable event identifier"},
    {
        "field": "event_date_utc",
        "type": "string (ISO 8601)",
        "description": "Event occurrence date",
    },
    {
        "field": "event_window_start_utc",
        "type": "string (ISO 8601)",
        "description": "Start of the temporal influence window",
    },
    {
        "field": "event_window_end_utc",
        "type": "string (ISO 8601)",
        "description": "End of the temporal influence window",
    },
    {"field": "domain", "type": "EventDomain enum", "description": "Life domain"},
    {
        "field": "yoga_types",
        "type": "string[]",
        "description": "Yoga names relevant to the event",
    },
    {
        "field": "expected_planets",
        "type": "string[]",
        "description": "Planets whose activation supports the event",
    },
)

EVALUATION_PROTOCOL = {
    "unit": "event-level scoring of every real KnownEvent exactly once",
    "tp": "a relevant prediction matched the event and was not CANCELLED",
    "fp": (
        "the event had no formed relevant prediction but the chart "
        "produced at least one non-CANCELLED prediction (includes the "
        "runner's CANCELLED best-prediction FALSE_NEGATIVE verdicts)"
    ),
    "fn": "no relevant prediction and no non-CANCELLED prediction anywhere",
    "excluded": "synthetic unmatched_<yoga> FALSE_POSITIVE entries",
    "micro_f1": "2*TP / (2*TP + FP + FN) over the pooled 120 decisions",
    "macro_f1": "unweighted mean of per-domain F1",
    "implementation": "jrs.validation.benchmark._score_event_level / evaluate_corpus",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_seal() -> dict[str, Any]:
    corpus_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    entries = corpus_manifest["entries"]
    fixture_ids = [e["fixture_id"] for e in entries]
    # Scope values as written by build_corpus_manifest():
    # "closed-world" (dev) / "open-world" (validation).
    dev = [e["fixture_id"] for e in entries if e.get("target_scope", "closed-world") == "closed-world"]
    validation = [e["fixture_id"] for e in entries if e.get("target_scope") == "open-world"]

    return {
        "benchmark_id": BENCH_ID,
        "schema_version": BENCH_SCHEMA_VERSION,
        "status": "FROZEN",
        "policy": {
            "immutability": (
                "This manifest is the immutable Phase F3 baseline. The corpus, "
                "labels, protocol, and thresholds must never be mutated in "
                "place; amendments create a new benchmark id (JRE-BENCH-002, "
                "JRE-BENCH-003, ...) with a fresh seal."
            ),
            "gate_enforcement": [
                "scripts/run_benchmark_eval.py (CI benchmark-eval job)",
                "scripts/audit_clean_reproduce.py (Phase 9A bit-for-bit audit)",
                "tests/unit/jrs/benchmarks/test_bench_integrity.py",
            ],
            "companion_baselines_policy": (
                "Flag-on companion baselines are recorded for ablation "
                "reference (Phase 10) but do NOT gate: the gating contract "
                "remains the flag-off Phase F3 baseline below."
            ),
            "ablation_protocol": (
                "Phase 10 ablations run scripts/calibration_benchmark.py "
                "scenario permutations against this seal; deltas are "
                "reported relative to the baseline and companion rows."
            ),
        },
        "corpus": {
            "total_charts": len(entries),
            "dev_charts": len(dev),
            "validation_charts": len(validation),
            "fixture_ids": fixture_ids,
            "corpus_manifest_path": str(MANIFEST_PATH.relative_to(REPO_ROOT)),
            "corpus_manifest_sha256": _sha256_file(MANIFEST_PATH),
            "total_inputs_sha256": corpus_manifest.get("total_inputs_sha256", ""),
        },
        "label_schema": {
            "fields": list(LABEL_SCHEMA_FIELDS),
            "event_domains": list(EVENT_DOMAINS),
        },
        "evaluation_protocol": EVALUATION_PROTOCOL,
        "baseline": {
            "name": "Phase F3 (flag-off)",
            "gating": True,
            "micro_f1": BASELINE_MICRO_F1,
            "macro_f1": BASELINE_MACRO_F1,
            "precision": BASELINE_PRECISION,
            "recall": BASELINE_RECALL,
            "confusion": {"tp": 71, "fp": 31, "fn": 18},
            "non_degradation_tolerance": F1_TOLERANCE,
        },
        "companion_baselines": list(COMPANION_BASELINES),
        "sealed_by": "scripts/seal_benchmark.py",
    }


def verify_seal() -> list[str]:
    failures: list[str] = []
    sealed = json.loads(SEAL_PATH.read_text(encoding="utf-8"))
    live = build_seal()
    for key in ("corpus", "label_schema", "evaluation_protocol", "baseline"):
        if sealed.get(key) != live[key]:
            failures.append(f"section drift: {key}")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Seal / verify JRE-BENCH-001.")
    parser.add_argument("--check", action="store_true", help="verify live == sealed")
    args = parser.parse_args(argv)

    if args.check:
        failures = verify_seal()
        if failures:
            print("BENCH SEAL: FAIL", file=sys.stderr)
            for f in failures:
                print(f"  - {f}", file=sys.stderr)
            return 1
        print(f"BENCH SEAL: PASS ({BENCH_ID} matches live repository state)")
        return 0

    seal = build_seal()
    SEAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SEAL_PATH.write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Sealed {BENCH_ID}: {SEAL_PATH}")
    print(f"  corpus: {seal['corpus']['total_charts']} charts | baseline micro-F1={seal['baseline']['micro_f1']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

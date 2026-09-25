#!/usr/bin/env python3
"""Phase F4 frozen benchmark corpus gate.

Executes the frozen 30-dev + 10-validation benchmark corpus with immutable
inputs and canonical ground-truth event labels through
``HistoricalValidationRunner.run_batch()``, then enforces the formal metric
thresholds (Macro vs Micro F1, precision/recall) against the Phase F3
baseline ($F_1 = 0.744$).

Plus golden-state provenance invariant reporting.

Usage::
    python scripts/run_benchmark_eval.py               # full gate
    python scripts/run_benchmark_eval.py --verify-only # hash-only check
    python scripts/run_benchmark_eval.py --metrics-only # metrics, no gate
    python scripts/run_benchmark_eval.py --write-manifest
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from jrs.validation.benchmark import (  # noqa: E402
    DEV_DIR,
    MANIFEST_PATH,
    VAL_DIR,
    assert_benchmark_gate,
    evaluate_corpus,
    verify_manifest,
    write_corpus_manifest,
)

__all__ = ["DEV_DIR", "MANIFEST_PATH", "VAL_DIR", "main"]


def main(argv=None) -> int:
    argv = list(argv or [])
    if "--write-manifest" in argv:
        write_corpus_manifest()
        return 0
    if "--metrics-only" in argv:
        metrics = evaluate_corpus()
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0
    if "--verify-only" in argv:
        mismatches = verify_manifest()
        if mismatches:
            print("HASH VERIFICATION FAILED", file=sys.stderr)
            for m in mismatches:
                print(f"  - {m}", file=sys.stderr)
            return 1
        print(f"40 fixture(s) verified, {len(mismatches)} mismatch(es)")
        return 0
    result = assert_benchmark_gate()
    print(result["verdict"])
    if result["verdict"] == "PASS":
        print("BENCHMARK GATE: PASS (Phase F3 baseline retained at F1=0.744)")
        return 0
    print("BENCHMARK GATE: FAIL", file=sys.stderr)
    for f in result["failures"]:
        print(f"  - {f}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

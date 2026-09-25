#!/usr/bin/env python3
"""Phase 9A: Clean-Room Reproducibility Audit.

One command, zero manual setup: verifies that a fresh checkout of this
repository reproduces every recorded artifact bit-for-bit:

1. environment report (Python, OS, Swiss Ephemeris, engine version);
2. locked-dependency check — every pinned ``requirements.txt``
   distribution is importable at the locked version;
3. golden-state regeneration — all 50 manifests re-hashed, Stage 1-9
   canonical hashes must match bit-for-bit;
4. benchmark reproduction — the frozen corpus must reproduce the
   Phase F3 baseline exactly: Micro-F1 = 0.7435 with TP=71 / FP=31 /
   FN=18 (bit-for-bit, not merely within tolerance);
5. test suites — backend (tests/unit/jrs), API/export contracts, and
   the frontend jest suite.

Exit code 0 only when every stage passes. Designed for CI and for the
Phase 9F release seal (JRE 1.0.0-rc1).

Usage::

    python scripts/audit_clean_reproduce.py            # full audit
    python scripts/audit_clean_reproduce.py --skip-frontend
    python scripts/audit_clean_reproduce.py --json     # machine report
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

AUDIT_SCHEMA_VERSION = "1.0.0"

# Frozen reproduction target (Phase F3 baseline; identical to the
# constants in jrs.validation.benchmark and the JRE-BENCH-001 seal).
FROZEN_BASELINE = {
    "micro_f1": 0.7435,
    "tp": 71,
    "fp": 31,
    "fn": 18,
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stage_environment() -> dict[str, Any]:
    from jrs.api.schemas import ENGINE_VERSION

    try:
        import swisseph as swe

        swe_version = str(swe.version)
    except Exception as exc:  # pragma: no cover - environment-dependent
        swe_version = f"UNAVAILABLE: {exc}"
    return {
        "python": platform.python_version(),
        "os": f"{platform.system()} {platform.release()} {platform.machine()}",
        "swisseph": swe_version,
        "engine_version": ENGINE_VERSION,
    }


def stage_dependencies() -> dict[str, Any]:
    """Verify every pinned requirements.txt entry at its locked version."""
    requirements = REPO_ROOT / "requirements.txt"
    mismatches: list[str] = []
    checked = 0
    for raw in requirements.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if any(marker in line for marker in ("git+", "http://", "https://", " @ ")):
            continue  # URL/path requirements: not version-pinnable here
        # PEP 508 minimal parse: name[extra] ==spec (we only emit == pins
        # plus a few >= floors; floors are checked for installability).
        name = line.split(";")[0].split("==")[0].split(">=")[0].split("<")[0]
        name = name.split("[")[0].strip()
        if not name:
            continue
        checked += 1
        try:
            installed = metadata.version(name)
        except metadata.PackageNotFoundError:
            mismatches.append(f"{name}: NOT INSTALLED (required: {line})")
            continue
        if "==" in line:
            expected = line.split("==")[1].split(";")[0].strip()
            if installed != expected:
                mismatches.append(
                    f"{name}: locked {expected}, installed {installed}"
                )
    return {
        "checked": checked,
        "mismatches": mismatches,
        "ok": not mismatches,
    }


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=1800,
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode, output


def stage_golden_states() -> dict[str, Any]:
    """Regenerate all 50 golden manifests and verify Stage 1-9 hashes."""
    gen_rc, gen_out = _run(
        [sys.executable, "scripts/generate_golden_states.py", "generate"]
    )
    if gen_rc != 0:
        return {"ok": False, "error": f"generate failed: {gen_out[-400:]}"}
    ver_rc, ver_out = _run(
        [sys.executable, "scripts/generate_golden_states.py", "verify"]
    )
    if ver_rc != 0:
        return {"ok": False, "error": f"verify failed: {ver_out[-400:]}"}
    # Parse the "50 fixture(s) verified, 0 mismatch(es)" line.
    return {"ok": True, "summary": ver_out.splitlines()[-1] if ver_out else ""}


def stage_benchmark() -> dict[str, Any]:
    """Re-execute the frozen benchmark; require bit-for-bit baseline."""
    from jrs.validation.benchmark import (
        BASELINE_MICRO_F1,
        evaluate_corpus,
    )

    metrics = evaluate_corpus()
    tp = metrics["overall_metrics"]["true_positives"]
    fp = metrics["overall_metrics"]["false_positives"]
    fn = metrics["overall_metrics"]["false_negatives"]
    micro = metrics["micro_f1"]
    # "Bit-for-bit" contract: the confusion counts must match exactly,
    # and micro-F1 must equal the recorded 4-decimal canonical value
    # (142/191 = 0.74345549... is stored rounded as 0.7435).
    bit_for_bit = (
        tp == FROZEN_BASELINE["tp"]
        and fp == FROZEN_BASELINE["fp"]
        and fn == FROZEN_BASELINE["fn"]
        and round(micro, 4) == FROZEN_BASELINE["micro_f1"]
    )
    return {
        "ok": bit_for_bit,
        "observed": {"tp": tp, "fp": fp, "fn": fn, "micro_f1": micro},
        "expected": FROZEN_BASELINE,
        "baseline_constant": BASELINE_MICRO_F1,
        "gate_within_tolerance": micro >= BASELINE_MICRO_F1 - 0.005,
    }


def stage_test_suites(skip_frontend: bool) -> dict[str, Any]:
    results: dict[str, Any] = {}
    rc, out = _run(
        [sys.executable, "-m", "pytest", "tests/unit/jrs", "-q", "--no-header"]
    )
    results["backend"] = {"ok": rc == 0, "tail": out.splitlines()[-1] if out else ""}

    rc, out = _run([sys.executable, "scripts/verify_openapi_contract.py"])
    results["openapi_contract"] = {"ok": rc == 0, "tail": out.splitlines()[-1] if out else ""}

    if not skip_frontend:
        rc, out = _run(["npx", "jest", "--ci", "--silent"], cwd=REPO_ROOT / "frontend")
        tail = out.splitlines()[-4:] if out else []
        results["frontend_jest"] = {"ok": rc == 0, "tail": " | ".join(tail)}
    return results


def run_audit(skip_frontend: bool = False) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "audit_id": "JRE-REPRODUCE-001",
        "stages": {},
    }
    report["stages"]["environment"] = stage_environment()
    report["stages"]["dependencies"] = stage_dependencies()
    report["stages"]["golden_states"] = stage_golden_states()
    report["stages"]["benchmark"] = stage_benchmark()
    report["stages"]["test_suites"] = stage_test_suites(skip_frontend)

    stage_oks = [
        report["stages"]["dependencies"]["ok"],
        report["stages"]["golden_states"]["ok"],
        report["stages"]["benchmark"]["ok"],
        all(v["ok"] for v in report["stages"]["test_suites"].values()),
    ]
    report["verdict"] = "REPRODUCIBLE" if all(stage_oks) else "DIVERGENT"
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 9A clean-room reproducibility audit."
    )
    parser.add_argument("--skip-frontend", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    report = run_audit(skip_frontend=args.skip_frontend)

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("PHASE 9A CLEAN-ROOM REPRODUCIBILITY AUDIT")
        env = report["stages"]["environment"]
        print(
            f"environment: python={env['python']} | {env['os']} | "
            f"swisseph={env['swisseph']} | engine={env['engine_version']}"
        )
        deps = report["stages"]["dependencies"]
        print(
            f"dependencies: {deps['checked']} pinned distributions — "
            + ("OK" if deps["ok"] else f"MISMATCH: {deps['mismatches'][:5]}")
        )
        golden = report["stages"]["golden_states"]
        print(
            "golden_states (Stage 1-9): "
            + ("OK — " + golden.get("summary", "") if golden["ok"] else "FAIL")
        )
        bench = report["stages"]["benchmark"]
        obs = bench["observed"]
        print(
            f"benchmark: {'BIT-FOR-BIT OK' if bench['ok'] else 'DIVERGED'} — "
            f"TP={obs['tp']} FP={obs['fp']} FN={obs['fn']} "
            f"micro-F1={obs['micro_f1']:.4f} "
            f"(target {FROZEN_BASELINE['tp']}/{FROZEN_BASELINE['fp']}/"
            f"{FROZEN_BASELINE['fn']} @ {FROZEN_BASELINE['micro_f1']})"
        )
        for name, suite in report["stages"]["test_suites"].items():
            print(f"suite {name}: {'OK' if suite['ok'] else 'FAIL'} — {suite['tail']}")
        print(f"VERDICT: {report['verdict']}")

    return 0 if report["verdict"] == "REPRODUCIBLE" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

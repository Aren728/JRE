#!/usr/bin/env python3
"""Standalone calibration runner — batch fixture evaluation and reporting.

Usage::

    python scripts/calibrate.py
    python scripts/calibrate.py --output-dir reports/
    python scripts/calibrate.py --format json
    python scripts/calibrate.py --format markdown
    python scripts/calibrate.py --format both

Outputs a structured JSON and/or Markdown report summarizing rule fidelity
and implementation correctness metrics per domain.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))


def main() -> int:
    """Run calibration and output reports."""
    parser = argparse.ArgumentParser(
        description="JRS Empirical Calibration & Rule Performance Measurement",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for reports (default: reports/)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "both"],
        default="both",
        help="Output format (default: both)",
    )
    args = parser.parse_args()

    # Import here to avoid path issues when running as script
    from tests.calibration.pipeline import run_calibration

    print("Running calibration across all domains...")
    print()

    report = run_calibration()

    # Print summary to stdout
    print("=" * 60)
    print("CALIBRATION SUMMARY")
    print("=" * 60)
    print(f"Domains evaluated: {len(report.domain_metrics)}")
    print(f"Overall Precision:     {report.precision:.4f}")
    print(f"Overall Recall:        {report.recall:.4f}")
    print(f"Overall F1 Score:      {report.f1_score:.4f}")
    print(f"Overall FPR:           {report.false_positive_rate:.4f}")
    print(f"Overall FNR:           {report.false_negative_rate:.4f}")
    print(f"Overall Timing Overlap:{report.timing_overlap_score:.4f}")
    print()

    for dm in report.domain_metrics:
        print(f"  {dm.domain:20s}  "
              f"P={dm.precision:.3f}  "
              f"R={dm.recall:.3f}  "
              f"F1={dm.f1_score:.3f}  "
              f"charts={dm.total_charts}")
    print()

    # Write reports
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.format in ("json", "both"):
        json_path = output_dir / "calibration_report.json"
        with json_path.open("w") as f:
            json.dump(report.to_dict(), f, indent=2, sort_keys=True)
        print(f"JSON report written to: {json_path}")

    if args.format in ("markdown", "both"):
        md_path = output_dir / "calibration_report.md"
        with md_path.open("w") as f:
            f.write(report.to_markdown())
        print(f"Markdown report written to: {md_path}")

    print()
    print("Calibration complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())

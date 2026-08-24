#!/usr/bin/env python3
"""Standalone calibration runner — batch fixture evaluation and reporting.

Usage::

    python scripts/calibrate.py
    python scripts/calibrate.py --output-dir reports/
    python scripts/calibrate.py --format json
    python scripts/calibrate.py --format markdown
    python scripts/calibrate.py --format both
    python scripts/calibrate.py --systems vedic,western,numerology
    python scripts/calibrate.py --compare

Outputs a structured JSON and/or Markdown report summarizing rule fidelity
and implementation correctness metrics per domain.  Supports optional
multi-system calibration comparing Vedic-only vs multi-system performance.
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
    parser.add_argument(
        "--systems",
        type=str,
        default="vedic",
        help=(
            "Comma-separated systems to run "
            "(e.g., vedic,western,numerology). Default: vedic"
        ),
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help=(
            "Run comparative calibration: single-system vs multi-system. "
            "Generates a comparative Markdown report."
        ),
    )
    args = parser.parse_args()

    # Import here to avoid path issues when running as script
    from tests.calibration.pipeline import (
        run_calibration,
        run_comparative_calibration,
        run_multi_system_calibration,
    )

    if args.compare:
        # Comparative mode: single vs multi-system
        print("Running comparative calibration (single vs multi-system)...")
        print()

        comparative = run_comparative_calibration()

        # Print summary to stdout
        print("=" * 60)
        print("COMPARATIVE CALIBRATION SUMMARY")
        print("=" * 60)
        print(f"Mode: {comparative.comparison_mode}")
        print()
        print(f"  Single-System F1:  {comparative.single_system_report.f1_score:.4f}")
        print(f"  Multi-System F1:   {comparative.multi_system_report.f1_score:.4f}")
        print(f"  F1 Delta:          {comparative.f1_delta:+.4f}")
        print(f"  Verdict:           {comparative.convergence_verdict}")
        print()

        # Write reports
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if args.format in ("json", "both"):
            json_path = output_dir / "calibration_report_multisystem.json"
            with json_path.open("w") as f:
                json.dump(
                    comparative.to_dict(), f, indent=2, sort_keys=True,
                )
            print(f"JSON report written to: {json_path}")

        if args.format in ("markdown", "both"):
            md_path = output_dir / "calibration_report_multisystem.md"
            with md_path.open("w") as f:
                f.write(comparative.to_markdown())
            print(f"Markdown report written to: {md_path}")

    else:
        # Standard single-system or multi-system mode
        requested_systems = tuple(
            s.strip().lower() for s in args.systems.split(",")
        )

        if len(requested_systems) > 1:
            print(
                f"Running multi-system calibration for: "
                f"{', '.join(requested_systems)}..."
            )
            report = run_multi_system_calibration(requested_systems)
        else:
            print("Running single-system calibration...")
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
            print(
                f"  {dm.domain:20s}  "
                f"P={dm.precision:.3f}  "
                f"R={dm.recall:.3f}  "
                f"F1={dm.f1_score:.3f}  "
                f"charts={dm.total_charts}"
            )
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

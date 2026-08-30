#!/usr/bin/env python3
"""Beta Feedback Analyzer — Reads and categorizes beta tester feedback.

Reads reports/beta_feedback_log.jsonl and generates a summary report
categorizing feedback into False Negatives, False Positives, and
UI/UX suggestions.

Usage::

    python scripts/analyze_beta_feedback.py
    python scripts/analyze_beta_feedback.py --input reports/beta_feedback_log.jsonl
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = _PROJECT_ROOT / "reports"


def load_feedback(path: Path) -> list[dict[str, Any]]:
    """Load feedback entries from JSONL file."""
    if not path.exists():
        return []
    entries = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def categorize_feedback(entries: list[dict[str, Any]]) -> dict[str, list[dict]]:
    """Categorize feedback by type based on content analysis."""
    categories: dict[str, list[dict]] = defaultdict(list)

    for entry in entries:
        notes = entry.get("notes", "").lower()
        expected = entry.get("expected_outcome", "").lower()
        actual = entry.get("actual_outcome", "").lower()

        # Auto-categorize based on content
        if "false negative" in notes or "missed" in notes or "should have" in notes:
            categories["false_negative"].append(entry)
        elif "false positive" in notes or "incorrect" in notes or "wrong" in notes:
            categories["false_positive"].append(entry)
        elif "timing" in notes or "dasha" in notes:
            categories["timing_error"].append(entry)
        elif any(kw in notes for kw in ["ui", "ux", "format", "report", "display", "readability"]):
            categories["ui_ux"].append(entry)
        elif any(kw in notes for kw in ["api", "endpoint", "documentation", "docs"]):
            categories["api_feedback"].append(entry)
        else:
            # Default categorization based on expected vs actual
            if expected and actual and expected != actual:
                if "not" in actual or "none" in actual or "no yoga" in actual:
                    categories["false_negative"].append(entry)
                else:
                    categories["uncategorized"].append(entry)
            else:
                categories["uncategorized"].append(entry)

    return dict(categories)


def generate_report(entries: list[dict], categories: dict[str, list]) -> str:
    """Generate a markdown report from categorized feedback."""
    lines: list[str] = []

    lines.append("# Beta Tester Feedback Analysis")
    lines.append("")
    lines.append(f"**Total Feedback Entries:** {len(entries)}")
    lines.append(f"**Analysis Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Category Summary ──
    lines.append("## Category Summary")
    lines.append("")
    lines.append("| Category | Count | Percentage |")
    lines.append("|----------|-------|------------|")
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        pct = len(items) / len(entries) * 100 if entries else 0
        lines.append(f"| {cat.replace('_', ' ').title()} | {len(items)} | {pct:.0f}% |")
    lines.append("")

    # ── False Negatives ──
    fn_entries = categories.get("false_negative", [])
    if fn_entries:
        lines.append("---")
        lines.append("")
        lines.append("## False Negatives (Missing Yogas)")
        lines.append("")
        lines.append("These are cases where the engine missed a yoga that should have been detected.")
        lines.append("")
        for i, entry in enumerate(fn_entries, 1):
            lines.append(f"### FN #{i}: {entry.get('fixture_id', 'Unknown')}")
            lines.append(f"- **Event Date:** {entry.get('event_date', '—')}")
            lines.append(f"- **Expected:** {entry.get('expected_outcome', '—')}")
            lines.append(f"- **Actual:** {entry.get('actual_outcome', '—')}")
            lines.append(f"- **Notes:** {entry.get('notes', '—')}")
            lines.append("")

        # Pattern analysis
        fixture_counter = Counter(e.get("fixture_id", "") for e in fn_entries)
        lines.append("### Pattern: Most Reported Fixtures")
        lines.append("")
        for fixture, count in fixture_counter.most_common(5):
            lines.append(f"- **{fixture}**: {count} reports")
        lines.append("")

    # ── False Positives ──
    fp_entries = categories.get("false_positive", [])
    if fp_entries:
        lines.append("---")
        lines.append("")
        lines.append("## False Positives (Over-triggering)")
        lines.append("")
        lines.append("These are cases where the engine detected a yoga that shouldn't exist.")
        lines.append("")
        for i, entry in enumerate(fp_entries, 1):
            lines.append(f"### FP #{i}: {entry.get('fixture_id', 'Unknown')}")
            lines.append(f"- **Event Date:** {entry.get('event_date', '—')}")
            lines.append(f"- **Expected:** {entry.get('expected_outcome', '—')}")
            lines.append(f"- **Actual:** {entry.get('actual_outcome', '—')}")
            lines.append(f"- **Notes:** {entry.get('notes', '—')}")
            lines.append("")

    # ── Timing Errors ──
    timing_entries = categories.get("timing_error", [])
    if timing_entries:
        lines.append("---")
        lines.append("")
        lines.append("## Timing Errors (Dasha/Activation)")
        lines.append("")
        for i, entry in enumerate(timing_entries, 1):
            lines.append(f"### TE #{i}: {entry.get('fixture_id', 'Unknown')}")
            lines.append(f"- **Event Date:** {entry.get('event_date', '—')}")
            lines.append(f"- **Notes:** {entry.get('notes', '—')}")
            lines.append("")

    # ── UI/UX Suggestions ──
    ui_entries = categories.get("ui_ux", [])
    if ui_entries:
        lines.append("---")
        lines.append("")
        lines.append("## UI/UX Suggestions")
        lines.append("")
        for i, entry in enumerate(ui_entries, 1):
            lines.append(f"- **{entry.get('fixture_id', 'Unknown')}**: {entry.get('notes', '—')}")
        lines.append("")

    # ── Recommendations ──
    lines.append("---")
    lines.append("")
    lines.append("## Recommendations")
    lines.append("")

    if fn_entries:
        lines.append(f"1. **Investigate {len(fn_entries)} False Negatives:** Review the reported missing yogas "
                     "and determine which require new yoga detectors vs. which are astronomically correct.")
    if fp_entries:
        lines.append(f"2. **Review {len(fp_entries)} False Positives:** Check if the reported over-triggering "
                     "is due to modifier pipeline gaps or incorrect yoga detection logic.")
    if timing_entries:
        lines.append(f"3. **Address {len(timing_entries)} Timing Errors:** Review Dasha activation logic "
                     "for the reported cases.")
    if ui_entries:
        lines.append(f"4. **Implement {len(ui_entries)} UI/UX Improvements:** Prioritize based on frequency.")

    if not entries:
        lines.append("No feedback received yet. Beta testers can submit feedback via:")
        lines.append("```")
        lines.append('curl -X POST http://localhost:8000/api/v1/feedback \\')
        lines.append('  -H "Content-Type: application/json" \\')
        lines.append("  -d '{\"fixture_id\": \"chart_001\", \"notes\": \"Your feedback here\"}'")
        lines.append("```")

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Analyze beta tester feedback.")
    parser.add_argument(
        "--input", type=Path,
        default=REPORTS_DIR / "beta_feedback_log.jsonl",
        help="Path to feedback JSONL file.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Beta Feedback Analyzer")
    print("=" * 60)
    print()

    entries = load_feedback(args.input)
    print(f"Loaded {len(entries)} feedback entries from {args.input}")

    if not entries:
        print("No feedback entries found.")
        print(f"Submit feedback via: POST /api/v1/feedback")
        return 0

    categories = categorize_feedback(entries)
    report = generate_report(entries, categories)

    # Write report
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / "beta_feedback_analysis.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write(report)
    print(f"Report written to: {report_path}")

    # Print summary
    print()
    print("Category Summary:")
    for cat, items in sorted(categories.items(), key=lambda x: -len(x[1])):
        print(f"  {cat}: {len(items)}")

    print()
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())

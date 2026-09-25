#!/usr/bin/env python3
"""Phase 5B/5C Ashtakavarga diagnostics CLI.

Renders the deterministic Ashtakavarga report (Phase 5B engine:
``jrs.calculations.ashtakavarga``) for benchmark fixtures:

- BAV grid: 8 anchors x 12 rashis (0-8 Rekhas each, row totals canonical)
- SAV with classical banding (strong >= 30, good >= 28, average >= 25,
  weak < 25 per the strong-house threshold convention)
- Shodhita SAV after Trikona + Ekadhipatya Shodhana
- Shodhita Pinda per anchor

Usage::

    python scripts/ashtakavarga_diagnostics.py chart_001_pilot
    python scripts/ashtakavarga_diagnostics.py --all --brief
    python scripts/ashtakavarga_diagnostics.py chart_002_curie --json

Deterministic: identical inputs always produce byte-identical output.
No engine state is mutated; the benchmark baseline is untouched.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from jrs.api.dependencies import build_jre_facts, compute_chart_from_fixture  # noqa: E402
from jrs.calculations.ashtakavarga import (  # noqa: E402
    ANCHORS,
    RASHI_ORDER,
    ashtakavarga_to_dict,
    compute_full_ashtakavarga,
)
from jrs.validation.benchmark import DEV_DIR, VAL_DIR, load_json  # noqa: E402

# Classical SAV banding per sign (337/12 ~ 28.08 mean).
SAV_BANDS: tuple[tuple[int, str], ...] = (
    (30, "STRONG"),
    (28, "GOOD"),
    (25, "AVERAGE"),
    (0, "WEAK"),
)


def sav_band(value: int) -> str:
    for threshold, label in SAV_BANDS:
        if value >= threshold:
            return label
    return "WEAK"


def _resolve_fixture(fixture_id: str) -> Path:
    for directory in (DEV_DIR, VAL_DIR):
        candidate = directory / f"{fixture_id}.json"
        if candidate.exists():
            found: Path = candidate
            return found
    raise SystemExit(
        f"fixture not found in benchmark corpus: {fixture_id!r} "
        f"(dev: {DEV_DIR.name}/, validation: {VAL_DIR.name}/)"
    )


def _load_fixture_by_id(fixture_id: str) -> dict[str, Any]:
    data: dict[str, Any] = load_json(_resolve_fixture(fixture_id))
    return data


def _all_fixture_ids() -> list[str]:
    ids: list[str] = []
    for directory in (DEV_DIR, VAL_DIR):
        ids.extend(p.stem for p in sorted(directory.glob("chart_*.json")))
    return ids


def compute_report(fixture_id: str) -> dict[str, Any]:
    """Compute the Ashtakavarga report for one benchmark fixture."""
    data = _load_fixture_by_id(fixture_id)
    natal = compute_chart_from_fixture(data)
    facts: dict[str, Any] = build_jre_facts(natal)
    report: dict[str, Any] = ashtakavarga_to_dict(compute_full_ashtakavarga(facts))
    report["fixture_id"] = fixture_id
    report["subject"] = str(data.get("_meta", {}).get("subject", ""))
    return report


# ── Rendering ───────────────────────────────────────────────────────────────
def render_table(report: dict[str, Any]) -> str:
    """Human-readable grid: BAV rows, SAV banding, Shodhita, Pinda."""
    bav = report["bav"]
    sav = report["sav"]
    shodhita = report["shodhita_sav"]
    pinda = report["pinda"]

    header = "SIGN        " + " ".join(f"{a[:3]:>3}" for a in ANCHORS) + " | SAV SHD"
    lines = [
        f"Fixture: {report['fixture_id']} ({report['subject']})",
        f"Version: {report['version']}",
        "",
        header,
        "-" * len(header),
    ]
    for idx, sign in enumerate(RASHI_ORDER):
        row = " ".join(f"{bav[a][idx]:>3}" for a in ANCHORS)
        lines.append(
            f"{sign:<12}{row} | {sav[idx]:>3} {shodhita[idx]:>3}"
        )
    lines.extend(
        [
            "-" * len(header),
            "TOTAL      " + " ".join(f"{sum(bav[a]):>3}" for a in ANCHORS) + f" | {sum(sav):>3} {sum(shodhita):>3}",
            "",
            "SAV bands  " + " ".join(f"{sav_band(v)[:3]:>3}" for v in sav),
            "",
        ]
    )

    lines.append("Shodhita Pinda (rashi + graha = shodhya):")
    for anchor in ANCHORS:
        p = pinda[anchor]
        lines.append(
            f"  {anchor:<8} {p['rashi_pinda']:>5} + {p['graha_pinda']:>5} = {p['shodhya_pinda']:>5}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "fixture",
        nargs="?",
        default=None,
        help="Fixture id from the frozen benchmark corpus (e.g. chart_001_pilot).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Render a brief summary for every corpus fixture.",
    )
    parser.add_argument(
        "--brief",
        action="store_true",
        help="One-line SAV summary per fixture (implies --all semantics).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the machine-readable report instead of the table.",
    )
    args = parser.parse_args(argv)

    if args.fixture is None and not args.all:
        parser.error("provide a fixture id or --all")

    if args.all:
        briefs: list[dict[str, Any]] = []
        for fid in _all_fixture_ids():
            report = compute_report(fid)
            briefs.append(
                {
                    "fixture_id": fid,
                    "subject": report["subject"],
                    "sav": report["sav"],
                    "sav_total": sum(report["sav"]),
                    "sav_band_counts": {
                        band: sum(1 for v in report["sav"] if sav_band(v) == band)
                        for band in ("STRONG", "GOOD", "AVERAGE", "WEAK")
                    },
                    "shodhita_total": sum(report["shodhita_sav"]),
                    "pinda_shodhya": {
                        a: report["pinda"][a]["shodhya_pinda"] for a in ANCHORS
                    },
                }
            )
        if args.json:
            print(json.dumps(briefs, indent=2, sort_keys=True))
        else:
            for b in briefs:
                counts = b["sav_band_counts"]
                print(
                    f"{b['fixture_id']:<22} SAV={b['sav_total']:>3} "
                    f"SHD={b['shodhita_total']:>3} "
                    f"[S{counts['STRONG']:>2} G{counts['GOOD']:>2} "
                    f"A{counts['AVERAGE']:>2} W{counts['WEAK']:>2}] "
                    f"{b['subject']}"
                )
        return 0

    report = compute_report(args.fixture)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_table(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())

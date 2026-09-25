#!/usr/bin/env python3
"""Phase 8: Export pipeline engine CLI.

Runs the deterministic pipeline for one fixture and exports artifacts
in the four Phase 8 formats (all writes happen here — the library
layer stays I/O-free):

- ``json``    diagnostic JSON of the full evidence DAG (provenance);
- ``graphml`` GraphML 1.1 export of the same DAG (Gephi/yEd/NetworkX);
- ``svg``     D1/D9/D10/D60 chart renderings (north/south/wheel);
- ``pdf``     executive forensic PDF report (ReportLab, optional extra);
- ``all``     everything above into one output directory.

Determinism: every artifact is a pure function of the fixture + flags.
The evaluation instant for dasha facts is pinned (never wall-clock),
and the PDF is built with ``invariant=1``, so re-runs are byte-stable.

Usage::

    python scripts/export_pipeline.py chart_001_pilot --out exports/chart_001
    python scripts/export_pipeline.py chart_001_pilot --formats json graphml
    python scripts/export_pipeline.py chart_001_pilot --formats svg --styles north wheel
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from jrs.api.dependencies import build_jre_facts, compute_chart_from_fixture, load_fixture  # noqa: E402
from jrs.api.schemas import ENGINE_VERSION  # noqa: E402
from jrs.export import (  # noqa: E402
    provenance_to_diagnostic_json,
    provenance_to_graphml,
    render_chart_svg,
)
from jrs.export.pdf_report import ForensicReportInput, render_forensic_pdf  # noqa: E402
from jrs.export.svg_renderer import ChartPlacement  # noqa: E402
from jrs.prediction_engine.provenance import EvidenceGraphService  # noqa: E402
from jrs.yoga_evaluator.service import YogaEvaluatorService  # noqa: E402

_FORMATS: tuple[str, ...] = ("json", "graphml", "svg", "pdf", "all")


def _build_artifacts(fixture_id: str) -> dict[str, Any]:
    """Run the deterministic pipeline once and collect export inputs."""
    fixture = load_fixture(fixture_id)
    chart = compute_chart_from_fixture(fixture)
    facts = build_jre_facts(chart)
    yoga_evals = YogaEvaluatorService().evaluate_classical_yogas(facts)
    graph = EvidenceGraphService(prediction_id=f"P-{fixture_id}").build_graph(
        jre_facts=facts,
        yoga_evals=yoga_evals,
    )

    positions: list[dict[str, Any]] = []
    longitudes: dict[str, float] = {}
    houses: dict[str, int] = {}
    lagna_sign = int(facts.get("lagna_sign", 1))
    for body, pdata in facts.get("planets", {}).items():
        sign = pdata.get("rashi", "")
        lon = pdata.get("longitude")
        if isinstance(lon, (int, float)):
            longitudes[body] = float(lon)
        house = pdata.get("house")
        if isinstance(house, int):
            houses[body] = house
        positions.append({"body": body, "sign": sign, "house": house})

    subject = str(fixture.get("_meta", {}).get("subject", fixture_id))
    yogas = [
        {
            "yoga_name": getattr(ev, "yoga_name", ""),
            "status": getattr(getattr(ev, "status", None), "value", ""),
            "chain_impact": getattr(ev, "chain_impact", None),
            "cancellation_reason": getattr(ev, "cancellation_reason", None),
        }
        for ev in yoga_evals
    ]

    return {
        "fixture_id": fixture_id,
        "subject": subject,
        "lagna_sign": lagna_sign,
        "lagna": str(facts.get("lagna", "")),
        "moon_nakshatra": str(facts.get("moon_nakshatra", "")),
        "longitudes": longitudes,
        "positions": positions,
        "yogas": yogas,
        "graph": graph,
    }


def _write_json(out_dir: Path, artifacts: dict[str, Any]) -> Path:
    payload = provenance_to_diagnostic_json(
        artifacts["graph"], fixture_id=artifacts["fixture_id"]
    )
    path = out_dir / "provenance.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _write_graphml(out_dir: Path, artifacts: dict[str, Any]) -> Path:
    path = out_dir / "provenance.graphml"
    path.write_text(
        provenance_to_graphml(artifacts["graph"], fixture_id=artifacts["fixture_id"]),
        encoding="utf-8",
    )
    return path


def _write_svg(out_dir: Path, artifacts: dict[str, Any], styles: list[str]) -> list[Path]:
    written: list[Path] = []
    lagna_sign = artifacts["lagna_sign"]
    placements = [
        ChartPlacement(body=body, sign_index=int(lon // 30.0) % 12)
        for body, lon in sorted(artifacts["longitudes"].items())
    ]
    for division in ("D1", "D9", "D10", "D60"):
        for style in styles:
            svg = render_chart_svg(
                placements,
                lagna_sign=lagna_sign,
                division=division,
                style=style,
                title=f"{artifacts['subject']} — {division} ({style})",
            )
            path = out_dir / f"chart_{division.lower()}_{style}.svg"
            path.write_text(svg, encoding="utf-8")
            written.append(path)
    return written


def _write_pdf(out_dir: Path, artifacts: dict[str, Any]) -> Path:
    report_input = ForensicReportInput(
        subject=artifacts["subject"],
        fixture_id=artifacts["fixture_id"],
        lagna=artifacts["lagna"],
        moon_nakshatra=artifacts["moon_nakshatra"],
        engine_version=ENGINE_VERSION,
        positions=artifacts["positions"],
        yogas=artifacts["yogas"],
        provenance_summary=provenance_to_diagnostic_json(
            artifacts["graph"], fixture_id=artifacts["fixture_id"]
        ),
    )
    path = out_dir / "forensic_report.pdf"
    path.write_bytes(render_forensic_pdf(report_input))
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 8 export pipeline: provenance JSON/GraphML, SVG charts, forensic PDF."
    )
    parser.add_argument("fixture_id", help="Fixture id (e.g. chart_001_pilot)")
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=_FORMATS,
        default=["all"],
        help="Artifacts to export (default: all)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory (default: exports/<fixture_id>)",
    )
    parser.add_argument(
        "--styles",
        nargs="+",
        choices=("north", "south", "wheel"),
        default=["north", "south", "wheel"],
        help="SVG chart styles (default: all three)",
    )
    args = parser.parse_args(argv)

    formats: list[str] = []
    for fmt in args.formats:
        if fmt == "all":
            formats = ["json", "graphml", "svg", "pdf"]
            break
        formats.append(fmt)

    artifacts = _build_artifacts(args.fixture_id)
    out_dir = args.out or Path("exports") / args.fixture_id
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    if "json" in formats:
        written.append(_write_json(out_dir, artifacts))
    if "graphml" in formats:
        written.append(_write_graphml(out_dir, artifacts))
    if "svg" in formats:
        written.extend(_write_svg(out_dir, artifacts, args.styles))
    if "pdf" in formats:
        try:
            written.append(_write_pdf(out_dir, artifacts))
        except ImportError as exc:
            print(f"SKIPPED pdf: {exc}", file=sys.stderr)

    for path in written:
        print(f"  WROTE {path}")
    print(f"EXPORT COMPLETE: {len(written)} artifact(s) in {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

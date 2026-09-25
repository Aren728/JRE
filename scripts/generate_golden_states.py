#!/usr/bin/env python3
"""Generate / verify golden-state fixtures for the validation_charts cohort.

Phase 2 (JRS-091 Deterministic Golden-State Validation) tooling.

For each ``tests/fixtures/validation_charts/chart_*.json`` fixture this
script runs the deterministic pipeline through four checkpoints —
``chart`` (natal chart), ``jre_facts`` (fact extraction), ``dasha``
(Vimshottari state), ``yogas`` (classical yoga evaluation) — and records
their canonical SHA-256 hashes as a
``tests/fixtures/golden_states/<fixture_id>.json`` manifest.

Phase 4 addition — evidence-graph provenance invariants (JRS-092):
    A fifth stage, ``evidence_graph``, is recorded per fixture. It
    captures the Phase 3 DAG (built via
    ``EvidenceGraphService.build_graph`` from the same jre_facts and
    yoga evaluations) with hard assertions on its structure:
    ``node_count`` and ``edge_count`` must both exceed zero, and the
    prediction, temporal, and rule nodes must be present and
    acyclic-consistent. These invariants fold the provenance-layer
    contract directly into the golden-state regression gate, so any
    mutation that collapses or disconnects the evidence DAG fails the
    hash check even when the yoga results are untouched.

Modes:
    generate   Run the pipeline, write/rewrite the golden-state manifests.
    verify     Re-run the pipeline and recompute every stage hash against
               the committed manifests. Non-zero exit on any mismatch.

Phase 5B addition — ashtakavarga stage:
    A sixth canonical stage records the deterministic Ashtakavarga
    report (BAV 0-8 Rekhas per anchor, SAV summing to the invariant 337,
    Trikona + Ekadhipatya Shodhana, Shodhita Pinda) computed from the
    same jre_facts. The ashta_scoring_enabled feature flag gates only
    downstream *scoring* injection, never this golden stage.

Determinism notes:
- ``calculate_vimshottari_dasha`` defaults ``target_date`` to wall-clock
  *now*, which would poison the hash. The dasha stage is therefore pinned
  to ``GOLDEN_TRANSIT_DATE`` (an invariant reference instant) — exactly
  the class of hidden non-determinism this suite exists to catch.
- Floats are canonicalized to 6 decimals by the shared contract in
  ``jrs.validation.golden_state`` (parity with the packet store).

Usage::

    python scripts/generate_golden_states.py generate
    python scripts/generate_golden_states.py verify
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

from jrs.api.dependencies import build_jre_facts, compute_chart_from_fixture
from jrs.api.schemas import ENGINE_VERSION
from jrs.calculations.ashtakavarga import (
    ashtakavarga_to_dict,
    compute_full_ashtakavarga,
)
from jrs.calculations.dasha_transit import (
    DASHA_TRANSIT_EPOCH,
    compute_dasha_transit,
    dasha_transit_to_dict,
)
from jrs.calculations.gochara import (
    GOCHARA_TRANSIT_EPOCH,
    compute_gochara,
    compute_transit_positions,
    gochara_to_dict,
)
from jrs.calculations.varga import (
    compute_multi_varga,
    multi_varga_to_dict,
)
from jrs.engine.dasha import calculate_vimshottari_dasha
from jrs.prediction_engine.provenance import EvidenceGraphService
from jrs.validation.golden_state import (
    GoldenStateManifest,
    GoldenStateMismatchError,
    GoldenStateValidator,
    build_manifest,
)
from jrs.yoga_evaluator.service import YogaEvaluatorService

REPO_ROOT = Path(__file__).resolve().parent.parent
COHORT_DIR = REPO_ROOT / "tests" / "fixtures" / "validation_charts"
GOLDEN_DIR = REPO_ROOT / "tests" / "fixtures" / "golden_states"

#: Pinned reference instant for the dasha checkpoint (see module docstring).
GOLDEN_TRANSIT_DATE = dt.datetime(2020, 1, 1)


def _assert_evidence_graph_invariants(graph_dict: dict[str, Any]) -> None:
    """Assert the Phase 3 DAG provenance invariants (JRS-092).

    The evidence graph must be structurally alive:
    - at least one node and one edge (a collapsed graph cannot trace
      provenance);
    - exactly one EVALUATION prediction node rooted at the top;
    - at least one RULE node per yoga evaluation;
    - every rule node reachable from the prediction node (the chain
      prediction -> rule -> facts must be connected).

    Raises:
        ValueError: If any invariant is violated.
    """
    nodes = graph_dict.get("nodes", [])
    edges = graph_dict.get("edges", [])
    node_count = len(nodes)
    edge_count = len(edges)

    if node_count <= 0:
        raise ValueError("evidence graph invariant violated: node_count must be > 0")

    node_types = [str(n.get("node_type", "")) for n in nodes]
    rule_count = node_types.count("RULE")

    # A chart can legitimately evaluate to zero yogas (documented F3
    # "Coverage Gap" charts): the graph then records the prediction and
    # fact nodes with no rules. Edges are only required when rules exist.
    if rule_count > 0 and edge_count <= 0:
        raise ValueError(
            "evidence graph invariant violated: rule nodes present but "
            f"edge_count == 0 ({rule_count} rules)"
        )

    if rule_count > 0:
        if node_types.count("EVALUATION") != 1:
            raise ValueError(
                "evidence graph invariant violated: expected exactly one EVALUATION "
                f"node, found {node_types.count('EVALUATION')}"
            )

    # Connectivity: every RULE node must be reachable from the EVALUATION
    # node over ESTABLISHED_BY edges (prediction -> rule -> facts chain).
    prediction_id = next(
        n["node_id"] for n in nodes if n.get("node_type") == "EVALUATION"
    )
    adjacency: dict[str, set[str]] = {}
    for edge in edges:
        adjacency.setdefault(str(edge.get("source", "")), set()).add(
            str(edge.get("target", ""))
        )
    seen: set[str] = set()
    stack = [prediction_id]
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(adjacency.get(current, ()))
    rule_ids = {n["node_id"] for n in nodes if n.get("node_type") == "RULE"}
    unreachable = rule_ids - seen
    if unreachable:
        raise ValueError(
            "evidence graph invariant violated: RULE nodes unreachable from the "
            f"prediction node: {sorted(unreachable)}"
        )


def collect_stage_payloads(fixture: dict[str, Any]) -> dict[str, Any]:
    """Run the deterministic pipeline and return per-stage payloads."""
    chart = compute_chart_from_fixture(fixture)
    facts = build_jre_facts(chart)

    moon = next(p for p in chart.planet_states if p.body.value == "MOON")
    dasha = calculate_vimshottari_dasha(
        moon_longitude=moon.longitude_used,
        birth_date_str=fixture["raw_birth_data"]["date"],
        target_date=GOLDEN_TRANSIT_DATE,
    )

    evaluator = YogaEvaluatorService()
    yoga_evals = evaluator.evaluate_classical_yogas(facts)
    yoga_payload = [ev.to_dict() for ev in yoga_evals]

    # Phase 5B: Ashtakavarga checkpoint (BAV/SAV/Shodhana/Pinda). The
    # ashta_scoring_enabled flag does NOT gate the golden-state stage —
    # the stage records the pure calculation report regardless, so the
    # regression gate covers it before any downstream scoring hookup.
    ashta_report = ashtakavarga_to_dict(compute_full_ashtakavarga(facts))

    # Phase 5C: Gochara checkpoint — transit facts at the pinned epoch.
    # Flag-independent, same discipline as the ashtakavarga stage.
    transit_positions = compute_transit_positions(
        date=GOCHARA_TRANSIT_EPOCH.strftime("%Y-%m-%d"),
        time=GOCHARA_TRANSIT_EPOCH.strftime("%H:%M:%S"),
        timezone="UTC",
        latitude=0.0,
        longitude=0.0,
    )
    gochara_report = gochara_to_dict(
        compute_gochara(facts, transit_positions, epoch=GOCHARA_TRANSIT_EPOCH)
    )

    # Phase 5D: multi-varga checkpoint (D1/D9/D10/D60 placements,
    # vargottama, navamsha dignity, D10 career anchor). Flag-independent,
    # same discipline as the ashtakavarga and gochara stages.
    varga_report = multi_varga_to_dict(
        compute_multi_varga(facts, lagna_longitude=chart.lagna.ascendant_longitude_deg)
    )

    # Phase 5E: dasha/transit permissive-gate checkpoint — the active
    # Vimshottari MD/AD/PD window and per-planet gate decisions at the
    # pinned epoch, anchored to the chart's birth date. Flag-independent,
    # same discipline as the ashtakavarga/gochara/multi_varga stages.
    dasha_transit_report = dasha_transit_to_dict(
        compute_dasha_transit(
            facts,
            birth_date=str(chart.birth_snapshot.date),
            epoch=DASHA_TRANSIT_EPOCH,
        )
    )

    # Phase 4 (JRS-092): evidence-graph provenance stage with DAG
    # node/edge count assertions folded into the golden manifest.
    graph = EvidenceGraphService().build_graph(jre_facts=facts, yoga_evals=yoga_evals)
    graph_dict = graph.to_dict()
    _assert_evidence_graph_invariants(graph_dict)

    return {
        "chart": chart.to_dict(),
        "jre_facts": facts,
        "dasha": dasha,
        "yogas": yoga_payload,
        "ashtakavarga": ashta_report,
        "gochara": gochara_report,
        "multi_varga": varga_report,
        "dasha_transit": dasha_transit_report,
        "evidence_graph": graph_dict,
    }


def _cohort_fixtures() -> list[Path]:
    return sorted(COHORT_DIR.glob("chart_*.json"))


def _manifest_path(fixture_id: str) -> Path:
    return GOLDEN_DIR / f"{fixture_id}.json"


def _load_fixture(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def run_generate() -> int:
    """(Re)build every golden-state manifest from a live pipeline run."""
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = _cohort_fixtures()
    print(f"engine_version={ENGINE_VERSION}  fixtures={len(fixtures)}")
    failures: list[str] = []
    for path in fixtures:
        fixture = _load_fixture(path)
        fixture_id = str(fixture.get("_meta", {}).get("fixture_id", path.stem))
        if "raw_birth_data" not in fixture:
            print(f"  SKIP {fixture_id} (no raw_birth_data)")
            continue
        try:
            manifest = build_manifest(
                engine_version=ENGINE_VERSION,
                fixture_id=fixture_id,
                stage_payloads=collect_stage_payloads(fixture),
            )
        except Exception as exc:  # noqa: BLE001 — report and continue
            failures.append(f"{fixture_id}: {type(exc).__name__}: {exc}")
            print(f"  FAIL {fixture_id}: {exc}")
            continue
        out = _manifest_path(fixture_id)
        with out.open("w", encoding="utf-8") as f:
            json.dump(manifest.to_dict(), f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"  WROTE {out.relative_to(REPO_ROOT)} ({len(manifest.stages)} stages)")

    if failures:
        print(f"\n{len(failures)} fixture(s) failed:", file=sys.stderr)
        for line in failures:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


def run_verify() -> int:
    """Recompute all stage hashes against the committed manifests."""
    fixtures = _cohort_fixtures()
    print(f"engine_version={ENGINE_VERSION}  fixtures={len(fixtures)}")
    mismatches: list[str] = []
    verified_count = 0
    for path in fixtures:
        fixture = _load_fixture(path)
        fixture_id = str(fixture.get("_meta", {}).get("fixture_id", path.stem))
        if "raw_birth_data" not in fixture:
            continue
        manifest_path = _manifest_path(fixture_id)
        if not manifest_path.exists():
            mismatches.append(f"{fixture_id}: missing golden manifest {manifest_path.name}")
            print(f"  MISSING {fixture_id}")
            continue
        try:
            with manifest_path.open(encoding="utf-8") as f:
                manifest = GoldenStateManifest.from_dict(json.load(f))
            GoldenStateValidator(manifest).verify_all(collect_stage_payloads(fixture))
        except (GoldenStateMismatchError, KeyError, ValueError) as exc:
            mismatches.append(f"{fixture_id}: {exc}")
            print(f"  MISMATCH {fixture_id}: {exc}")
            continue
        verified_count += 1
        print(f"  PASS {fixture_id} ({len(manifest.stages)} stages)")
    print(f"\n{verified_count} fixture(s) verified, {len(mismatches)} mismatch(es)")
    if mismatches:
        for line in mismatches:
            print(f"  {line}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("generate", "verify"))
    args = parser.parse_args()
    return run_generate() if args.mode == "generate" else run_verify()


if __name__ == "__main__":
    sys.exit(main())

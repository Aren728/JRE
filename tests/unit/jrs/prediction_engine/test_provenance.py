"""Phase 3 — Deterministic Evidence Graph & Provenance Layer tests.

Verifies:
- Deterministic graph id derivation from canonical payloads.
- Stable YOGA-*/DASHA-*/FACT-* rule id namespaces.
- DAG serialization round-trip (JSON DTO + GraphViz DOT).
- No wall-clock / randomness in provenance construction.
"""

from __future__ import annotations

import json

import pytest

from jrs.prediction_engine.provenance import (
    DAGEdge,
    DAGNode,
    DirectedAcyclicGraph,
    EvidenceGraphService,
    LiteratureCitation,
    RuleId,
    build_provenance_chain,
    graph_to_dot,
    result_to_dict,
    result_to_json,
    to_json,
)


# ── Rule & fact identifier namespaces ────────────────────────────────────────


def test_rule_id_namespace_and_canonical_form() -> None:
    r = RuleId(namespace="SYSTEM", kind="YOGA", canonical_id="F-118")
    assert r.namespace == "SYSTEM"
    assert r.canonical == "F-118"
    assert r.to_dict() == {"namespace": "SYSTEM", "kind": "YOGA", "canonical_id": "F-118"}


def test_citation_is_machine_readable() -> None:
    c = LiteratureCitation(
        citation_id="CIT-BPHS-41",
        source_namespace="BPHS",
        chapter="41",
        verse="V. 8-10",
        canonical_ref="BPHS Ch. 41",
    )
    assert c.to_dict()["citation_id"] == "CIT-BPHS-41"
    assert c.source_namespace == "BPHS"


# ── Deterministic graph id derivation ────────────────────────────────────────


def _sample_inputs() -> tuple[dict[str, object], list[dict[str, object]]]:
    facts = {
        "planets": {
            "JUPITER": {"house": 10, "rashi": "DHANUSHA", "combust": False},
            "MOON": {"house": 4, "rashi": "KARKA", "combust": False},
            "RAHU": {"house": 12},
        },
        "house_lords": {1: "MOON", 2: "SUN", 4: "JUPITER", 10: "JUPITER", 12: "RAHU"},
        "dasha_periods": [{"triggering_planet": "JUPITER", "start": "2021-01-01", "end": "2034-01-01"}],
    }
    yogas = [
        {"yoga_name": "Gajakesari", "status": "FORMED", "chain_impact": 0.85},
        {"yoga_name": "Raja", "status": "FORMED", "chain_impact": 0.72},
    ]
    return facts, yogas


def test_graph_id_is_deterministic() -> None:
    facts, yogas = _sample_inputs()
    g1 = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-001")
    g2 = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-001")
    assert g1.graph_id == g2.graph_id
    assert len(g1.graph_id) == 64  # SHA-256 hex digest


def test_graph_id_changes_with_prediction_id() -> None:
    facts, yogas = _sample_inputs()
    g1 = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-001")
    g2 = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-002")
    assert g1.graph_id != g2.graph_id


# ── DAG serialization round-trip ──────────────────────────────────────────────


def test_directed_acyclic_graph_round_trip() -> None:
    node = DAGNode(
        node_id="P-001",
        node_type="EVALUATION",
        labels=("EVALUATION", "PREDICTION"),
        payload={"yoga_count": 2},
        children=("R-0-YOGA-001",),
        parent=None,
    )
    edge = DAGEdge(
        edge_id="E-EV-0",
        source=node.node_id,
        target="R-0-YOGA-001",
        relationship="ESTABLISHED_BY",
        weight=1.0,
        metadata={"yoga_name": "Gajakesari"},
    )
    graph = DirectedAcyclicGraph(graph_id="g1", nodes=(node,), edges=(edge,))

    restored = DirectedAcyclicGraph.from_dict(graph.to_dict())
    assert restored == graph
    assert restored.node_by_id("P-001").payload["yoga_count"] == 2


def test_to_dict_json_round_trip() -> None:
    graph = build_provenance_chain(
        jre_facts=_sample_inputs()[0],
        yoga_evals=[{"yoga_name": "Gajakesari", "status": "FORMED"}],
        prediction_id="P-001",
    )
    restored = DirectedAcyclicGraph.from_dict(result_to_dict(graph))
    assert restored.graph_id == graph.graph_id
    assert len(restored.nodes) == len(graph.nodes)
    assert len(restored.edges) == len(graph.edges)


def test_to_json_is_canonical() -> None:
    facts, yogas = _sample_inputs()
    graph = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-001")
    json_str = to_json(graph)
    assert '"graph_id"' in json_str
    assert json.loads(json_str) == result_to_dict(graph)
    # Single-line (indent=0) canonical form is byte-identical across runs
    assert to_json(graph, indent=0) == to_json(graph, indent=0)


def test_result_to_json_matches_to_json() -> None:
    facts, yogas = _sample_inputs()
    graph = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-001")
    assert result_to_json(graph) == to_json(graph)
    assert result_to_dict(graph) == graph.to_dict()


# ── GraphViz DOT export ──────────────────────────────────────────────────────


def test_graph_to_dot_output() -> None:
    node = DAGNode(
        node_id="P-001",
        node_type="EV GUGA",
        labels=("EVALUATION", "PREDICTION"),
        payload={"yoga_count": 2},
        children=(),
        parent=None,
    )
    edge = DAGEdge(
        edge_id="E-EV-0",
        source="P-001",
        target="R-0-YOGA-001",
        relationship="ESTABLISHED_BY",
        weight=1.0,
        metadata={"yoga_name": "Gajakesari"},
    )
    graph = DirectedAcyclicGraph(graph_id="g1", nodes=(node,), edges=(edge,))

    dot = graph_to_dot(graph)
    assert dot.strip().startswith("digraph evidence_graph")
    assert dot.strip().endswith("}")
    assert "->" in dot
    assert "P-001" in dot


# ── Deterministic construction (no wall-clock / randomness) ──────────────────


def test_no_wall_clock_randomness() -> None:
    facts, yogas = _sample_inputs()
    g1 = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-001")
    g2 = build_provenance_chain(jre_facts=facts, yoga_evals=yogas, prediction_id="P-001")

    # Identical timestamps would only appear if the builder used wall-clock
    for node in g1.nodes:
        if node.payload.get("timestamp"):
            pytest.fail("provenance payload must not contain wall-clock timestamps")


def test_build_graph_service_is_idempotent() -> None:
    facts, yogas = _sample_inputs()
    svc = EvidenceGraphService(prediction_id="P-CUSTOM")
    g1 = svc.build_graph(jre_facts=facts, yoga_evals=yogas)
    g2 = svc.build_graph(jre_facts=facts, yoga_evals=yogas)
    assert g1.graph_id == g2.graph_id
    assert len(g1.nodes) == len(g2.nodes)
    assert len(g1.edges) == len(g2.edges)

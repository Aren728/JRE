"""Phase 8: Provenance exporter — diagnostic JSON + GraphML.

Full-provenance export of a :class:`DirectedAcyclicGraph` (the same
deterministic evidence DAG the golden-state ``evidence_graph`` stage
covers) into two audit formats:

- **Diagnostic JSON** — canonical, versioned, round-trip-ready payload
  with node/edge counts and layer summaries; serialized with the same
  float canonicalization the golden-state contract uses.
- **GraphML** — the standard graph-exchange XML consumed by Gephi,
  yEd, Cytoscape, and NetworkX. Node/edge ids are XML-attribute safe
  (provenance ids are alphanumeric + ``-_`` by construction) and the
  payload is carried as canonical JSON text on each element.

Both exports are pure functions of the graph: no wall-clock stamps, no
I/O — byte-identical inputs yield byte-identical outputs.
"""

from __future__ import annotations

import json
from typing import Any
from xml.sax.saxutils import escape, quoteattr

from jrs.prediction_engine.provenance import DirectedAcyclicGraph
from jrs.validation.golden_state import _canonicalize_floats

__all__ = [
    "EXPORT_SCHEMA_VERSION",
    "GRAPHML_SCHEMA_VERSION",
    "provenance_to_diagnostic_json",
    "provenance_to_graphml",
]

#: Version of the diagnostic-JSON export payload (bump on shape change).
EXPORT_SCHEMA_VERSION = "1.0.0"

#: Version of the GraphML export payload.
GRAPHML_SCHEMA_VERSION = "1.0.0"

#: Ordered layer taxonomy used for the layer summary (unknown types are
#: appended alphabetically, keeping output deterministic).
_KNOWN_NODE_TYPES: tuple[str, ...] = (
    "ANALYSIS",
    "CITATION",
    "EVALUATION",
    "FACT",
    "RULE",
    "TEMPORAL",
)

#: GraphML keys declared in the <key> block.
_GRAPHML_NODE_KEYS: tuple[tuple[str, str, str], ...] = (
    # (attr.name, attr.type, description)
    ("node_type", "string", "Layer: EVALUATION/RULE/FACT/CITATION/TEMPORAL/ANALYSIS"),
    ("labels", "string", "Comma-separated classification labels"),
    ("payload", "string", "Canonical JSON of the node payload"),
)
_GRAPHML_EDGE_KEYS: tuple[tuple[str, str, str], ...] = (
    ("relationship", "string", "Directed relationship type"),
    ("weight", "double", "Edge weight"),
    ("metadata", "string", "Canonical JSON of the edge metadata"),
)


def _layer_summary(nodes: list[dict[str, Any]]) -> dict[str, int]:
    """Deterministic per-layer node counts."""
    counts: dict[str, int] = {}
    for node in nodes:
        counts[node["node_type"]] = counts.get(node["node_type"], 0) + 1
    ordered = {t: counts[t] for t in _KNOWN_NODE_TYPES if t in counts}
    for extra in sorted(set(counts) - set(_KNOWN_NODE_TYPES)):
        ordered[extra] = counts[extra]
    return ordered


def provenance_to_diagnostic_json(
    graph: DirectedAcyclicGraph,
    fixture_id: str = "",
) -> dict[str, Any]:
    """Export the evidence DAG as a canonical diagnostic-JSON payload.

    The payload is round-trip-ready (it embeds the standard
    ``graph.to_dict()`` form) and adds audit metadata: layer summary,
    relationship histogram, and connectivity invariants. Floats are
    canonicalized to 6 decimals exactly like the golden-state contract,
    so the export participates in the same byte-stability discipline.
    """
    graph_payload = _canonicalize_floats(graph.to_dict())
    nodes: list[dict[str, Any]] = graph_payload["nodes"]
    edges: list[dict[str, Any]] = graph_payload["edges"]

    relationship_counts: dict[str, int] = {}
    for edge in edges:
        relationship_counts[edge["relationship"]] = (
            relationship_counts.get(edge["relationship"], 0) + 1
        )

    node_ids = {n["node_id"] for n in nodes}
    dangling = sorted(
        edge["edge_id"]
        for edge in edges
        if edge["source"] not in node_ids or edge["target"] not in node_ids
    )

    return {
        "schema_version": EXPORT_SCHEMA_VERSION,
        "graph_id": graph.graph_id,
        "fixture_id": fixture_id,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "layer_summary": _layer_summary(nodes),
        "relationship_histogram": dict(sorted(relationship_counts.items())),
        "invariants": {
            "dangling_edges": dangling,
            "acyclic_consistent": bool(dangling) is False,
        },
        "graph": graph_payload,
    }


def provenance_to_graphml(
    graph: DirectedAcyclicGraph,
    fixture_id: str = "",
) -> str:
    """Export the evidence DAG as GraphML 1.1 XML text.

    Node payloads and edge metadata ride as canonical-JSON strings on
    ``<data>`` elements declared by the <key> block, so the full
    provenance survives the round trip into graph tooling. Output is
    deterministic: nodes and edges are emitted in their canonical
    (already-sorted) graph order.
    """
    payload = _canonicalize_floats(graph.to_dict())
    nodes: list[dict[str, Any]] = payload["nodes"]
    edges: list[dict[str, Any]] = payload["edges"]

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns'
        ' http://graphml.graphdrawing.org/xmlns/1.1/graphml.xsd">'
    )
    lines.append(
        f'  <key id="graphml:d" for="graph" attr.name="description"'
        f' attr.type="string">{escape("")}</key>'
    )
    for name, key_type, desc in _GRAPHML_NODE_KEYS:
        lines.append(
            f'  <key id="{name}" for="node" attr.name="{name}"'
            f' attr.type="{key_type}">{escape(desc)}</key>'
        )
    for name, key_type, desc in _GRAPHML_EDGE_KEYS:
        lines.append(
            f'  <key id="{name}" for="edge" attr.name="{name}"'
            f' attr.type="{key_type}">{escape(desc)}</key>'
        )
    lines.append('  <graph id=' + quoteattr(graph.graph_id) + ' edgedefault="directed">')
    desc = f"JRE evidence graph for {fixture_id}" if fixture_id else "JRE evidence graph"
    lines.append(f'    <data key="graphml:d">{escape(desc)}</data>')

    for node in nodes:
        lines.append(f'    <node id={quoteattr(node["node_id"])}>')
        lines.append(f'      <data key="node_type">{escape(node["node_type"])}</data>')
        labels = ",".join(node.get("labels") or [])
        lines.append(f'      <data key="labels">{escape(labels)}</data>')
        lines.append(
            f'      <data key="payload">'
            f'{escape(json.dumps(node.get("payload") or {}, sort_keys=True))}</data>'
        )
        lines.append("    </node>")

    for edge in edges:
        lines.append(
            f'    <edge id={quoteattr(edge["edge_id"])}'
            f' source={quoteattr(edge["source"])}'
            f' target={quoteattr(edge["target"])}>'
        )
        lines.append(
            f'      <data key="relationship">{escape(edge["relationship"])}</data>'
        )
        lines.append(f'      <data key="weight">{float(edge.get("weight", 1.0))}</data>')
        lines.append(
            f'      <data key="metadata">'
            f'{escape(json.dumps(edge.get("metadata") or {}, sort_keys=True))}</data>'
        )
        lines.append("    </edge>")

    lines.append("  </graph>")
    lines.append("</graphml>")
    lines.append("")
    return "\n".join(lines)

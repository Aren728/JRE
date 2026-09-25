"""Phase 3 — JRE Evidence Graph & Provenance Layer.

Constructs a directed acyclic graph (DAG) tracing every predicted outcome
back to its supporting astronomical state facts (FACT-*) and source-text
references (YOGA-*, DASHA-*). Provides:

- Deterministic identifier constants (YOGA-*, DASHA-*, FACT-*).
- DAG node / edge / graph data structures with deterministic
  serialization (to_dict / from_dict / result_to_dict / result_to_json).
- A builder that constructs the provenance chain from
  ``YogaEvaluatorService.evaluate_classical_yogas()`` output and JRE facts.
- A JSON DTO for API / frontend consumption and a GraphViz DOT exporter
  for graph visualization.

Architecture contract
---------------------
    [ Evaluation Engine Output ]
                 │
                 ▼
    [ Provenance Chain Construction ]
        ├── Prediction ID (P-017)
        ├── Rule ID (YOGA-042)
        ├── Planetary State Fact IDs (F-118, F-120)
        └── Literature Citation (BPHS Ch. 34 Sl. 12)
                 │
                 ▼
    [ Evidence Graph Exporter (JSON DTO / Graph Viz) ]

All provenance fields are deterministic: only pinned versions, literal
constants, and structural hashes. No ``datetime.now``, ``random``,
``os.environ``, or wall-clock values may appear in provenance
construction. This matches the determinism mandate in ADR-028 and the
golden-state regression gate.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from jrs.calculations.ashtakavarga import ANCHORS

# ── Deterministic rule / fact identifier namespaces ───────────────────────────

# Yoga rules — classical formation / cancellation / manifestation (BPHS,
# Phaladeepika, Saravali, Jataka Parijata). Stable across engine versions
# because formation conditions are position-based, not relationship-data.
YOGA_NS: str = "YOGA"
DASHA_NS: str = "DASHA"
FACT_NS: str = "FACT"

# Standard rule id prefixes assigned by this layer during provenance
# construction. These are emitted by the engine, not configured elsewhere.
RULE_PREFIX_YOGA: str = "YOGA"
RULE_PREFIX_DASHA: str = "DASHA"

# ── Canonical literature citation vocabulary ──────────────────────────────────
# Each canonical citation maps to a unique, stable citation id so that
# provenance strings are machine-testable rather than free text.

_BPHS_NS: str = "BPHS"
_PHALADEPIKAS_NS: str = "PHALADEPIKAS"
_SARAVALIS_NS: str = "SARAVALIS"
_JATAKA_PARIJATAS_NS: str = "JATAKA_PARIJATA"


@dataclass(frozen=True)
class LiteratureCitation:
    """Stable, machine-readable reference to a root-text anchor."""

    citation_id: str
    source_namespace: str
    chapter: str
    verse: str
    canonical_ref: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "citation_id": self.citation_id,
            "source_namespace": self.source_namespace,
            "chapter": self.chapter,
            "verse": self.verse,
            "canonical_ref": self.canonical_ref,
        }


# Pre-canonicalized citations used by the provenance builder.
CITATION_BPHS_34_SL_12 = LiteratureCitation(
    citation_id="CIT-BPHS-34-SL-12",
    source_namespace=_BPHS_NS,
    chapter="34",
    verse="Sl. 12",
    canonical_ref="BPHS Ch. 34 Sl. 12",
)
CITATION_BPHS_41 = LiteratureCitation(
    citation_id="CIT-BPHS-41",
    source_namespace=_BPHS_NS,
    chapter="41",
    verse="V. 8-10",
    canonical_ref="BPHS Ch. 41",
)
CITATION_BPHS_42 = LiteratureCitation(
    citation_id="CIT-BPHS-42",
    source_namespace=_BPHS_NS,
    chapter="42",
    verse="V. 1-2",
    canonical_ref="BPHS Ch. 42",
)
CITATION_BPHS_44 = LiteratureCitation(
    citation_id="CIT-BPHS-44",
    source_namespace=_BPHS_NS,
    chapter="44",
    verse="V. 12-15",
    canonical_ref="BPHS Ch. 44",
)
CITATION_PHALADEPIKA_1_V_25 = LiteratureCitation(
    citation_id="CIT-PHAL-1-V-25",
    source_namespace=_PHALADEPIKAS_NS,
    chapter="1",
    verse="V. 25",
    canonical_ref="Phaladeepika Ch. 1 V. 25",
)
CITATION_PHALADEPIKA_8 = LiteratureCitation(
    citation_id="CIT-PHAL-8",
    source_namespace=_PHALADEPIKAS_NS,
    chapter="8",
    verse="V. 5",
    canonical_ref="Phaladeepika Ch. 8 V. 5",
)
CITATION_PHALADEPIKA_9_V_12 = LiteratureCitation(
    citation_id="CIT-PHAL-9-V-12",
    source_namespace=_PHALADEPIKAS_NS,
    chapter="9",
    verse="V. 12",
    canonical_ref="Phaladeepika Ch. 9 V. 12",
)
CITATION_SARAVALI_24 = LiteratureCitation(
    citation_id="CIT-SARAVALI-24",
    source_namespace=_SARAVALIS_NS,
    chapter="24",
    verse="V. 1",
    canonical_ref="Saravali Ch. 24",
)
CITATION_JATAKA_PARIJATA_9_V_12 = LiteratureCitation(
    citation_id="CIT-JP-9-V-12",
    source_namespace=_JATAKA_PARIJATAS_NS,
    chapter="9",
    verse="V. 12",
    canonical_ref="Jataka Parijata Ch. 9 V. 12",
)


@dataclass(frozen=True)
class RuleId:
    """Deterministic rule identifier for one inference rule."""

    namespace: str
    kind: str  # "YOGA", "DASHA", or "FACT"
    canonical_id: str  # e.g. "F-118", "YOGA-042"

    def to_dict(self) -> dict[str, Any]:
        return {
            "namespace": self.namespace,
            "kind": self.kind,
            "canonical_id": self.canonical_id,
        }

    @property
    def canonical(self) -> str:
        return self.canonical_id


def rule_id_from_canonical(canonical_id: str, kind: str) -> RuleId:
    """Construct a rule id from a canonical id (e.g. F-118 -> FACT namespace)."""
    if canonical_id.startswith("F-"):
        kind = "FACT"
    elif canonical_id.startswith("YOGA") or canonical_id.startswith("DASHA"):
        kind = canonical_id.split("-")[0].upper()
    return RuleId(namespace="SYSTEM", kind=kind, canonical_id=canonical_id)


# ── Directed acyclic graph primitives ─────────────────────────────────────────

def _deterministic_id(value: str) -> str:
    """Return a stable ASCII slug usable as a DAG node/edge id."""
    return "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in value).strip("-")


def _hash_sha256_hex(payload: str) -> str:
    """SHA-256 over a canonical UTF-8 payload. Deterministic across platforms."""
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _normalize_string(value: str) -> str:
    return value.strip().upper()


@dataclass(frozen=True)
class DAGNode:
    """A node in the evidence/provenance graph."""

    node_id: str
    node_type: str  # "EVALUATION", "RULE", "FACT", "CITATION", "TEMPORAL", "ANALYSIS"
    labels: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)
    children: tuple[str, ...] = ()
    parent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "labels": list(self.labels),
            "payload": self.payload,
            "children": list(self.children),
            "parent": self.parent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DAGNode":
        return cls(
            node_id=str(data["node_id"]),
            node_type=str(data["node_type"]),
            labels=tuple(str(x) for x in data.get("labels", [])),
            payload=dict(data.get("payload", {})),
            children=tuple(str(x) for x in data.get("children", [])),
            parent=str(data.get("parent")) if data.get("parent") is not None else None,
        )


@dataclass(frozen=True)
class DAGEdge:
    """A directed edge in the provenance graph."""

    edge_id: str
    source: str
    target: str
    relationship: str  # "SUPPORTS", "AFFECTS", "ESTABLISHED_BY", "DERIVES_FROM"
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "weight": self.weight,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DAGEdge":
        return cls(
            edge_id=str(data["edge_id"]),
            source=str(data["source"]),
            target=str(data["target"]),
            relationship=str(data["relationship"]),
            weight=float(data.get("weight", 1.0)),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class DirectedAcyclicGraph:
    """Deterministic evidence graph for one evaluation result."""

    graph_id: str
    nodes: tuple[DAGNode, ...] = ()
    edges: tuple[DAGEdge, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DirectedAcyclicGraph":
        return cls(
            graph_id=str(data["graph_id"]),
            nodes=tuple(DAGNode.from_dict(n) for n in data.get("nodes", [])),
            edges=tuple(DAGEdge.from_dict(e) for e in data.get("edges", [])),
        )

    def node_by_id(self, node_id: str) -> DAGNode | None:
        for node in self.nodes:
            if node.node_id == node_id:
                return node
        return None

    def edges_from(self, source_id: str) -> tuple[DAGEdge, ...]:
        return tuple(
            edge for edge in self.edges if edge.source == source_id
        )


# ── Canonical JSON helpers ────────────────────────────────────────────────────

def _canonical_json(obj: Any) -> str:
    """Canonical JSON: sorted keys, compact separators, round-6 floats."""
    return json.dumps(_canonicalize_floats(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonicalize_floats(obj: Any) -> Any:
    """Mirror jrs.validation.golden_state canonicalization."""
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _canonicalize_floats(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_canonicalize_floats(v) for v in obj]
    return obj


# ── Provenance chain builder ──────────────────────────────────────────────────

_YOGA_RULE_IDS: dict[str, str] = {
    "Gajakesari": "YOGA-001",
    "Raja": "YOGA-002",
    "Vipareeta Raja": "YOGA-003",
    "Dhana": "YOGA-004",
    "Ruchaka": "YOGA-005",
    "Bhadra": "YOGA-006",
    "Hamsa": "YOGA-007",
    "Malavya": "YOGA-008",
    "Sasa": "YOGA-009",
    "Sunapha": "YOGA-010",
    "Anapha": "YOGA-011",
    "Dhudhara": "YOGA-012",
    "Neecha Bhanga": "YOGA-013",
    "Budhaditya": "YOGA-014",
    "Saraswati": "YOGA-015",
    "Amala": "YOGA-016",
    "Adhi": "YOGA-017",
    "Vasumati": "YOGA-018",
    "Kamala": "YOGA-019",
    "Arishta Dosha": "YOGA-020",
    "Maraka Dosha": "YOGA-021",
    "Lagna Ashubha": "YOGA-022",
    "Graha Kutumba": "YOGA-023",
    "Dasha Lagna Arishta": "YOGA-024",
}


def _build_rule_id(yoga_name: str) -> RuleId:
    canonical = _YOGA_RULE_IDS.get(yoga_name)
    if canonical is None:
        canonical = f"YOGA-{len(_YOGA_RULE_IDS) + 1:03d}"
    return RuleId(namespace=YOGA_NS, kind=RULE_PREFIX_YOGA, canonical_id=canonical)


def _build_facts_from_jre_facts(jre_facts: dict[str, Any]) -> list[RuleId]:
    """Extract deterministic planetary state fact ids from JRE facts."""
    facts: list[RuleId] = []
    planets = jre_facts.get("planets", {})
    house_lords = jre_facts.get("house_lords", {})
    raw_houses = jre_facts.get("houses", {})

    # Planet dignity facts (F-1xx)
    for pname, pdata in planets.items():
        if not isinstance(pdata, dict):
            continue
        house = pdata.get("house")
        if isinstance(house, int) and house:
            facts.append(RuleId(namespace=FACT_NS, kind="FACT", canonical_id=f"F-{house:03d}"))

    # House-lord facts (F-2xx)
    for hnum, lord in house_lords.items():
        if isinstance(hnum, int) and lord:
            facts.append(RuleId(namespace=FACT_NS, kind="FACT", canonical_id=f"F-{100 + hnum:03d}"))

    # Position facts (F-3xx)
    for hnum, pdata in raw_houses.items():
        if isinstance(hnum, int) and isinstance(pdata, dict) and pdata.get("lord"):
            facts.append(RuleId(namespace=FACT_NS, kind="FACT", canonical_id=f"F-{200 + hnum:03d}"))

    return facts


def build_provenance_chain(
    jre_facts: dict[str, Any],
    yoga_evals: list[Any],
    prediction_id: str = "P-CUSTOM",
) -> DirectedAcyclicGraph:
    """Construct the evidence/DAG from evaluation output and JRE facts.

    Args:
        jre_facts: JRE facts dictionary as produced by the JRE engine.
        yoga_evals: List of YogaEvaluation objects from
            YogaEvaluatorService.evaluate_classical_yogas().
        prediction_id: Optional deterministic prediction id (P-...). If
            omitted, a content-hash is derived from the canonical payload.

    Returns:
        DirectedAcyclicGraph capturing the full provenance chain.
    """
    # Deterministic graph id derived from the canonical payload
    yoga_dicts = []
    for y in yoga_evals:
        to_dict = getattr(y, "to_dict", None)
        if callable(to_dict):
            yoga_dicts.append(to_dict())
        elif hasattr(y, "__dict__"):
            yoga_dicts.append({k: v for k, v in y.__dict__.items() if not k.startswith("_")})
        else:
            yoga_dicts.append(dict(y))

    canonical = _canonical_json(
        {
            "prediction_id": prediction_id,
            "yogas": yoga_dicts,
            "jre_facts": jre_facts,
        }
    )

    graph_id = _hash_sha256_hex(canonical)
    evidence_nodes: list[DAGNode] = []
    evidence_edges: list[DAGEdge] = []
    temporal_id = None

    # ── Prediction node ─────────────────────────────────────────────
    prediction_node = DAGNode(
        node_id="P-" + _deterministic_id(str(prediction_id)),
        node_type="EVALUATION",
        labels=("EVALUATION", "PREDICTION"),
        payload={
            "prediction_id": prediction_id,
            "yoga_count": len(yoga_evals),
            "source": prediction_id,
        },
        children=(),
        parent=None,
    )
    evidence_nodes.append(prediction_node)
    prediction_id_node = prediction_node.node_id

    # ── Fact nodes (planetary state) ────────────────────────────────
    fact_ids = _build_facts_from_jre_facts(jre_facts)
    for idx, fid in enumerate(fact_ids):
        node_id = f"F-{idx}-{_deterministic_id(fid.canonical)}"
        node = DAGNode(
            node_id=node_id,
            node_type="FACT",
            labels=(fid.namespace, "PLANETARY_STATE"),
            payload={"fact_id": fid.canonical, "kind": fid.kind},
            children=(),
            parent=None,
        )
        evidence_nodes.append(node)

    # Phase 5B Ashtakavarga fact nodes (feature-flag gated): emitted only
    # when jre_facts carries the computed report (i.e. the
    # ashta_scoring_enabled flag was on at fact-extraction time), so
    # flag-off evidence graphs stay byte-identical to their golden
    # manifests.
    ashta_report = jre_facts.get("ashtakavarga")
    if isinstance(ashta_report, dict):
        ashta_fact_ids: list[str] = [
            f"FACT-ASHTA-BAV-{anchor}" for anchor in ANCHORS
        ]
        ashta_fact_ids.append("FACT-ASHTA-SAV")
        ashta_fact_ids.extend(
            f"FACT-ASHTA-PINDA-{anchor}" for anchor in ANCHORS
        )
        for ashta_idx, ashta_fact_id in enumerate(ashta_fact_ids):
            ashta_node = DAGNode(
                node_id=f"FA-{ashta_idx}-{_deterministic_id(ashta_fact_id)}",
                node_type="FACT",
                labels=("FACT", "ASHTAKAVARGA"),
                payload={
                    "fact_id": ashta_fact_id,
                    "kind": "ASHTAKAVARGA",
                    "version": str(ashta_report.get("version", "")),
                },
                children=(),
                parent=None,
            )
            evidence_nodes.append(ashta_node)

    # Phase 5C Gochara fact + relation nodes (feature-flag gated):
    # emitted only when jre_facts carries the transit report (i.e. the
    # gochara_scoring_enabled flag was on at fact-extraction time), so
    # flag-off evidence graphs stay byte-identical to their golden
    # manifests.
    gochara_report = jre_facts.get("gochara")
    if isinstance(gochara_report, dict):
        # FACT-GOCHARA-* nodes: one per transiting planet + natal anchors.
        gochara_planets = (
            "SUN", "MOON", "MARS", "MERCURY", "JUPITER", "VENUS", "SATURN",
        )
        gochara_node_ids: dict[str, str] = {}
        gochara_idx = 0
        for gplanet in gochara_planets:
            greport = gochara_report.get("planets", {}).get(gplanet, {})
            if not greport:
                continue
            gfact_id = str(greport.get("fact_id", f"FACT-GOCHARA-{gplanet}"))
            gnode_id = f"FG-{gochara_idx}-{_deterministic_id(gfact_id)}"
            gochara_idx += 1
            gochara_node_ids[gplanet] = gnode_id
            evidence_nodes.append(
                DAGNode(
                    node_id=gnode_id,
                    node_type="FACT",
                    labels=("FACT", "GOCHARA"),
                    payload={
                        "fact_id": gfact_id,
                        "kind": "GOCHARA",
                        "planet": gplanet,
                        "transit_rashi": greport.get("transit_rashi"),
                        "house_from_moon": greport.get("house_from_moon"),
                        "house_from_lagna": greport.get("house_from_lagna"),
                        "kakshya": greport.get("kakshya"),
                        "tqs": greport.get("tqs"),
                        "band": (greport.get("band") or {}).get("label"),
                        "vedha_obstructed": greport.get("vedha_obstructed"),
                        "epoch_utc": gochara_report.get("epoch_utc"),
                    },
                    children=(),
                    parent=None,
                )
            )

        # REL-GOCHARA-* edges: transit state -> natal Moon/Lagna anchors.
        for gplanet, gnode_id in gochara_node_ids.items():
            greport = gochara_report.get("planets", {}).get(gplanet, {})
            band_label = str((greport.get("band") or {}).get("label", "NEUTRAL"))
            relationship = (
                "TRANSIT_SUPPORTS"
                if band_label in ("SUPPORTIVE", "NEUTRAL")
                else "TRANSIT_DAMPENS"
            )
            for anchor_name, anchor_fact in (
                ("MOON", "FACT-GOCHARA-MOON-NATAL"),
                ("LAGNA", "FACT-GOCHARA-LAGNA-NATAL"),
            ):
                edge_id = (
                    f"REL-GOCHARA-{gplanet}-{anchor_name}-"
                    f"{_deterministic_id(gnode_id)}"
                )
                evidence_edges.append(
                    DAGEdge(
                        edge_id=edge_id,
                        source=gnode_id,
                        target=anchor_fact,
                        relationship=relationship,
                        metadata={
                            "house_from_"
                            + anchor_name.lower(): greport.get(
                                "house_from_" + anchor_name.lower()
                            ),
                            "band": band_label,
                            "vedha_obstructed": greport.get(
                                "vedha_obstructed"
                            ),
                        },
                    ),
                )

    # ── Temporal node (dasha/transit) ───────────────────────────────
    if any(k in jre_facts for k in ("dasha_periods", "transit_houses", "moon_nakshatra")):
        temporal_node = DAGNode(
            node_id="temporal",
            node_type="TEMPORAL",
            labels=("TEMPORAL", "DASHA", "TRANSIT"),
            payload={
                "dasha_active": jre_facts.get("dasha_periods"),
                "transit_houses": jre_facts.get("transit_houses"),
                "moon_nakshatra": jre_facts.get("moon_nakshatra"),
            },
            children=(),
            parent=None,
        )
        evidence_nodes.append(temporal_node)
        temporal_id = temporal_node.node_id

    # ── Rule nodes per yoga evaluation ──────────────────────────────
    rule_nodes: dict[str, DAGNode] = {}
    # Keep a deterministic order for edge construction
    for idx, ev in enumerate(yoga_evals):
        yoga_name = getattr(ev, "yoga_name", f"yoga_{idx}")
        status = getattr(ev, "status", None)
        status_str = str(status) if status is not None else "UNKNOWN"
        rule_id = _build_rule_id(yoga_name)

        node_id = f"R-{idx}-{_deterministic_id(rule_id.canonical)}"
        node = DAGNode(
            node_id=node_id,
            node_type="RULE",
            labels=(rule_id.namespace, rule_id.canonical),
            payload={
                "yoga_name": yoga_name,
                "status": status_str,
                "rule_id": rule_id.canonical,
                "evaluation_idx": idx,
            },
            children=(),
            parent=None,
        )
        rule_nodes[node_id] = node
        evidence_nodes.append(node)

    # ── Edges: evaluation -> rule, rule -> facts, rule -> temporal ─
    for idx, node in enumerate(rule_nodes.values()):
        # Evaluation -> rule
        evidence_edges.append(
            DAGEdge(
                edge_id=f"E-EV-{idx}",
                source=prediction_id_node,
                target=node.node_id,
                relationship="ESTABLISHED_BY",
                metadata={"yoga_name": node.payload.get("yoga_name")},
            )
        )

        # rule -> each fact
        for fact_node in evidence_nodes:
            if fact_node.node_type != "FACT":
                continue
            evidence_edges.append(
                DAGEdge(
                    edge_id=f"E-RF-{idx}-{_deterministic_id(fact_node.node_id)}",
                    source=node.node_id,
                    target=fact_node.node_id,
                    relationship="SUPPORTS",
                    metadata={"fact_type": "PLANETARY_STATE"},
                )
            )

        # rule -> temporal (when temporal node present)
        if temporal_id is not None:
            evidence_edges.append(
                DAGEdge(
                    edge_id=f"E-RT-{idx}",
                    source=node.node_id,
                    target=temporal_id,
                    relationship="AFFECTS",
                    metadata={"aspect": "Dasha/Transit multiplier"},
                )
            )

    return DirectedAcyclicGraph(graph_id=graph_id, nodes=tuple(evidence_nodes), edges=tuple(evidence_edges))


# ── JSON DTO + GraphViz DOT export ───────────────────────────────────────────

def to_json(graph: DirectedAcyclicGraph, indent: int = 2) -> str:
    """Serialize a DirectedAcyclicGraph to pretty-printed JSON.

    Deterministic: sorted keys, compact separators, round-6 floats.
    Suitable for the Evidence Graph Exporter (JSON DTO).
    """
    return json.dumps(
        _canonicalize_floats(graph.to_dict()),
        sort_keys=True,
        indent=indent,
        ensure_ascii=False,
    )


def result_to_json(graph: DirectedAcyclicGraph, indent: int = 2) -> str:
    """Alias for :func:`to_json` — canonical JSON serializer."""
    return to_json(graph, indent)


def result_to_dict(graph: DirectedAcyclicGraph) -> dict[str, Any]:
    """Serialize a DirectedAcyclicGraph to a dict (round-trip ready)."""
    result: dict[str, Any] = _canonicalize_floats(graph.to_dict())
    return result


def graph_to_dot(graph: DirectedAcyclicGraph) -> str:
    """Expose the evidence graph as a GraphViz DOT string.

    The DOT output is deterministic given the same graph; it preserves
    node_type / relationship / payload ordering for audit tooling.
    """
    lines = [
        "digraph evidence_graph {",
        "    rankdir=TB;",
        "    node [shape=box, style=filled, fontname=Helvetica];",
        "    edge [fontname=Helvetica];",
    ]

    # Node declarations
    for node in graph.nodes:
        label = " | ".join(node.labels) if node.labels else node.node_type
        payload = json.dumps(node.payload, sort_keys=True, ensure_ascii=False)
        # Build the DOT label with minimal escaping: backslash -> double-backslash,
        # double-quote -> backslash-quote, newline -> backslash-n. Force DOT to
        # render the label inside a pair of braces per line.
        escaped_payload = payload.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
        escaped_label = label.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(
            "    "
            + node.node_id
            + " [label=\"{"
            + escaped_label
            + "\n{"
            + escaped_payload
            + "}}\", shape=box];"
        )

    # Edge declarations
    for edge in graph.edges:
        escaped_rel = str(edge.relationship).replace("\\", "\\\\").replace('"', '\\"')
        lines.append(
            "    "
            + str(edge.source)
            + " -> "
            + str(edge.target)
            + " [label=\"{"
            + escaped_rel
            + "}, weight="
            + str(edge.weight)
            + "];"
        )

    lines.append("}")
    return "\n".join(lines)


# ── Provenance service ───────────────────────────────────────────────────────

class EvidenceGraphService:
    """Facade for building and exporting the JRE evidence graph.

    Usage::

        svc = EvidenceGraphService()
        graph = svc.build_graph(jre_facts, yoga_evals)
        dot = graph_to_dot(graph)          # GraphViz DOT
        payload = result_to_dict(graph)    # JSON DTO
    """

    def __init__(self, prediction_id: str = "P-CUSTOM") -> None:
        self._prediction_id = prediction_id

    def build_graph(
        self,
        jre_facts: dict[str, Any],
        yoga_evals: list[Any],
        prediction_id: str | None = None,
    ) -> DirectedAcyclicGraph:
        """Build the evidence graph from live pipeline output.

        Deterministic: identical jre_facts + yoga_evals always produce the
        same graph structure and payloads.
        """
        pid = prediction_id or self._prediction_id
        return build_provenance_chain(
            jre_facts=jre_facts,
            yoga_evals=yoga_evals,
            prediction_id=pid,
        )

    def to_dot(self, graph: DirectedAcyclicGraph) -> str:
        """Export the graph as GraphViz DOT."""
        return graph_to_dot(graph)

    def to_json(self, graph: DirectedAcyclicGraph, indent: int = 2) -> str:
        """Export the graph as canonical JSON."""
        return to_json(graph, indent)

    def to_dict(self, graph: DirectedAcyclicGraph) -> dict[str, Any]:
        """Export the graph to a JSON-serializable dict."""
        return result_to_dict(graph)

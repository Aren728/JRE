"""Phase 8: Export layer tests.

Covers the three export engines:

- provenance exporter: canonical diagnostic JSON + GraphML 1.1 of the
  evidence DAG (deterministic, well-formed, invariant-checked);
- SVG renderer: D1/D9/D10/D60 in north/south/wheel styles (deterministic,
  escaped, validated inputs);
- PDF report: ReportLab executive forensic report (deterministic bytes,
  lazy optional-extra import).
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from xml.etree import ElementTree as ET

import pytest

from jrs.api.dependencies import build_jre_facts, compute_chart_from_fixture, load_fixture
from jrs.export import (
    EXPORT_SCHEMA_VERSION,
    provenance_to_diagnostic_json,
    provenance_to_graphml,
    render_chart_svg,
)
from jrs.export.pdf_report import (
    ForensicReportInput,
    render_forensic_pdf,
    rows_from_evaluation,
)
from jrs.export.svg_renderer import (
    ChartPlacement,
    placements_from_longitudes,
)
from jrs.prediction_engine.provenance import EvidenceGraphService
from jrs.yoga_evaluator.service import YogaEvaluatorService


@pytest.fixture(scope="module")
def pilot_graph():
    fixture = load_fixture("chart_001_pilot")
    chart = compute_chart_from_fixture(fixture)
    facts = build_jre_facts(chart)
    yoga_evals = YogaEvaluatorService().evaluate_classical_yogas(facts)
    return EvidenceGraphService(prediction_id="P-chart_001_pilot").build_graph(
        jre_facts=facts, yoga_evals=yoga_evals
    )


# ── Provenance exporter ─────────────────────────────────────────────────────
class TestProvenanceJson:
    def test_payload_shape(self, pilot_graph) -> None:
        payload = provenance_to_diagnostic_json(pilot_graph, fixture_id="chart_001_pilot")
        assert payload["schema_version"] == EXPORT_SCHEMA_VERSION
        assert payload["graph_id"] == pilot_graph.graph_id
        assert payload["fixture_id"] == "chart_001_pilot"
        assert payload["node_count"] == len(payload["graph"]["nodes"])
        assert payload["edge_count"] == len(payload["graph"]["edges"])
        # Layer summary sums to the node count.
        assert sum(payload["layer_summary"].values()) == payload["node_count"]
        # Relationship histogram sums to the edge count.
        assert sum(payload["relationship_histogram"].values()) == payload["edge_count"]
        # Invariants: connected, no dangling edges.
        assert payload["invariants"]["dangling_edges"] == []

    def test_deterministic(self, pilot_graph) -> None:
        a = provenance_to_diagnostic_json(pilot_graph)
        b = provenance_to_diagnostic_json(pilot_graph)
        assert a == b

    def test_dangling_edges_detected(self, pilot_graph) -> None:
        # Corrupt one edge target and confirm the invariant flags it.
        from jrs.prediction_engine.provenance import DAGEdge, DAGNode, DirectedAcyclicGraph

        node = DAGNode(node_id="X", node_type="FACT")
        broken = DAGEdge(
            edge_id="BAD", source="X", target="MISSING", relationship="SUPPORTS"
        )
        graph = DirectedAcyclicGraph(graph_id="g", nodes=(node,), edges=(broken,))
        payload = provenance_to_diagnostic_json(graph)
        assert payload["invariants"]["dangling_edges"] == ["BAD"]


class TestProvenanceGraphml:
    NS = "{http://graphml.graphdrawing.org/xmlns}"

    def test_well_formed_and_complete(self, pilot_graph) -> None:
        text = provenance_to_graphml(pilot_graph, fixture_id="chart_001_pilot")
        root = ET.fromstring(text)
        assert root.tag == f"{self.NS}graphml"
        graph = root.find(f"{self.NS}graph")
        assert graph is not None
        assert graph.get("edgedefault") == "directed"
        nodes = graph.findall(f"{self.NS}node")
        edges = graph.findall(f"{self.NS}edge")
        assert len(nodes) == len(pilot_graph.nodes)
        assert len(edges) == len(pilot_graph.edges)
        # Every node carries the declared data keys.
        for node in nodes:
            keys = {d.get("key") for d in node.findall(f"{self.NS}data")}
            assert {"node_type", "labels", "payload"} <= keys

    def test_payload_is_canonical_json(self, pilot_graph) -> None:
        text = provenance_to_graphml(pilot_graph)
        root = ET.fromstring(text)
        graph = root.find(f"{self.NS}graph")
        first_data = graph.find(f"{self.NS}node/{self.NS}data[@key='payload']")
        decoded = json.loads(first_data.text)
        assert isinstance(decoded, dict)

    def test_deterministic(self, pilot_graph) -> None:
        assert provenance_to_graphml(pilot_graph) == provenance_to_graphml(pilot_graph)

    def test_escapes_unsafe_text(self) -> None:
        from jrs.prediction_engine.provenance import DAGNode, DirectedAcyclicGraph

        node = DAGNode(
            node_id="X<1>",
            node_type="FACT",
            payload={"note": 'a < b & "c"'},
        )
        text = provenance_to_graphml(DirectedAcyclicGraph(graph_id="g", nodes=(node,)))
        # Must parse (no raw < & in text nodes) and round-trip the payload.
        root = ET.fromstring(text)
        payload_el = root.find(f".//{self.NS}data[@key='payload']")
        assert json.loads(payload_el.text)["note"] == 'a < b & "c"'


# ── SVG renderer ────────────────────────────────────────────────────────────
class TestSvgRenderer:
    EINSTEIN_LON = {
        "SUN": 331.32419345824417,
        "MOON": 232.22148712046456,
        "MARS": 274.7331682026066,
    }

    def test_placements_from_longitudes(self) -> None:
        placements = placements_from_longitudes(self.EINSTEIN_LON)
        by_body = {p.body: p for p in placements}
        assert by_body["SUN"].sign_index == 11  # MEENA
        assert by_body["MOON"].sign_index == 7  # VRISHCHIKA
        assert by_body["MARS"].short == "Ma"

    def test_longitude_range_enforced(self) -> None:
        with pytest.raises(ValueError, match="out of range"):
            placements_from_longitudes({"SUN": 361.0})
        with pytest.raises(ValueError, match="out of range"):
            placements_from_longitudes({"SUN": -1.0})

    def test_all_styles_render_and_differ(self) -> None:
        placements = placements_from_longitudes(self.EINSTEIN_LON)
        outputs = {
            style: render_chart_svg(placements, lagna_sign=8, division="D9", style=style)
            for style in ("north", "south", "wheel")
        }
        assert len(set(outputs.values())) == 3
        for style, svg in outputs.items():
            assert svg.startswith("<svg ")
            ET.fromstring(svg)  # well-formed
        assert "<circle" in outputs["wheel"]
        assert "<rect" in outputs["north"]

    def test_deterministic_bytes(self) -> None:
        placements = placements_from_longitudes(self.EINSTEIN_LON)
        a = render_chart_svg(placements, lagna_sign=8, division="D10", style="south")
        b = render_chart_svg(placements, lagna_sign=8, division="D10", style="south")
        assert a == b

    def test_wheel_rotates_with_lagna(self) -> None:
        placements = placements_from_longitudes(self.EINSTEIN_LON)
        a = render_chart_svg(placements, lagna_sign=1, division="D1", style="wheel")
        b = render_chart_svg(placements, lagna_sign=2, division="D1", style="wheel")
        assert a != b

    def test_input_validation(self) -> None:
        placements = placements_from_longitudes(self.EINSTEIN_LON)
        with pytest.raises(ValueError, match="unsupported style"):
            render_chart_svg(placements, lagna_sign=1, division="D1", style="kaleidoscope")
        with pytest.raises(ValueError, match="unsupported division"):
            render_chart_svg(placements, lagna_sign=1, division="D7", style="north")
        with pytest.raises(ValueError, match="lagna_sign must be 1-12"):
            render_chart_svg(placements, lagna_sign=0, division="D1", style="north")
        with pytest.raises(ValueError, match="duplicate body"):
            render_chart_svg(
                [ChartPlacement("SUN", 0), ChartPlacement("SUN", 1)],
                lagna_sign=1,
                division="D1",
                style="north",
            )

    def test_title_is_escaped(self) -> None:
        svg = render_chart_svg(
            placements_from_longitudes({"SUN": 5.0}),
            lagna_sign=1,
            division="D1",
            style="north",
            title="a <b> & c",
        )
        assert "a &lt;b&gt; &amp; c" in svg

    def test_house_numbering_follows_lagna(self) -> None:
        # SUN in MESHA with MESHA lagna -> house 1.
        svg = render_chart_svg(
            placements_from_longitudes({"SUN": 5.0}),
            lagna_sign=1,
            division="D1",
            style="north",
        )
        assert "(1)" in svg
        # Same placement with TULA lagna -> MESHA is house 7.
        svg = render_chart_svg(
            placements_from_longitudes({"SUN": 5.0}),
            lagna_sign=7,
            division="D1",
            style="north",
        )
        assert "(7)" in svg


# ── PDF report ──────────────────────────────────────────────────────────────
class TestPdfReport:
    def _input(self) -> ForensicReportInput:
        return ForensicReportInput(
            subject="Albert Einstein",
            fixture_id="chart_001_pilot",
            lagna="MEENA",
            moon_nakshatra="SHATABHISHA",
            engine_version="v1.0.0-beta",
            positions=[
                {"body": "SUN", "sign": "MEENA", "house": 1, "dignity": "Neutral"},
                {"body": "MOON", "sign": "VRISHCHIKA", "house": 9, "dignity": "Neutral"},
            ],
            yogas=[
                {
                    "yoga_name": "Gajakesari",
                    "status": "FORMED",
                    "category": "GAJAKESARI",
                    "involved": "JUPITER, MOON",
                    "chain_impact": 0.72,
                    "cancellation_reason": None,
                },
                {
                    "yoga_name": "Raja",
                    "status": "CANCELLED",
                    "category": "RAJA",
                    "involved": "MARS, SATURN",
                    "chain_impact": -0.4,
                    "cancellation_reason": "MARS debilitated in D9 (Navamsha)",
                },
            ],
            provenance_summary={
                "graph_id": "abcdef0123456789",
                "node_count": 26,
                "edge_count": 69,
                "layer_summary": {"EVALUATION": 1, "RULE": 3, "FACT": 21, "TEMPORAL": 1},
            },
        )

    def test_renders_pdf_bytes(self) -> None:
        pdf = render_forensic_pdf(self._input())
        assert pdf.startswith(b"%PDF-")
        assert len(pdf) > 1000

    def test_deterministic_bytes(self) -> None:
        assert render_forensic_pdf(self._input()) == render_forensic_pdf(self._input())

    def test_missing_reportlab_raises_descriptive_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Simulate the optional extra being absent: blocking the reportlab
        # import must surface the descriptive ImportError, not a traceback.
        monkeypatch.setitem(__import__("sys").modules, "reportlab", None)
        monkeypatch.setitem(__import__("sys").modules, "reportlab.lib", None)
        monkeypatch.setitem(__import__("sys").modules, "reportlab.lib.pagesizes", None)
        monkeypatch.setitem(__import__("sys").modules, "reportlab.lib.styles", None)
        monkeypatch.setitem(__import__("sys").modules, "reportlab.lib.units", None)
        monkeypatch.setitem(__import__("sys").modules, "reportlab.platypus", None)
        with pytest.raises(ImportError, match=r"\[export\]"):
            render_forensic_pdf(self._input())

    def test_rows_from_evaluation(self) -> None:
        yoga = SimpleNamespace(
            model_dump=lambda: {
                "yoga_name": "Dhana",
                "status": "FORMED",
                "category": "DHANA",
                "involved_planets": ["JUPITER", "SATURN"],
                "chain_impact": 0.5,
                "cancellation_reason": None,
            }
        )
        evaluation = SimpleNamespace(
            subject="Test Subject",
            lagna="SIMHA",
            moon_nakshatra="MAGHA",
            engine_version="v1.0.0-beta",
            yogas=[yoga],
        )
        rows = rows_from_evaluation(evaluation)
        assert rows["subject"] == "Test Subject"
        assert rows["lagna"] == "SIMHA"
        assert rows["yogas"][0]["involved"] == "JUPITER, SATURN"
        assert rows["yogas"][0]["chain_impact"] == 0.5

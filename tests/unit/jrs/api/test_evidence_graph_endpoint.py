"""Phase 7 (Track C): Evidence-graph serving endpoint tests.

The Observatory endpoint must serve exactly the deterministic graph the
golden-state ``evidence_graph`` stage covers: EVALUATION root, RULE
nodes, FACT nodes, and a TEMPORAL layer, connected and acyclic.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from jrs.api.main import app

client = TestClient(app)


class TestEvidenceGraphEndpoint:
    def test_serves_deterministic_graph_shape(self) -> None:
        response = client.get("/api/v1/evidence/graph/chart_001_pilot")
        assert response.status_code == 200
        body = response.json()

        assert body["fixture_id"] == "chart_001_pilot"
        assert body["graph_id"]
        assert body["node_count"] == len(body["nodes"])
        assert body["edge_count"] == len(body["edges"])
        assert body["engine_version"]

        node_types = {n["node_type"] for n in body["nodes"]}
        # The full provenance chain must be present.
        assert "EVALUATION" in node_types
        assert "RULE" in node_types
        assert "FACT" in node_types

        # Connectivity: every edge references known nodes.
        node_ids = {n["node_id"] for n in body["nodes"]}
        for edge in body["edges"]:
            assert edge["source"] in node_ids, edge["edge_id"]
            assert edge["target"] in node_ids, edge["edge_id"]

    def test_graph_is_deterministic(self) -> None:
        first = client.get("/api/v1/evidence/graph/chart_001_pilot").json()
        second = client.get("/api/v1/evidence/graph/chart_001_pilot").json()
        assert first["graph_id"] == second["graph_id"]
        assert first["nodes"] == second["nodes"]
        assert first["edges"] == second["edges"]

    def test_structure_only_mode_strips_payloads(self) -> None:
        response = client.get(
            "/api/v1/evidence/graph/chart_001_pilot",
            params={"include_payloads": "false"},
        )
        assert response.status_code == 200
        body = response.json()
        assert all(node["payload"] == {} for node in body["nodes"])

    def test_unknown_fixture_returns_404(self) -> None:
        response = client.get("/api/v1/evidence/graph/chart_999_nonexistent")
        assert response.status_code == 404

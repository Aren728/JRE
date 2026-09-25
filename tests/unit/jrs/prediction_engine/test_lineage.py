"""Phase 9D: Prediction lineage tracer tests.

Validates the backward-chain contract on the real chart_001_pilot
pipeline: ordered layers, flag-off availability reporting (with the
enabling flag named), raw-float fidelity of the deepest layer, and
end-to-end determinism via the API route.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from jrs.api.dependencies import build_jre_facts, compute_chart_from_fixture, load_fixture
from jrs.api.main import app
from jrs.prediction_engine.lineage import (
    LINEAGE_LAYERS,
    trace_prediction,
)
from jrs.prediction_engine.provenance import EvidenceGraphService
from jrs.yoga_evaluator.service import YogaEvaluatorService

client = TestClient(app)


def _evaluate(fixture_id: str = "chart_001_pilot") -> dict[str, Any]:
    fixture = load_fixture(fixture_id)
    chart = compute_chart_from_fixture(fixture)
    facts = build_jre_facts(chart)
    yoga_evals = YogaEvaluatorService().evaluate_classical_yogas(facts)
    graph = EvidenceGraphService(prediction_id=f"P-{fixture_id}").build_graph(
        jre_facts=facts, yoga_evals=yoga_evals
    )
    return {"facts": facts, "yoga_evals": yoga_evals, "graph": graph}


@pytest.fixture(scope="module")
def lineage() -> dict[str, Any]:
    state = _evaluate()
    return trace_prediction(
        prediction_id="P-chart_001_pilot",
        jre_facts=state["facts"],
        yoga_evals=state["yoga_evals"],
        graph_dict=state["graph"].to_dict(),
    )


class TestLineageContract:
    def test_ordered_chain_layers(self, lineage: dict[str, Any]) -> None:
        assert lineage["chain_order"] == [
            "PREDICTION",
            "RULE",
            "DASHA_GATE",
            "TRANSIT",
            "VARGA",
            "YOGA",
            "SAV",
            "NATAL_LONGITUDES",
        ]
        assert list(lineage["chain"]) == list(LINEAGE_LAYERS)

    def test_flag_off_layers_report_unavailability(
        self, lineage: dict[str, Any]
    ) -> None:
        # No scoring flags are set in the test environment: the
        # flag-gated layers must be explicit about it.
        for layer in ("DASHA_GATE", "TRANSIT", "VARGA", "SAV"):
            entry = lineage["chain"][layer]
            assert entry["available"] is False, layer
            assert "JRS_" in entry["reason"], layer

    def test_always_available_layers(self, lineage: dict[str, Any]) -> None:
        for layer in ("PREDICTION", "RULE", "YOGA", "NATAL_LONGITUDES"):
            assert lineage["chain"][layer]["available"] is True, layer

    def test_rule_layer_carries_rule_ids(self, lineage: dict[str, Any]) -> None:
        rules = lineage["chain"]["RULE"]["details"]["rules"]
        assert rules
        assert all(rule["rule_id"] for rule in rules)

    def test_natal_longitudes_exact_floats(self, lineage: dict[str, Any]) -> None:
        deep = lineage["chain"]["NATAL_LONGITUDES"]["details"]
        lon = deep["longitudes"]
        assert lon["SUN"] == pytest.approx(331.324193, abs=1e-5)
        assert lon["MOON"] == pytest.approx(232.221487, abs=1e-5)
        assert deep["lagna"] == "MITHUNA"
        assert deep["moon_nakshatra"] == "JYESHTHA"

    def test_deterministic(self, lineage: dict[str, Any]) -> None:
        state = _evaluate()
        repeat = trace_prediction(
            prediction_id="P-chart_001_pilot",
            jre_facts=state["facts"],
            yoga_evals=state["yoga_evals"],
            graph_dict=state["graph"].to_dict(),
        )
        assert repeat == lineage


class TestLineageFlagOn:
    def test_flag_on_layers_become_available(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("JRS_DASHA_TRANSIT_SCORING", "1")
        monkeypatch.setenv("JRS_ASHTA_SCORING", "1")
        state = _evaluate()
        lineage = trace_prediction(
            prediction_id="P-chart_001_pilot",
            jre_facts=state["facts"],
            yoga_evals=state["yoga_evals"],
            graph_dict=state["graph"].to_dict(),
        )
        gate = lineage["chain"]["DASHA_GATE"]
        assert gate["available"] is True
        assert "VENUS/SUN/SATURN" in gate["summary"]
        sav = lineage["chain"]["SAV"]
        assert sav["available"] is True
        assert sum(sav["details"]["sav"]) == 337  # classical SAV invariant


class TestLineageEndpoint:
    def test_endpoint_serves_full_chain(self) -> None:
        response = client.get("/api/v1/evidence/lineage/chart_001_pilot")
        assert response.status_code == 200
        body = response.json()
        assert body["prediction_id"] == "P-chart_001_pilot"
        assert len(body["chain_order"]) == 8
        assert body["chain"]["NATAL_LONGITUDES"]["available"] is True

    def test_endpoint_unknown_fixture_404(self) -> None:
        response = client.get("/api/v1/evidence/lineage/chart_999_nonexistent")
        assert response.status_code == 404

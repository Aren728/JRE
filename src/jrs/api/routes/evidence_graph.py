"""Phase 7 (Track C): Evidence-graph serving endpoints (JRE Observatory).

Serves the deterministic Phase 3 evidence DAG for any frozen fixture so
the frontend Evidence Graph Inspector can render the full provenance
chain: Prediction (EVALUATION) ──► Rules ──► Facts ──► Classical
References (CITATION), plus the TEMPORAL (dasha/transit) layer.

The graph is built by the same :class:`EvidenceGraphService` call the
golden-state ``evidence_graph`` stage covers, so what the Observatory
renders is exactly what the regression gate verifies.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from jrs.api.dependencies import (
    build_jre_facts,
    compute_chart_from_fixture,
    load_fixture,
)
from jrs.api.offload import offload
from jrs.api.schemas import ENGINE_VERSION, EvidenceGraphResponse, LineageResponse
from jrs.prediction_engine.lineage import trace_prediction
from jrs.prediction_engine.provenance import (
    EvidenceGraphService,
    result_to_dict,
)
from jrs.yoga_evaluator.service import YogaEvaluatorService

router = APIRouter(prefix="/api/v1/evidence", tags=["Evidence"])


def _build_graph_payload(fixture_id: str, include_payloads: bool) -> dict[str, Any]:
    """Build the evidence DAG for one fixture (blocking; runs offloaded)."""
    fixture = load_fixture(fixture_id)
    chart = compute_chart_from_fixture(fixture)
    facts = build_jre_facts(chart)
    yoga_evals = YogaEvaluatorService().evaluate_classical_yogas(facts)
    graph = EvidenceGraphService(prediction_id=f"P-{fixture_id}").build_graph(
        jre_facts=facts,
        yoga_evals=yoga_evals,
    )
    payload = result_to_dict(graph)
    if not include_payloads:
        # Structure-only mode: strip raw payloads for compact transport.
        for node in payload["nodes"]:
            node["payload"] = {}
    return payload


def _build_lineage_payload(fixture_id: str) -> dict[str, Any]:
    """Build the full prediction lineage for one fixture (blocking)."""
    fixture = load_fixture(fixture_id)
    chart = compute_chart_from_fixture(fixture)
    facts = build_jre_facts(chart)
    yoga_evals = YogaEvaluatorService().evaluate_classical_yogas(facts)
    graph = EvidenceGraphService(prediction_id=f"P-{fixture_id}").build_graph(
        jre_facts=facts,
        yoga_evals=yoga_evals,
    )
    return trace_prediction(
        prediction_id=f"P-{fixture_id}",
        jre_facts=facts,
        yoga_evals=yoga_evals,
        graph_dict=graph.to_dict(),
    )


@router.get("/graph/{fixture_id}", response_model=EvidenceGraphResponse)
async def get_evidence_graph(
    fixture_id: str,
    include_payloads: bool = Query(
        True,
        description="Include full node payloads (False = structure only).",
    ),
) -> EvidenceGraphResponse:
    """Serve the evidence DAG for a frozen benchmark fixture.

    Renders the same deterministic graph the golden-state regression
    gate hashes: EVALUATION root ──► RULE nodes per yoga ──► FACT nodes
    per planetary state ──► CITATION (BPHS) references, with the
    TEMPORAL dasha/transit layer attached.
    """
    try:
        payload = await offload(_build_graph_payload, fixture_id, include_payloads)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Evidence graph construction failed: {e}",
        )

    return EvidenceGraphResponse(
        graph_id=str(payload["graph_id"]),
        fixture_id=fixture_id,
        node_count=len(payload["nodes"]),
        edge_count=len(payload["edges"]),
        nodes=payload["nodes"],
        edges=payload["edges"],
        engine_version=ENGINE_VERSION,
    )


@router.get("/lineage/{fixture_id}", response_model=LineageResponse)
async def get_prediction_lineage(fixture_id: str) -> LineageResponse:
    """Serve the full backward lineage for a fixture's prediction id.

    Phase 9D: maps ``P-<fixture_id>`` to its supporting chain —
    Rule ──► Dasha Gate ──► Transit ──► Varga ──► Yoga ──► SAV ──►
    Natal Longitudes (the exact ephemeris raw floats). Flag-gated
    layers report ``available: false`` with the enabling flag named
    when their report was not injected.
    """
    try:
        payload = await offload(_build_lineage_payload, fixture_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Lineage construction failed: {e}",
        )

    return LineageResponse(
        prediction_id=str(payload["prediction_id"]),
        graph_id=payload.get("graph_id"),
        chain_order=list(payload["chain_order"]),
        chain=payload["chain"],
        engine_version=ENGINE_VERSION,
    )

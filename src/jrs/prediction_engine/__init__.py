"""Prediction Engine — Deep predictive modules for JRE."""

try:
    from jrs.prediction_engine.aspects import AspectMatrixEngine
    from jrs.prediction_engine.deep_dasha import DeepVimshottariEngine
    from jrs.prediction_engine.parivartana import ParivartanaEngine
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
    )
except ImportError:
    from .aspects import AspectMatrixEngine
    from .deep_dasha import DeepVimshottariEngine
    from .parivartana import ParivartanaEngine
    from .provenance import (
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
    )

__all__ = [
    "ParivartanaEngine",
    "AspectMatrixEngine",
    "DeepVimshottariEngine",
    "DirectedAcyclicGraph",
    "DAGNode",
    "DAGEdge",
    "EvidenceGraphService",
    "LiteratureCitation",
    "RuleId",
    "build_provenance_chain",
    "graph_to_dot",
    "result_to_dict",
    "result_to_json",
]

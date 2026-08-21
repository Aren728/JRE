"""JRS (Jyotish Research System) — Orchestrator & Evidence Layer.

Public API
----------
- ``OrchestratorService``  – routes queries and aggregates engine outputs
- ``QueryIntent``          – structured user query
- ``EvidenceRequest``      – resolved routing decision
- ``EvidencePacket``       – aggregated engine outputs
- ``JRSConfig``            – orchestrator configuration
- ``load_jrs_config``      – TOML config loader
"""

from __future__ import annotations

from .config import load_jrs_config
from .errors import (
    EngineExecutionError,
    InvalidJRSConfigError,
    InvalidQueryError,
    JRSerror,
    OrchestrationError,
)
from .models import (
    ALL_ENGINES,
    EngineOutput,
    EvidencePacket,
    EvidenceRequest,
    JRSConfig,
    QueryCategory,
    QueryIntent,
    RoutingRule,
    route_query_intent,
)
from .serialize import (
    engine_output_from_dict,
    evidence_packet_from_dict,
    evidence_request_from_dict,
    jrs_config_from_dict,
    query_intent_from_dict,
    result_to_dict,
    result_to_json,
    routing_rule_from_dict,
)
from .service import OrchestratorService

__all__: tuple[str, ...] = (
    # Errors
    "JRSerror",
    "InvalidJRSConfigError",
    "InvalidQueryError",
    "EngineExecutionError",
    "OrchestrationError",
    # Models
    "QueryCategory",
    "QueryIntent",
    "EvidenceRequest",
    "EngineOutput",
    "EvidencePacket",
    "RoutingRule",
    "JRSConfig",
    "ALL_ENGINES",
    "route_query_intent",
    # Config
    "load_jrs_config",
    # Serialize
    "query_intent_from_dict",
    "evidence_request_from_dict",
    "engine_output_from_dict",
    "evidence_packet_from_dict",
    "routing_rule_from_dict",
    "jrs_config_from_dict",
    "result_to_dict",
    "result_to_json",
    # Service
    "OrchestratorService",
)

"""JRS Orchestrator deterministic serialization."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from .errors import InvalidJRSConfigError
from .models import (
    EngineOutput,
    EvidencePacket,
    EvidenceRequest,
    JRSConfig,
    QueryCategory,
    QueryIntent,
    RoutingRule,
)


def query_intent_from_dict(data: dict[str, Any]) -> QueryIntent:
    """Deserialize a QueryIntent from a dict."""
    category_str = data["category"]
    try:
        category = QueryCategory(category_str)
    except ValueError as exc:
        raise InvalidJRSConfigError(f"Unknown query category: {category_str}") from exc

    return QueryIntent(
        query_id=data["query_id"],
        category=category,
        context=dict(data.get("context", {})),
    )


def evidence_request_from_dict(data: dict[str, Any]) -> EvidenceRequest:
    """Deserialize an EvidenceRequest from a dict."""
    intent = query_intent_from_dict(data["intent"])
    return EvidenceRequest(
        intent=intent,
        required_engines=tuple(data.get("required_engines", [])),
        required_research_topics=tuple(data.get("required_research_topics", [])),
        required_houses=tuple(data.get("required_houses", [])),
    )


def engine_output_from_dict(data: dict[str, Any]) -> EngineOutput:
    """Deserialize an EngineOutput from a dict."""
    computed_at_str = data.get("computed_at", "")
    computed_at = (
        datetime.fromisoformat(computed_at_str)
        if computed_at_str
        else datetime.now(UTC)
    )

    return EngineOutput(
        engine_name=data["engine_name"],
        result=None,  # Results are opaque; restored by the engine
        computed_at=computed_at,
    )


def evidence_packet_from_dict(data: dict[str, Any]) -> EvidencePacket:
    """Deserialize an EvidencePacket from a dict."""
    aggregated_at_str = data.get("aggregated_at", "")
    aggregated_at = (
        datetime.fromisoformat(aggregated_at_str)
        if aggregated_at_str
        else datetime.now(UTC)
    )

    return EvidencePacket(
        query_id=data["query_id"],
        engine_outputs=tuple(
            engine_output_from_dict(eo) for eo in data.get("engine_outputs", [])
        ),
        research_evidence=tuple(data.get("research_evidence", [])),
        aggregated_at=aggregated_at,
    )


def routing_rule_from_dict(data: dict[str, Any]) -> RoutingRule:
    """Deserialize a RoutingRule from a dict."""
    return RoutingRule(
        required_engines=tuple(data.get("required_engines", [])),
        research_topics=tuple(data.get("research_topics", [])),
        required_houses=tuple(data.get("required_houses", [])),
    )


def jrs_config_from_dict(data: dict[str, Any]) -> JRSConfig:
    """Deserialize a JRSConfig from a dict."""
    routing_raw = data.get("routing", {})
    routing = {
        k: routing_rule_from_dict(v) for k, v in routing_raw.items()
    }
    return JRSConfig(
        version=data.get("version", "1.0"),
        default_research_depth=data.get("default_research_depth", "standard"),
        routing=routing,
        engine_hints=dict(data.get("engine_hints", {})),
    )


def result_to_dict(packet: EvidencePacket) -> dict[str, Any]:
    """Deterministic dict serialization of an EvidencePacket."""
    return packet.to_dict()


def result_to_json(packet: EvidencePacket, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of an EvidencePacket."""
    d = result_to_dict(packet)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)

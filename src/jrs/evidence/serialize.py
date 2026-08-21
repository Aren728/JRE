"""Evidence framework deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from .errors import InvalidEvidenceRecordError
from .models import (
    ClassicalSource,
    EvidenceChain,
    EvidenceConfig,
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
    RuleCatalogEntry,
)


def classical_source_from_dict(data: dict[str, Any]) -> ClassicalSource:
    """Deserialize a ClassicalSource from a dict."""
    return ClassicalSource(
        source_id=data["source_id"],
        name=data["name"],
        author=data.get("author", ""),
        era=data.get("era", ""),
        reliability_weight=float(data.get("reliability_weight", 1.0)),
    )


def evidence_record_from_dict(data: dict[str, Any]) -> EvidenceRecord:
    """Deserialize an EvidenceRecord from a dict."""
    direction_str = data.get("direction", "SUPPORT")
    try:
        direction = EvidenceDirection(direction_str)
    except ValueError as exc:
        raise InvalidEvidenceRecordError(
            f"Unknown direction: {direction_str}",
        ) from exc

    strength_str = data.get("strength", "MODERATE")
    try:
        strength = EvidenceStrength(strength_str)
    except ValueError as exc:
        raise InvalidEvidenceRecordError(
            f"Unknown strength: {strength_str}",
        ) from exc

    return EvidenceRecord(
        evidence_id=data["evidence_id"],
        outcome_taxonomy=data.get("outcome_taxonomy", ""),
        supporting_fact_type=data.get("supporting_fact_type", ""),
        rule_id=data.get("rule_id", ""),
        source_id=data.get("source_id", ""),
        location=data.get("location", ""),
        direction=direction,
        strength=strength,
        timing_relevance=data.get("timing_relevance", ""),
        independence_group=data.get("independence_group", ""),
        contradicted_by=tuple(data.get("contradicted_by", [])),
        mitigated_by=tuple(data.get("mitigated_by", [])),
    )


def rule_catalog_entry_from_dict(data: dict[str, Any]) -> RuleCatalogEntry:
    """Deserialize a RuleCatalogEntry from a dict."""
    return RuleCatalogEntry(
        rule_id=data["rule_id"],
        description=data.get("description", ""),
        required_conditions=tuple(data.get("required_conditions", [])),
        outcome_taxonomy=data.get("outcome_taxonomy", ""),
    )


def evidence_chain_from_dict(data: dict[str, Any]) -> EvidenceChain:
    """Deserialize an EvidenceChain from a dict."""
    return EvidenceChain(
        record=evidence_record_from_dict(data["record"]),
        contradictions=tuple(
            evidence_record_from_dict(r)
            for r in data.get("contradictions", [])
        ),
        mitigations=tuple(
            evidence_record_from_dict(r)
            for r in data.get("mitigations", [])
        ),
        supporting=tuple(
            evidence_record_from_dict(r)
            for r in data.get("supporting", [])
        ),
    )


def evidence_config_from_dict(data: dict[str, Any]) -> EvidenceConfig:
    """Deserialize an EvidenceConfig from a dict."""
    return EvidenceConfig(
        version=data.get("version", "1.0"),
        source_weights=dict(data.get("source_weights", {})),
        strength_multipliers=dict(data.get("strength_multipliers", {})),
        max_chain_depth=int(data.get("max_chain_depth", 10)),
    )


def result_to_dict(chain: EvidenceChain) -> dict[str, Any]:
    """Deterministic dict serialization of an EvidenceChain."""
    return chain.to_dict()


def result_to_json(chain: EvidenceChain, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of an EvidenceChain."""
    d = result_to_dict(chain)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def record_to_json(record: EvidenceRecord, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of an EvidenceRecord."""
    return json.dumps(record.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

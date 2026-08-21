"""Marriage domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from .models import (
    MarriageConfig,
    MarriageOutcomeTaxonomy,
    MarriageRule,
    MarriageRuleCatalog,
)


def marriage_rule_from_dict(data: dict[str, Any]) -> MarriageRule:
    """Deserialize a MarriageRule from a dict."""
    outcome_str = data.get("outcome", "")
    outcome = MarriageOutcomeTaxonomy(outcome_str)

    from jrs.evidence.models import EvidenceDirection, EvidenceStrength

    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return MarriageRule(
        rule_id=data["rule_id"],
        description=data.get("description", ""),
        condition_facts=tuple(data.get("condition_facts", [])),
        outcome=outcome,
        direction=direction,
        strength=strength,
        source_id=data.get("source_id", "BPHS"),
        location=data.get("location", ""),
        timing_relevance=data.get("timing_relevance", ""),
    )


def marriage_config_from_dict(data: dict[str, Any]) -> MarriageConfig:
    """Deserialize a MarriageConfig from a dict."""
    return MarriageConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def marriage_rule_catalog_from_dict(data: dict[str, Any]) -> MarriageRuleCatalog:
    """Deserialize a MarriageRuleCatalog from a dict."""
    rules = tuple(
        marriage_rule_from_dict(r) for r in data.get("rules", [])
    )
    return MarriageRuleCatalog(rules=rules)


def result_to_dict(catalog: MarriageRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a MarriageRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: MarriageRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a MarriageRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: MarriageRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a MarriageRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

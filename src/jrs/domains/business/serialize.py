"""Business domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    BusinessConfig,
    BusinessOutcomeTaxonomy,
    BusinessRule,
    BusinessRuleCatalog,
)


def business_rule_from_dict(data: dict[str, Any]) -> BusinessRule:
    """Deserialize a BusinessRule from a dict."""
    outcome = BusinessOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return BusinessRule(
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


def business_config_from_dict(data: dict[str, Any]) -> BusinessConfig:
    """Deserialize a BusinessConfig from a dict."""
    return BusinessConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def business_rule_catalog_from_dict(
    data: dict[str, Any],
) -> BusinessRuleCatalog:
    """Deserialize a BusinessRuleCatalog from a dict."""
    rules = tuple(
        business_rule_from_dict(r) for r in data.get("rules", [])
    )
    return BusinessRuleCatalog(rules=rules)


def result_to_dict(catalog: BusinessRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a BusinessRuleCatalog."""
    return catalog.to_dict()


def result_to_json(
    catalog: BusinessRuleCatalog, *, indent: int | None = None,
) -> str:
    """Deterministic JSON serialization of a BusinessRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: BusinessRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a BusinessRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

"""Property domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    PropertyConfig,
    PropertyOutcomeTaxonomy,
    PropertyRule,
    PropertyRuleCatalog,
)


def property_rule_from_dict(data: dict[str, Any]) -> PropertyRule:
    """Deserialize a PropertyRule from a dict."""
    outcome = PropertyOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return PropertyRule(
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


def property_config_from_dict(data: dict[str, Any]) -> PropertyConfig:
    """Deserialize a PropertyConfig from a dict."""
    return PropertyConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def property_rule_catalog_from_dict(data: dict[str, Any]) -> PropertyRuleCatalog:
    """Deserialize a PropertyRuleCatalog from a dict."""
    rules = tuple(
        property_rule_from_dict(r) for r in data.get("rules", [])
    )
    return PropertyRuleCatalog(rules=rules)


def result_to_dict(catalog: PropertyRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a PropertyRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: PropertyRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a PropertyRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: PropertyRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a PropertyRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

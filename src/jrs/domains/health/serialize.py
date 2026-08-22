"""Health/Vitality domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    HealthConfig,
    HealthOutcomeTaxonomy,
    HealthRule,
    HealthRuleCatalog,
)


def health_rule_from_dict(data: dict[str, Any]) -> HealthRule:
    """Deserialize a HealthRule from a dict."""
    outcome = HealthOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return HealthRule(
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


def health_config_from_dict(data: dict[str, Any]) -> HealthConfig:
    """Deserialize a HealthConfig from a dict."""
    return HealthConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def health_rule_catalog_from_dict(
    data: dict[str, Any],
) -> HealthRuleCatalog:
    """Deserialize a HealthRuleCatalog from a dict."""
    rules = tuple(
        health_rule_from_dict(r) for r in data.get("rules", [])
    )
    return HealthRuleCatalog(rules=rules)


def result_to_dict(catalog: HealthRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a HealthRuleCatalog."""
    return catalog.to_dict()


def result_to_json(
    catalog: HealthRuleCatalog, *, indent: int | None = None,
) -> str:
    """Deterministic JSON serialization of a HealthRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: HealthRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a HealthRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

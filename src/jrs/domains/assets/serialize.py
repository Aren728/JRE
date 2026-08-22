"""Assets/Vehicles domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    AssetsConfig,
    AssetsOutcomeTaxonomy,
    AssetsRule,
    AssetsRuleCatalog,
)


def assets_rule_from_dict(data: dict[str, Any]) -> AssetsRule:
    """Deserialize an AssetsRule from a dict."""
    outcome = AssetsOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return AssetsRule(
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


def assets_config_from_dict(data: dict[str, Any]) -> AssetsConfig:
    """Deserialize an AssetsConfig from a dict."""
    return AssetsConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def assets_rule_catalog_from_dict(
    data: dict[str, Any],
) -> AssetsRuleCatalog:
    """Deserialize an AssetsRuleCatalog from a dict."""
    rules = tuple(
        assets_rule_from_dict(r) for r in data.get("rules", [])
    )
    return AssetsRuleCatalog(rules=rules)


def result_to_dict(catalog: AssetsRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of an AssetsRuleCatalog."""
    return catalog.to_dict()


def result_to_json(
    catalog: AssetsRuleCatalog, *, indent: int | None = None,
) -> str:
    """Deterministic JSON serialization of an AssetsRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: AssetsRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of an AssetsRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

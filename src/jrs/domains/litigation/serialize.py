"""Litigation/Conflict domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    LitigationConfig,
    LitigationOutcomeTaxonomy,
    LitigationRule,
    LitigationRuleCatalog,
)


def litigation_rule_from_dict(data: dict[str, Any]) -> LitigationRule:
    """Deserialize a LitigationRule from a dict."""
    outcome = LitigationOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return LitigationRule(
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


def litigation_config_from_dict(data: dict[str, Any]) -> LitigationConfig:
    """Deserialize a LitigationConfig from a dict."""
    return LitigationConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def litigation_rule_catalog_from_dict(
    data: dict[str, Any],
) -> LitigationRuleCatalog:
    """Deserialize a LitigationRuleCatalog from a dict."""
    rules = tuple(
        litigation_rule_from_dict(r) for r in data.get("rules", [])
    )
    return LitigationRuleCatalog(rules=rules)


def result_to_dict(catalog: LitigationRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a LitigationRuleCatalog."""
    return catalog.to_dict()


def result_to_json(
    catalog: LitigationRuleCatalog, *, indent: int | None = None,
) -> str:
    """Deterministic JSON serialization of a LitigationRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: LitigationRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a LitigationRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

"""Wealth domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    WealthConfig,
    WealthOutcomeTaxonomy,
    WealthRule,
    WealthRuleCatalog,
)


def wealth_rule_from_dict(data: dict[str, Any]) -> WealthRule:
    """Deserialize a WealthRule from a dict."""
    outcome = WealthOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return WealthRule(
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


def wealth_config_from_dict(data: dict[str, Any]) -> WealthConfig:
    """Deserialize a WealthConfig from a dict."""
    return WealthConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def wealth_rule_catalog_from_dict(data: dict[str, Any]) -> WealthRuleCatalog:
    """Deserialize a WealthRuleCatalog from a dict."""
    rules = tuple(
        wealth_rule_from_dict(r) for r in data.get("rules", [])
    )
    return WealthRuleCatalog(rules=rules)


def result_to_dict(catalog: WealthRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a WealthRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: WealthRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a WealthRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: WealthRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a WealthRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

"""Traits domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    TraitOutcomeTaxonomy,
    TraitRule,
    TraitRuleCatalog,
    TraitsConfig,
)


def trait_rule_from_dict(data: dict[str, Any]) -> TraitRule:
    """Deserialize a TraitRule from a dict."""
    outcome = TraitOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return TraitRule(
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


def traits_config_from_dict(data: dict[str, Any]) -> TraitsConfig:
    """Deserialize a TraitsConfig from a dict."""
    return TraitsConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def trait_rule_catalog_from_dict(data: dict[str, Any]) -> TraitRuleCatalog:
    """Deserialize a TraitRuleCatalog from a dict."""
    rules = tuple(
        trait_rule_from_dict(r) for r in data.get("rules", [])
    )
    return TraitRuleCatalog(rules=rules)


def result_to_dict(catalog: TraitRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a TraitRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: TraitRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a TraitRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: TraitRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a TraitRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

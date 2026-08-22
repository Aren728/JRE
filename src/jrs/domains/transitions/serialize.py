"""Transitions domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    TransitionConfig,
    TransitionOutcomeTaxonomy,
    TransitionRule,
    TransitionRuleCatalog,
)


def transition_rule_from_dict(data: dict[str, Any]) -> TransitionRule:
    """Deserialize a TransitionRule from a dict."""
    outcome = TransitionOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return TransitionRule(
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


def transition_config_from_dict(data: dict[str, Any]) -> TransitionConfig:
    """Deserialize a TransitionConfig from a dict."""
    return TransitionConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def transition_rule_catalog_from_dict(
    data: dict[str, Any],
) -> TransitionRuleCatalog:
    """Deserialize a TransitionRuleCatalog from a dict."""
    rules = tuple(
        transition_rule_from_dict(r) for r in data.get("rules", [])
    )
    return TransitionRuleCatalog(rules=rules)


def result_to_dict(catalog: TransitionRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a TransitionRuleCatalog."""
    return catalog.to_dict()


def result_to_json(
    catalog: TransitionRuleCatalog, *, indent: int | None = None,
) -> str:
    """Deterministic JSON serialization of a TransitionRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: TransitionRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a TransitionRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

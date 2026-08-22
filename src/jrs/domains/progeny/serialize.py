"""Progeny domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    ProgenyConfig,
    ProgenyOutcomeTaxonomy,
    ProgenyRule,
    ProgenyRuleCatalog,
)


def progeny_rule_from_dict(data: dict[str, Any]) -> ProgenyRule:
    """Deserialize a ProgenyRule from a dict."""
    outcome = ProgenyOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return ProgenyRule(
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


def progeny_config_from_dict(data: dict[str, Any]) -> ProgenyConfig:
    """Deserialize a ProgenyConfig from a dict."""
    return ProgenyConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def progeny_rule_catalog_from_dict(data: dict[str, Any]) -> ProgenyRuleCatalog:
    """Deserialize a ProgenyRuleCatalog from a dict."""
    rules = tuple(
        progeny_rule_from_dict(r) for r in data.get("rules", [])
    )
    return ProgenyRuleCatalog(rules=rules)


def result_to_dict(catalog: ProgenyRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a ProgenyRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: ProgenyRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a ProgenyRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: ProgenyRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a ProgenyRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

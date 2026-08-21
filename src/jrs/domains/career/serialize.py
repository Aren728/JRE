"""Career domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    CareerConfig,
    CareerOutcomeTaxonomy,
    CareerRule,
    CareerRuleCatalog,
)


def career_rule_from_dict(data: dict[str, Any]) -> CareerRule:
    """Deserialize a CareerRule from a dict."""
    outcome = CareerOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return CareerRule(
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


def career_config_from_dict(data: dict[str, Any]) -> CareerConfig:
    """Deserialize a CareerConfig from a dict."""
    return CareerConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def career_rule_catalog_from_dict(data: dict[str, Any]) -> CareerRuleCatalog:
    """Deserialize a CareerRuleCatalog from a dict."""
    rules = tuple(
        career_rule_from_dict(r) for r in data.get("rules", [])
    )
    return CareerRuleCatalog(rules=rules)


def result_to_dict(catalog: CareerRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a CareerRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: CareerRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a CareerRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: CareerRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a CareerRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

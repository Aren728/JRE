"""Spirituality domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    SpiritualityConfig,
    SpiritualityOutcomeTaxonomy,
    SpiritualityRule,
    SpiritualityRuleCatalog,
)


def spirituality_rule_from_dict(data: dict[str, Any]) -> SpiritualityRule:
    """Deserialize a SpiritualityRule from a dict."""
    outcome = SpiritualityOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return SpiritualityRule(
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


def spirituality_config_from_dict(data: dict[str, Any]) -> SpiritualityConfig:
    """Deserialize a SpiritualityConfig from a dict."""
    return SpiritualityConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def spirituality_rule_catalog_from_dict(
    data: dict[str, Any],
) -> SpiritualityRuleCatalog:
    """Deserialize a SpiritualityRuleCatalog from a dict."""
    rules = tuple(
        spirituality_rule_from_dict(r) for r in data.get("rules", [])
    )
    return SpiritualityRuleCatalog(rules=rules)


def result_to_dict(catalog: SpiritualityRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a SpiritualityRuleCatalog."""
    return catalog.to_dict()


def result_to_json(
    catalog: SpiritualityRuleCatalog, *, indent: int | None = None,
) -> str:
    """Deterministic JSON serialization of a SpiritualityRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: SpiritualityRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a SpiritualityRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

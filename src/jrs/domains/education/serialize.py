"""Education domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    EducationConfig,
    EducationOutcomeTaxonomy,
    EducationRule,
    EducationRuleCatalog,
)


def education_rule_from_dict(data: dict[str, Any]) -> EducationRule:
    """Deserialize an EducationRule from a dict."""
    outcome = EducationOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return EducationRule(
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


def education_config_from_dict(data: dict[str, Any]) -> EducationConfig:
    """Deserialize an EducationConfig from a dict."""
    return EducationConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def education_rule_catalog_from_dict(data: dict[str, Any]) -> EducationRuleCatalog:
    """Deserialize an EducationRuleCatalog from a dict."""
    rules = tuple(
        education_rule_from_dict(r) for r in data.get("rules", [])
    )
    return EducationRuleCatalog(rules=rules)


def result_to_dict(catalog: EducationRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of an EducationRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: EducationRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of an EducationRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: EducationRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of an EducationRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

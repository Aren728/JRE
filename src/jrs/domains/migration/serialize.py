"""Migration domain deterministic serialization."""

from __future__ import annotations

import json
from typing import Any

from jrs.evidence.models import EvidenceDirection, EvidenceStrength

from .models import (
    MigrationConfig,
    MigrationOutcomeTaxonomy,
    MigrationRule,
    MigrationRuleCatalog,
)


def migration_rule_from_dict(data: dict[str, Any]) -> MigrationRule:
    """Deserialize a MigrationRule from a dict."""
    outcome = MigrationOutcomeTaxonomy(data["outcome"])
    direction = EvidenceDirection(data.get("direction", "SUPPORT"))
    strength = EvidenceStrength(data.get("strength", "MODERATE"))

    return MigrationRule(
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


def migration_config_from_dict(data: dict[str, Any]) -> MigrationConfig:
    """Deserialize a MigrationConfig from a dict."""
    return MigrationConfig(
        version=data.get("version", "1.0"),
        source_id=data.get("source_id", "BPHS"),
        default_strength=data.get("default_strength", "MODERATE"),
    )


def migration_rule_catalog_from_dict(data: dict[str, Any]) -> MigrationRuleCatalog:
    """Deserialize a MigrationRuleCatalog from a dict."""
    rules = tuple(
        migration_rule_from_dict(r) for r in data.get("rules", [])
    )
    return MigrationRuleCatalog(rules=rules)


def result_to_dict(catalog: MigrationRuleCatalog) -> dict[str, Any]:
    """Deterministic dict serialization of a MigrationRuleCatalog."""
    return catalog.to_dict()


def result_to_json(catalog: MigrationRuleCatalog, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a MigrationRuleCatalog."""
    d = result_to_dict(catalog)
    return json.dumps(d, indent=indent, sort_keys=True, ensure_ascii=True)


def rule_to_json(rule: MigrationRule, *, indent: int | None = None) -> str:
    """Deterministic JSON serialization of a MigrationRule."""
    return json.dumps(rule.to_dict(), indent=indent, sort_keys=True, ensure_ascii=True)

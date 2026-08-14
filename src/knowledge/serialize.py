"""JSON serialization for the knowledge layer (SPEC §15, DATA-CONTRACT §0/§9).

Conventions identical to JRE-002/JRE-003: UTF-8, snake_case keys, enums as
their string values, tuples as arrays, ``None`` as ``null``, floats via
Python's round-trip repr, ``-0.0 -> 0.0``. ``fact_snapshot`` is opaque: it
round-trips as the JSON object the caller supplied.
"""

from __future__ import annotations

import json
from typing import Any

from .models import (
    KnowledgeConfig,
    ProvenanceRef,
    RuleCondition,
    RuleDomain,
    RuleQuery,
    model_to_dict,
)
from .schema import parse_path


def result_to_dict(result: Any) -> Any:
    """Serialize any knowledge result object (or tuple of objects) to a dict."""
    return model_to_dict(result)


def result_to_json(result: Any) -> str:
    """Serialize a knowledge result to JSON (exact float round-trip)."""
    return json.dumps(result_to_dict(result))


def config_from_dict(data: dict[str, Any]) -> KnowledgeConfig:
    """Deserialize a ``KnowledgeConfig`` from a JSON-shaped dict."""
    rule_pins = data.get("rule_catalog_versions") or {}
    completeness_raw = data.get("provenance_completeness") or {}

    def _opt_str(key: str) -> str | None:
        value = data.get(key)
        return None if value is None or value == "" else str(value)

    from .models import ConflictPolicy

    config = KnowledgeConfig(
        default_profile_id=str(data.get("default_profile_id", "bphs-classical")),
        default_conflict_policy=ConflictPolicy(
            data.get("default_conflict_policy", ConflictPolicy.FIRST_WINS.value)
        ),
        source_catalog_version=_opt_str("source_catalog_version"),
        rule_catalog_versions={str(k): str(v) for k, v in rule_pins.items()},
        profile_catalog_version=_opt_str("profile_catalog_version"),
        facts_catalog_version=_opt_str("facts_catalog_version"),
        enforce_provenance=bool(data.get("enforce_provenance", True)),
        verify_checksums=bool(data.get("verify_checksums", True)),
        max_rules_per_synthesis=int(data.get("max_rules_per_synthesis", 200)),
        weight_authority_coeff=float(data.get("weight_authority_coeff", 1.0)),
        weight_specificity_coeff=float(data.get("weight_specificity_coeff", 0.5)),
        weight_source_rank_coeff=float(data.get("weight_source_rank_coeff", 0.05)),
        credibility_authority_weight=float(data.get("credibility_authority_weight", 0.55)),
        credibility_provenance_weight=float(data.get("credibility_provenance_weight", 0.30)),
        credibility_specificity_weight=float(data.get("credibility_specificity_weight", 0.15)),
        provenance_completeness={str(key): float(value) for key, value in completeness_raw.items()},
    )
    from .config import validate

    return validate(config)


def provenance_from_dict(data: dict[str, Any]) -> ProvenanceRef:
    """Deserialize a ``ProvenanceRef`` from a JSON-shaped dict."""

    def _opt(key: str) -> str | None:
        value = data.get(key)
        return None if value is None else str(value)

    return ProvenanceRef(
        source_id=str(data["source_id"]),
        chapter=_opt("chapter"),
        verse_start=_opt("verse_start"),
        verse_end=_opt("verse_end"),
        edition_id=_opt("edition_id"),
        commentary=_opt("commentary"),
    )


def rule_query_from_dict(data: dict[str, Any]) -> RuleQuery:
    """Deserialize a ``RuleQuery`` from a JSON-shaped dict."""
    domain_raw = data.get("domain")
    snapshot = data.get("fact_snapshot")
    if not isinstance(snapshot, dict):
        raise ValueError("RuleQuery.fact_snapshot must be an object")
    return RuleQuery(
        domain=None if domain_raw is None else RuleDomain(str(domain_raw)),
        fact_snapshot=snapshot,
        profile_id=data.get("profile_id"),
        include_suppressed=bool(data.get("include_suppressed", False)),
    )


def condition_from_dict(data: dict[str, Any]) -> RuleCondition:
    """Deserialize a ``RuleCondition`` (used by tests/tools)."""
    from .rules import _condition_from_dict

    return _condition_from_dict(data)


def validate_path(path: str) -> None:
    """Validate a fact-vocabulary path (exposed for catalog tooling)."""
    parse_path(path)

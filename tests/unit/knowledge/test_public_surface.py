"""Static gate 1: ``knowledge.__all__`` matches the public-surface allow-list.

The explicit ``__all__`` in ``src/knowledge/__init__.py`` is the only public
surface future engines rely on (SPEC §1, ADR-011). Any change here is a
versioned decision.
"""

from __future__ import annotations

import knowledge

EXPECTED_PUBLIC_API = {
    # facade
    "KnowledgeService",
    # config
    "KnowledgeConfig",
    "ConflictPolicy",
    "load_config",
    "validate_config",
    # enums
    "SourceStatus",
    "RuleStatus",
    "RuleDomain",
    "ConditionOp",
    "ConditionCombiner",
    # models
    "Source",
    "Edition",
    "ProvenanceRef",
    "RuleCondition",
    "RuleConclusion",
    "Rule",
    "ResolvedRule",
    "TraditionProfile",
    "RuleQuery",
    "ConflictRecord",
    "SearchMetadata",
    "SynthesisResult",
    # registries / catalog readers
    "SourceRegistry",
    "ProfileRegistry",
    "RuleRegistry",
    "FactsRegistry",
    "validate_passthrough_config",
    "SOURCE_CATALOG_VERSION",
    "PROFILE_CATALOG_VERSION",
    "FACTS_CATALOG_VERSION",
    "load_sources",
    "load_profiles",
    "load_rule_catalogs",
    "load_facts",
    # classical facts layer (ADR-012)
    "enrich_snapshot",
    "derive_nature",
    "derive_dignity",
    "derive_combusted",
    "derive_aspect_strength",
    # schema / vocabulary
    "FACT_VOCABULARY",
    "FACT_VOCABULARY_VERSION",
    "DOMAIN_REQUIREMENTS",
    "parse_path",
    "validate_condition",
    "evaluate",
    "evaluate_atom",
    # provenance
    "canonical_provenance",
    "completeness_level",
    "resolve_bibliography",
    "provenance_strings",
    "provenance_index",
    # precedence / resolution
    "precedence_key",
    "semver_tuple",
    "order_rules",
    "effective_weight",
    "credibility",
    "credibility_summary",
    "ExceptionResolution",
    "resolve_exceptions",
    "conflict_pairs",
    "apply_conflict_policy",
    # synthesis
    "normalize_snapshot",
    "domains_in_scope",
    "require_sections",
    "ALGORITHM_NAME",
    # serialization
    "result_to_json",
    "result_to_dict",
    "config_from_dict",
    "rule_query_from_dict",
    "provenance_from_dict",
    # errors
    "KnowledgeError",
    "InvalidConfigError",
    "UnknownSourceError",
    "UnknownEditionError",
    "UnknownProfileError",
    "RuleSchemaError",
    "ProvenanceError",
    "CatalogIntegrityError",
    "ConflictResolutionError",
    "SynthesisError",
}


def test_public_api_allow_list():
    assert set(knowledge.__all__) == EXPECTED_PUBLIC_API
    assert len(knowledge.__all__) == len(EXPECTED_PUBLIC_API)


def test_version_matches_spec():
    assert knowledge.__version__ == "0.5.0"

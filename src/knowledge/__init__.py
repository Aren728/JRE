"""JRE-004 Classical Knowledge & Rule Engine — deterministic classical rules.

A machine-readable knowledge base of classical Jyotish sources and rules with
full provenance, consumed by future interpretation engines through
``KnowledgeService.synthesize`` (ADR-011). Rules are data, never code
(ADR-009); sources are bibliographic provenance, never prose (ADR-008);
synthesis always runs inside a named, versioned tradition profile (ADR-010).

Boundaries (enforced by static gates):

- imports only stdlib and the ``jyotish`` public API (ADR-007);
- never imports ``astronomy``/``swisseph``/interpretation layers;
- no network, no personal data, no prediction code paths.

``__version__`` mirrors the Specialist implementation spec (v0.4.0).
"""

from .config import load_config
from .config import validate as validate_config
from .errors import (
    CatalogIntegrityError,
    ConflictResolutionError,
    InvalidConfigError,
    KnowledgeError,
    ProvenanceError,
    RuleSchemaError,
    SynthesisError,
    UnknownEditionError,
    UnknownProfileError,
    UnknownSourceError,
)
from .facts import (
    FACTS_CATALOG_VERSION,
    FactsRegistry,
    derive_aspect_strength,
    derive_combusted,
    derive_dignity,
    derive_nature,
    enrich_snapshot,
    load_facts,
)
from .models import (
    ConditionCombiner,
    ConditionOp,
    ConflictPolicy,
    ConflictRecord,
    Edition,
    KnowledgeConfig,
    ProvenanceRef,
    ResolvedRule,
    Rule,
    RuleConclusion,
    RuleCondition,
    RuleDomain,
    RuleQuery,
    RuleStatus,
    SearchMetadata,
    Source,
    SourceStatus,
    SynthesisResult,
    TraditionProfile,
)
from .precedence import (
    credibility,
    credibility_summary,
    effective_weight,
    order_rules,
    precedence_key,
    semver_tuple,
)
from .provenance import (
    canonical_provenance,
    completeness_level,
    provenance_index,
    provenance_strings,
    resolve_bibliography,
)
from .resolution import (
    ExceptionResolution,
    apply_conflict_policy,
    conflict_pairs,
    resolve_exceptions,
)
from .rules import RuleRegistry, load_rule_catalogs
from .schema import (
    DOMAIN_REQUIREMENTS,
    FACT_VOCABULARY,
    FACT_VOCABULARY_VERSION,
    evaluate,
    evaluate_atom,
    parse_path,
    validate_condition,
)
from .serialize import (
    config_from_dict,
    provenance_from_dict,
    result_to_dict,
    result_to_json,
    rule_query_from_dict,
)
from .service import KnowledgeService
from .sources import (
    SOURCE_CATALOG_VERSION,
    SourceRegistry,
    load_sources,
)
from .synthesis import (
    ALGORITHM_NAME,
    domains_in_scope,
    normalize_snapshot,
    require_sections,
)
from .traditions import (
    PROFILE_CATALOG_VERSION,
    ProfileRegistry,
    load_profiles,
    validate_passthrough_config,
)

__version__ = "0.5.0"

__all__ = [
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
]

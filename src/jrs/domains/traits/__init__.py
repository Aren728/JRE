"""JRS Traits/Birth Signature Interpretation Domain — Classical Rules & Evidence Mapping.

This is a JRS (interpretation) domain that consumes deterministic facts
from JRE-027 (BirthSignature) and outputs trait assessments mapped to
classical TraitOutcomeTaxonomy categories.

Public API
----------
- ``TraitsDomainService``       – rule loader and fact evaluator
- ``TraitOutcomeTaxonomy``      – trait outcome categories
- ``TraitRule``                 – a single classical rule
- ``TraitRuleCatalog``          – complete rule catalog
- ``TraitsConfig``              – domain configuration
- ``load_traits_config``        – TOML config loader
- ``load_traits_rules``         – rule loader
- ``evaluate_facts``            – fact evaluation logic
"""

from __future__ import annotations

from .config import load_traits_config, load_traits_rules
from .errors import (
    InvalidFactError,
    InvalidTraitsConfigError,
    RuleEvaluationError,
    TraitsDomainError,
)
from .models import (
    TraitOutcomeTaxonomy,
    TraitRule,
    TraitRuleCatalog,
    TraitsConfig,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    result_to_dict,
    result_to_json,
    rule_to_json,
    trait_rule_catalog_from_dict,
    trait_rule_from_dict,
    traits_config_from_dict,
)
from .service import TraitsDomainService

__all__: tuple[str, ...] = (
    # Errors
    "TraitsDomainError",
    "InvalidTraitsConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "TraitOutcomeTaxonomy",
    # Models
    "TraitRule",
    "TraitRuleCatalog",
    "TraitsConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_traits_config",
    "load_traits_rules",
    # Serialize
    "trait_rule_from_dict",
    "traits_config_from_dict",
    "trait_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "TraitsDomainService",
)

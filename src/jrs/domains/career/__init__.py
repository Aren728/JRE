"""JRS Career/Profession Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``CareerDomainService``        – rule loader and fact evaluator
- ``CareerOutcomeTaxonomy``      – specific career outcome categories
- ``CareerRule``                 – a single classical rule
- ``CareerRuleCatalog``          – complete rule catalog
- ``CareerConfig``               – domain configuration
- ``load_career_config``         – TOML config loader
- ``load_career_rules``          – rule loader
- ``evaluate_facts``             – fact evaluation logic
"""

from __future__ import annotations

from .config import load_career_config, load_career_rules
from .errors import (
    CareerDomainError,
    InvalidCareerConfigError,
    InvalidFactError,
    RuleEvaluationError,
)
from .models import (
    CareerConfig,
    CareerOutcomeTaxonomy,
    CareerRule,
    CareerRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    career_config_from_dict,
    career_rule_catalog_from_dict,
    career_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import CareerDomainService

__all__: tuple[str, ...] = (
    # Errors
    "CareerDomainError",
    "InvalidCareerConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "CareerOutcomeTaxonomy",
    # Models
    "CareerRule",
    "CareerRuleCatalog",
    "CareerConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_career_config",
    "load_career_rules",
    # Serialize
    "career_rule_from_dict",
    "career_config_from_dict",
    "career_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "CareerDomainService",
)

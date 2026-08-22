"""JRS Litigation/Conflict Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``LitigationDomainService``     – rule loader and fact evaluator
- ``LitigationOutcomeTaxonomy``   – specific litigation outcome categories
- ``LitigationRule``              – a single classical rule
- ``LitigationRuleCatalog``       – complete rule catalog
- ``LitigationConfig``            – domain configuration
- ``load_litigation_config``      – TOML config loader
- ``load_litigation_rules``       – rule loader
- ``evaluate_facts``              – fact evaluation logic
"""

from __future__ import annotations

from .config import load_litigation_config, load_litigation_rules
from .errors import (
    InvalidFactError,
    InvalidLitigationConfigError,
    LitigationDomainError,
    RuleEvaluationError,
)
from .models import (
    LitigationConfig,
    LitigationOutcomeTaxonomy,
    LitigationRule,
    LitigationRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    litigation_config_from_dict,
    litigation_rule_catalog_from_dict,
    litigation_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import LitigationDomainService

__all__: tuple[str, ...] = (
    # Errors
    "LitigationDomainError",
    "InvalidLitigationConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "LitigationOutcomeTaxonomy",
    # Models
    "LitigationRule",
    "LitigationRuleCatalog",
    "LitigationConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_litigation_config",
    "load_litigation_rules",
    # Serialize
    "litigation_rule_from_dict",
    "litigation_config_from_dict",
    "litigation_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "LitigationDomainService",
)

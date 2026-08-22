"""JRS Business/Entrepreneurship Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``BusinessDomainService``     – rule loader and fact evaluator
- ``BusinessOutcomeTaxonomy``   – specific business outcome categories
- ``BusinessRule``              – a single classical rule
- ``BusinessRuleCatalog``       – complete rule catalog
- ``BusinessConfig``            – domain configuration
- ``load_business_config``      – TOML config loader
- ``load_business_rules``       – rule loader
- ``evaluate_facts``            – fact evaluation logic
"""

from __future__ import annotations

from .config import load_business_config, load_business_rules
from .errors import (
    BusinessDomainError,
    InvalidBusinessConfigError,
    InvalidFactError,
    RuleEvaluationError,
)
from .models import (
    BusinessConfig,
    BusinessOutcomeTaxonomy,
    BusinessRule,
    BusinessRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    business_config_from_dict,
    business_rule_catalog_from_dict,
    business_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import BusinessDomainService

__all__: tuple[str, ...] = (
    # Errors
    "BusinessDomainError",
    "InvalidBusinessConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "BusinessOutcomeTaxonomy",
    # Models
    "BusinessRule",
    "BusinessRuleCatalog",
    "BusinessConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_business_config",
    "load_business_rules",
    # Serialize
    "business_rule_from_dict",
    "business_config_from_dict",
    "business_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "BusinessDomainService",
)

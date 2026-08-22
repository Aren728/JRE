"""JRS Property/Residence Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``PropertyDomainService``       – rule loader and fact evaluator
- ``PropertyOutcomeTaxonomy``     – specific property outcome categories
- ``PropertyRule``                – a single classical rule
- ``PropertyRuleCatalog``         – complete rule catalog
- ``PropertyConfig``              – domain configuration
- ``load_property_config``        – TOML config loader
- ``load_property_rules``         – rule loader
- ``evaluate_facts``              – fact evaluation logic
"""

from __future__ import annotations

from .config import load_property_config, load_property_rules
from .errors import (
    InvalidFactError,
    InvalidPropertyConfigError,
    PropertyDomainError,
    RuleEvaluationError,
)
from .models import (
    PropertyConfig,
    PropertyOutcomeTaxonomy,
    PropertyRule,
    PropertyRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    property_config_from_dict,
    property_rule_catalog_from_dict,
    property_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import PropertyDomainService

__all__: tuple[str, ...] = (
    # Errors
    "PropertyDomainError",
    "InvalidPropertyConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "PropertyOutcomeTaxonomy",
    # Models
    "PropertyRule",
    "PropertyRuleCatalog",
    "PropertyConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_property_config",
    "load_property_rules",
    # Serialize
    "property_rule_from_dict",
    "property_config_from_dict",
    "property_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "PropertyDomainService",
)

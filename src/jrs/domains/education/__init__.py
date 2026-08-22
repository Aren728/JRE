"""JRS Education Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``EducationDomainService``      – rule loader and fact evaluator
- ``EducationOutcomeTaxonomy``    – specific education outcome categories
- ``EducationRule``               – a single classical rule
- ``EducationRuleCatalog``        – complete rule catalog
- ``EducationConfig``             – domain configuration
- ``load_education_config``       – TOML config loader
- ``load_education_rules``        – rule loader
- ``evaluate_facts``              – fact evaluation logic
"""

from __future__ import annotations

from .config import load_education_config, load_education_rules
from .errors import (
    EducationDomainError,
    InvalidEducationConfigError,
    InvalidFactError,
    RuleEvaluationError,
)
from .models import (
    EducationConfig,
    EducationOutcomeTaxonomy,
    EducationRule,
    EducationRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    education_config_from_dict,
    education_rule_catalog_from_dict,
    education_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import EducationDomainService

__all__: tuple[str, ...] = (
    # Errors
    "EducationDomainError",
    "InvalidEducationConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "EducationOutcomeTaxonomy",
    # Models
    "EducationRule",
    "EducationRuleCatalog",
    "EducationConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_education_config",
    "load_education_rules",
    # Serialize
    "education_rule_from_dict",
    "education_config_from_dict",
    "education_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "EducationDomainService",
)

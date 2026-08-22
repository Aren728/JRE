"""JRS Health/Vitality Domain — Traditional Constitution & Vitality Indicators.

SAFETY CONSTRAINT: This module maps traditional astrological indicators of
physical constitution and vitality. It does NOT generate, contain, or imply
medical diagnoses, disease names, surgical indicators, or death predictions.
All terminology is strictly limited to constitutional vitality assessments.

Public API
----------
- ``HealthDomainService``     – rule loader and fact evaluator
- ``HealthOutcomeTaxonomy``   – specific vitality outcome categories
- ``HealthRule``              – a single classical rule
- ``HealthRuleCatalog``       – complete rule catalog
- ``HealthConfig``            – domain configuration
- ``load_health_config``      – TOML config loader
- ``load_health_rules``       – rule loader
- ``evaluate_facts``          – fact evaluation logic
"""

from __future__ import annotations

from .config import load_health_config, load_health_rules
from .errors import (
    HealthDomainError,
    InvalidFactError,
    InvalidHealthConfigError,
    RuleEvaluationError,
)
from .models import (
    HealthConfig,
    HealthOutcomeTaxonomy,
    HealthRule,
    HealthRuleCatalog,
    _validate_no_medical_terms,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    health_config_from_dict,
    health_rule_catalog_from_dict,
    health_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import HealthDomainService

__all__: tuple[str, ...] = (
    # Safety
    "_validate_no_medical_terms",
    # Errors
    "HealthDomainError",
    "InvalidHealthConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "HealthOutcomeTaxonomy",
    # Models
    "HealthRule",
    "HealthRuleCatalog",
    "HealthConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_health_config",
    "load_health_rules",
    # Serialize
    "health_rule_from_dict",
    "health_config_from_dict",
    "health_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "HealthDomainService",
)

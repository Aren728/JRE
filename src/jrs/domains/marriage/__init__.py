"""JRS Marriage/Relationship Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``MarriageDomainService``      – rule loader and fact evaluator
- ``MarriageOutcomeTaxonomy``    – specific marriage outcome categories
- ``MarriageRule``               – a single classical rule
- ``MarriageRuleCatalog``        – complete rule catalog
- ``MarriageConfig``             – domain configuration
- ``load_marriage_config``       – TOML config loader
- ``load_marriage_rules``        – rule loader
- ``evaluate_facts``             – fact evaluation logic
"""

from __future__ import annotations

from .config import load_marriage_config, load_marriage_rules
from .errors import (
    InvalidFactError,
    InvalidMarriageConfigError,
    MarriageDomainError,
    RuleEvaluationError,
)
from .models import (
    MarriageConfig,
    MarriageOutcomeTaxonomy,
    MarriageRule,
    MarriageRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    marriage_config_from_dict,
    marriage_rule_catalog_from_dict,
    marriage_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import MarriageDomainService

__all__: tuple[str, ...] = (
    # Errors
    "MarriageDomainError",
    "InvalidMarriageConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "MarriageOutcomeTaxonomy",
    # Models
    "MarriageRule",
    "MarriageRuleCatalog",
    "MarriageConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_marriage_config",
    "load_marriage_rules",
    # Serialize
    "marriage_rule_from_dict",
    "marriage_config_from_dict",
    "marriage_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "MarriageDomainService",
)

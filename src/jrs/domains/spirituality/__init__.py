"""JRS Spirituality/Renunciation Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``SpiritualityDomainService``    – rule loader and fact evaluator
- ``SpiritualityOutcomeTaxonomy``  – specific spirituality outcome categories
- ``SpiritualityRule``             – a single classical rule
- ``SpiritualityRuleCatalog``      – complete rule catalog
- ``SpiritualityConfig``           – domain configuration
- ``load_spirituality_config``     – TOML config loader
- ``load_spirituality_rules``      – rule loader
- ``evaluate_facts``               – fact evaluation logic
"""

from __future__ import annotations

from .config import load_spirituality_config, load_spirituality_rules
from .errors import (
    InvalidFactError,
    InvalidSpiritualityConfigError,
    RuleEvaluationError,
    SpiritualityDomainError,
)
from .models import (
    SpiritualityConfig,
    SpiritualityOutcomeTaxonomy,
    SpiritualityRule,
    SpiritualityRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    result_to_dict,
    result_to_json,
    rule_to_json,
    spirituality_config_from_dict,
    spirituality_rule_catalog_from_dict,
    spirituality_rule_from_dict,
)
from .service import SpiritualityDomainService

__all__: tuple[str, ...] = (
    # Errors
    "SpiritualityDomainError",
    "InvalidSpiritualityConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "SpiritualityOutcomeTaxonomy",
    # Models
    "SpiritualityRule",
    "SpiritualityRuleCatalog",
    "SpiritualityConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_spirituality_config",
    "load_spirituality_rules",
    # Serialize
    "spirituality_rule_from_dict",
    "spirituality_config_from_dict",
    "spirituality_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "SpiritualityDomainService",
)

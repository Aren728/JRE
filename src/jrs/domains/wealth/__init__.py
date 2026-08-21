"""JRS Wealth/Finances Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``WealthDomainService``        – rule loader and fact evaluator
- ``WealthOutcomeTaxonomy``      – specific wealth outcome categories
- ``WealthRule``                 – a single classical rule
- ``WealthRuleCatalog``          – complete rule catalog
- ``WealthConfig``               – domain configuration
- ``load_wealth_config``         – TOML config loader
- ``load_wealth_rules``          – rule loader
- ``evaluate_facts``             – fact evaluation logic
"""

from __future__ import annotations

from .config import load_wealth_config, load_wealth_rules
from .errors import (
    InvalidFactError,
    InvalidWealthConfigError,
    RuleEvaluationError,
    WealthDomainError,
)
from .models import (
    WealthConfig,
    WealthOutcomeTaxonomy,
    WealthRule,
    WealthRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    result_to_dict,
    result_to_json,
    rule_to_json,
    wealth_config_from_dict,
    wealth_rule_catalog_from_dict,
    wealth_rule_from_dict,
)
from .service import WealthDomainService

__all__: tuple[str, ...] = (
    # Errors
    "WealthDomainError",
    "InvalidWealthConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "WealthOutcomeTaxonomy",
    # Models
    "WealthRule",
    "WealthRuleCatalog",
    "WealthConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_wealth_config",
    "load_wealth_rules",
    # Serialize
    "wealth_rule_from_dict",
    "wealth_config_from_dict",
    "wealth_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "WealthDomainService",
)

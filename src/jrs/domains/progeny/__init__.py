"""JRS Children/Progeny Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``ProgenyDomainService``       – rule loader and fact evaluator
- ``ProgenyOutcomeTaxonomy``     – specific progeny outcome categories
- ``ProgenyRule``                – a single classical rule
- ``ProgenyRuleCatalog``         – complete rule catalog
- ``ProgenyConfig``              – domain configuration
- ``load_progeny_config``        – TOML config loader
- ``load_progeny_rules``         – rule loader
- ``evaluate_facts``             – fact evaluation logic
"""

from __future__ import annotations

from .config import load_progeny_config, load_progeny_rules
from .errors import (
    InvalidFactError,
    InvalidProgenyConfigError,
    ProgenyDomainError,
    RuleEvaluationError,
)
from .models import (
    ProgenyConfig,
    ProgenyOutcomeTaxonomy,
    ProgenyRule,
    ProgenyRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    progeny_config_from_dict,
    progeny_rule_catalog_from_dict,
    progeny_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import ProgenyDomainService

__all__: tuple[str, ...] = (
    # Errors
    "ProgenyDomainError",
    "InvalidProgenyConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "ProgenyOutcomeTaxonomy",
    # Models
    "ProgenyRule",
    "ProgenyRuleCatalog",
    "ProgenyConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_progeny_config",
    "load_progeny_rules",
    # Serialize
    "progeny_rule_from_dict",
    "progeny_config_from_dict",
    "progeny_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "ProgenyDomainService",
)

"""JRS Major Life Transitions Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``TransitionsDomainService``    – rule loader and fact evaluator
- ``TransitionOutcomeTaxonomy``  – specific transition outcome categories
- ``TransitionRule``             – a single classical rule
- ``TransitionRuleCatalog``      – complete rule catalog
- ``TransitionConfig``           – domain configuration
- ``load_transitions_config``    – TOML config loader
- ``load_transitions_rules``     – rule loader
- ``evaluate_facts``             – fact evaluation logic
"""

from __future__ import annotations

from .config import load_transitions_config, load_transitions_rules
from .errors import (
    InvalidFactError,
    InvalidTransitionsConfigError,
    RuleEvaluationError,
    TransitionsDomainError,
)
from .models import (
    TransitionConfig,
    TransitionOutcomeTaxonomy,
    TransitionRule,
    TransitionRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    result_to_dict,
    result_to_json,
    rule_to_json,
    transition_config_from_dict,
    transition_rule_catalog_from_dict,
    transition_rule_from_dict,
)
from .service import TransitionsDomainService

__all__: tuple[str, ...] = (
    # Errors
    "TransitionsDomainError",
    "InvalidTransitionsConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "TransitionOutcomeTaxonomy",
    # Models
    "TransitionRule",
    "TransitionRuleCatalog",
    "TransitionConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_transitions_config",
    "load_transitions_rules",
    # Serialize
    "transition_rule_from_dict",
    "transition_config_from_dict",
    "transition_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "TransitionsDomainService",
)

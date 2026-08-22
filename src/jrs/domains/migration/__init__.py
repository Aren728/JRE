"""JRS Foreign Travel/Migration Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``MigrationDomainService``      – rule loader and fact evaluator
- ``MigrationOutcomeTaxonomy``    – specific migration outcome categories
- ``MigrationRule``               – a single classical rule
- ``MigrationRuleCatalog``        – complete rule catalog
- ``MigrationConfig``             – domain configuration
- ``load_migration_config``       – TOML config loader
- ``load_migration_rules``        – rule loader
- ``evaluate_facts``              – fact evaluation logic
"""

from __future__ import annotations

from .config import load_migration_config, load_migration_rules
from .errors import (
    InvalidFactError,
    InvalidMigrationConfigError,
    MigrationDomainError,
    RuleEvaluationError,
)
from .models import (
    MigrationConfig,
    MigrationOutcomeTaxonomy,
    MigrationRule,
    MigrationRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    migration_config_from_dict,
    migration_rule_catalog_from_dict,
    migration_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import MigrationDomainService

__all__: tuple[str, ...] = (
    # Errors
    "MigrationDomainError",
    "InvalidMigrationConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "MigrationOutcomeTaxonomy",
    # Models
    "MigrationRule",
    "MigrationRuleCatalog",
    "MigrationConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_migration_config",
    "load_migration_rules",
    # Serialize
    "migration_rule_from_dict",
    "migration_config_from_dict",
    "migration_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "MigrationDomainService",
)

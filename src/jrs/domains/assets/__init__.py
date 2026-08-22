"""JRS Assets/Vehicles Domain — Classical Rules & Evidence Mapping.

Public API
----------
- ``AssetsDomainService``     – rule loader and fact evaluator
- ``AssetsOutcomeTaxonomy``   – specific assets outcome categories
- ``AssetsRule``              – a single classical rule
- ``AssetsRuleCatalog``       – complete rule catalog
- ``AssetsConfig``            – domain configuration
- ``load_assets_config``      – TOML config loader
- ``load_assets_rules``       – rule loader
- ``evaluate_facts``          – fact evaluation logic
"""

from __future__ import annotations

from .config import load_assets_config, load_assets_rules
from .errors import (
    AssetsDomainError,
    InvalidAssetsConfigError,
    InvalidFactError,
    RuleEvaluationError,
)
from .models import (
    AssetsConfig,
    AssetsOutcomeTaxonomy,
    AssetsRule,
    AssetsRuleCatalog,
    evaluate_condition,
    evaluate_facts,
    evaluate_rule,
)
from .serialize import (
    assets_config_from_dict,
    assets_rule_catalog_from_dict,
    assets_rule_from_dict,
    result_to_dict,
    result_to_json,
    rule_to_json,
)
from .service import AssetsDomainService

__all__: tuple[str, ...] = (
    # Errors
    "AssetsDomainError",
    "InvalidAssetsConfigError",
    "InvalidFactError",
    "RuleEvaluationError",
    # Enums
    "AssetsOutcomeTaxonomy",
    # Models
    "AssetsRule",
    "AssetsRuleCatalog",
    "AssetsConfig",
    "evaluate_condition",
    "evaluate_rule",
    "evaluate_facts",
    # Config
    "load_assets_config",
    "load_assets_rules",
    # Serialize
    "assets_rule_from_dict",
    "assets_config_from_dict",
    "assets_rule_catalog_from_dict",
    "result_to_dict",
    "result_to_json",
    "rule_to_json",
    # Service
    "AssetsDomainService",
)

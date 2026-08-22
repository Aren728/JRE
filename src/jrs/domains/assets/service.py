"""Assets domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_assets_config, load_assets_rules
from .errors import InvalidFactError
from .models import (
    AssetsConfig,
    AssetsOutcomeTaxonomy,
    AssetsRule,
    AssetsRuleCatalog,
    evaluate_facts,
)


class AssetsDomainService:
    """Assets domain service: loads rules and evaluates facts.

    Usage::

        svc = AssetsDomainService()
        catalog = svc.load_assets_rules()
        records = svc.evaluate_assets_facts({"4th_lord_strong": True, ...})
    """

    def __init__(
        self,
        config: AssetsConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the assets domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_assets_config(config_path)
        self._rules: tuple[AssetsRule, ...] | None = None
        self._config_path = config_path

    def load_assets_rules(self) -> AssetsRuleCatalog:
        """Load and return the assets rule catalog from config.

        Returns:
            An AssetsRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_assets_rules(self._config_path)
        return AssetsRuleCatalog(rules=self._rules)

    def evaluate_assets_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the assets rule catalog.

        Takes a dictionary of JRE facts and emits EvidenceRecord objects
        linked to the correct AssetsOutcomeTaxonomy.

        Args:
            facts: Dictionary of JRE facts.

        Returns:
            A tuple of EvidenceRecord objects for all matching rules.

        Raises:
            InvalidFactError: If facts is not a valid dictionary.
        """
        if not isinstance(facts, dict):
            raise InvalidFactError("facts must be a dictionary")

        if self._rules is None:
            self._rules = load_assets_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: AssetsOutcomeTaxonomy,
    ) -> tuple[AssetsRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching AssetsRule objects.
        """
        if self._rules is None:
            self._rules = load_assets_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[AssetsOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique AssetsOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_assets_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> AssetsConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_assets_rules(self._config_path)
        return len(self._rules)

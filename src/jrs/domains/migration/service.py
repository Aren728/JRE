"""Migration domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_migration_config, load_migration_rules
from .errors import InvalidFactError
from .models import (
    MigrationConfig,
    MigrationOutcomeTaxonomy,
    MigrationRule,
    MigrationRuleCatalog,
    evaluate_facts,
)


class MigrationDomainService:
    """Migration domain service: loads rules and evaluates facts.

    Usage::

        svc = MigrationDomainService()
        catalog = svc.load_migration_rules()
        records = svc.evaluate_migration_facts({"rahu_in_12th": True, ...})
    """

    def __init__(
        self,
        config: MigrationConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the migration domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_migration_config(config_path)
        self._rules: tuple[MigrationRule, ...] | None = None
        self._config_path = config_path

    def load_migration_rules(self) -> MigrationRuleCatalog:
        """Load and return the migration rule catalog from config.

        Returns:
            A MigrationRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_migration_rules(self._config_path)
        return MigrationRuleCatalog(rules=self._rules)

    def evaluate_migration_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the migration rule catalog.

        Takes a dictionary of JRE facts (e.g., ``{"rahu_in_12th": True,
        "saturn_bala": 7.0}``) and emits EvidenceRecord objects linked to
        the correct MigrationOutcomeTaxonomy.

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
            self._rules = load_migration_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: MigrationOutcomeTaxonomy,
    ) -> tuple[MigrationRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching MigrationRule objects.
        """
        if self._rules is None:
            self._rules = load_migration_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[MigrationOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique MigrationOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_migration_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> MigrationConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_migration_rules(self._config_path)
        return len(self._rules)

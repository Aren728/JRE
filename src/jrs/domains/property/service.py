"""Property domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_property_config, load_property_rules
from .errors import InvalidFactError
from .models import (
    PropertyConfig,
    PropertyOutcomeTaxonomy,
    PropertyRule,
    PropertyRuleCatalog,
    evaluate_facts,
)


class PropertyDomainService:
    """Property domain service: loads rules and evaluates facts.

    Usage::

        svc = PropertyDomainService()
        catalog = svc.load_property_rules()
        records = svc.evaluate_property_facts({"4th_lord_strong": True, ...})
    """

    def __init__(
        self,
        config: PropertyConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the property domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_property_config(config_path)
        self._rules: tuple[PropertyRule, ...] | None = None
        self._config_path = config_path

    def load_property_rules(self) -> PropertyRuleCatalog:
        """Load and return the property rule catalog from config.

        Returns:
            A PropertyRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_property_rules(self._config_path)
        return PropertyRuleCatalog(rules=self._rules)

    def evaluate_property_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the property rule catalog.

        Takes a dictionary of JRE facts (e.g., ``{"4th_lord_strong": True,
        "mars_bala": 7.0}``) and emits EvidenceRecord objects linked to
        the correct PropertyOutcomeTaxonomy.

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
            self._rules = load_property_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: PropertyOutcomeTaxonomy,
    ) -> tuple[PropertyRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching PropertyRule objects.
        """
        if self._rules is None:
            self._rules = load_property_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[PropertyOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique PropertyOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_property_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> PropertyConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_property_rules(self._config_path)
        return len(self._rules)

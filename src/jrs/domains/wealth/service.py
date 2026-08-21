"""Wealth domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_wealth_config, load_wealth_rules
from .errors import InvalidFactError
from .models import (
    WealthConfig,
    WealthOutcomeTaxonomy,
    WealthRule,
    WealthRuleCatalog,
    evaluate_facts,
)


class WealthDomainService:
    """Wealth domain service: loads rules and evaluates facts.

    Usage::

        svc = WealthDomainService()
        catalog = svc.load_wealth_rules()
        records = svc.evaluate_wealth_facts({"2nd_lord_house": 11, ...})
    """

    def __init__(
        self,
        config: WealthConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the wealth domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_wealth_config(config_path)
        self._rules: tuple[WealthRule, ...] | None = None
        self._config_path = config_path

    def load_wealth_rules(self) -> WealthRuleCatalog:
        """Load and return the wealth rule catalog from config.

        Returns:
            A WealthRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_wealth_rules(self._config_path)
        return WealthRuleCatalog(rules=self._rules)

    def evaluate_wealth_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the wealth rule catalog.

        Takes a dictionary of JRE facts (e.g., ``{"2nd_lord_house": 11,
        "jupiter_bala": 7.0}``) and emits EvidenceRecord objects linked to
        the correct WealthOutcomeTaxonomy.

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
            self._rules = load_wealth_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: WealthOutcomeTaxonomy,
    ) -> tuple[WealthRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching WealthRule objects.
        """
        if self._rules is None:
            self._rules = load_wealth_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[WealthOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique WealthOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_wealth_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> WealthConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_wealth_rules(self._config_path)
        return len(self._rules)

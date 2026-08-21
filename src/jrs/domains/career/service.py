"""Career domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_career_config, load_career_rules
from .errors import InvalidFactError
from .models import (
    CareerConfig,
    CareerOutcomeTaxonomy,
    CareerRule,
    CareerRuleCatalog,
    evaluate_facts,
)


class CareerDomainService:
    """Career domain service: loads rules and evaluates facts.

    Usage::

        svc = CareerDomainService()
        catalog = svc.load_career_rules()
        records = svc.evaluate_career_facts({"10th_lord_house": 1, ...})
    """

    def __init__(
        self,
        config: CareerConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the career domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_career_config(config_path)
        self._rules: tuple[CareerRule, ...] | None = None
        self._config_path = config_path

    def load_career_rules(self) -> CareerRuleCatalog:
        """Load and return the career rule catalog from config.

        Returns:
            A CareerRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_career_rules(self._config_path)
        return CareerRuleCatalog(rules=self._rules)

    def evaluate_career_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the career rule catalog.

        Takes a dictionary of JRE facts (e.g., ``{"10th_lord_house": 1,
        "saturn_bala": 6.5}``) and emits EvidenceRecord objects linked to
        the correct CareerOutcomeTaxonomy.

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
            self._rules = load_career_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: CareerOutcomeTaxonomy,
    ) -> tuple[CareerRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching CareerRule objects.
        """
        if self._rules is None:
            self._rules = load_career_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[CareerOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique CareerOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_career_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> CareerConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_career_rules(self._config_path)
        return len(self._rules)

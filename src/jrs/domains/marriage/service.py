"""Marriage domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_marriage_config, load_marriage_rules
from .errors import InvalidFactError
from .models import (
    MarriageConfig,
    MarriageOutcomeTaxonomy,
    MarriageRule,
    MarriageRuleCatalog,
    evaluate_facts,
)


class MarriageDomainService:
    """Marriage domain service: loads rules and evaluates facts.

    Usage::

        svc = MarriageDomainService()
        catalog = svc.load_marriage_rules()
        records = svc.evaluate_marriage_facts({"7th_lord_house": 8, ...})
    """

    def __init__(
        self,
        config: MarriageConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the marriage domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_marriage_config(config_path)
        self._rules: tuple[MarriageRule, ...] | None = None
        self._config_path = config_path

    def load_marriage_rules(self) -> MarriageRuleCatalog:
        """Load and return the marriage rule catalog from config.

        Returns:
            A MarriageRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_marriage_rules(self._config_path)
        return MarriageRuleCatalog(rules=self._rules)

    def evaluate_marriage_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the marriage rule catalog.

        Takes a dictionary of JRE facts (e.g., ``{"7th_lord_house": 8,
        "venus_bala": 4.5}``) and emits EvidenceRecord objects linked to
        the correct MarriageOutcomeTaxonomy.

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
            self._rules = load_marriage_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: MarriageOutcomeTaxonomy,
    ) -> tuple[MarriageRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching MarriageRule objects.
        """
        if self._rules is None:
            self._rules = load_marriage_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[MarriageOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique MarriageOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_marriage_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> MarriageConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_marriage_rules(self._config_path)
        return len(self._rules)

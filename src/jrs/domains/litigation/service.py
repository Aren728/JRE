"""Litigation domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_litigation_config, load_litigation_rules
from .errors import InvalidFactError
from .models import (
    LitigationConfig,
    LitigationOutcomeTaxonomy,
    LitigationRule,
    LitigationRuleCatalog,
    evaluate_facts,
)


class LitigationDomainService:
    """Litigation domain service: loads rules and evaluates facts.

    Usage::

        svc = LitigationDomainService()
        catalog = svc.load_litigation_rules()
        records = svc.evaluate_litigation_facts({"6th_lord_strong": True, ...})
    """

    def __init__(
        self,
        config: LitigationConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the litigation domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_litigation_config(config_path)
        self._rules: tuple[LitigationRule, ...] | None = None
        self._config_path = config_path

    def load_litigation_rules(self) -> LitigationRuleCatalog:
        """Load and return the litigation rule catalog from config.

        Returns:
            A LitigationRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_litigation_rules(self._config_path)
        return LitigationRuleCatalog(rules=self._rules)

    def evaluate_litigation_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the litigation rule catalog.

        Takes a dictionary of JRE facts and emits EvidenceRecord objects
        linked to the correct LitigationOutcomeTaxonomy.

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
            self._rules = load_litigation_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: LitigationOutcomeTaxonomy,
    ) -> tuple[LitigationRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching LitigationRule objects.
        """
        if self._rules is None:
            self._rules = load_litigation_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[LitigationOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique LitigationOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_litigation_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> LitigationConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_litigation_rules(self._config_path)
        return len(self._rules)

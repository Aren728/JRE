"""Progeny domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_progeny_config, load_progeny_rules
from .errors import InvalidFactError
from .models import (
    ProgenyConfig,
    ProgenyOutcomeTaxonomy,
    ProgenyRule,
    ProgenyRuleCatalog,
    evaluate_facts,
)


class ProgenyDomainService:
    """Progeny domain service: loads rules and evaluates facts.

    Usage::

        svc = ProgenyDomainService()
        catalog = svc.load_progeny_rules()
        records = svc.evaluate_progeny_facts({"5th_lord_in_kendra": True, ...})
    """

    def __init__(
        self,
        config: ProgenyConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the progeny domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_progeny_config(config_path)
        self._rules: tuple[ProgenyRule, ...] | None = None
        self._config_path = config_path

    def load_progeny_rules(self) -> ProgenyRuleCatalog:
        """Load and return the progeny rule catalog from config.

        Returns:
            A ProgenyRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_progeny_rules(self._config_path)
        return ProgenyRuleCatalog(rules=self._rules)

    def evaluate_progeny_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the progeny rule catalog.

        Takes a dictionary of JRE facts (e.g., ``{"5th_lord_in_kendra": True,
        "jupiter_bala": 7.0}``) and emits EvidenceRecord objects linked to
        the correct ProgenyOutcomeTaxonomy.

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
            self._rules = load_progeny_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: ProgenyOutcomeTaxonomy,
    ) -> tuple[ProgenyRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching ProgenyRule objects.
        """
        if self._rules is None:
            self._rules = load_progeny_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[ProgenyOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique ProgenyOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_progeny_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> ProgenyConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_progeny_rules(self._config_path)
        return len(self._rules)

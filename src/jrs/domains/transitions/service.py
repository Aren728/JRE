"""Transitions domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_transitions_config, load_transitions_rules
from .errors import InvalidFactError
from .models import (
    TransitionConfig,
    TransitionOutcomeTaxonomy,
    TransitionRule,
    TransitionRuleCatalog,
    evaluate_facts,
)


class TransitionsDomainService:
    """Transitions domain service: loads rules and evaluates facts.

    Usage::

        svc = TransitionsDomainService()
        catalog = svc.load_transitions_rules()
        records = svc.evaluate_transitions_facts({"saturn_return": True, ...})
    """

    def __init__(
        self,
        config: TransitionConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the transitions domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_transitions_config(config_path)
        self._rules: tuple[TransitionRule, ...] | None = None
        self._config_path = config_path

    def load_transitions_rules(self) -> TransitionRuleCatalog:
        """Load and return the transitions rule catalog from config.

        Returns:
            A TransitionRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_transitions_rules(self._config_path)
        return TransitionRuleCatalog(rules=self._rules)

    def evaluate_transitions_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the transitions rule catalog.

        Takes a dictionary of JRE facts and emits EvidenceRecord objects
        linked to the correct TransitionOutcomeTaxonomy.

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
            self._rules = load_transitions_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: TransitionOutcomeTaxonomy,
    ) -> tuple[TransitionRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching TransitionRule objects.
        """
        if self._rules is None:
            self._rules = load_transitions_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[TransitionOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique TransitionOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_transitions_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> TransitionConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_transitions_rules(self._config_path)
        return len(self._rules)

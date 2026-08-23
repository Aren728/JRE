"""Traits domain service — rule loader and fact evaluator.

``TraitsDomainService`` loads trait interpretation rules from TOML config
and evaluates JRE-027 BirthSignature facts against them, producing
``EvidenceRecord`` objects linked to ``TraitOutcomeTaxonomy``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_traits_config, load_traits_rules
from .errors import InvalidFactError
from .models import (
    TraitOutcomeTaxonomy,
    TraitRule,
    TraitRuleCatalog,
    TraitsConfig,
    evaluate_facts,
)


class TraitsDomainService:
    """Traits domain service: loads rules and evaluates facts.

    Usage::

        svc = TraitsDomainService()
        catalog = svc.load_traits_rules()
        records = svc.evaluate_traits_facts({
            "tithi": "SHUKLA_PRATIPADA",
            "yoga": "BRAHMA",
            "hora": "MERCURY",
            ...
        })
    """

    def __init__(
        self,
        config: TraitsConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the traits domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_traits_config(config_path)
        self._rules: tuple[TraitRule, ...] | None = None
        self._config_path = config_path

    def load_traits_rules(self) -> TraitRuleCatalog:
        """Load and return the traits rule catalog from config.

        Returns:
            A TraitRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_traits_rules(self._config_path)
        return TraitRuleCatalog(rules=self._rules)

    def evaluate_traits_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE-027 facts against the traits rule catalog.

        Takes a dictionary of BirthSignature facts (e.g.,
        ``{"tithi": "SHUKLA_PRATIPADA", "yoga": "BRAHMA", ...}``) and
        emits EvidenceRecord objects linked to the correct
        TraitOutcomeTaxonomy.

        Args:
            facts: Dictionary of JRE-027 BirthSignature facts.

        Returns:
            A tuple of EvidenceRecord objects for all matching rules.

        Raises:
            InvalidFactError: If facts is not a valid dictionary.
        """
        if not isinstance(facts, dict):
            raise InvalidFactError("facts must be a dictionary")

        if self._rules is None:
            self._rules = load_traits_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: TraitOutcomeTaxonomy,
    ) -> tuple[TraitRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching TraitRule objects.
        """
        if self._rules is None:
            self._rules = load_traits_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[TraitOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique TraitOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_traits_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> TraitsConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_traits_rules(self._config_path)
        return len(self._rules)

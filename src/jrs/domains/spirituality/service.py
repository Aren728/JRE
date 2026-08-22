"""Spirituality domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_spirituality_config, load_spirituality_rules
from .errors import InvalidFactError
from .models import (
    SpiritualityConfig,
    SpiritualityOutcomeTaxonomy,
    SpiritualityRule,
    SpiritualityRuleCatalog,
    evaluate_facts,
)


class SpiritualityDomainService:
    """Spirituality domain service: loads rules and evaluates facts.

    Usage::

        svc = SpiritualityDomainService()
        catalog = svc.load_spirituality_rules()
        records = svc.evaluate_spirituality_facts({"ketu_strong": True, ...})
    """

    def __init__(
        self,
        config: SpiritualityConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the spirituality domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_spirituality_config(config_path)
        self._rules: tuple[SpiritualityRule, ...] | None = None
        self._config_path = config_path

    def load_spirituality_rules(self) -> SpiritualityRuleCatalog:
        """Load and return the spirituality rule catalog from config.

        Returns:
            A SpiritualityRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_spirituality_rules(self._config_path)
        return SpiritualityRuleCatalog(rules=self._rules)

    def evaluate_spirituality_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the spirituality rule catalog.

        Takes a dictionary of JRE facts and emits EvidenceRecord objects
        linked to the correct SpiritualityOutcomeTaxonomy.

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
            self._rules = load_spirituality_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: SpiritualityOutcomeTaxonomy,
    ) -> tuple[SpiritualityRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching SpiritualityRule objects.
        """
        if self._rules is None:
            self._rules = load_spirituality_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[SpiritualityOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique SpiritualityOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_spirituality_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> SpiritualityConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_spirituality_rules(self._config_path)
        return len(self._rules)

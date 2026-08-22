"""Education domain service — rule loader and fact evaluator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_education_config, load_education_rules
from .errors import InvalidFactError
from .models import (
    EducationConfig,
    EducationOutcomeTaxonomy,
    EducationRule,
    EducationRuleCatalog,
    evaluate_facts,
)


class EducationDomainService:
    """Education domain service: loads rules and evaluates facts.

    Usage::

        svc = EducationDomainService()
        catalog = svc.load_education_rules()
        records = svc.evaluate_education_facts({"4th_lord_in_kendra": True, ...})
    """

    def __init__(
        self,
        config: EducationConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the education domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_education_config(config_path)
        self._rules: tuple[EducationRule, ...] | None = None
        self._config_path = config_path

    def load_education_rules(self) -> EducationRuleCatalog:
        """Load and return the education rule catalog from config.

        Returns:
            An EducationRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_education_rules(self._config_path)
        return EducationRuleCatalog(rules=self._rules)

    def evaluate_education_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the education rule catalog.

        Takes a dictionary of JRE facts (e.g., ``{"4th_lord_in_kendra": True,
        "jupiter_bala": 7.0}``) and emits EvidenceRecord objects linked to
        the correct EducationOutcomeTaxonomy.

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
            self._rules = load_education_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: EducationOutcomeTaxonomy,
    ) -> tuple[EducationRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching EducationRule objects.
        """
        if self._rules is None:
            self._rules = load_education_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[EducationOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique EducationOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_education_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    @property
    def config(self) -> EducationConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_education_rules(self._config_path)
        return len(self._rules)

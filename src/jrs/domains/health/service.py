"""Health domain service — rule loader and fact evaluator.

SAFETY CONSTRAINT: This service maps traditional astrological indicators
of physical constitution and vitality. It does NOT generate, contain, or
imply medical diagnoses, disease names, surgical indicators, or death
predictions. All terminology is strictly limited to constitutional
vitality assessments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jrs.evidence.models import EvidenceRecord

from .config import load_health_config, load_health_rules
from .errors import InvalidFactError
from .models import (
    HealthConfig,
    HealthOutcomeTaxonomy,
    HealthRule,
    HealthRuleCatalog,
    _validate_no_medical_terms,
    evaluate_facts,
)


class HealthDomainService:
    """Health domain service: loads rules and evaluates facts.

    SAFETY: All output is strictly limited to traditional vitality
    indicators. No medical diagnosis terminology is ever produced.

    Usage::

        svc = HealthDomainService()
        catalog = svc.load_health_rules()
        records = svc.evaluate_health_facts({"1st_lord_strong": True, ...})
    """

    def __init__(
        self,
        config: HealthConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        """Initialize the health domain service.

        Args:
            config: Optional pre-loaded config. If ``None``, loads from TOML.
            config_path: Optional path to the TOML config file.
        """
        self._config = config or load_health_config(config_path)
        self._rules: tuple[HealthRule, ...] | None = None
        self._config_path = config_path

    def load_health_rules(self) -> HealthRuleCatalog:
        """Load and return the health rule catalog from config.

        Returns:
            A HealthRuleCatalog containing all rules.
        """
        if self._rules is None:
            self._rules = load_health_rules(self._config_path)
        return HealthRuleCatalog(rules=self._rules)

    def evaluate_health_facts(
        self,
        facts: dict[str, Any],
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate JRE facts against the health rule catalog.

        Takes a dictionary of JRE facts and emits EvidenceRecord objects
        linked to the correct HealthOutcomeTaxonomy.

        SAFETY: All resulting EvidenceRecord objects will have
        outcome_taxonomy values that are traditional vitality indicators,
        never medical terms.

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
            self._rules = load_health_rules(self._config_path)

        return evaluate_facts(self._rules, facts)

    def get_rules_for_outcome(
        self,
        outcome: HealthOutcomeTaxonomy,
    ) -> tuple[HealthRule, ...]:
        """Get all rules for a specific outcome taxonomy.

        Args:
            outcome: The outcome taxonomy to filter by.

        Returns:
            A tuple of matching HealthRule objects.
        """
        if self._rules is None:
            self._rules = load_health_rules(self._config_path)
        return tuple(r for r in self._rules if r.outcome is outcome)

    def get_outcome_taxonomies(self) -> tuple[HealthOutcomeTaxonomy, ...]:
        """Get all unique outcome taxonomies in the catalog.

        Returns:
            A tuple of unique HealthOutcomeTaxonomy values.
        """
        if self._rules is None:
            self._rules = load_health_rules(self._config_path)
        outcomes = {r.outcome for r in self._rules}
        return tuple(sorted(outcomes, key=lambda o: o.value))

    def validate_output_safety(self, text: str) -> bool:
        """Validate that output text contains no medical terminology.

        Args:
            text: The text to validate.

        Returns:
            True if the text is safe (no medical terms), False otherwise.
        """
        try:
            _validate_no_medical_terms(text)
            return True
        except ValueError:
            return False

    @property
    def config(self) -> HealthConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_health_rules(self._config_path)
        return len(self._rules)

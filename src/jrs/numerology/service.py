"""JRS Numerology — Domain service.

``NumerologyDomainService`` loads classical Pythagorean interpretation
rules from TOML config and evaluates NumerologyChart facts against them,
producing ``SystemAssessment`` objects with ``SystemType.NUMEROLOGY``
provenance.
"""

from __future__ import annotations

from pathlib import Path

from jrs.evidence.models import EvidenceRecord
from jrs.multisystem.models import SystemAssessment
from numerology.models import NumerologyChart

from .config import load_numerology_config, load_numerology_rules
from .models import (
    NumerologyConfig,
    NumerologyRule,
    NumerologyRuleCatalog,
    build_system_assessment,
    evaluate_facts,
    extract_facts_from_chart,
)


class NumerologyDomainService:
    """Numerology domain service: loads rules and evaluates charts.

    Usage::

        svc = NumerologyDomainService()
        assessment = svc.assess_chart(numerology_chart)
    """

    def __init__(
        self,
        config: NumerologyConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        self._config = config or load_numerology_config(config_path)
        self._rules: tuple[NumerologyRule, ...] | None = None
        self._config_path = config_path

    def load_rules(self) -> NumerologyRuleCatalog:
        """Load and return the Numerology rule catalog from config."""
        if self._rules is None:
            self._rules = load_numerology_rules(self._config_path)
        return NumerologyRuleCatalog(rules=self._rules)

    def evaluate_chart_facts(
        self, chart: NumerologyChart
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate a NumerologyChart against the rule catalog.

        Args:
            chart: A NumerologyChart from the Numerology JRE.

        Returns:
            A tuple of EvidenceRecord objects for all matching rules.
        """
        if self._rules is None:
            self._rules = load_numerology_rules(self._config_path)

        facts = extract_facts_from_chart(chart)
        return evaluate_facts(self._rules, facts)

    def assess_chart(self, chart: NumerologyChart) -> SystemAssessment:
        """Produce a SystemAssessment for a NumerologyChart.

        Evaluates all rules against the chart, aggregates the evidence
        by outcome taxonomy, and produces a single SystemAssessment.

        Args:
            chart: A NumerologyChart from the Numerology JRE.

        Returns:
            A SystemAssessment with SystemType.NUMEROLOGY provenance.
        """
        records = self.evaluate_chart_facts(chart)
        return build_system_assessment(
            records, source_tradition=self._config.source_id
        )

    @property
    def config(self) -> NumerologyConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_numerology_rules(self._config_path)
        return len(self._rules)

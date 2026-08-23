"""JRS-067 Western Astrology domain service.

``WesternDomainService`` loads classical Western interpretation rules
from TOML config and evaluates JRE-066 WesternChart facts against them,
producing ``SystemAssessment`` objects with ``SystemType.WESTERN``
provenance.
"""

from __future__ import annotations

from pathlib import Path

from jrs.evidence.models import EvidenceDirection, EvidenceRecord
from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
)
from western.models import WesternChart

from .config import load_western_config, load_western_rules
from .models import (
    WesternConfig,
    WesternRule,
    WesternRuleCatalog,
    evaluate_facts,
    extract_facts_from_chart,
)


class WesternDomainService:
    """Western domain service: loads rules and evaluates charts.

    Usage::

        svc = WesternDomainService()
        assessment = svc.assess_chart(western_chart)
    """

    def __init__(
        self,
        config: WesternConfig | None = None,
        config_path: Path | None = None,
    ) -> None:
        self._config = config or load_western_config(config_path)
        self._rules: tuple[WesternRule, ...] | None = None
        self._config_path = config_path

    def load_rules(self) -> WesternRuleCatalog:
        """Load and return the Western rule catalog from config."""
        if self._rules is None:
            self._rules = load_western_rules(self._config_path)
        return WesternRuleCatalog(rules=self._rules)

    def evaluate_chart_facts(
        self, chart: WesternChart
    ) -> tuple[EvidenceRecord, ...]:
        """Evaluate a WesternChart against the rule catalog.

        Args:
            chart: A WesternChart from JRE-066.

        Returns:
            A tuple of EvidenceRecord objects for all matching rules.
        """
        if self._rules is None:
            self._rules = load_western_rules(self._config_path)

        facts = extract_facts_from_chart(chart)
        return evaluate_facts(self._rules, facts)

    def assess_chart(self, chart: WesternChart) -> SystemAssessment:
        """Produce a SystemAssessment for a WesternChart.

        Evaluates all rules against the chart, aggregates the evidence
        by outcome taxonomy, and produces a single SystemAssessment.

        Args:
            chart: A WesternChart from JRE-066.

        Returns:
            A SystemAssessment with SystemType.WESTERN provenance.
        """
        records = self.evaluate_chart_facts(chart)

        if not records:
            return SystemAssessment(
                system_type=SystemType.WESTERN,
                outcome_taxonomy="NO_MATCH",
                assessment_status="NEUTRAL",
                timing_status="INACTIVE",
                provenance=EvidenceProvenance(
                    system_type=SystemType.WESTERN,
                    source_tradition=self._config.source_id,
                ),
            )

        # Aggregate by outcome taxonomy
        outcome_support: dict[str, int] = {}
        outcome_contradict: dict[str, int] = {}
        for record in records:
            outcome = record.outcome_taxonomy
            if record.direction is EvidenceDirection.SUPPORT:
                outcome_support[outcome] = outcome_support.get(outcome, 0) + 1
            elif record.direction is EvidenceDirection.CONTRADICT:
                outcome_contradict[outcome] = (
                    outcome_contradict.get(outcome, 0) + 1
                )

        # Find the outcome with the strongest net support
        all_outcomes = set(outcome_support.keys()) | set(
            outcome_contradict.keys()
        )
        best_outcome = ""
        best_score = -1
        for outcome in all_outcomes:
            score = outcome_support.get(outcome, 0) - outcome_contradict.get(
                outcome, 0
            )
            if score > best_score:
                best_score = score
                best_outcome = outcome

        # Determine assessment status
        net_support = outcome_support.get(best_outcome, 0)
        net_contradict = outcome_contradict.get(best_outcome, 0)

        if net_support >= 3 and net_contradict == 0:
            status = "STRONGLY_SUPPORTED"
        elif net_support >= 2 and net_contradict == 0:
            status = "SUPPORTED"
        elif net_support >= 1:
            status = "WEAKLY_SUPPORTED"
        elif net_contradict >= 2 or net_contradict >= 1 and net_support == 0:
            status = "CONTRADICTED"
        else:
            status = "NEUTRAL"

        return SystemAssessment(
            system_type=SystemType.WESTERN,
            outcome_taxonomy=best_outcome,
            assessment_status=status,
            timing_status="INACTIVE",
            provenance=EvidenceProvenance(
                system_type=SystemType.WESTERN,
                source_tradition=self._config.source_id,
            ),
        )

    def assess_chart_per_outcome(
        self, chart: WesternChart
    ) -> tuple[SystemAssessment, ...]:
        """Produce one SystemAssessment per outcome taxonomy.

        Useful for feeding into CrossSystemEvidence which expects
        per-outcome assessments.

        Args:
            chart: A WesternChart from JRE-066.

        Returns:
            A tuple of SystemAssessment objects, one per outcome.
        """
        records = self.evaluate_chart_facts(chart)

        if not records:
            return ()

        # Group by outcome
        outcome_records: dict[str, list[EvidenceRecord]] = {}
        for record in records:
            outcome = record.outcome_taxonomy
            if outcome not in outcome_records:
                outcome_records[outcome] = []
            outcome_records[outcome].append(record)

        assessments: list[SystemAssessment] = []
        for outcome, recs in outcome_records.items():
            support = sum(
                1 for r in recs if r.direction is EvidenceDirection.SUPPORT
            )
            contradict = sum(
                1 for r in recs if r.direction is EvidenceDirection.CONTRADICT
            )

            if support >= 3 and contradict == 0:
                status = "STRONGLY_SUPPORTED"
            elif support >= 2 and contradict == 0:
                status = "SUPPORTED"
            elif support >= 1:
                status = "WEAKLY_SUPPORTED"
            elif contradict >= 2 or contradict >= 1 and support == 0:
                status = "CONTRADICTED"
            else:
                status = "NEUTRAL"

            assessments.append(
                SystemAssessment(
                    system_type=SystemType.WESTERN,
                    outcome_taxonomy=outcome,
                    assessment_status=status,
                    timing_status="INACTIVE",
                    provenance=EvidenceProvenance(
                        system_type=SystemType.WESTERN,
                        source_tradition=self._config.source_id,
                    ),
                )
            )

        return tuple(assessments)

    @property
    def config(self) -> WesternConfig:
        """Return the loaded configuration."""
        return self._config

    @property
    def rule_count(self) -> int:
        """Return the number of loaded rules."""
        if self._rules is None:
            self._rules = load_western_rules(self._config_path)
        return len(self._rules)

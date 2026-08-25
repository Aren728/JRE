"""JRS Numerology — Interpretation models.

Defines the outcome taxonomy, rule catalog, and fact extraction logic
for the Numerology interpretation layer.  Consumes NumerologyChart
facts and produces SystemAssessment objects with SystemType.NUMEROLOGY
provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from jrs.evidence.models import (
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
)
from jrs.multisystem.models import (
    EvidenceProvenance,
    SystemAssessment,
    SystemType,
)
from numerology.models import NumerologyChart

# ── Outcome Taxonomy ─────────────────────────────────────────────────────────


class NumerologyOutcomeTaxonomy(Enum):
    """Numerology outcome categories.

    Derived from classical Pythagorean numerology interpretations.
    """

    CAREER_PROMINENCE = "CAREER_PROMINENCE"
    RELATIONSHIP_HARMONY = "RELATIONSHIP_HARMONY"
    EMOTIONAL_TENSION = "EMOTIONAL_TENSION"
    FINANCIAL_GAIN = "FINANCIAL_GAIN"
    INTELLECTUAL_CAPACITY = "INTELLECTUAL_CAPACITY"
    LEADERSHIP_AUTHORITY = "LEADERSHIP_AUTHORITY"
    SOCIAL_INFLUENCE = "SOCIAL_INFLUENCE"
    PHILOSOPHICAL_DEPTH = "PHILOSOPHICAL_DEPTH"
    CREATIVE_TALENT = "CREATIVE_TALENT"
    DOMESTIC_PROMINENCE = "DOMESTIC_PROMINENCE"


# ── Core Models ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NumerologyRule:
    """A single numerology rule mapping chart facts to an outcome."""

    rule_id: str
    description: str
    condition_facts: tuple[str, ...]
    outcome: NumerologyOutcomeTaxonomy
    direction: EvidenceDirection
    strength: EvidenceStrength = EvidenceStrength.MODERATE
    source_id: str = "PYTHAGOREAN"
    location: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "rule_id": self.rule_id,
            "description": self.description,
            "condition_facts": list(self.condition_facts),
            "outcome": self.outcome.value,
            "direction": self.direction.value,
            "strength": self.strength.value,
            "source_id": self.source_id,
            "location": self.location,
        }


@dataclass(frozen=True)
class NumerologyRuleCatalog:
    """Complete catalog of Numerology domain rules."""

    rules: tuple[NumerologyRule, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "rules": [r.to_dict() for r in self.rules],
            "rule_count": len(self.rules),
        }

    def get_rules_by_outcome(
        self, outcome: NumerologyOutcomeTaxonomy
    ) -> tuple[NumerologyRule, ...]:
        """Get all rules for a specific outcome taxonomy."""
        return tuple(r for r in self.rules if r.outcome is outcome)


@dataclass(frozen=True)
class NumerologyConfig:
    """Configuration metadata for the Numerology domain."""

    version: str = "1.0"
    source_id: str = "PYTHAGOREAN"
    default_strength: str = "MODERATE"


# ── Fact Extraction from NumerologyChart ─────────────────────────────────────


def extract_facts_from_chart(chart: NumerologyChart) -> dict[str, Any]:
    """Extract a flat fact dictionary from a NumerologyChart for rule evaluation.

    The fact dictionary maps condition strings (as used in TOML rules)
    to their values from the chart.

    Args:
        chart: A NumerologyChart from the Numerology JRE.

    Returns:
        A dictionary of fact_key -> value pairs.
    """
    facts: dict[str, Any] = {}

    # Life Path facts
    if chart.life_path is not None:
        facts["life_path"] = str(chart.life_path.reduced)
        facts["life_path_type"] = chart.life_path.life_path_type.value
        facts["life_path_raw_sum"] = str(chart.life_path.raw_sum)

    # Destiny facts
    if chart.destiny is not None:
        facts["destiny"] = str(chart.destiny.reduced)
        facts["destiny_raw_sum"] = str(chart.destiny.raw_sum)

    # Soul Urge facts
    if chart.soul_urge is not None:
        facts["soul_urge"] = str(chart.soul_urge.reduced)
        facts["soul_urge_raw_sum"] = str(chart.soul_urge.raw_sum)

    # Personality facts
    if chart.personality is not None:
        facts["personality"] = str(chart.personality.reduced)
        facts["personality_raw_sum"] = str(chart.personality.raw_sum)

    # Personal Year facts
    if chart.personal_year is not None:
        facts["personal_year"] = str(chart.personal_year.reduced)

    return facts


# ── Condition Evaluation ─────────────────────────────────────────────────────


def evaluate_condition(condition: str, facts: dict[str, Any]) -> bool:
    """Evaluate a single condition against the facts dictionary.

    Supports:
    - ``fact_name=value``: equality check
    - ``fact_name!=value``: inequality check

    Args:
        condition: The condition string to evaluate.
        facts: The facts dictionary.

    Returns:
        True if the condition is satisfied.
    """
    condition = condition.strip()

    if "!=" in condition:
        parts = condition.split("!=", 1)
        fact_name = parts[0].strip()
        target = parts[1].strip().strip("'\"")
        fact_val = facts.get(fact_name)
        if fact_val is None:
            return True  # Missing fact means inequality holds
        return str(fact_val).lower() != target.lower()

    if "=" in condition:
        parts = condition.split("=", 1)
        fact_name = parts[0].strip()
        target = parts[1].strip().strip("'\"")
        fact_val = facts.get(fact_name)
        if fact_val is None:
            return False
        return str(fact_val).lower() == target.lower()

    # Truthy check
    fact_val = facts.get(condition)
    return bool(fact_val) if fact_val is not None else False


def evaluate_rule(
    rule: NumerologyRule, facts: dict[str, Any]
) -> EvidenceRecord | None:
    """Evaluate a single rule against facts and produce an EvidenceRecord.

    All condition_facts must be satisfied (AND logic).

    Args:
        rule: The Numerology rule to evaluate.
        facts: The facts dictionary from the chart.

    Returns:
        An EvidenceRecord if all conditions are met, None otherwise.
    """
    if not rule.condition_facts:
        return None

    for condition in rule.condition_facts:
        if not evaluate_condition(condition, facts):
            return None

    return EvidenceRecord(
        evidence_id=f"{rule.rule_id}-auto",
        outcome_taxonomy=rule.outcome.value,
        supporting_fact_type=",".join(rule.condition_facts),
        rule_id=rule.rule_id,
        source_id=rule.source_id,
        location=rule.location,
        direction=rule.direction,
        strength=rule.strength,
    )


def evaluate_facts(
    rules: tuple[NumerologyRule, ...], facts: dict[str, Any]
) -> tuple[EvidenceRecord, ...]:
    """Evaluate all rules against facts and return matching EvidenceRecords.

    Args:
        rules: The tuple of Numerology rules.
        facts: The facts dictionary from the chart.

    Returns:
        A tuple of EvidenceRecord objects for all rules that fired.
    """
    records: list[EvidenceRecord] = []
    for rule in rules:
        record = evaluate_rule(rule, facts)
        if record is not None:
            records.append(record)
    return tuple(records)


# ── Assessment Helpers ───────────────────────────────────────────────────────


def build_system_assessment(
    records: tuple[EvidenceRecord, ...],
    source_tradition: str = "PYTHAGOREAN",
) -> SystemAssessment:
    """Build a SystemAssessment from evidence records.

    Aggregates evidence by outcome taxonomy and produces a single
    SystemAssessment with the best-supported outcome.

    Args:
        records: Tuple of EvidenceRecord objects.
        source_tradition: Source tradition string for provenance.

    Returns:
        A SystemAssessment with SystemType.NUMEROLOGY provenance.
    """
    if not records:
        return SystemAssessment(
            system_type=SystemType.NUMEROLOGY,
            outcome_taxonomy="NO_MATCH",
            assessment_status="NEUTRAL",
            timing_status="INACTIVE",
            provenance=EvidenceProvenance(
                system_type=SystemType.NUMEROLOGY,
                source_tradition=source_tradition,
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
    elif net_contradict >= 2 or (net_contradict >= 1 and net_support == 0):
        status = "CONTRADICTED"
    else:
        status = "NEUTRAL"

    return SystemAssessment(
        system_type=SystemType.NUMEROLOGY,
        outcome_taxonomy=best_outcome,
        assessment_status=status,
        timing_status="INACTIVE",
        provenance=EvidenceProvenance(
            system_type=SystemType.NUMEROLOGY,
            source_tradition=source_tradition,
        ),
    )

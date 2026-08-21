"""Marriage domain data models — outcome taxonomy, rule catalog, fact evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from jrs.evidence.models import (
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
)

# ── Enums ────────────────────────────────────────────────────────────────────

class MarriageOutcomeTaxonomy(Enum):
    """Highly specific marriage/relationship outcome taxonomies."""

    MARRIAGE_FORMATION = "MARRIAGE_FORMATION"
    DELAYED_MARRIAGE = "DELAYED_MARRIAGE"
    MULTIPLE_SIMULTANEOUS_SPOUSES = "MULTIPLE_SIMULTANEOUS_SPOUSES"
    REMARRIAGE_AFTER_DIVORCE = "REMARRIAGE_AFTER_DIVORCE"
    REMARRIAGE_AFTER_SPOUSE_DEATH = "REMARRIAGE_AFTER_SPOUSE_DEATH"
    SEPARATION = "SEPARATION"
    SPOUSE_LOSS = "SPOUSE_LOSS"
    MARITAL_HARMONY = "MARITAL_HARMONY"
    MARITAL_CONFLICT = "MARITAL_CONFLICT"
    LOVE_MARRIAGE = "LOVE_MARRIAGE"
    ARRANGED_MARRIAGE = "ARRANGED_MARRIAGE"
    CROSS_CULTURAL_MARRIAGE = "CROSS_CULTURAL_MARRIAGE"
    LATE_MARRIAGE = "LATE_MARRIAGE"
    MARRIAGE_AVOIDANCE = "MARRIAGE_AVOIDANCE"


# ── Core Models ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MarriageRule:
    """A single classical rule mapping JRE facts to a marriage outcome."""

    rule_id: str
    description: str
    condition_facts: tuple[str, ...]
    outcome: MarriageOutcomeTaxonomy
    direction: EvidenceDirection
    strength: EvidenceStrength = EvidenceStrength.MODERATE
    source_id: str = "BPHS"
    location: str = ""
    timing_relevance: str = ""

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
            "timing_relevance": self.timing_relevance,
        }


@dataclass(frozen=True)
class MarriageRuleCatalog:
    """Complete catalog of marriage domain rules."""

    rules: tuple[MarriageRule, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "rules": [r.to_dict() for r in self.rules],
            "rule_count": len(self.rules),
        }

    def get_rules_by_outcome(
        self,
        outcome: MarriageOutcomeTaxonomy,
    ) -> tuple[MarriageRule, ...]:
        """Get all rules for a specific outcome taxonomy."""
        return tuple(r for r in self.rules if r.outcome is outcome)

    def get_rule_by_id(self, rule_id: str) -> MarriageRule | None:
        """Get a rule by its ID."""
        for r in self.rules:
            if r.rule_id == rule_id:
                return r
        return None


@dataclass(frozen=True)
class MarriageConfig:
    """Configuration for the marriage domain."""

    version: str = "1.0"
    source_id: str = "BPHS"
    default_strength: str = "MODERATE"


# ── Fact Evaluation Logic ────────────────────────────────────────────────────

def evaluate_condition(
    condition: str,
    facts: dict[str, Any],
) -> bool:
    """Evaluate a single condition against the facts dictionary.

    Supports the following condition formats:
    - ``fact_name``: truthy check (fact exists and is truthy)
    - ``fact_name=value``: equality check
    - ``fact_name>value``: greater-than check
    - ``fact_name<value``: less-than check
    - ``fact_name>=value``: greater-than-or-equal check
    - ``fact_name<=value``: less-than-or-equal check
    - ``fact_name in (v1,v2,...)``: membership check

    Args:
        condition: The condition string to evaluate.
        facts: The facts dictionary.

    Returns:
        True if the condition is satisfied, False otherwise.
    """
    condition = condition.strip()

    # Membership check: "fact_name in (v1,v2,...)"
    if " in (" in condition:
        parts = condition.split(" in (", 1)
        fact_name = parts[0].strip()
        values_str = parts[1].rstrip(")")
        values = [v.strip().strip("'\"") for v in values_str.split(",")]
        fact_val = facts.get(fact_name)
        return str(fact_val) in values if fact_val is not None else False

    # Comparison operators
    for op in (">=", "<=", "!=", ">", "<", "="):
        if op in condition:
            parts = condition.split(op, 1)
            fact_name = parts[0].strip()
            target_str = parts[1].strip().strip("'\"")
            fact_val = facts.get(fact_name)
            if fact_val is None:
                return False

            # Try numeric comparison
            try:
                fact_num = float(fact_val)
                target_num = float(target_str)
            except (ValueError, TypeError):
                # String comparison (case-insensitive for booleans)
                fact_str = str(fact_val).lower()
                target_lower = target_str.lower()
                if op == "=":
                    return fact_str == target_lower
                if op == "!=":
                    return fact_str != target_lower
                return False

            if op == "=":
                return fact_num == target_num
            if op == "!=":
                return fact_num != target_num
            if op == ">":
                return fact_num > target_num
            if op == "<":
                return fact_num < target_num
            if op == ">=":
                return fact_num >= target_num
            if op == "<=":
                return fact_num <= target_num

    # Truthy check
    fact_val = facts.get(condition)
    return bool(fact_val) if fact_val is not None else False


def evaluate_rule(
    rule: MarriageRule,
    facts: dict[str, Any],
) -> EvidenceRecord | None:
    """Evaluate a single rule against facts and produce an EvidenceRecord.

    All condition_facts must be satisfied for the rule to fire.

    Args:
        rule: The marriage rule to evaluate.
        facts: The facts dictionary from JRE engines.

    Returns:
        An EvidenceRecord if all conditions are met, None otherwise.
    """
    if not rule.condition_facts:
        return None

    # All conditions must be satisfied (AND logic)
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
        timing_relevance=rule.timing_relevance,
    )


def evaluate_facts(
    rules: tuple[MarriageRule, ...],
    facts: dict[str, Any],
) -> tuple[EvidenceRecord, ...]:
    """Evaluate all rules against facts and return matching EvidenceRecords.

    Args:
        rules: The tuple of marriage rules to evaluate.
        facts: The facts dictionary from JRE engines.

    Returns:
        A tuple of EvidenceRecord objects for all rules that fired.
    """
    records: list[EvidenceRecord] = []
    for rule in rules:
        record = evaluate_rule(rule, facts)
        if record is not None:
            records.append(record)
    return tuple(records)

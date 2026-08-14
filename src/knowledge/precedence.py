"""Deterministic rule precedence and weight/credibility metadata (SPEC §8, §10).

Precedence is a pure comparator over matched ACTIVE rules in a profile —
higher first (ADR-010): source-priority rank, then condition specificity,
then authority tier, then ``rule_version`` (semver, newer first), then
``rule_id`` tiebreak. ``effective_weight`` and ``credibility`` are pinned,
deterministic metadata (SPEC §10): they never feed rule *selection* and are
never predictions.

This module imports models only (pure; the completeness helper lives in
``models`` so the import graph stays one-way).
"""

from __future__ import annotations

from collections.abc import Sequence

from .models import (
    KnowledgeConfig,
    Rule,
    RuleCondition,
    TraditionProfile,
    provenance_completeness_level,
)


def semver_tuple(version: str) -> tuple[int, ...]:
    """Parse a ``N.N.N`` semver string into an int tuple (SPEC §8)."""
    return tuple(int(part) for part in version.split("."))


def count_atoms(condition: RuleCondition) -> int:
    """Number of atoms in a condition tree (specificity, SPEC §8)."""
    if condition.combiner is None:
        return 1
    return sum(count_atoms(child) for child in condition.children)


def source_priority_rank(profile: TraditionProfile, source_id: str) -> int:
    """Rank of ``source_id`` in the profile's priority list.

    A source included but not listed in ``source_priority`` gets the lowest
    rank (``len(source_priority)``) — deterministic, never an error.
    """
    try:
        return profile.source_priority.index(source_id)
    except ValueError:
        return len(profile.source_priority)


def precedence_key(rule: Rule, profile: TraditionProfile) -> tuple[object, ...]:
    """The exact comparator tuple (SPEC §8), negated for ascending sort.

    Higher-first ordering is achieved by negating the numeric fields so
    Python's ascending tuple sort yields the desired order. Echoed verbatim
    on ``ResolvedRule.precedence_key`` for audit.
    """
    rank = source_priority_rank(profile, rule.provenance.source_id)
    specificity = count_atoms(rule.condition)
    version = semver_tuple(rule.rule_version)
    return (
        rank,
        -specificity,
        -rule.authority_tier,
        tuple(-part for part in version),
        rule.rule_id,
    )


def order_rules(rules: Sequence[Rule], profile: TraditionProfile) -> list[Rule]:
    """Order rules by the §8 key, higher first (deterministic).

    The key negates specificity/tier/semver so a plain **ascending** sort
    yields higher-priority rules first (SPEC §8).
    """
    return sorted(rules, key=lambda rule: precedence_key(rule, profile))


def effective_weight(rule: Rule, profile: TraditionProfile, config: KnowledgeConfig) -> float:
    """Display/ordering scalar (SPEC §10.1) — never a selection input."""
    rank = source_priority_rank(profile, rule.provenance.source_id)
    specificity = count_atoms(rule.condition)
    n_sources = len(profile.source_priority)
    value = (
        config.weight_authority_coeff * rule.authority_tier
        + config.weight_specificity_coeff * specificity
        + config.weight_source_rank_coeff * (n_sources - rank)
    )
    return round(value, 4)


def credibility(rule: Rule, config: KnowledgeConfig) -> float:
    """Evidence confidence in [0, 1] (SPEC §10.2) — never outcome likelihood."""
    level = provenance_completeness_level(rule.provenance)
    completeness = config.provenance_completeness[level]
    specificity = count_atoms(rule.condition)
    value = (
        config.credibility_authority_weight * (rule.authority_tier / 5.0)
        + config.credibility_provenance_weight * completeness
        + config.credibility_specificity_weight * min(specificity / 5.0, 1.0)
    )
    return round(value, 4)


def credibility_summary(
    credibilities: Sequence[float],
) -> dict[str, float | int | None]:
    """Deterministic ``{mean, min, max, n}`` over matched rules (§10.2)."""
    if not credibilities:
        return {"mean": None, "min": None, "max": None, "n": 0}
    return {
        "mean": round(sum(credibilities) / len(credibilities), 4),
        "min": round(min(credibilities), 4),
        "max": round(max(credibilities), 4),
        "n": len(credibilities),
    }

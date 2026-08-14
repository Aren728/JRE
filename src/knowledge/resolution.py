"""Conflict/exception detection and policy application (SPEC §9).

Detection is explicit-pairs primary (authored ``conflicts_with``); structural
contradiction is a load-time validation warning only (``rules.py``), never
auto-suppression. Exceptions (``exception_for``) override base rules
regardless of normal precedence and are always recorded with
``resolution="exception"``. ``REPORT_ALL`` never changes exception semantics.

These functions are pure and take a ``key_fn`` (the §8 precedence key) so
this module stays decoupled from ``precedence``; the caller supplies the
ordering used to pick exception winners and conflict winners.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from .models import ConflictPolicy, ConflictRecord, Rule

PrecedenceKey = tuple[object, ...]


@dataclass(frozen=True)
class ExceptionResolution:
    """Outcome of exception processing for one synthesis."""

    suppressed_ids: tuple[str, ...]
    overrides: dict[str, str]
    records: tuple[ConflictRecord, ...]


def resolve_exceptions(
    matched: Sequence[Rule],
    *,
    key_fn: Callable[[Rule], PrecedenceKey],
    policy: ConflictPolicy,
) -> ExceptionResolution:
    """Apply ``exception_for`` overrides over the matched rules (SPEC §9.2).

    Each base rule targeted by at least one *matching* exception is
    overridden (regardless of normal precedence). If several exceptions
    target the same base, the higher-precedence exception wins and the
    losers are themselves suppressed; a base is processed once, in sorted
    order, and an exception already suppressed by one contest cannot win
    another — deterministic.
    """
    by_id = {rule.rule_id: rule for rule in matched}
    targets: dict[str, list[Rule]] = {}
    for rule in matched:
        if not rule.exception_for:
            continue
        for base_id in rule.exception_for:
            if base_id in by_id:
                targets.setdefault(base_id, []).append(rule)

    suppressed: set[str] = set()
    overrides: dict[str, str] = {}
    records: list[ConflictRecord] = []
    for base_id in sorted(targets):
        contenders = [e for e in targets[base_id] if e.rule_id not in suppressed]
        if not contenders:
            continue
        # ascending §8 key: first element is the highest-precedence exception
        ordered = sorted(contenders, key=key_fn)
        winner = ordered[0]
        overrides[base_id] = winner.rule_id
        suppressed.add(base_id)
        records.append(
            ConflictRecord(
                rule_a_id=winner.rule_id,
                rule_b_id=base_id,
                reason=f"exception {winner.rule_id} overrides {base_id}",
                resolution="exception",
                policy=policy,
            )
        )
        for loser in ordered[1:]:
            suppressed.add(loser.rule_id)
            records.append(
                ConflictRecord(
                    rule_a_id=winner.rule_id,
                    rule_b_id=loser.rule_id,
                    reason=(
                        f"exception conflict: {loser.rule_id} loses to "
                        f"{winner.rule_id} for base {base_id}"
                    ),
                    resolution="exception",
                    policy=policy,
                )
            )
    return ExceptionResolution(
        suppressed_ids=tuple(sorted(suppressed)),
        overrides=overrides,
        records=tuple(records),
    )


def conflict_pairs(matched: Sequence[Rule]) -> list[tuple[Rule, Rule]]:
    """Authored conflict pairs among ``matched`` (explicit pairs, deduped).

    Both directions of a symmetric declaration collapse to one pair; pair
    order follows the (deterministic) input order.
    """
    remaining = {rule.rule_id: rule for rule in matched}
    seen: set[frozenset[str]] = set()
    pairs: list[tuple[Rule, Rule]] = []
    for rule in matched:
        for other_id in rule.conflicts_with:
            other = remaining.get(other_id)
            if other is None or other_id == rule.rule_id:
                continue
            key = frozenset({rule.rule_id, other_id})
            if key in seen:
                continue
            seen.add(key)
            pairs.append((rule, other))
    return pairs


def apply_conflict_policy(
    pairs: Sequence[tuple[Rule, Rule]],
    *,
    key_fn: Callable[[Rule], PrecedenceKey],
    policy: ConflictPolicy,
) -> tuple[frozenset[str], tuple[ConflictRecord, ...]]:
    """Apply the profile policy to conflict pairs (SPEC §9.1).

    ``FIRST_WINS`` suppresses the lower-precedence participant; ``REPORT_ALL``
    suppresses nothing. A ``ConflictRecord`` is always emitted — never silent.
    """
    if policy is ConflictPolicy.REPORT_ALL:
        records: list[ConflictRecord] = []
        for first, second in pairs:
            higher, lower = (first, second) if key_fn(first) <= key_fn(second) else (second, first)
            records.append(
                ConflictRecord(
                    rule_a_id=higher.rule_id,
                    rule_b_id=lower.rule_id,
                    reason=f"declared conflict between {higher.rule_id} and {lower.rule_id}",
                    resolution="reported together",
                    policy=policy,
                )
            )
        return frozenset(), tuple(records)

    suppressed: set[str] = set()
    records = []
    for first, second in pairs:
        # ascending §8 key: the smaller key is the higher-precedence rule
        winner, loser = (first, second) if key_fn(first) <= key_fn(second) else (second, first)
        suppressed.add(loser.rule_id)
        records.append(
            ConflictRecord(
                rule_a_id=winner.rule_id,
                rule_b_id=loser.rule_id,
                reason=f"declared conflict between {winner.rule_id} and {loser.rule_id}",
                resolution="first wins",
                policy=policy,
            )
        )
    return frozenset(suppressed), tuple(records)

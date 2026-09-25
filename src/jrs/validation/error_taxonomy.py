"""JRS Phase 5A: Error Attribution Taxonomy.

Automatic root-cause classification for every FALSE_POSITIVE and
FALSE_NEGATIVE :class:`EventPredictionMatch` produced by
:class:`jrs.validation.runner.HistoricalValidationRunner`, mapping each
failure back to its root provenance nodes in the Phase 3 evidence graph:

- ``RULE-*`` nodes  — the yoga rule that fired (or failed to fire),
  carrying its canonical ``YOGA-xxx`` rule id;
- ``FACT-*`` nodes  — the planetary-state facts supporting that rule
  (``F-xxx`` fact ids, reached over ``SUPPORTS`` edges);
- the ``TEMPORAL`` node — implicated when the rule has an ``AFFECTS``
  edge (Dasha/Transit layer participated in the outcome).

Failure kinds mirror the Phase F3 error-attribution report
(``scripts/error_attribution.py``):

===========================  ========  =========================================
Kind                         Polarity  Meaning
===========================  ========  =========================================
``COVERAGE_GAP``             FN        No rule node fired for the event at all.
``FORMATION_CANCELLED``      FN        Rule fired but the modifier pipeline
                                       (D9 / combustion / debilitation / node
                                       taint) cancelled the best prediction.
``DASHA_MISMATCH``           FP        Activation fired outside any event
                                       timing window (Dasha coincidence).
``DOMAIN_OVERLAP``           FP        Activation unsupported by any
                                       ground-truth event in its domain.
``UNCLASSIFIED``             —         Verdict not attributable (defensive).
===========================  ========  =========================================

Determinism contract
--------------------
This module performs no I/O, uses no wall-clock or randomness, and never
iterates unordered collections, so identical (match, graph) inputs always
yield byte-identical attributions — safe to embed in benchmark reports
and golden fixtures.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, replace
from enum import Enum
from typing import Any, Iterable

from jrs.prediction_engine.provenance import DirectedAcyclicGraph

from .models import (
    ChartValidationResult,
    EventPredictionMatch,
    PredictionVerdict,
    TimingMatchStatus,
)

__all__ = [
    "ErrorKind",
    "ErrorAttribution",
    "attribute_match",
    "attribute_result",
    "attach_provenance",
    "classify_match",
    "summarize_attributions",
]


class ErrorKind(Enum):
    """Failure-mode taxonomy for FP/FN matches (Phase F3 categories)."""

    COVERAGE_GAP = "COVERAGE_GAP"
    FORMATION_CANCELLED = "FORMATION_CANCELLED"
    DASHA_MISMATCH = "DASHA_MISMATCH"
    DOMAIN_OVERLAP = "DOMAIN_OVERLAP"
    UNCLASSIFIED = "UNCLASSIFIED"

    @property
    def polarity(self) -> str:
        """Whether this kind describes a false positive or false negative."""
        if self in (ErrorKind.COVERAGE_GAP, ErrorKind.FORMATION_CANCELLED):
            return "FN"
        if self in (ErrorKind.DASHA_MISMATCH, ErrorKind.DOMAIN_OVERLAP):
            return "FP"
        return ""


# Canonical rule ids live in RULE node payloads; the prediction's own
# node is EVALUATION. Kept here as the vocabulary of node types mined
# for root provenance.
_RULE_NODE_TYPE = "RULE"
_FACT_NODE_TYPE = "FACT"
_TEMPORAL_NODE_TYPE = "TEMPORAL"


def _is_unmatched_prediction(match: EventPredictionMatch) -> bool:
    """True for the runner's synthetic unmatched-prediction entries."""
    return match.event_id.startswith("unmatched_")


def classify_match(match: EventPredictionMatch) -> ErrorKind:
    """Classify one FP/FN match into the failure-kind taxonomy.

    Deterministic and pure: derived only from the match verdict, the
    attached provenance roots, and its timing status.
    """
    if match.verdict == PredictionVerdict.FALSE_NEGATIVE:
        if match.root_rule_ids:
            # A rule fired for this event but the best prediction was
            # cancelled (modifiers / D9 confirmation) — formation failure.
            return ErrorKind.FORMATION_CANCELLED
        # No rule node exists for this event in the evidence graph.
        return ErrorKind.COVERAGE_GAP

    if match.verdict == PredictionVerdict.FALSE_POSITIVE:
        if match.timing_status in (
            TimingMatchStatus.NO_OVERLAP,
            TimingMatchStatus.PREDICTED_ONLY,
        ) and match.timing_overlap_ratio <= 0.0:
            # Activation fired outside every event window — Dasha coincidence.
            return ErrorKind.DASHA_MISMATCH
        # Activation unsupported by ground truth in its domain.
        return ErrorKind.DOMAIN_OVERLAP

    return ErrorKind.UNCLASSIFIED


# ── Provenance mining ───────────────────────────────────────────────────────
def _mine_provenance(
    yoga_name: str,
    graph: DirectedAcyclicGraph,
) -> tuple[tuple[str, ...], tuple[str, ...], bool]:
    """Map a yoga name to its root provenance ids in the evidence graph.

    Returns:
        (canonical_rule_ids, fact_ids, temporal_affected) where
        canonical_rule_ids are the ``YOGA-xxx`` rule ids of every RULE
        node for this yoga, fact_ids are the ``F-xxx`` ids of the FACT
        nodes its rules connect to over ``SUPPORTS`` edges, and
        temporal_affected is True when any rule reaches the TEMPORAL
        node over an ``AFFECTS`` edge.

        Order is deterministic (graph construction order, deduplicated).
    """
    rule_node_ids: list[str] = []
    canonical_rule_ids: list[str] = []
    for node in graph.nodes:
        if node.node_type == _RULE_NODE_TYPE and node.payload.get("yoga_name") == yoga_name:
            rule_node_ids.append(node.node_id)
            rule_id = str(node.payload.get("rule_id", ""))
            if rule_id and rule_id not in canonical_rule_ids:
                canonical_rule_ids.append(rule_id)

    if not rule_node_ids:
        return (), (), False

    rule_id_set = set(rule_node_ids)
    fact_ids: list[str] = []
    temporal_affected = False
    for edge in graph.edges:
        if edge.source not in rule_id_set:
            continue
        target = graph.node_by_id(edge.target)
        if target is None:
            continue
        if target.node_type == _FACT_NODE_TYPE:
            fact_id = str(target.payload.get("fact_id", ""))
            if fact_id and fact_id not in fact_ids:
                fact_ids.append(fact_id)
        elif target.node_type == _TEMPORAL_NODE_TYPE:
            temporal_affected = True

    return tuple(canonical_rule_ids), tuple(fact_ids), temporal_affected


def attach_provenance(
    match: EventPredictionMatch,
    graph: DirectedAcyclicGraph,
) -> EventPredictionMatch:
    """Return a copy of ``match`` with root provenance node ids attached.

    Pure: the input match is untouched (frozen dataclass — a copy is
    returned with ``root_rule_ids`` / ``root_fact_ids`` /
    ``temporal_affected`` populated from the evidence graph).
    """
    rule_ids, fact_ids, temporal = _mine_provenance(match.yoga_name, graph)
    return replace(
        match,
        root_rule_ids=rule_ids,
        root_fact_ids=fact_ids,
        temporal_affected=temporal,
    )


# ── Attribution records ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class ErrorAttribution:
    """Root-cause attribution for one FP or FN prediction match.

    Attributes:
        chart_id: Chart the failure occurred on.
        event_id: Ground-truth event id (synthetic ``unmatched_<yoga>``
            for chart-level unsupported activations).
        yoga_name: Predicted yoga (empty for coverage gaps).
        verdict: Raw runner verdict ("FALSE_POSITIVE" / "FALSE_NEGATIVE").
        kind: Failure-mode category.
        polarity: "FP" or "FN" (empty only for UNCLASSIFIED).
        timing_status: Timing-match status of the original match.
        timing_overlap_ratio: Timing overlap ratio of the original match.
        confidence: Prediction confidence.
        root_rule_ids: Canonical ``YOGA-xxx`` rule ids implicated (empty
            for coverage gaps — the absence of a rule *is* the cause).
        root_fact_ids: ``F-xxx`` fact ids supporting the implicated rules.
        temporal_affected: Whether the TEMPORAL (Dasha/Transit) node is
            connected to the implicated rules.
        detail: Human-readable root-cause sentence.
    """

    chart_id: str
    event_id: str
    yoga_name: str
    verdict: str
    kind: ErrorKind
    polarity: str
    timing_status: str
    timing_overlap_ratio: float
    confidence: float
    root_rule_ids: tuple[str, ...]
    root_fact_ids: tuple[str, ...]
    temporal_affected: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "chart_id": self.chart_id,
            "event_id": self.event_id,
            "yoga_name": self.yoga_name,
            "verdict": self.verdict,
            "kind": self.kind.value,
            "polarity": self.polarity,
            "timing_status": self.timing_status,
            "timing_overlap_ratio": round(self.timing_overlap_ratio, 6),
            "confidence": round(self.confidence, 6),
            "root_rule_ids": list(self.root_rule_ids),
            "root_fact_ids": list(self.root_fact_ids),
            "temporal_affected": self.temporal_affected,
            "detail": self.detail,
        }


def _detail_for(match: EventPredictionMatch, kind: ErrorKind) -> str:
    """Human-readable root-cause sentence (deterministic)."""
    if kind == ErrorKind.COVERAGE_GAP:
        return "no RULE node fired for this event in the evidence graph"
    if kind == ErrorKind.FORMATION_CANCELLED:
        return (
            f"rule(s) {','.join(match.root_rule_ids)} fired but the best "
            "prediction was cancelled by the modifier pipeline"
        )
    if kind == ErrorKind.DASHA_MISMATCH:
        return (
            f"activation fired outside every event timing window "
            f"(timing_status={match.timing_status})"
        )
    if kind == ErrorKind.DOMAIN_OVERLAP:
        return (
            f"activation not supported by any ground-truth event "
            f"(timing_status={match.timing_status})"
        )
    return "unclassified failure mode"


def attribute_match(
    chart_id: str,
    match: EventPredictionMatch,
) -> ErrorAttribution:
    """Attribute one FP/FN match to its root provenance nodes.

    The match must already carry provenance roots (see
    :func:`attach_provenance`); unattached matches classify with empty
    roots, which for FALSE_NEGATIVE verdicts lands on COVERAGE_GAP.
    """
    kind = classify_match(match)
    return ErrorAttribution(
        chart_id=chart_id,
        event_id=match.event_id,
        yoga_name=match.yoga_name,
        verdict=match.verdict.value,
        kind=kind,
        polarity=kind.polarity,
        timing_status=match.timing_status.value,
        timing_overlap_ratio=match.timing_overlap_ratio,
        confidence=match.confidence,
        root_rule_ids=match.root_rule_ids,
        root_fact_ids=match.root_fact_ids,
        temporal_affected=match.temporal_affected,
        detail=_detail_for(match, kind),
    )


def attribute_result(
    result: ChartValidationResult,
    graph: DirectedAcyclicGraph,
) -> tuple[ErrorAttribution, ...]:
    """Attach provenance to and attribute every FP/FN match of one chart.

    Pure: ``result.matches`` entries are replaced with provenance-attached
    copies internally, but the caller-visible result object is unchanged.
    """
    attributed: list[ErrorAttribution] = []
    for match in result.matches:
        if match.verdict not in (
            PredictionVerdict.FALSE_POSITIVE,
            PredictionVerdict.FALSE_NEGATIVE,
        ):
            continue
        attached = attach_provenance(match, graph)
        attributed.append(attribute_match(result.chart_id, attached))
    return tuple(attributed)


# ── Aggregation ─────────────────────────────────────────────────────────────
def summarize_attributions(
    attributions: Iterable[ErrorAttribution],
) -> dict[str, Any]:
    """Aggregate attributions into a deterministic per-run summary.

    Output keys are sorted; ``top_facts`` is capped at the 10 most-implicated
    fact ids (ties broken alphabetically) to keep benchmark reports bounded.
    """
    items = list(attributions)
    by_kind: Counter[str] = Counter(a.kind.value for a in items)
    by_rule: Counter[str] = Counter(rid for a in items for rid in a.root_rule_ids)
    by_fact: Counter[str] = Counter(fid for a in items for fid in a.root_fact_ids)
    top_facts = sorted(by_fact.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
    return {
        "total_fp": sum(1 for a in items if a.polarity == "FP"),
        "total_fn": sum(1 for a in items if a.polarity == "FN"),
        "by_kind": {k: c for k, c in sorted(by_kind.items())},
        "by_rule": {k: c for k, c in sorted(by_rule.items())},
        "top_facts": dict(top_facts),
    }

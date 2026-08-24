"""Calibration metrics — Precision, Recall, F1, FPR, FNR, Timing Overlap.

Measures rule fidelity and implementation correctness against ground truth.
Does NOT claim empirical validity of astrology; this is strictly a
measurement tool for implementation correctness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# ── Status Classification Helpers ────────────────────────────────────────────

# Statuses that count as "predicted positive" for a given outcome.
_POSITIVE_STATUSES: frozenset[str] = frozenset({
    "STRONGLY_SUPPORTED",
    "SUPPORTED",
    "WEAKLY_SUPPORTED",
})

# Statuses that count as "predicted negative" for a given outcome.
_NEGATIVE_STATUSES: frozenset[str] = frozenset({
    "NEUTRAL",
    "CONTRADICTED",
    "STRONGLY_CONTRADICTED",
})


def _is_positive(status: str) -> bool:
    """Check if an assessment_status counts as a positive prediction."""
    return status in _POSITIVE_STATUSES


# ── Per-Outcome Metrics ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class OutcomeMetrics:
    """Metrics for a single outcome taxonomy."""

    outcome: str
    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    timing_overlap_score: float

    @property
    def precision(self) -> float:
        """Precision = TP / (TP + FP)."""
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        """Recall = TP / (TP + FN)."""
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1_score(self) -> float:
        """F1 = 2 * precision * recall / (precision + recall)."""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def false_positive_rate(self) -> float:
        """FPR = FP / (FP + TN)."""
        denom = self.false_positives + self.true_negatives
        return self.false_positives / denom if denom > 0 else 0.0

    @property
    def false_negative_rate(self) -> float:
        """FNR = FN / (FN + TP)."""
        denom = self.false_negatives + self.true_positives
        return self.false_negatives / denom if denom > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "outcome": self.outcome,
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
            "timing_overlap_score": round(self.timing_overlap_score, 4),
        }


# ── Domain-Level Metrics ─────────────────────────────────────────────────────


@dataclass(frozen=True)
class DomainMetrics:
    """Aggregated metrics for a single domain (e.g., marriage, career)."""

    domain: str
    outcome_metrics: tuple[OutcomeMetrics, ...] = ()
    total_charts: int = 0

    @property
    def precision(self) -> float:
        """Macro-averaged precision across outcomes."""
        if not self.outcome_metrics:
            return 0.0
        return sum(m.precision for m in self.outcome_metrics) / len(self.outcome_metrics)

    @property
    def recall(self) -> float:
        """Macro-averaged recall across outcomes."""
        if not self.outcome_metrics:
            return 0.0
        return sum(m.recall for m in self.outcome_metrics) / len(self.outcome_metrics)

    @property
    def f1_score(self) -> float:
        """Macro-averaged F1 across outcomes."""
        if not self.outcome_metrics:
            return 0.0
        return sum(m.f1_score for m in self.outcome_metrics) / len(self.outcome_metrics)

    @property
    def false_positive_rate(self) -> float:
        """Macro-averaged FPR across outcomes."""
        if not self.outcome_metrics:
            return 0.0
        return (
            sum(m.false_positive_rate for m in self.outcome_metrics)
            / len(self.outcome_metrics)
        )

    @property
    def false_negative_rate(self) -> float:
        """Macro-averaged FNR across outcomes."""
        if not self.outcome_metrics:
            return 0.0
        return (
            sum(m.false_negative_rate for m in self.outcome_metrics)
            / len(self.outcome_metrics)
        )

    @property
    def timing_overlap_score(self) -> float:
        """Average timing overlap across outcomes."""
        if not self.outcome_metrics:
            return 0.0
        return (
            sum(m.timing_overlap_score for m in self.outcome_metrics)
            / len(self.outcome_metrics)
        )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "domain": self.domain,
            "total_charts": self.total_charts,
            "outcome_count": len(self.outcome_metrics),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
            "timing_overlap_score": round(self.timing_overlap_score, 4),
            "outcomes": [m.to_dict() for m in self.outcome_metrics],
        }


# ── Overall Metrics ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CalibrationReport:
    """Complete calibration report across all domains."""

    domain_metrics: tuple[DomainMetrics, ...] = ()
    timestamp: str = ""

    @property
    def precision(self) -> float:
        """Macro-averaged precision across all domains."""
        if not self.domain_metrics:
            return 0.0
        return sum(d.precision for d in self.domain_metrics) / len(self.domain_metrics)

    @property
    def recall(self) -> float:
        """Macro-averaged recall across all domains."""
        if not self.domain_metrics:
            return 0.0
        return sum(d.recall for d in self.domain_metrics) / len(self.domain_metrics)

    @property
    def f1_score(self) -> float:
        """Macro-averaged F1 across all domains."""
        if not self.domain_metrics:
            return 0.0
        return sum(d.f1_score for d in self.domain_metrics) / len(self.domain_metrics)

    @property
    def false_positive_rate(self) -> float:
        """Macro-averaged FPR across all domains."""
        if not self.domain_metrics:
            return 0.0
        return (
            sum(d.false_positive_rate for d in self.domain_metrics)
            / len(self.domain_metrics)
        )

    @property
    def false_negative_rate(self) -> float:
        """Macro-averaged FNR across all domains."""
        if not self.domain_metrics:
            return 0.0
        return (
            sum(d.false_negative_rate for d in self.domain_metrics)
            / len(self.domain_metrics)
        )

    @property
    def timing_overlap_score(self) -> float:
        """Average timing overlap across all domains."""
        if not self.domain_metrics:
            return 0.0
        return (
            sum(d.timing_overlap_score for d in self.domain_metrics)
            / len(self.domain_metrics)
        )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "timestamp": self.timestamp,
            "domain_count": len(self.domain_metrics),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
            "false_negative_rate": round(self.false_negative_rate, 4),
            "timing_overlap_score": round(self.timing_overlap_score, 4),
            "domains": [d.to_dict() for d in self.domain_metrics],
        }

    def to_markdown(self) -> str:
        """Generate a Markdown summary report."""
        lines: list[str] = []
        lines.append("# Calibration Report")
        lines.append("")
        lines.append(f"**Timestamp:** {self.timestamp}")
        lines.append("")
        lines.append("## Overall Metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Precision | {self.precision:.4f} |")
        lines.append(f"| Recall | {self.recall:.4f} |")
        lines.append(f"| F1 Score | {self.f1_score:.4f} |")
        lines.append(f"| False Positive Rate | {self.false_positive_rate:.4f} |")
        lines.append(f"| False Negative Rate | {self.false_negative_rate:.4f} |")
        lines.append(f"| Timing Overlap Score | {self.timing_overlap_score:.4f} |")
        lines.append(f"| Domains Evaluated | {len(self.domain_metrics)} |")
        lines.append("")

        for dm in self.domain_metrics:
            lines.append(f"## {dm.domain}")
            lines.append("")
            lines.append(f"**Charts:** {dm.total_charts} | "
                         f"**Outcomes:** {len(dm.outcome_metrics)}")
            lines.append("")
            lines.append("| Outcome | Precision | Recall | F1 | FPR | FNR | Timing |")
            lines.append("|---------|-----------|--------|-----|-----|-----|--------|")
            for om in dm.outcome_metrics:
                lines.append(
                    f"| {om.outcome} "
                    f"| {om.precision:.4f} "
                    f"| {om.recall:.4f} "
                    f"| {om.f1_score:.4f} "
                    f"| {om.false_positive_rate:.4f} "
                    f"| {om.false_negative_rate:.4f} "
                    f"| {om.timing_overlap_score:.4f} |"
                )
            lines.append("")

        return "\n".join(lines)


# ── Metric Computation ───────────────────────────────────────────────────────


def compute_outcome_metrics(
    outcome: str,
    ground_truth_status: str,
    predicted_status: str,
    timing_match: bool = False,
) -> OutcomeMetrics:
    """Compute metrics for a single outcome across one chart.

    Args:
        outcome: The outcome taxonomy name.
        ground_truth_status: The expected assessment_status from the fixture.
        predicted_status: The system's generated assessment_status.
        timing_match: Whether the timing status matches ground truth.

    Returns:
        An OutcomeMetrics with TP/FP/TN/FN counts.
    """
    gt_positive = _is_positive(ground_truth_status)
    pred_positive = _is_positive(predicted_status)

    if gt_positive and pred_positive:
        tp, fp, tn, fn = 1, 0, 0, 0
    elif not gt_positive and pred_positive:
        tp, fp, tn, fn = 0, 1, 0, 0
    elif not gt_positive and not pred_positive:
        tp, fp, tn, fn = 0, 0, 1, 0
    else:  # gt_positive and not pred_positive
        tp, fp, tn, fn = 0, 0, 0, 1

    timing_score = 1.0 if timing_match else 0.0

    return OutcomeMetrics(
        outcome=outcome,
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        timing_overlap_score=timing_score,
    )


def compute_timing_overlap(
    ground_truth_timing: str,
    predicted_timing: str,
) -> bool:
    """Check if timing statuses match.

    Both INACTIVE timing statuses are considered a match (no timing
    claim was made by either side).
    """
    return ground_truth_timing == predicted_timing


# ── Comparative Calibration Report ───────────────────────────────────────────


class ComparativeCalibrationReport:
    """Comparative report: Single-System vs Multi-System metrics.

    Answers the question: Does multi-system convergence improve,
    degrade, or maintain the F1 score compared to single-system?
    """

    def __init__(
        self,
        single_system_report: CalibrationReport,
        multi_system_report: CalibrationReport,
        comparison_mode: str = "vedic_only_vs_multi",
    ) -> None:
        self.single_system_report = single_system_report
        self.multi_system_report = multi_system_report
        self.comparison_mode = comparison_mode

    @property
    def f1_delta(self) -> float:
        """Difference in F1: multi - single.

        Positive means multi-system improved F1.
        Negative means multi-system degraded F1.
        """
        return self.multi_system_report.f1_score - self.single_system_report.f1_score

    @property
    def precision_delta(self) -> float:
        """Difference in Precision: multi - single."""
        return (
            self.multi_system_report.precision
            - self.single_system_report.precision
        )

    @property
    def recall_delta(self) -> float:
        """Difference in Recall: multi - single."""
        return (
            self.multi_system_report.recall
            - self.single_system_report.recall
        )

    @property
    def timing_delta(self) -> float:
        """Difference in Timing Overlap: multi - single."""
        return (
            self.multi_system_report.timing_overlap_score
            - self.single_system_report.timing_overlap_score
        )

    @property
    def convergence_verdict(self) -> str:
        """String verdict on multi-system impact."""
        if self.f1_delta > 0.001:
            return "IMPROVED"
        elif self.f1_delta < -0.001:
            return "DEGRADED"
        else:
            return "MAINTAINED"

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "comparison_mode": self.comparison_mode,
            "single_system": self.single_system_report.to_dict(),
            "multi_system": self.multi_system_report.to_dict(),
            "deltas": {
                "precision": round(self.precision_delta, 4),
                "recall": round(self.recall_delta, 4),
                "f1_score": round(self.f1_delta, 4),
                "timing_overlap": round(self.timing_delta, 4),
            },
            "convergence_verdict": self.convergence_verdict,
        }

    def to_markdown(self) -> str:
        """Generate comparative Markdown report."""
        lines: list[str] = []
        lines.append("# Multi-System Empirical Calibration Report")
        lines.append("")
        lines.append(f"**Mode:** {self.comparison_mode}")
        lines.append("")
        lines.append("## Comparative Summary")
        lines.append("")
        lines.append(
            "| Metric | Single-System | Multi-System | Delta |"
        )
        lines.append(
            "|--------|--------------|-------------|-------|"
        )
        lines.append(
            f"| Precision "
            f"| {self.single_system_report.precision:.4f} "
            f"| {self.multi_system_report.precision:.4f} "
            f"| {self.precision_delta:+.4f} |"
        )
        lines.append(
            f"| Recall "
            f"| {self.single_system_report.recall:.4f} "
            f"| {self.multi_system_report.recall:.4f} "
            f"| {self.recall_delta:+.4f} |"
        )
        lines.append(
            f"| F1 Score "
            f"| {self.single_system_report.f1_score:.4f} "
            f"| {self.multi_system_report.f1_score:.4f} "
            f"| {self.f1_delta:+.4f} |"
        )
        lines.append(
            f"| Timing Overlap "
            f"| {self.single_system_report.timing_overlap_score:.4f} "
            f"| {self.multi_system_report.timing_overlap_score:.4f} "
            f"| {self.timing_delta:+.4f} |"
        )
        lines.append("")
        lines.append(
            f"**Convergence Verdict:** {self.convergence_verdict}"
        )
        lines.append("")

        if self.f1_delta > 0.001:
            lines.append(
                "Multi-system convergence **improved** F1 by "
                f"{self.f1_delta:+.4f}, demonstrating that "
                "independence-adjusted cross-system evidence adds "
                "measurable value."
            )
        elif self.f1_delta < -0.001:
            lines.append(
                "Multi-system convergence **degraded** F1 by "
                f"{self.f1_delta:+.4f}. This may indicate that "
                "the independence penalty is dampening valid "
                "convergence, or that non-Vedic systems add noise "
                "for these fixtures."
            )
        else:
            lines.append(
                "Multi-system convergence **maintained** F1 at "
                "essentially the same level, suggesting the "
                "independence penalty neither adds nor removes "
                "significant value."
            )
        lines.append("")

        # Domain-level comparison
        single_domains = {
            d.domain: d for d in self.single_system_report.domain_metrics
        }
        multi_domains = {
            d.domain: d for d in self.multi_system_report.domain_metrics
        }
        all_domains = sorted(set(single_domains) | set(multi_domains))

        if all_domains:
            lines.append("## Domain-Level Comparison")
            lines.append("")
            lines.append(
                "| Domain | Single F1 | Multi F1 | Delta | Verdict |"
            )
            lines.append(
                "|--------|-----------|----------|-------|---------|"
            )
            for domain in all_domains:
                s_dm = single_domains.get(domain)
                m_dm = multi_domains.get(domain)
                s_f1 = s_dm.f1_score if s_dm else 0.0
                m_f1 = m_dm.f1_score if m_dm else 0.0
                delta = m_f1 - s_f1
                if delta > 0.001:
                    verdict = "IMPROVED"
                elif delta < -0.001:
                    verdict = "DEGRADED"
                else:
                    verdict = "MAINTAINED"
                lines.append(
                    f"| {domain} "
                    f"| {s_f1:.4f} "
                    f"| {m_f1:.4f} "
                    f"| {delta:+.4f} "
                    f"| {verdict} |"
                )
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(
            "*Report generated by JRS Multi-System Calibration Pipeline."
        )
        lines.append(
            "Metrics measure implementation correctness against ground truth,"
        )
        lines.append(
            "not empirical validity of astrology.*"
        )
        lines.append("")

        return "\n".join(lines)

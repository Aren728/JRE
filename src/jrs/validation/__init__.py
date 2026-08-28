"""JRS Phase A: Empirical Validation Harness.

Ingests historical birth charts with verified life events, executes the
5-Layer Yoga Pipeline (frozen weights), and produces statistical evaluation
reports comparing predicted activations against real outcomes.

Usage::

    from jrs.validation import (
        BirthChart, BirthData, KnownEvent, EventDomain,
        HistoricalValidationRunner, StatisticalEvaluator,
    )

    chart = BirthChart(
        chart_id="chart_01",
        birth_data=BirthData(date="1988-06-15", time="09:00:00"),
        jre_facts={...},
        known_events=(KnownEvent(...),),
        domain=EventDomain.CAREER,
    )

    runner = HistoricalValidationRunner()
    result = runner.run_single_chart(chart)

    evaluator = StatisticalEvaluator()
    report = evaluator.evaluate([result])
"""

from .models import (
    BirthChart,
    BirthData,
    ChartValidationResult,
    ClassificationMetrics,
    DomainCalibration,
    EventDomain,
    EventPredictionMatch,
    KnownEvent,
    PredictionVerdict,
    PredictedYoga,
    StatisticalReport,
    TimingAnalysis,
    TimingMatchStatus,
    TimingWindow,
)
from .runner import HistoricalValidationRunner
from .stats import StatisticalEvaluator

__all__ = [
    "BirthChart",
    "BirthData",
    "ChartValidationResult",
    "ClassificationMetrics",
    "DomainCalibration",
    "EventDomain",
    "EventPredictionMatch",
    "HistoricalValidationRunner",
    "KnownEvent",
    "PredictionVerdict",
    "PredictedYoga",
    "StatisticalEvaluator",
    "StatisticalReport",
    "TimingAnalysis",
    "TimingMatchStatus",
    "TimingWindow",
]

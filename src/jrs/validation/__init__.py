"""JRS Phase A: Empirical Validation Harness.

Ingests historical birth charts with verified life events, executes the
5-Layer Yoga Pipeline (frozen weights), and produces statistical evaluation
reports comparing predicted activations against real outcomes.

JRS-087 additions: Blind Validation Protocol with SHA-256 sealed
prediction packets and independent ground-truth evaluation.

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

Blind Validation (JRS-087)::

    from jrs.validation import (
        ChartSubject, HistoricalEvent, BlindValidationProtocol,
        RoddenRating, DomainType, BirthProvenance,
    )

    protocol = BlindValidationProtocol()
    packet = protocol.generate_prediction_packet(subject, target_ts)
    metric = protocol.evaluate_prediction_against_event(packet, event)
"""

from .models import (
    BirthChart,
    BirthData,
    BirthProvenance,
    ChartSubject,
    ChartValidationResult,
    ClassificationMetrics,
    DomainCalibration,
    DomainType,
    EventDomain,
    EventPredictionMatch,
    FrozenPredictionPacket,
    HistoricalEvent,
    KnownEvent,
    MetricEvaluation,
    PredictionVerdict,
    PredictedYoga,
    RoddenRating,
    StatisticalReport,
    TimingAnalysis,
    TimingMatchStatus,
    TimingWindow,
)
from .protocol import BlindValidationProtocol
from .runner import HistoricalValidationRunner
from .stats import StatisticalEvaluator

__all__ = [
    "BirthChart",
    "BirthData",
    "BirthProvenance",
    "BlindValidationProtocol",
    "ChartSubject",
    "ChartValidationResult",
    "ClassificationMetrics",
    "DomainCalibration",
    "DomainType",
    "EventDomain",
    "EventPredictionMatch",
    "FrozenPredictionPacket",
    "HistoricalEvent",
    "HistoricalValidationRunner",
    "KnownEvent",
    "MetricEvaluation",
    "PredictionVerdict",
    "PredictedYoga",
    "RoddenRating",
    "StatisticalEvaluator",
    "StatisticalReport",
    "TimingAnalysis",
    "TimingMatchStatus",
    "TimingWindow",
]

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

from .calibration import CohortCalibrationEngine
from .models import (
    BatchValidationReport,
    BirthChart,
    BirthData,
    BirthProvenance,
    ChartSubject,
    ChartValidationResult,
    ClassificationMetrics,
    CohortCalibrationReport,
    CryptographicTamperError,
    DomainCalibration,
    DomainType,
    EventDomain,
    EventPredictionMatch,
    FrozenPredictionPacket,
    HistoricalEvent,
    KnownEvent,
    LayerPerformance,
    MetricEvaluation,
    PredictionVerdict,
    PredictedYoga,
    RoddenRating,
    SingleValidationReport,
    StatisticalReport,
    TimingAnalysis,
    TimingMatchStatus,
    TimingWindow,
    ValidationStatus,
)
from .datasets import DatasetLoader, REFERENCE_COHORT_12
from .protocol import BlindValidationProtocol
from .runner import BlindValidationRunner, HistoricalValidationRunner
from .stats import StatisticalEvaluator
from .storage import PredictionPacketStore

__all__ = [
    "BatchValidationReport",
    "BirthChart",
    "BirthData",
    "BirthProvenance",
    "BlindValidationProtocol",
    "BlindValidationRunner",
    "ChartSubject",
    "ChartValidationResult",
    "ClassificationMetrics",
    "CohortCalibrationEngine",
    "CohortCalibrationReport",
    "CryptographicTamperError",
    "DomainCalibration",
    "DomainType",
    "EventDomain",
    "EventPredictionMatch",
    "FrozenPredictionPacket",
    "HistoricalEvent",
    "HistoricalValidationRunner",
    "KnownEvent",
    "LayerPerformance",
    "MetricEvaluation",
    "PredictionPacketStore",
    "PredictionVerdict",
    "PredictedYoga",
    "RoddenRating",
    "SingleValidationReport",
    "StatisticalEvaluator",
    "StatisticalReport",
    "TimingAnalysis",
    "TimingMatchStatus",
    "TimingWindow",
    "DatasetLoader",
    "REFERENCE_COHORT_12",
    "ValidationStatus",
]

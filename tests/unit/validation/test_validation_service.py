"""Unit tests for ValidationService."""

from __future__ import annotations

from typing import Any

import pytest

from tests.unit.validation.conftest import make_extracted_trigger, make_known_event
from validation.errors import InvalidReferenceChartError, TriggerExtractionError
from validation.models import (
    EventType,
    ExtractedTrigger,
    ReferenceChart,
    TriggerSource,
    ValidationConfig,
    ValidationReport,
)
from validation.service import ValidationService


class FakeEngineOutput:
    """Minimal fake EngineOutput for testing."""

    def __init__(self, engine_name: str) -> None:
        self.engine_name = engine_name


class FakeEvidencePacket:
    """Minimal fake EvidencePacket for testing."""

    def __init__(
        self,
        engine_names: tuple[str, ...] = (),
        research: tuple[str, ...] = (),
    ) -> None:
        self.engine_outputs = tuple(FakeEngineOutput(n) for n in engine_names)
        self.research_evidence = research


class TestValidationServiceInit:
    """Tests for ValidationService initialization."""

    def test_default_config(self) -> None:
        svc = ValidationService()
        assert svc.config is not None
        assert svc.config.version == "1.0"

    def test_custom_config(self) -> None:
        config = ValidationConfig(match_threshold=0.7)
        svc = ValidationService(config=config)
        assert svc.config.match_threshold == 0.7


class TestValidationServiceRunValidation:
    """Tests for the run_validation method."""

    def test_perfect_match(self) -> None:
        svc = ValidationService(config=ValidationConfig(
            trigger_weights={},
            source_reliability={},
        ))
        chart = ReferenceChart(
            chart_id="test_001",
            known_events=(
                make_known_event(
                    event_type=EventType.MARRIAGE,
                    triggers=("Venus_Yoga",),
                ),
            ),
        )
        packet = FakeEvidencePacket(engine_names=("yoga",))
        report = svc.run_validation(chart, packet)
        assert report.total_charts == 1
        assert len(report.results) == 1
        result = report.results[0]
        assert result.chart_id == "test_001"
        assert result.total_events == 1

    def test_empty_chart_raises(self) -> None:
        svc = ValidationService()
        chart = ReferenceChart(chart_id="test_empty", known_events=())
        with pytest.raises(InvalidReferenceChartError, match="no known events"):
            svc.run_validation(chart)

    def test_empty_chart_id_raises(self) -> None:
        svc = ValidationService()
        chart = ReferenceChart(chart_id="", known_events=(make_known_event(),))
        with pytest.raises(InvalidReferenceChartError, match="chart_id must not be empty"):
            svc.run_validation(chart)

    def test_without_jrs_output(self) -> None:
        svc = ValidationService()
        chart = ReferenceChart(
            chart_id="test_002",
            known_events=(make_known_event(),),
            ground_truth={"lagna": "CANCER"},
        )
        report = svc.run_validation(chart)
        assert report.total_charts == 1
        assert len(report.results[0].actual_triggers) > 0

    def test_invalid_jrs_output_raises(self) -> None:
        svc = ValidationService()
        chart = ReferenceChart(
            chart_id="test_003",
            known_events=(make_known_event(),),
        )
        with pytest.raises(TriggerExtractionError):
            svc.run_validation(chart, jrs_output="invalid")

    def test_multiple_events(self) -> None:
        svc = ValidationService(config=ValidationConfig(
            trigger_weights={},
            source_reliability={},
        ))
        chart = ReferenceChart(
            chart_id="test_multi",
            known_events=(
                make_known_event(triggers=("Venus_Yoga",)),
                make_known_event(
                    event_type=EventType.PROMOTION,
                    triggers=("Saturn_Yoga",),
                ),
            ),
        )
        packet = FakeEvidencePacket(engine_names=("yoga",))
        report = svc.run_validation(chart, packet)
        result = report.results[0]
        assert result.total_events == 2
        assert len(result.expected_triggers) == 2


class TestValidationServiceBatchValidation:
    """Tests for the run_batch_validation method."""

    def test_batch_multiple_charts(self) -> None:
        svc = ValidationService(config=ValidationConfig(
            trigger_weights={},
            source_reliability={},
        ))
        charts = (
            ReferenceChart(
                chart_id="chart_1",
                known_events=(make_known_event(triggers=("Venus_Yoga",),),),
            ),
            ReferenceChart(
                chart_id="chart_2",
                known_events=(
                    make_known_event(
                        event_type=EventType.PROMOTION,
                        triggers=("Saturn_Yoga",),
                    ),
                ),
            ),
        )
        report = svc.run_batch_validation(charts)
        assert report.total_charts == 2
        assert len(report.results) == 2

    def test_batch_empty(self) -> None:
        svc = ValidationService()
        report = svc.run_batch_validation(())
        assert report.total_charts == 0
        assert report.overall_score == 0.0

    def test_batch_with_jrs_outputs(self) -> None:
        svc = ValidationService(config=ValidationConfig(
            trigger_weights={},
            source_reliability={},
        ))
        charts = (
            ReferenceChart(
                chart_id="chart_1",
                known_events=(make_known_event(triggers=("Venus_Yoga",),),),
            ),
        )
        outputs = (FakeEvidencePacket(engine_names=("yoga",)),)
        report = svc.run_batch_validation(charts, outputs)
        assert report.total_charts == 1


class TestValidationServiceDeterminism:
    """Tests for deterministic output."""

    def test_same_input_same_output(self) -> None:
        svc = ValidationService(config=ValidationConfig(
            trigger_weights={},
            source_reliability={},
        ))
        chart = ReferenceChart(
            chart_id="det_001",
            known_events=(make_known_event(triggers=("Venus_Yoga",),),),
        )
        packet = FakeEvidencePacket(engine_names=("yoga",))
        r1 = svc.run_validation(chart, packet)
        r2 = svc.run_validation(chart, packet)
        assert r1.results[0].match_score == r2.results[0].match_score
        assert r1.results[0].expected_triggers == r2.results[0].expected_triggers

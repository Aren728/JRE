"""Integration tests for the Validation system against reference chart fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from validation.config import load_validation_config
from validation.models import (
    EventType,
    ExtractedTrigger,
    ReferenceChart,
    TriggerSource,
    ValidationReport,
    extract_triggers_from_engines,
)
from validation.service import ValidationService
from validation.serialize import (
    reference_chart_from_dict,
    result_to_json,
    validation_report_from_dict,
)

_FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures" / "validation_charts"


@pytest.fixture
def reference_chart_01() -> ReferenceChart:
    """Load reference_chart_01.json from fixtures."""
    path = _FIXTURES_DIR / "reference_chart_01.json"
    with path.open() as f:
        data = json.load(f)
    return reference_chart_from_dict(data)


@pytest.fixture
def svc() -> ValidationService:
    """Create a ValidationService with the real config."""
    return ValidationService()


class TestReferenceChartLoading:
    """Integration tests for loading reference charts from fixtures."""

    def test_fixture_exists(self) -> None:
        path = _FIXTURES_DIR / "reference_chart_01.json"
        assert path.exists()

    def test_fixture_valid_json(self) -> None:
        path = _FIXTURES_DIR / "reference_chart_01.json"
        with path.open() as f:
            data = json.load(f)
        assert "chart_id" in data
        assert "known_events" in data

    def test_fixture_has_events(self, reference_chart_01: ReferenceChart) -> None:
        assert len(reference_chart_01.known_events) == 5

    def test_fixture_event_types(self, reference_chart_01: ReferenceChart) -> None:
        types = {e.event_type for e in reference_chart_01.known_events}
        assert EventType.MARRIAGE in types
        assert EventType.PROMOTION in types
        assert EventType.CHILD_BIRTH in types

    def test_fixture_has_ground_truth(self, reference_chart_01: ReferenceChart) -> None:
        assert "lagna_rashi" in reference_chart_01.ground_truth
        assert "moon_rashi" in reference_chart_01.ground_truth


class TestValidationWithFixture:
    """Integration tests for running validation against the reference chart."""

    def test_run_validation_no_jrs(
        self,
        svc: ValidationService,
        reference_chart_01: ReferenceChart,
    ) -> None:
        report = svc.run_validation(reference_chart_01)
        assert report.total_charts == 1
        result = report.results[0]
        assert result.chart_id == "validation_chart_01"
        assert result.total_events == 5
        assert len(result.expected_triggers) > 0

    def test_run_validation_with_jrs(
        self,
        svc: ValidationService,
        reference_chart_01: ReferenceChart,
    ) -> None:
        # Simulate JRS output with some matching engines
        from tests.unit.validation.test_validation_service import FakeEvidencePacket

        packet = FakeEvidencePacket(
            engine_names=("yoga", "dasha", "bhava", "karaka"),
            research=("marriage_indicators", "career_indicators"),
        )
        report = svc.run_validation(reference_chart_01, packet)
        assert report.total_charts == 1
        result = report.results[0]
        assert len(result.actual_triggers) > 0

    def test_expected_triggers_all_events(
        self,
        svc: ValidationService,
        reference_chart_01: ReferenceChart,
    ) -> None:
        report = svc.run_validation(reference_chart_01)
        result = report.results[0]
        # All expected triggers from all 5 events should be collected
        assert "Venus_Yoga" in result.expected_triggers
        assert "Saturn_Mahadasha" in result.expected_triggers
        assert "Jupiter_Mahadasha" in result.expected_triggers
        assert "7th_Lord_Yoga" in result.expected_triggers

    def test_match_score_is_bounded(
        self,
        svc: ValidationService,
        reference_chart_01: ReferenceChart,
    ) -> None:
        report = svc.run_validation(reference_chart_01)
        for result in report.results:
            assert 0.0 <= result.match_score <= 1.0


class TestConfigLoading:
    """Integration tests for config loading."""

    def test_loads_default_config(self) -> None:
        config = load_validation_config()
        assert config.version == "1.0"
        assert config.match_threshold == 0.5

    def test_trigger_weights_loaded(self) -> None:
        config = load_validation_config()
        assert "Venus_Yoga" in config.trigger_weights
        assert "Saturn_Mahadasha" in config.trigger_weights

    def test_source_reliability_loaded(self) -> None:
        config = load_validation_config()
        assert "yoga" in config.source_reliability
        assert "dasha" in config.source_reliability


class TestTriggerExtraction:
    """Integration tests for trigger extraction from engines."""

    def test_all_engine_sources(self) -> None:
        engine_names = (
            "yoga", "dasha", "bala", "ashtakavarga", "avastha",
            "karaka", "drik", "synthesis", "bhava", "jaimini", "tajika",
        )
        triggers = extract_triggers_from_engines(engine_names)
        assert len(triggers) == 11
        sources = {t.source for t in triggers}
        expected_sources = set(TriggerSource)
        assert sources == expected_sources

    def test_research_topics_added(self) -> None:
        triggers = extract_triggers_from_engines(
            ("yoga",),
            research_evidence=("topic_a", "topic_b"),
        )
        assert len(triggers) == 3
        research = [t for t in triggers if t.trigger_id.startswith("research_")]
        assert len(research) == 2


class TestSerializationRoundTrip:
    """Integration tests for serialization round-trip."""

    def test_report_round_trip(
        self,
        svc: ValidationService,
        reference_chart_01: ReferenceChart,
    ) -> None:
        report = svc.run_validation(reference_chart_01)
        d = report.to_dict()
        restored = validation_report_from_dict(d)
        assert restored.total_charts == report.total_charts
        assert len(restored.results) == len(report.results)

    def test_report_json_serializable(
        self,
        svc: ValidationService,
        reference_chart_01: ReferenceChart,
    ) -> None:
        report = svc.run_validation(reference_chart_01)
        json_str = result_to_json(report)
        parsed = json.loads(json_str)
        assert "results" in parsed
        assert "overall_score" in parsed

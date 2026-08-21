"""Unit tests for validation models and trigger extraction logic."""

from __future__ import annotations

import json

import pytest

from tests.unit.validation.conftest import make_extracted_trigger, make_known_event
from validation.models import (
    EventType,
    ExtractedTrigger,
    KnownEvent,
    ReferenceChart,
    TriggerSource,
    ValidationConfig,
    ValidationReport,
    ValidationResult,
    compute_match_score,
    extract_triggers_from_engines,
    find_missing_and_false_positives,
)


class TestEventType:
    """Tests for the EventType enum."""

    def test_all_types_have_string_values(self) -> None:
        for et in EventType:
            assert isinstance(et.value, str)
            assert et.value == et.name

    def test_event_type_count(self) -> None:
        assert len(EventType) == 16

    def test_event_type_from_value(self) -> None:
        assert EventType("MARRIAGE") is EventType.MARRIAGE
        assert EventType("PROMOTION") is EventType.PROMOTION

    def test_invalid_event_type(self) -> None:
        with pytest.raises(ValueError):
            EventType("INVALID")


class TestTriggerSource:
    """Tests for the TriggerSource enum."""

    def test_all_sources_have_string_values(self) -> None:
        for ts in TriggerSource:
            assert isinstance(ts.value, str)

    def test_trigger_source_count(self) -> None:
        assert len(TriggerSource) == 11

    def test_trigger_source_from_value(self) -> None:
        assert TriggerSource("YOGA") is TriggerSource.YOGA
        assert TriggerSource("DASHA") is TriggerSource.DASHA


class TestKnownEvent:
    """Tests for the KnownEvent model."""

    def test_creation(self) -> None:
        event = KnownEvent(
            event_date_utc="2020-01-01T00:00:00Z",
            event_type=EventType.MARRIAGE,
            expected_triggers=("Venus_Yoga",),
        )
        assert event.event_type is EventType.MARRIAGE
        assert event.expected_triggers == ("Venus_Yoga",)

    def test_frozen(self) -> None:
        event = make_known_event()
        with pytest.raises(AttributeError):
            event.description = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        event = KnownEvent(
            event_date_utc="2020-01-01T00:00:00Z",
            event_type=EventType.PROMOTION,
            expected_triggers=("10th_Lord_Yoga",),
            description="Promotion",
        )
        d = event.to_dict()
        assert d["event_type"] == "PROMOTION"
        assert d["expected_triggers"] == ["10th_Lord_Yoga"]

    def test_to_dict_deterministic(self) -> None:
        event = make_known_event()
        d1 = event.to_dict()
        d2 = event.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_defaults(self) -> None:
        event = KnownEvent(
            event_date_utc="2020-01-01T00:00:00Z",
            event_type=EventType.OTHER,
        )
        assert event.expected_triggers == ()
        assert event.description == ""


class TestReferenceChart:
    """Tests for the ReferenceChart model."""

    def test_creation(self) -> None:
        chart = ReferenceChart(
            chart_id="test_001",
            birth_data={"date": "1990-01-01"},
        )
        assert chart.chart_id == "test_001"

    def test_frozen(self) -> None:
        chart = ReferenceChart(chart_id="test_001")
        with pytest.raises(AttributeError):
            chart.chart_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        chart = ReferenceChart(
            chart_id="test_001",
            birth_data={"time": "12:00:00"},
        )
        d = chart.to_dict()
        assert d["chart_id"] == "test_001"
        assert d["birth_data"]["time"] == "12:00:00"

    def test_to_dict_sorted_birth_data(self) -> None:
        chart = ReferenceChart(
            chart_id="test_001",
            birth_data={"z": "1", "a": "2"},
        )
        d = chart.to_dict()
        keys = list(d["birth_data"].keys())
        assert keys == sorted(keys)


class TestExtractedTrigger:
    """Tests for the ExtractedTrigger model."""

    def test_creation(self) -> None:
        trigger = ExtractedTrigger(
            trigger_id="yoga_present",
            source=TriggerSource.YOGA,
        )
        assert trigger.trigger_id == "yoga_present"
        assert trigger.source is TriggerSource.YOGA

    def test_defaults(self) -> None:
        trigger = ExtractedTrigger(trigger_id="test", source=TriggerSource.YOGA)
        assert trigger.confidence == 1.0
        assert trigger.metadata == ""

    def test_to_dict(self) -> None:
        trigger = ExtractedTrigger(
            trigger_id="dasha_present",
            source=TriggerSource.DASHA,
            confidence=0.9,
        )
        d = trigger.to_dict()
        assert d["trigger_id"] == "dasha_present"
        assert d["source"] == "DASHA"
        assert d["confidence"] == 0.9

    def test_frozen(self) -> None:
        trigger = ExtractedTrigger(trigger_id="test", source=TriggerSource.YOGA)
        with pytest.raises(AttributeError):
            trigger.trigger_id = "changed"  # type: ignore[misc]


class TestExtractTriggersFromEngines:
    """Tests for the extract_triggers_from_engines function."""

    def test_single_engine(self) -> None:
        triggers = extract_triggers_from_engines(("yoga",))
        assert len(triggers) == 1
        assert triggers[0].trigger_id == "yoga_present"
        assert triggers[0].source is TriggerSource.YOGA

    def test_multiple_engines(self) -> None:
        triggers = extract_triggers_from_engines(("yoga", "dasha", "bala"))
        assert len(triggers) == 3
        ids = {t.trigger_id for t in triggers}
        assert ids == {"yoga_present", "dasha_present", "bala_present"}

    def test_unknown_engine_skipped(self) -> None:
        triggers = extract_triggers_from_engines(("yoga", "unknown_engine"))
        assert len(triggers) == 1
        assert triggers[0].trigger_id == "yoga_present"

    def test_research_evidence_added(self) -> None:
        triggers = extract_triggers_from_engines(
            ("yoga",),
            research_evidence=("career_indicators",),
        )
        assert len(triggers) == 2
        research = [t for t in triggers if t.trigger_id.startswith("research_")]
        assert len(research) == 1
        assert research[0].source is TriggerSource.SYNTHESIS

    def test_source_reliability_applied(self) -> None:
        triggers = extract_triggers_from_engines(
            ("yoga",),
            source_reliability={"yoga": 0.8},
        )
        assert triggers[0].confidence == 0.8

    def test_empty_engines(self) -> None:
        triggers = extract_triggers_from_engines(())
        assert triggers == ()

    def test_deterministic_output(self) -> None:
        t1 = extract_triggers_from_engines(("yoga", "dasha"))
        t2 = extract_triggers_from_engines(("yoga", "dasha"))
        ids1 = [t.trigger_id for t in t1]
        ids2 = [t.trigger_id for t in t2]
        assert ids1 == ids2


class TestComputeMatchScore:
    """Tests for the compute_match_score function."""

    def test_perfect_match(self) -> None:
        actual = (make_extracted_trigger("Venus_Yoga"),)
        score = compute_match_score(("Venus_Yoga",), actual)
        assert score == 1.0

    def test_no_match(self) -> None:
        actual = (make_extracted_trigger("Saturn_Yoga"),)
        score = compute_match_score(("Venus_Yoga",), actual)
        assert score == 0.0

    def test_empty_both(self) -> None:
        score = compute_match_score((), ())
        assert score == 1.0

    def test_empty_expected(self) -> None:
        actual = (make_extracted_trigger("Venus_Yoga"),)
        score = compute_match_score((), actual)
        assert score == 0.0

    def test_empty_actual(self) -> None:
        score = compute_match_score(("Venus_Yoga",), ())
        assert score == 0.0

    def test_partial_match(self) -> None:
        actual = (
            make_extracted_trigger("Venus_Yoga"),
            make_extracted_trigger("Other_Yoga"),
        )
        score = compute_match_score(("Venus_Yoga", "Saturn_Yoga"), actual)
        # precision = 1/2, recall = 1/2, f1 = 1/2
        assert abs(score - 0.5) < 0.01

    def test_weighted_match(self) -> None:
        actual = (make_extracted_trigger("Venus_Yoga"),)
        weights = {"Venus_Yoga": 2.0}
        score = compute_match_score(("Venus_Yoga",), actual, weights)
        assert score == 1.0

    def test_weighted_partial(self) -> None:
        actual = (make_extracted_trigger("Venus_Yoga"),)
        weights = {"Venus_Yoga": 2.0, "Saturn_Yoga": 1.0}
        score = compute_match_score(
            ("Venus_Yoga", "Saturn_Yoga"),
            actual,
            weights,
        )
        # matched_weight=2, expected_weight=3, actual_weight=2
        # precision = 2/2 = 1.0, recall = 2/3 ≈ 0.667
        # f1 = 2 * 1.0 * 0.667 / (1.0 + 0.667) ≈ 0.8
        assert 0.7 < score < 0.9

    def test_multiple_triggers(self) -> None:
        actual = (
            make_extracted_trigger("Venus_Yoga"),
            make_extracted_trigger("Saturn_Yoga"),
        )
        score = compute_match_score(
            ("Venus_Yoga", "Saturn_Yoga"),
            actual,
        )
        assert score == 1.0


class TestFindMissingAndFalsePositives:
    """Tests for the find_missing_and_false_positives function."""

    def test_all_match(self) -> None:
        actual = (make_extracted_trigger("Venus_Yoga"),)
        missing, false_pos = find_missing_and_false_positives(
            ("Venus_Yoga",), actual,
        )
        assert missing == ()
        assert false_pos == ()

    def test_missing_triggers(self) -> None:
        actual = (make_extracted_trigger("Venus_Yoga"),)
        missing, _ = find_missing_and_false_positives(
            ("Venus_Yoga", "Saturn_Yoga"), actual,
        )
        assert missing == ("Saturn_Yoga",)

    def test_false_positives(self) -> None:
        actual = (
            make_extracted_trigger("Venus_Yoga"),
            make_extracted_trigger("Other_Yoga"),
        )
        _, false_pos = find_missing_and_false_positives(
            ("Venus_Yoga",), actual,
        )
        assert false_pos == ("Other_Yoga",)

    def test_both_missing_and_false_positives(self) -> None:
        actual = (
            make_extracted_trigger("Venus_Yoga"),
            make_extracted_trigger("Other_Yoga"),
        )
        missing, false_pos = find_missing_and_false_positives(
            ("Venus_Yoga", "Saturn_Yoga"), actual,
        )
        assert missing == ("Saturn_Yoga",)
        assert false_pos == ("Other_Yoga",)

    def test_empty_actual(self) -> None:
        missing, false_pos = find_missing_and_false_positives(
            ("Venus_Yoga",), (),
        )
        assert missing == ("Venus_Yoga",)
        assert false_pos == ()

    def test_empty_expected(self) -> None:
        actual = (make_extracted_trigger("Venus_Yoga"),)
        missing, false_pos = find_missing_and_false_positives((), actual)
        assert missing == ()
        assert false_pos == ("Venus_Yoga",)


class TestValidationResult:
    """Tests for the ValidationResult model."""

    def test_creation(self) -> None:
        result = ValidationResult(
            chart_id="test_001",
            expected_triggers=("Venus_Yoga",),
            match_score=0.85,
        )
        assert result.chart_id == "test_001"
        assert result.match_score == 0.85

    def test_to_dict(self) -> None:
        result = ValidationResult(
            chart_id="test_001",
            expected_triggers=("Venus_Yoga",),
            match_score=0.85,
            missing_triggers=("Saturn_Yoga",),
        )
        d = result.to_dict()
        assert d["chart_id"] == "test_001"
        assert d["match_score"] == 0.85
        assert d["missing_triggers"] == ["Saturn_Yoga"]

    def test_frozen(self) -> None:
        result = ValidationResult(chart_id="test_001")
        with pytest.raises(AttributeError):
            result.chart_id = "changed"  # type: ignore[misc]


class TestValidationReport:
    """Tests for the ValidationReport model."""

    def test_creation(self) -> None:
        report = ValidationReport(
            results=(ValidationResult(chart_id="test_001"),),
            overall_score=0.9,
            total_charts=1,
        )
        assert report.total_charts == 1
        assert report.overall_score == 0.9

    def test_to_dict_deterministic(self) -> None:
        report = ValidationReport(
            results=(ValidationResult(chart_id="test_001"),),
            overall_score=0.9,
        )
        d1 = report.to_dict()
        d2 = report.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_empty_report(self) -> None:
        report = ValidationReport()
        d = report.to_dict()
        assert d["results"] == []
        assert d["overall_score"] == 0.0


class TestValidationConfig:
    """Tests for the ValidationConfig model."""

    def test_defaults(self) -> None:
        config = ValidationConfig()
        assert config.version == "1.0"
        assert config.match_threshold == 0.5
        assert config.trigger_weights == {}

    def test_frozen(self) -> None:
        config = ValidationConfig()
        with pytest.raises(AttributeError):
            config.version = "changed"  # type: ignore[misc]

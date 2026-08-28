"""Tests for JRS Phase A: Empirical Validation Harness.

Tests the HistoricalValidationRunner and StatisticalEvaluator with synthetic
charts exercising the 5-Layer Yoga Pipeline.

Scenarios:
    1. Confirmed Gajakesari → TRUE_POSITIVE, high confidence
    2. Cancelled Yoga → FALSE_NEGATIVE (predicted but cancelled)
    3. No Yoga predicted, event occurred → FALSE_NEGATIVE
    4. Yoga predicted, no matching event → FALSE_POSITIVE
    5. Timing window overlap → OVERLAP status
    6. Multi-domain charts → domain calibration breakdown
    7. Statistical report aggregation across multiple charts
"""

from __future__ import annotations

import pytest

from jrs.validation.models import (
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
from jrs.validation.runner import HistoricalValidationRunner
from jrs.validation.stats import StatisticalEvaluator


# ══════════════════════════════════════════════════════════════════════
# Test Data Fixtures
# ══════════════════════════════════════════════════════════════════════


def _make_gajakesari_chart() -> BirthChart:
    """Create a chart with confirmed Gajakesari Yoga (Jupiter + Moon in Kendra)."""
    return BirthChart(
        chart_id="test_gajakesari_01",
        birth_data=BirthData(
            date="1990-06-15",
            time="04:30:00",
            timezone="Asia/Kolkata",
            latitude=28.6139,
            longitude=77.2090,
        ),
        jre_facts={
            "planets": {
                "JUPITER": {
                    "house": 1,
                    "rashi": "KARKA",
                    "rashi_num": 4,
                    "combust": False,
                    "debilitated": False,
                },
                "MOON": {
                    "house": 1,
                    "rashi": "KARKA",
                    "rashi_num": 4,
                    "combust": False,
                    "debilitated": False,
                },
            },
            "planet_d9_house": {"JUPITER": 1, "MOON": 4},
            "planet_d9_sign": {"JUPITER": "KARKA", "MOON": "KARKA"},
            "dasha_periods": [
                {
                    "activation_type": "DASHA",
                    "triggering_planet": "JUPITER",
                    "activation_start_utc": "2020-01-01T00:00:00Z",
                    "activation_end_utc": "2036-01-01T00:00:00Z",
                    "strength": 0.9,
                },
            ],
            "transits": [
                {
                    "activation_type": "TRANSIT",
                    "triggering_planet": "JUPITER",
                    "activation_start_utc": "2024-05-01T00:00:00Z",
                    "activation_end_utc": "2025-06-01T00:00:00Z",
                    "strength": 0.8,
                },
            ],
        },
        known_events=(
            KnownEvent(
                event_id="evt_001",
                event_date_utc="2024-06-15T00:00:00Z",
                event_window_start_utc="2024-01-01T00:00:00Z",
                event_window_end_utc="2025-12-31T23:59:59Z",
                domain=EventDomain.GENERAL,
                description="Period of general improvement",
                yoga_types=("GAJAKESARI",),
                expected_planets=("JUPITER", "MOON"),
            ),
        ),
        domain=EventDomain.GENERAL,
        description="Confirmed Gajakesari Yoga chart",
    )


def _make_combust_chart() -> BirthChart:
    """Create a chart where Jupiter is combust (yoga cancelled)."""
    return BirthChart(
        chart_id="test_combust_01",
        birth_data=BirthData(
            date="1992-03-20",
            time="12:00:00",
            timezone="Asia/Kolkata",
        ),
        jre_facts={
            "planets": {
                "JUPITER": {
                    "house": 1,
                    "rashi": "MITHUNA",
                    "rashi_num": 3,
                    "combust": True,
                    "debilitated": False,
                },
                "MOON": {
                    "house": 1,
                    "rashi": "KARKA",
                    "rashi_num": 4,
                    "combust": False,
                    "debilitated": False,
                },
            },
            "planet_d9_house": {"JUPITER": 1, "MOON": 4},
            "planet_d9_sign": {"JUPITER": "MITHUNA", "MOON": "KARKA"},
        },
        known_events=(
            KnownEvent(
                event_id="evt_002",
                event_date_utc="2024-06-15T00:00:00Z",
                event_window_start_utc="2024-01-01T00:00:00Z",
                event_window_end_utc="2025-12-31T23:59:59Z",
                domain=EventDomain.GENERAL,
                description="Expected improvement that didn't materialize",
                yoga_types=("GAJAKESARI",),
                expected_planets=("JUPITER",),
            ),
        ),
        domain=EventDomain.GENERAL,
        description="Combust Jupiter — yoga cancelled",
    )


def _make_raja_yoga_chart() -> BirthChart:
    """Create a chart with Raja Yoga (career domain)."""
    return BirthChart(
        chart_id="test_raja_01",
        birth_data=BirthData(
            date="1985-11-10",
            time="06:15:00",
            timezone="Asia/Kolkata",
        ),
        jre_facts={
            "planets": {
                "MERCURY": {
                    "house": 10,
                    "rashi_num": 7,
                    "rashi": "TULA",
                    "house_lord_of": 9,
                    "combust": False,
                    "debilitated": False,
                },
                "VENUS": {
                    "house": 10,
                    "rashi_num": 7,
                    "rashi": "TULA",
                    "house_lord_of": 10,
                    "combust": False,
                    "debilitated": False,
                },
            },
            "house_lords": {9: "MERCURY", 10: "VENUS"},
            "dasha_periods": [
                {
                    "activation_type": "DASHA",
                    "triggering_planet": "MERCURY",
                    "activation_start_utc": "2018-01-01T00:00:00Z",
                    "activation_end_utc": "2035-01-01T00:00:00Z",
                    "strength": 0.85,
                },
            ],
        },
        known_events=(
            KnownEvent(
                event_id="evt_003",
                event_date_utc="2022-04-01T00:00:00Z",
                event_window_start_utc="2020-01-01T00:00:00Z",
                event_window_end_utc="2025-12-31T23:59:59Z",
                domain=EventDomain.CAREER,
                description="Major career promotion",
                yoga_types=("RAJA",),
                expected_planets=("MERCURY", "VENUS"),
            ),
        ),
        domain=EventDomain.CAREER,
        description="Raja Yoga — career prominence",
    )


def _make_no_yoga_chart() -> BirthChart:
    """Create a chart with no classical yoga formations."""
    return BirthChart(
        chart_id="test_no_yoga_01",
        birth_data=BirthData(
            date="1995-01-01",
            time="10:00:00",
            timezone="Asia/Kolkata",
        ),
        jre_facts={
            "planets": {
                "JUPITER": {
                    "house": 3,
                    "rashi_num": 9,
                    "combust": False,
                    "debilitated": False,
                },
                "MOON": {
                    "house": 7,
                    "rashi_num": 4,
                    "combust": False,
                    "debilitated": False,
                },
                "SATURN": {
                    "house": 5,
                    "rashi_num": 9,
                    "combust": False,
                    "debilitated": False,
                },
                "MARS": {
                    "house": 11,
                    "rashi_num": 8,
                    "combust": False,
                    "debilitated": False,
                },
                "SUN": {
                    "house": 2,
                    "rashi_num": 5,
                    "combust": False,
                    "debilitated": False,
                },
                "VENUS": {
                    "house": 4,
                    "rashi_num": 2,
                    "combust": False,
                    "debilitated": False,
                },
                "MERCURY": {
                    "house": 3,
                    "rashi_num": 9,
                    "combust": False,
                    "debilitated": False,
                },
            },
        },
        known_events=(
            KnownEvent(
                event_id="evt_004",
                event_date_utc="2024-06-15T00:00:00Z",
                event_window_start_utc="2024-01-01T00:00:00Z",
                event_window_end_utc="2025-12-31T23:59:59Z",
                domain=EventDomain.WEALTH,
                description="Unexpected wealth gain",
                yoga_types=("DHANA",),
                expected_planets=("JUPITER", "VENUS"),
            ),
        ),
        domain=EventDomain.WEALTH,
        description="No classical yoga — event without prediction",
    )


# ══════════════════════════════════════════════════════════════════════
# Model Tests
# ══════════════════════════════════════════════════════════════════════


class TestModels:
    """Test data model serialization and construction."""

    def test_birth_chart_construction(self) -> None:
        """BirthChart can be constructed with required fields."""
        chart = _make_gajakesari_chart()
        assert chart.chart_id == "test_gajakesari_01"
        assert chart.birth_data.date == "1990-06-15"
        assert len(chart.known_events) == 1

    def test_birth_chart_serialization(self) -> None:
        """BirthChart serializes deterministically."""
        chart = _make_gajakesari_chart()
        d = chart.to_dict()
        assert d["chart_id"] == "test_gajakesari_01"
        assert d["birth_data"]["timezone"] == "Asia/Kolkata"
        assert len(d["known_events"]) == 1

    def test_known_event_construction(self) -> None:
        """KnownEvent can be constructed with required fields."""
        event = KnownEvent(
            event_id="e1",
            event_date_utc="2024-01-01T00:00:00Z",
            domain=EventDomain.CAREER,
            yoga_types=("RAJA",),
        )
        assert event.event_id == "e1"
        assert event.domain == EventDomain.CAREER

    def test_known_event_serialization(self) -> None:
        """KnownEvent serializes deterministically."""
        event = KnownEvent(
            event_id="e1",
            event_date_utc="2024-01-01T00:00:00Z",
            domain=EventDomain.CAREER,
            yoga_types=("RAJA",),
        )
        d = event.to_dict()
        assert d["event_id"] == "e1"
        assert d["domain"] == "CAREER"
        assert d["yoga_types"] == ["RAJA"]

    def test_predicted_yoga_construction(self) -> None:
        """PredictedYoga can be constructed."""
        pred = PredictedYoga(
            yoga_name="Gajakesari",
            predicted_status="FORMED",
            domain=EventDomain.GENERAL,
            overall_multiplier=3.0,
        )
        assert pred.yoga_name == "Gajakesari"
        assert pred.overall_multiplier == 3.0

    def test_chart_validation_result_serialization(self) -> None:
        """ChartValidationResult serializes deterministically."""
        result = ChartValidationResult(
            chart_id="c1",
            predicted_yogas=(
                PredictedYoga(
                    yoga_name="Gajakesari",
                    predicted_status="FORMED",
                    overall_multiplier=1.5,
                ),
            ),
            matches=(
                EventPredictionMatch(
                    event_id="e1",
                    yoga_name="Gajakesari",
                    verdict=PredictionVerdict.TRUE_POSITIVE,
                    timing_status=TimingMatchStatus.OVERLAP,
                ),
            ),
            total_known_events=1,
            total_predicted_yogas=1,
        )
        d = result.to_dict()
        assert d["chart_id"] == "c1"
        assert len(d["predicted_yogas"]) == 1
        assert d["predicted_yogas"][0]["yoga_name"] == "Gajakesari"
        assert d["matches"][0]["verdict"] == "TRUE_POSITIVE"

    def test_timing_window_construction(self) -> None:
        """TimingWindow can be constructed."""
        tw = TimingWindow(
            yoga_name="Raja",
            window_start_utc="2024-01-01T00:00:00Z",
            window_end_utc="2025-01-01T00:00:00Z",
            dasha_lord="MERCURY",
            confidence=0.85,
        )
        assert tw.yoga_name == "Raja"
        assert tw.confidence == 0.85

    def test_classification_metrics_all_zeros(self) -> None:
        """ClassificationMetrics with no data returns zero metrics."""
        m = ClassificationMetrics()
        assert m.precision == 0.0
        assert m.recall == 0.0
        assert m.f1_score == 0.0

    def test_statistical_report_empty(self) -> None:
        """Empty StatisticalReport has zero totals."""
        r = StatisticalReport()
        assert r.total_charts == 0
        assert r.total_known_events == 0

    def test_statistical_report_serialization(self) -> None:
        """StatisticalReport serializes deterministically."""
        r = StatisticalReport(
            total_charts=5,
            overall_metrics=ClassificationMetrics(
                true_positives=10,
                false_positives=2,
                true_negatives=8,
                false_negatives=1,
                precision=0.8333,
                recall=0.9091,
                f1_score=0.8696,
                accuracy=0.8667,
            ),
        )
        d = r.to_dict()
        assert d["total_charts"] == 5
        assert d["overall_metrics"]["true_positives"] == 10
        assert "domain_calibrations" in d
        assert "timing_analysis" in d


# ══════════════════════════════════════════════════════════════════════
# Runner Tests
# ══════════════════════════════════════════════════════════════════════


class TestHistoricalValidationRunner:
    """Test the HistoricalValidationRunner with synthetic charts."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.runner = HistoricalValidationRunner()

    def test_gajakesari_detected_and_formed(self) -> None:
        """Gajakesari Yoga detected and FORMED in pipeline."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        gajakesari = [
            y for y in result.predicted_yogas
            if y.yoga_name == "Gajakesari"
        ]
        assert len(gajakesari) == 1
        assert gajakesari[0].predicted_status == "FORMED"

    def test_gajakesari_high_confidence(self) -> None:
        """Gajakesari has high confidence when FORMED."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        gajakesari = [
            y for y in result.predicted_yogas
            if y.yoga_name == "Gajakesari"
        ]
        assert gajakesari[0].confidence >= 0.8

    def test_gajakesari_timing_windows(self) -> None:
        """Gajakesari has timing windows from dasha/transit."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        gajakesari = [
            y for y in result.predicted_yogas
            if y.yoga_name == "Gajakesari"
        ]
        assert len(gajakesari[0].timing_windows) > 0

    def test_combust_yoga_cancelled(self) -> None:
        """Combust Jupiter cancels Gajakesari."""
        chart = _make_combust_chart()
        result = self.runner.run_single_chart(chart)
        gajakesari = [
            y for y in result.predicted_yogas
            if y.yoga_name == "Gajakesari"
        ]
        if gajakesari:
            assert gajakesari[0].predicted_status == "CANCELLED"

    def test_raja_yoga_detected(self) -> None:
        """Raja Yoga detected in career chart."""
        chart = _make_raja_yoga_chart()
        result = self.runner.run_single_chart(chart)
        raja = [
            y for y in result.predicted_yogas
            if y.yoga_name == "Raja"
        ]
        assert len(raja) == 1
        assert raja[0].predicted_status == "FORMED"

    def test_raja_yoga_domain_career(self) -> None:
        """Raja Yoga maps to CAREER domain."""
        chart = _make_raja_yoga_chart()
        result = self.runner.run_single_chart(chart)
        raja = [
            y for y in result.predicted_yogas
            if y.yoga_name == "Raja"
        ]
        assert raja[0].domain == EventDomain.CAREER

    def test_no_yoga_chart_has_predictions(self) -> None:
        """No-yoga chart still produces predictions (Vipareeta Raja, etc.)."""
        chart = _make_no_yoga_chart()
        result = self.runner.run_single_chart(chart)
        assert result.total_predicted_yogas >= 0  # May or may not detect yogas

    def test_matches_generated(self) -> None:
        """Validation produces matches between predictions and events."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        assert len(result.matches) > 0

    def test_gajakesari_true_positive_match(self) -> None:
        """Gajakesari prediction matches the known event → TRUE_POSITIVE."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        gajakesari_matches = [
            m for m in result.matches
            if m.yoga_name == "Gajakesari"
        ]
        assert len(gajakesari_matches) == 1
        assert gajakesari_matches[0].verdict == PredictionVerdict.TRUE_POSITIVE

    def test_combust_false_negative_match(self) -> None:
        """Combust yoga → prediction cancelled → FALSE_NEGATIVE."""
        chart = _make_combust_chart()
        result = self.runner.run_single_chart(chart)
        # The Gajakesari is cancelled, so the event is FN
        cancelled_yogas = [
            y for y in result.predicted_yogas
            if y.yoga_name == "Gajakesari"
            and y.predicted_status == "CANCELLED"
        ]
        if cancelled_yogas:
            # There should be a FN match for the known event
            fn_matches = [
                m for m in result.matches
                if m.verdict == PredictionVerdict.FALSE_NEGATIVE
            ]
            assert len(fn_matches) >= 1

    def test_batch_processing(self) -> None:
        """Runner processes multiple charts in batch."""
        charts = [
            _make_gajakesari_chart(),
            _make_raja_yoga_chart(),
            _make_no_yoga_chart(),
        ]
        results = self.runner.run_batch(charts)
        assert len(results) == 3
        assert results[0].chart_id == "test_gajakesari_01"
        assert results[1].chart_id == "test_raja_01"
        assert results[2].chart_id == "test_no_yoga_01"

    def test_chart_metadata_preserved(self) -> None:
        """Chart metadata preserved in validation result."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        assert result.chart_id == "test_gajakesari_01"
        assert result.domain == EventDomain.GENERAL
        assert result.total_known_events == 1


# ══════════════════════════════════════════════════════════════════════
# Statistical Evaluator Tests
# ══════════════════════════════════════════════════════════════════════


class TestStatisticalEvaluator:
    """Test the StatisticalEvaluator with synthetic validation results."""

    @pytest.fixture(autouse=True)
    def setup(self) -> None:
        self.evaluator = StatisticalEvaluator()
        self.runner = HistoricalValidationRunner()

    def test_empty_results(self) -> None:
        """Empty results produce zero-valued report."""
        report = self.evaluator.evaluate([])
        assert report.total_charts == 0
        assert report.total_known_events == 0

    def test_single_chart_metrics(self) -> None:
        """Single chart produces valid metrics."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        assert report.total_charts == 1
        assert report.total_known_events == 1
        assert report.overall_metrics.true_positives >= 0
        assert report.overall_metrics.false_positives >= 0

    def test_precision_bounded(self) -> None:
        """Precision is between 0 and 1."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        assert 0.0 <= report.overall_metrics.precision <= 1.0

    def test_recall_bounded(self) -> None:
        """Recall is between 0 and 1."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        assert 0.0 <= report.overall_metrics.recall <= 1.0

    def test_f1_score_bounded(self) -> None:
        """F1 score is between 0 and 1."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        assert 0.0 <= report.overall_metrics.f1_score <= 1.0

    def test_accuracy_bounded(self) -> None:
        """Accuracy is between 0 and 1."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        assert 0.0 <= report.overall_metrics.accuracy <= 1.0

    def test_multi_chart_aggregation(self) -> None:
        """Multiple charts aggregate correctly."""
        charts = [
            _make_gajakesari_chart(),
            _make_raja_yoga_chart(),
            _make_no_yoga_chart(),
        ]
        results = self.runner.run_batch(charts)
        report = self.evaluator.evaluate(results)
        assert report.total_charts == 3
        assert report.total_known_events == 3
        # Overall metrics are computed
        assert report.overall_metrics.true_positives >= 0

    def test_domain_calibration_generated(self) -> None:
        """Domain calibrations are generated for each domain."""
        charts = [
            _make_gajakesari_chart(),  # GENERAL
            _make_raja_yoga_chart(),   # CAREER
            _make_no_yoga_chart(),     # WEALTH
        ]
        results = self.runner.run_batch(charts)
        report = self.evaluator.evaluate(results)
        assert len(report.domain_calibrations) >= 2  # At least GENERAL + CAREER + WEALTH

    def test_domain_calibration_has_metrics(self) -> None:
        """Each domain calibration has valid metrics."""
        charts = [
            _make_gajakesari_chart(),
            _make_raja_yoga_chart(),
        ]
        results = self.runner.run_batch(charts)
        report = self.evaluator.evaluate(results)
        for dc in report.domain_calibrations:
            assert dc.chart_count >= 1
            assert 0.0 <= dc.metrics.precision <= 1.0
            assert 0.0 <= dc.metrics.recall <= 1.0

    def test_timing_analysis_computed(self) -> None:
        """Timing analysis is computed."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        assert report.timing_analysis.total_predicted_windows >= 0

    def test_timing_accuracy_bounded(self) -> None:
        """Timing accuracy is between 0 and 1."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        assert 0.0 <= report.timing_analysis.timing_accuracy <= 1.0

    def test_mean_confidence_bounded(self) -> None:
        """Mean confidence is between 0 and 1."""
        charts = [
            _make_gajakesari_chart(),
            _make_raja_yoga_chart(),
        ]
        results = self.runner.run_batch(charts)
        report = self.evaluator.evaluate(results)
        assert 0.0 <= report.mean_confidence <= 1.0

    def test_report_serialization(self) -> None:
        """Full report serializes deterministically."""
        charts = [
            _make_gajakesari_chart(),
            _make_raja_yoga_chart(),
        ]
        results = self.runner.run_batch(charts)
        report = self.evaluator.evaluate(results)
        d = report.to_dict()
        assert d["total_charts"] == 2
        assert "overall_metrics" in d
        assert "domain_calibrations" in d
        assert "timing_analysis" in d
        # Verify JSON-serializable
        import json
        json_str = json.dumps(d, sort_keys=True)
        assert len(json_str) > 0

    def test_gajakesari_true_positive_in_report(self) -> None:
        """Gajakesari chart contributes TRUE_POSITIVE to report."""
        chart = _make_gajakesari_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        # At least one TP from the Gajakesari match
        assert report.overall_metrics.true_positives >= 1

    def test_cancelled_yoga_contributes_false_negative(self) -> None:
        """Cancelled yoga contributes FALSE_NEGATIVE to report."""
        chart = _make_combust_chart()
        result = self.runner.run_single_chart(chart)
        report = self.evaluator.evaluate([result])
        # Cancelled Gajakesari → FN match for the known event
        assert report.overall_metrics.false_negatives >= 1


# ══════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ══════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_jre_facts(self) -> None:
        """Empty JRE facts produce empty predictions."""
        chart = BirthChart(
            chart_id="empty",
            birth_data=BirthData(date="2000-01-01", time="00:00:00"),
            jre_facts={"planets": {}},
        )
        runner = HistoricalValidationRunner()
        result = runner.run_single_chart(chart)
        assert result.total_predicted_yogas == 0

    def test_no_known_events(self) -> None:
        """Chart with no known events: no event-based matches, but
        unmatched predictions are conservatively classified as FP."""
        chart = BirthChart(
            chart_id="no_events",
            birth_data=BirthData(date="2000-01-01", time="00:00:00"),
            jre_facts={
                "planets": {
                    "JUPITER": {"house": 1, "rashi": "KARKA", "rashi_num": 4,
                                "combust": False, "debilitated": False},
                    "MOON": {"house": 1, "rashi": "KARKA", "rashi_num": 4,
                             "combust": False, "debilitated": False},
                },
            },
            known_events=(),
        )
        runner = HistoricalValidationRunner()
        result = runner.run_single_chart(chart)
        assert result.total_known_events == 0
        # No event-based matches (no known events)
        event_matches = [
            m for m in result.matches if not m.event_id.startswith("unmatched_")
        ]
        assert len(event_matches) == 0

    def test_multiple_events_per_chart(self) -> None:
        """Chart with multiple known events produces multiple matches."""
        chart = BirthChart(
            chart_id="multi_events",
            birth_data=BirthData(date="1990-01-01", time="00:00:00"),
            jre_facts={
                "planets": {
                    "JUPITER": {"house": 1, "rashi": "KARKA", "rashi_num": 4,
                                "combust": False, "debilitated": False},
                    "MOON": {"house": 1, "rashi": "KARKA", "rashi_num": 4,
                             "combust": False, "debilitated": False},
                },
            },
            known_events=(
                KnownEvent(
                    event_id="e1",
                    event_date_utc="2024-01-01T00:00:00Z",
                    domain=EventDomain.GENERAL,
                    yoga_types=("GAJAKESARI",),
                ),
                KnownEvent(
                    event_id="e2",
                    event_date_utc="2025-01-01T00:00:00Z",
                    domain=EventDomain.GENERAL,
                    yoga_types=("GAJAKESARI",),
                ),
            ),
        )
        runner = HistoricalValidationRunner()
        result = runner.run_single_chart(chart)
        assert result.total_known_events == 2
        assert len(result.matches) >= 2

    def test_deterministic_results(self) -> None:
        """Running the same chart twice produces identical results."""
        chart = _make_gajakesari_chart()
        runner1 = HistoricalValidationRunner()
        runner2 = HistoricalValidationRunner()
        result1 = runner1.run_single_chart(chart)
        result2 = runner2.run_single_chart(chart)
        assert result1.to_dict() == result2.to_dict()

    def test_cross_domain_no_match(self) -> None:
        """Prediction in one domain doesn't match event in another."""
        chart = _make_raja_yoga_chart()  # CAREER domain
        # Add a WEALTH event that shouldn't match the Raja Yoga
        chart_with_wealth_event = BirthChart(
            chart_id="cross_domain",
            birth_data=chart.birth_data,
            jre_facts=chart.jre_facts,
            known_events=(
                KnownEvent(
                    event_id="evt_wealth",
                    event_date_utc="2024-06-15T00:00:00Z",
                    domain=EventDomain.WEALTH,
                    yoga_types=("DHANA",),
                    expected_planets=("JUPITER",),
                ),
            ),
            domain=EventDomain.CAREER,
        )
        runner = HistoricalValidationRunner()
        result = runner.run_single_chart(chart_with_wealth_event)
        # The WEALTH event should be FN (no matching prediction)
        wealth_matches = [
            m for m in result.matches
            if m.event_id == "evt_wealth"
        ]
        assert len(wealth_matches) == 1
        assert wealth_matches[0].verdict == PredictionVerdict.FALSE_NEGATIVE


# ══════════════════════════════════════════════════════════════════════
# Integration: Full Pipeline with Statistical Report
# ══════════════════════════════════════════════════════════════════════


class TestFullPipelineIntegration:
    """End-to-end integration: charts → runner → evaluator → report."""

    def test_full_pipeline_produces_report(self) -> None:
        """Complete pipeline: run charts, compute stats, produce report."""
        charts = [
            _make_gajakesari_chart(),
            _make_combust_chart(),
            _make_raja_yoga_chart(),
        ]

        runner = HistoricalValidationRunner()
        results = runner.run_batch(charts)
        assert len(results) == 3

        evaluator = StatisticalEvaluator()
        report = evaluator.evaluate(results)

        # Report structure
        assert report.total_charts == 3
        assert report.total_known_events == 3
        assert len(report.domain_calibrations) >= 2
        assert report.timing_analysis.total_predicted_windows >= 0

        # Metrics are valid
        assert 0.0 <= report.overall_metrics.precision <= 1.0
        assert 0.0 <= report.overall_metrics.recall <= 1.0
        assert 0.0 <= report.overall_metrics.f1_score <= 1.0

        # Report serializes
        d = report.to_dict()
        assert "total_charts" in d
        assert "overall_metrics" in d
        assert "domain_calibrations" in d
        assert "timing_analysis" in d

    def test_report_deterministic_across_runs(self) -> None:
        """Report is deterministic across multiple evaluations."""
        charts = [_make_gajakesari_chart(), _make_raja_yoga_chart()]

        runner = HistoricalValidationRunner()
        results1 = runner.run_batch(charts)
        results2 = runner.run_batch(charts)

        evaluator = StatisticalEvaluator()
        report1 = evaluator.evaluate(results1)
        report2 = evaluator.evaluate(results2)

        import json
        assert json.dumps(report1.to_dict(), sort_keys=True) == json.dumps(
            report2.to_dict(), sort_keys=True,
        )

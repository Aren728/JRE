"""Phase 5A: Error Taxonomy tests.

Validates the deterministic FP/FN root-cause attribution contract against
an isolated JSON fixture (``tests/fixtures/error_taxonomy/``), plus
purity, determinism, and classification edge cases.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jrs.prediction_engine.provenance import DirectedAcyclicGraph
from jrs.validation.error_taxonomy import (
    ErrorAttribution,
    ErrorKind,
    attribute_match,
    attribute_result,
    attach_provenance,
    classify_match,
    summarize_attributions,
)
from jrs.validation.models import (
    ChartValidationResult,
    EventPredictionMatch,
    PredictionVerdict,
    TimingMatchStatus,
)

FIXTURE_PATH = (
    Path(__file__).resolve().parents[3]
    / "fixtures"
    / "error_taxonomy"
    / "fixture_000_attribution.json"
)


@pytest.fixture(scope="module")
def fixture_data() -> dict:
    """Load the isolated deterministic fixture."""
    with FIXTURE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def graph(fixture_data: dict) -> DirectedAcyclicGraph:
    return DirectedAcyclicGraph.from_dict(fixture_data["input"]["graph"])


def _result_from(fixture_data: dict) -> ChartValidationResult:
    """Rebuild the ChartValidationResult from the fixture's serialized form.

    Provenance roots are deliberately NOT round-tripped through to_dict —
    they are derived from the graph, mirroring runtime behavior.
    """
    data = fixture_data["input"]["result"]
    matches = tuple(
        EventPredictionMatch(
            event_id=m["event_id"],
            yoga_name=m["yoga_name"],
            verdict=PredictionVerdict(m["verdict"]),
            timing_status=TimingMatchStatus(m["timing_status"]),
            timing_overlap_ratio=m["timing_overlap_ratio"],
            confidence=m["confidence"],
        )
        for m in data["matches"]
    )
    return ChartValidationResult(
        chart_id=data["chart_id"],
        matches=matches,
        total_known_events=data["total_known_events"],
        total_predicted_yogas=data["total_predicted_yogas"],
    )


# ── Classification contract ──────────────────────────────────────────────────
class TestClassifyMatch:
    def test_fn_without_rules_is_coverage_gap(self) -> None:
        match = EventPredictionMatch(
            event_id="EV-1",
            yoga_name="",
            verdict=PredictionVerdict.FALSE_NEGATIVE,
        )
        assert classify_match(match) is ErrorKind.COVERAGE_GAP

    def test_fn_with_attached_rules_is_formation_cancelled(self, graph: DirectedAcyclicGraph) -> None:
        match = attach_provenance(
            EventPredictionMatch(
                event_id="EV-2",
                yoga_name="Raja",
                verdict=PredictionVerdict.FALSE_NEGATIVE,
            ),
            graph,
        )
        assert classify_match(match) is ErrorKind.FORMATION_CANCELLED

    def test_fp_without_timing_overlap_is_dasha_mismatch(self) -> None:
        match = EventPredictionMatch(
            event_id="EV-3",
            yoga_name="Malavya",
            verdict=PredictionVerdict.FALSE_POSITIVE,
            timing_status=TimingMatchStatus.NO_OVERLAP,
        )
        assert classify_match(match) is ErrorKind.DASHA_MISMATCH

    def test_fp_with_partial_overlap_is_domain_overlap(self) -> None:
        match = EventPredictionMatch(
            event_id="EV-4",
            yoga_name="Malavya",
            verdict=PredictionVerdict.FALSE_POSITIVE,
            timing_status=TimingMatchStatus.PARTIAL_OVERLAP,
            timing_overlap_ratio=0.4,
        )
        assert classify_match(match) is ErrorKind.DOMAIN_OVERLAP

    def test_tp_is_unclassified(self) -> None:
        match = EventPredictionMatch(
            event_id="EV-5",
            yoga_name="Malavya",
            verdict=PredictionVerdict.TRUE_POSITIVE,
        )
        assert classify_match(match) is ErrorKind.UNCLASSIFIED

    def test_polarity_mapping(self) -> None:
        assert ErrorKind.COVERAGE_GAP.polarity == "FN"
        assert ErrorKind.FORMATION_CANCELLED.polarity == "FN"
        assert ErrorKind.DASHA_MISMATCH.polarity == "FP"
        assert ErrorKind.DOMAIN_OVERLAP.polarity == "FP"
        assert ErrorKind.UNCLASSIFIED.polarity == ""


# ── Provenance mining ────────────────────────────────────────────────────────
class TestAttachProvenance:
    def test_rules_and_facts_mined(self, graph: DirectedAcyclicGraph) -> None:
        match = attach_provenance(
            EventPredictionMatch(
                event_id="EV-3",
                yoga_name="Malavya",
                verdict=PredictionVerdict.FALSE_POSITIVE,
            ),
            graph,
        )
        assert match.root_rule_ids == ("YOGA-008",)
        assert match.root_fact_ids == ("F-001", "F-002")
        assert match.temporal_affected is True

    def test_unknown_yoga_has_empty_roots(self, graph: DirectedAcyclicGraph) -> None:
        match = attach_provenance(
            EventPredictionMatch(
                event_id="EV-X",
                yoga_name="Nonexistent",
                verdict=PredictionVerdict.FALSE_NEGATIVE,
            ),
            graph,
        )
        assert match.root_rule_ids == ()
        assert match.root_fact_ids == ()
        assert match.temporal_affected is False

    def test_pure_original_match_untouched(self, graph: DirectedAcyclicGraph) -> None:
        original = EventPredictionMatch(
            event_id="EV-3",
            yoga_name="Malavya",
            verdict=PredictionVerdict.FALSE_POSITIVE,
        )
        attach_provenance(original, graph)
        assert original.root_rule_ids == ()
        assert original.root_fact_ids == ()
        assert original.temporal_affected is False


# ── Fixture contract (deterministic JSON) ────────────────────────────────────
class TestFixtureContract:
    def test_fixture_exists(self) -> None:
        assert FIXTURE_PATH.exists(), f"missing deterministic fixture: {FIXTURE_PATH}"

    def test_attributions_match_fixture(self, fixture_data: dict, graph: DirectedAcyclicGraph) -> None:
        result = _result_from(fixture_data)
        attributions = attribute_result(result, graph)
        expected = fixture_data["expected"]["attributions"]
        assert [a.to_dict() for a in attributions] == expected

    def test_summary_matches_fixture(self, fixture_data: dict, graph: DirectedAcyclicGraph) -> None:
        result = _result_from(fixture_data)
        attributions = attribute_result(result, graph)
        assert summarize_attributions(attributions) == fixture_data["expected"]["summary"]

    def test_tp_matches_excluded(self, fixture_data: dict) -> None:
        event_ids = {a["event_id"] for a in fixture_data["expected"]["attributions"]}
        assert "EV-5" not in event_ids  # the TRUE_POSITIVE

    def test_all_four_kinds_covered(self, fixture_data: dict) -> None:
        kinds = {a["kind"] for a in fixture_data["expected"]["attributions"]}
        assert kinds == {
            "COVERAGE_GAP",
            "FORMATION_CANCELLED",
            "DASHA_MISMATCH",
            "DOMAIN_OVERLAP",
        }


# ── Determinism & serialization ──────────────────────────────────────────────
class TestDeterminism:
    def test_repeated_attribution_is_byte_identical(self, graph: DirectedAcyclicGraph) -> None:
        match = EventPredictionMatch(
            event_id="EV-3",
            yoga_name="Malavya",
            verdict=PredictionVerdict.FALSE_POSITIVE,
        )
        first = attribute_match("chart_fixture_000", attach_provenance(match, graph))
        second = attribute_match("chart_fixture_000", attach_provenance(match, graph))
        assert first == second
        assert first.to_dict() == second.to_dict()

    def test_summary_keys_sorted_and_bounded(self) -> None:
        attributions = [
            ErrorAttribution(
                chart_id="c",
                event_id=f"unmatched_Y{i % 3}",
                yoga_name=f"Y{i % 3}",
                verdict="FALSE_POSITIVE",
                kind=ErrorKind.DASHA_MISMATCH,
                polarity="FP",
                timing_status="NO_OVERLAP",
                timing_overlap_ratio=0.0,
                confidence=0.5,
                root_rule_ids=("YOGA-001",),
                root_fact_ids=(f"F-{100 + i:03d}",),
                temporal_affected=False,
                detail="",
            )
            for i in range(40)
        ]
        summary = summarize_attributions(attributions)
        assert list(summary["by_kind"]) == sorted(summary["by_kind"])
        assert list(summary["by_rule"]) == sorted(summary["by_rule"])
        assert len(summary["top_facts"]) <= 10

    def test_attribution_to_dict_round_trip_fields(self, graph: DirectedAcyclicGraph) -> None:
        match = attach_provenance(
            EventPredictionMatch(
                event_id="EV-2",
                yoga_name="Raja",
                verdict=PredictionVerdict.FALSE_NEGATIVE,
                confidence=0.123456789,
            ),
            graph,
        )
        d = attribute_match("chart_fixture_000", match).to_dict()
        assert d["kind"] == "FORMATION_CANCELLED"
        assert d["polarity"] == "FN"
        assert d["confidence"] == round(0.123456789, 6)
        assert d["root_rule_ids"] == ["YOGA-002"]

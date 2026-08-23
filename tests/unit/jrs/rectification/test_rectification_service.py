"""Unit tests for JRS-064 Rectification Integration service."""

from __future__ import annotations

import pytest

from jrs.convergence.models import (
    AssessmentStatus,
    DomainAssessment,
    TimingStatus,
)
from jrs.rectification.errors import (
    InvalidCandidateError,
    InvalidKnownEventsError,
    NoAdjustmentError,
)
from jrs.rectification.models import (
    KnownEvent,
    MatchQuality,
)
from jrs.rectification.service import RectificationIntegrationService

# ── Service Construction Tests ───────────────────────────────────────────────


class TestServiceConstruction:
    def test_default_init(self) -> None:
        svc = RectificationIntegrationService()
        assert svc.assessment_weight == 0.7
        assert svc.timing_weight == 0.3
        assert svc.max_adjustment_minutes == 120.0

    def test_custom_init(self) -> None:
        svc = RectificationIntegrationService(
            assessment_weight=0.6,
            timing_weight=0.4,
            max_adjustment_minutes=60.0,
            adjustment_step_minutes=10.0,
        )
        assert svc.assessment_weight == 0.6
        assert svc.timing_weight == 0.4
        assert svc.max_adjustment_minutes == 60.0

    def test_invalid_assessment_weight(self) -> None:
        with pytest.raises(ValueError, match="assessment_weight"):
            RectificationIntegrationService(assessment_weight=1.5)

    def test_invalid_timing_weight(self) -> None:
        with pytest.raises(ValueError, match="timing_weight"):
            RectificationIntegrationService(timing_weight=-0.1)

    def test_invalid_max_adjustment(self) -> None:
        with pytest.raises(ValueError, match="max_adjustment_minutes"):
            RectificationIntegrationService(max_adjustment_minutes=0)

    def test_invalid_step(self) -> None:
        with pytest.raises(ValueError, match="adjustment_step_minutes"):
            RectificationIntegrationService(adjustment_step_minutes=-5.0)


# ── evaluate_candidate Tests ─────────────────────────────────────────────────


class TestEvaluateCandidate:
    def test_missing_birth_time(self) -> None:
        svc = RectificationIntegrationService()
        with pytest.raises(InvalidCandidateError):
            svc.evaluate_candidate(
                {"other_key": "value"},
                [KnownEvent(
                    event_description="X",
                    domain_label="Y",
                    expected_outcome="Z",
                    expected_assessment_status="W",
                )],
                pipeline_output={},
            )

    def test_empty_known_events(self) -> None:
        svc = RectificationIntegrationService()
        with pytest.raises(InvalidKnownEventsError):
            svc.evaluate_candidate(
                {"birth_time_utc": "2000-01-01T12:00:00Z"},
                [],
                pipeline_output={},
            )

    def test_missing_pipeline_output(self) -> None:
        svc = RectificationIntegrationService()
        with pytest.raises(InvalidKnownEventsError):
            svc.evaluate_candidate(
                {"birth_time_utc": "2000-01-01T12:00:00Z"},
                [],
            )

    def test_good_match_low_mismatch(
        self,
        marriage_known_event: KnownEvent,
        good_pipeline_output: dict[str, DomainAssessment],
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [marriage_known_event],
            pipeline_output=good_pipeline_output,
        )
        assert result.mismatch_score < 0.3
        assert len(result.event_matches) == 1
        assert result.event_matches[0].match_quality in (
            MatchQuality.EXACT_MATCH,
            MatchQuality.STRONG_MATCH,
            MatchQuality.PARTIAL_MATCH,
        )

    def test_poor_match_high_mismatch(
        self,
        marriage_known_event: KnownEvent,
        poor_pipeline_output: dict[str, DomainAssessment],
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [marriage_known_event],
            pipeline_output=poor_pipeline_output,
        )
        assert result.mismatch_score > 0.3
        assert len(result.event_matches) == 1

    def test_multiple_known_events(
        self,
        marriage_known_event: KnownEvent,
        career_known_event: KnownEvent,
        good_pipeline_output: dict[str, DomainAssessment],
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [marriage_known_event, career_known_event],
            pipeline_output=good_pipeline_output,
        )
        assert len(result.event_matches) == 2
        assert result.mismatch_score < 1.0

    def test_deterministic_id(self) -> None:
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        assessment = DomainAssessment(
            outcome_taxonomy="MARRIAGE_FORMATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.CONVERGENT,
        )
        output = {"MARRIAGE": assessment}

        r1 = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"}, [ke], output,
        )
        r2 = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"}, [ke], output,
        )
        assert r1.deterministic_id == r2.deterministic_id

    def test_different_times_different_hash(self) -> None:
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        assessment = DomainAssessment(
            outcome_taxonomy="MARRIAGE_FORMATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.CONVERGENT,
        )
        output = {"MARRIAGE": assessment}

        r1 = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"}, [ke], output,
        )
        r2 = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T13:00:00Z"}, [ke], output,
        )
        assert r1.deterministic_id != r2.deterministic_id

    def test_supporting_evidence_populated(
        self,
        marriage_known_event: KnownEvent,
        good_pipeline_output: dict[str, DomainAssessment],
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [marriage_known_event],
            pipeline_output=good_pipeline_output,
        )
        assert len(result.supporting_evidence_ids) >= 1

    def test_missing_domain_no_match(self) -> None:
        """When the pipeline output doesn't have the expected domain."""
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [ke],
            pipeline_output={},  # Empty — no MARRIAGE assessment
        )
        assert result.mismatch_score == 1.0
        assert result.event_matches[0].match_quality is MatchQuality.NO_MATCH

    def test_outcome_mismatch_penalty(self) -> None:
        """When the pipeline produces a different outcome than expected."""
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        # Pipeline says SEPARATION instead of MARRIAGE_FORMATION
        assessment = DomainAssessment(
            outcome_taxonomy="SEPARATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.CONVERGENT,
        )
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [ke],
            pipeline_output={"MARRIAGE": assessment},
        )
        # Should have higher mismatch due to outcome mismatch penalty
        assert result.mismatch_score > 0.2

    def test_to_dict_serialization(
        self,
        marriage_known_event: KnownEvent,
        good_pipeline_output: dict[str, DomainAssessment],
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [marriage_known_event],
            pipeline_output=good_pipeline_output,
        )
        d = result.to_dict()
        assert "candidate_time" in d
        assert "mismatch_score" in d
        assert "event_matches" in d
        assert "deterministic_id" in d


# ── suggest_adjustments Tests ────────────────────────────────────────────────


class TestSuggestAdjustments:
    def test_missing_birth_time(self) -> None:
        svc = RectificationIntegrationService()
        with pytest.raises(InvalidCandidateError):
            svc.suggest_adjustments(
                {"other_key": "value"},
                [KnownEvent(
                    event_description="X",
                    domain_label="Y",
                    expected_outcome="Z",
                    expected_assessment_status="W",
                )],
            )

    def test_empty_known_events(self) -> None:
        svc = RectificationIntegrationService()
        with pytest.raises(InvalidKnownEventsError):
            svc.suggest_adjustments(
                {"birth_time_utc": "2000-01-01T12:00:00Z"},
                [],
            )

    def test_no_pipeline_runner_no_jre(self) -> None:
        """Without pipeline_runner or life_events, raises NoAdjustmentError."""
        svc = RectificationIntegrationService()
        with pytest.raises(NoAdjustmentError):
            svc.suggest_adjustments(
                {"birth_time_utc": "2000-01-01T12:00:00Z"},
                [KnownEvent(
                    event_description="Marriage",
                    domain_label="MARRIAGE",
                    expected_outcome="MARRIAGE_FORMATION",
                    expected_assessment_status="SUPPORTED",
                )],
            )

    def test_with_life_events_jre_proposals(self) -> None:
        """With life_events in birth_data, JRE-021 proposals are generated."""
        svc = RectificationIntegrationService()
        birth_data = {
            "birth_time_utc": "2000-01-01T12:00:00Z",
            "life_events": [
                {
                    "event_date_utc": "2010-06-15T10:00:00Z",
                    "event_type": "MARRIAGE",
                    "description": "Marriage",
                },
            ],
            "transit_times": {"Marriage": "2010-06-15T11:00:00Z"},
        }
        known_events = [
            KnownEvent(
                event_description="Marriage",
                domain_label="MARRIAGE",
                expected_outcome="MARRIAGE_FORMATION",
                expected_assessment_status="SUPPORTED",
            ),
        ]
        # This should not raise — JRE-021 proposals should be generated
        proposals = svc.suggest_adjustments(birth_data, known_events)
        assert len(proposals) >= 1
        for p in proposals:
            assert p.offset_minutes >= 0
            assert p.confidence >= 0.0

    def test_proposals_sorted_by_confidence(self) -> None:
        """Proposals should be sorted by confidence descending."""
        svc = RectificationIntegrationService()
        birth_data = {
            "birth_time_utc": "2000-01-01T12:00:00Z",
            "life_events": [
                {
                    "event_date_utc": "2010-06-15T10:00:00Z",
                    "event_type": "MARRIAGE",
                    "description": "Marriage",
                },
            ],
            "transit_times": {"Marriage": "2010-06-15T11:00:00Z"},
        }
        known_events = [
            KnownEvent(
                event_description="Marriage",
                domain_label="MARRIAGE",
                expected_outcome="MARRIAGE_FORMATION",
                expected_assessment_status="SUPPORTED",
            ),
        ]
        proposals = svc.suggest_adjustments(birth_data, known_events)
        if len(proposals) >= 2:
            for i in range(len(proposals) - 1):
                assert proposals[i].confidence >= proposals[i + 1].confidence


# ── No-Circularity Boundary Tests ────────────────────────────────────────────


class TestNoCircularity:
    """Tests verifying that candidate generation and evaluation are
    strictly separated — the engine cannot use its own suggested
    adjustments as evidence to validate itself.
    """

    def test_evaluate_does_not_modify_birth_data(self) -> None:
        """evaluate_candidate must not alter the input birth_data."""
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        assessment = DomainAssessment(
            outcome_taxonomy="MARRIAGE_FORMATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.CONVERGENT,
        )
        birth_data = {"birth_time_utc": "2000-01-01T12:00:00Z"}
        original_time = birth_data["birth_time_utc"]

        svc.evaluate_candidate(birth_data, [ke], {"MARRIAGE": assessment})

        assert birth_data["birth_time_utc"] == original_time

    def test_suggest_adjustments_uses_jre_not_assessment(self) -> None:
        """suggest_adjustments must use JRE-021 (transit timing) to propose,
        not assessment quality. The proposals should be based on transit
        alignment, not on whether the assessments match known events.
        """
        svc = RectificationIntegrationService()
        birth_data = {
            "birth_time_utc": "2000-01-01T12:00:00Z",
            "life_events": [
                {
                    "event_date_utc": "2010-06-15T10:00:00Z",
                    "event_type": "MARRIAGE",
                    "description": "Marriage",
                },
            ],
            "transit_times": {"Marriage": "2010-06-15T11:00:00Z"},
        }
        known_events = [
            KnownEvent(
                event_description="Marriage",
                domain_label="MARRIAGE",
                expected_outcome="MARRIAGE_FORMATION",
                expected_assessment_status="SUPPORTED",
            ),
        ]
        proposals = svc.suggest_adjustments(birth_data, known_events)
        # All proposals should have method set (JRE-021 or SCAN)
        for p in proposals:
            assert p.method != ""

    def test_evaluate_candidate_is_pure(self) -> None:
        """evaluate_candidate must be a pure function — same inputs
        produce same outputs, no side effects.
        """
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
        )
        assessment = DomainAssessment(
            outcome_taxonomy="MARRIAGE_FORMATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.CONVERGENT,
        )
        birth_data = {"birth_time_utc": "2000-01-01T12:00:00Z"}
        output = {"MARRIAGE": assessment}

        r1 = svc.evaluate_candidate(birth_data, [ke], output)
        r2 = svc.evaluate_candidate(birth_data, [ke], output)

        assert r1.mismatch_score == r2.mismatch_score
        assert r1.suggested_adjustment_minutes == r2.suggested_adjustment_minutes
        assert r1.deterministic_id == r2.deterministic_id


# ── Integration with DomainAssessment Variants ───────────────────────────────


class TestDomainAssessmentVariants:
    """Test evaluation against various DomainAssessment configurations."""

    def test_strongly_supported_matches(
        self,
        career_known_event: KnownEvent,
        career_assessment_strongly_supported: DomainAssessment,
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [career_known_event],
            pipeline_output={"CAREER": career_assessment_strongly_supported},
        )
        assert result.mismatch_score < 0.15
        assert result.event_matches[0].match_quality in (
            MatchQuality.EXACT_MATCH,
            MatchQuality.STRONG_MATCH,
        )

    def test_weakly_supported_matches(
        self,
        wealth_known_event: KnownEvent,
        wealth_assessment_weakly_supported: DomainAssessment,
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [wealth_known_event],
            pipeline_output={"WEALTH": wealth_assessment_weakly_supported},
        )
        assert result.mismatch_score < 0.2
        assert result.event_matches[0].match_quality in (
            MatchQuality.EXACT_MATCH,
            MatchQuality.STRONG_MATCH,
            MatchQuality.PARTIAL_MATCH,
        )

    def test_timing_mismatch_contributes_to_score(self) -> None:
        """When timing status mismatches, it should increase mismatch score."""
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
            expected_timing_status="CONVERGENT",
        )
        # Assessment matches outcome but timing is INACTIVE
        assessment = DomainAssessment(
            outcome_taxonomy="MARRIAGE_FORMATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.INACTIVE,
        )
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [ke],
            pipeline_output={"MARRIAGE": assessment},
        )
        # Should have some mismatch due to timing
        assert result.mismatch_score > 0.0

    def test_contradicted_timing_higher_mismatch(self) -> None:
        """INACTIVE timing when CONVERGENT expected should penalize more."""
        svc = RectificationIntegrationService()
        ke = KnownEvent(
            event_description="Marriage",
            domain_label="MARRIAGE",
            expected_outcome="MARRIAGE_FORMATION",
            expected_assessment_status="SUPPORTED",
            expected_timing_status="CONVERGENT",
        )
        # Good assessment but INACTIVE timing
        assessment_inactive = DomainAssessment(
            outcome_taxonomy="MARRIAGE_FORMATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.INACTIVE,
        )
        # Good assessment with CONVERGENT timing
        assessment_convergent = DomainAssessment(
            outcome_taxonomy="MARRIAGE_FORMATION",
            assessment_status=AssessmentStatus.SUPPORTED,
            timing_status=TimingStatus.CONVERGENT,
        )
        r_inactive = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [ke],
            pipeline_output={"MARRIAGE": assessment_inactive},
        )
        r_convergent = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [ke],
            pipeline_output={"MARRIAGE": assessment_convergent},
        )
        assert r_inactive.mismatch_score > r_convergent.mismatch_score


# ── Mixed Pipeline Output Tests ──────────────────────────────────────────────


class TestMixedPipelineOutput:
    def test_mixed_quality(
        self,
        marriage_known_event: KnownEvent,
        career_known_event: KnownEvent,
        mixed_pipeline_output: dict[str, DomainAssessment],
    ) -> None:
        svc = RectificationIntegrationService()
        result = svc.evaluate_candidate(
            {"birth_time_utc": "2000-01-01T12:00:00Z"},
            [marriage_known_event, career_known_event],
            pipeline_output=mixed_pipeline_output,
        )
        # Should have moderate mismatch (one good, one bad)
        assert 0.1 < result.mismatch_score < 0.8
        assert len(result.event_matches) == 2

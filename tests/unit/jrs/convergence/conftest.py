"""Shared test fixtures and builders for convergence engine unit tests."""

from __future__ import annotations

from typing import Any

import pytest

from jrs.convergence.models import (
    AssessmentStatus,
    ConvergenceConfig,
    DomainAssessment,
    EvidenceDimensions,
    OverallEvidenceStrength,
    SourceConfidence,
    TimingStatus,
)
from jrs.evidence.models import EvidenceDirection, EvidenceRecord, EvidenceStrength
from jrs.temporal.models import ActivationType, ConvergenceLevel, EventWindow, TemporalTrigger


@pytest.fixture
def sample_config() -> ConvergenceConfig:
    """A minimal ConvergenceConfig for testing."""
    return ConvergenceConfig(
        version="1.0",
        source_weights={"BPHS": 1.0, "Phaladeepika": 0.9},
        strength_weights={"HIGH": 0.8, "MODERATE": 0.6},
        independence_penalty=0.5,
        strongly_supported_min_independent=3,
        strongly_supported_min_supporting=4,
        supported_min_independent=2,
        supported_min_supporting=2,
        weakly_supported_min_supporting=1,
        strongly_contradicted_min_contradicting=3,
        contradicted_min_contradicting=2,
        convergent_min_windows=1,
    )


@pytest.fixture
def sample_support_records() -> tuple[EvidenceRecord, ...]:
    """Sample supporting evidence records."""
    return (
        EvidenceRecord(
            evidence_id="E-001",
            outcome_taxonomy="MARRIAGE_FORMATION",
            supporting_fact_type="7TH_LORD_IN_KENDRA",
            rule_id="R-001",
            source_id="BPHS",
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
            independence_group="BPHS-7L",
        ),
        EvidenceRecord(
            evidence_id="E-002",
            outcome_taxonomy="MARRIAGE_FORMATION",
            supporting_fact_type="VENUS_STRONG",
            rule_id="R-002",
            source_id="BPHS",
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.MODERATE,
            independence_group="BPHS-VEN",
        ),
        EvidenceRecord(
            evidence_id="E-003",
            outcome_taxonomy="MARRIAGE_FORMATION",
            supporting_fact_type="JUPITER_ASPECTS_7TH",
            rule_id="R-003",
            source_id="Phaladeepika",
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.MODERATE,
            independence_group="PD-7L",
        ),
    )


@pytest.fixture
def sample_contradict_records() -> tuple[EvidenceRecord, ...]:
    """Sample contradicting evidence records."""
    return (
        EvidenceRecord(
            evidence_id="E-101",
            outcome_taxonomy="MARRIAGE_DELAYED",
            supporting_fact_type="SATURN_ASPECTS_7TH_LORD",
            rule_id="R-101",
            source_id="Phaladeepika",
            direction=EvidenceDirection.CONTRADICT,
            strength=EvidenceStrength.HIGH,
            independence_group="PD-7L",
        ),
    )


@pytest.fixture
def sample_event_window() -> EventWindow:
    """A sample convergent event window."""
    return EventWindow(
        candidate_event_taxonomy="MARRIAGE_FORMATION",
        window_start_utc="2024-01-01T00:00:00Z",
        window_end_utc="2024-12-31T23:59:59Z",
        triggers=(
            TemporalTrigger(
                activation_type=ActivationType.DASHA,
                triggering_planet="VENUS",
                activation_start_utc="2024-01-01T00:00:00Z",
                activation_end_utc="2024-12-31T23:59:59Z",
            ),
            TemporalTrigger(
                activation_type=ActivationType.TRANSIT,
                triggering_planet="JUPITER",
                activation_start_utc="2024-06-01T00:00:00Z",
                activation_end_utc="2024-12-31T23:59:59Z",
            ),
        ),
        convergence_level=ConvergenceLevel.HIGH,
    )


def make_evidence_record(
    evidence_id: str = "E-001",
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    strength: EvidenceStrength = EvidenceStrength.MODERATE,
    source_id: str = "BPHS",
    independence_group: str = "GRP-1",
    outcome_taxonomy: str = "TEST_OUTCOME",
) -> EvidenceRecord:
    """Builder for EvidenceRecord test objects."""
    return EvidenceRecord(
        evidence_id=evidence_id,
        outcome_taxonomy=outcome_taxonomy,
        supporting_fact_type="TEST_FACT",
        rule_id="R-TEST",
        source_id=source_id,
        direction=direction,
        strength=strength,
        independence_group=independence_group,
    )


def make_event_window(
    convergence: ConvergenceLevel = ConvergenceLevel.MODERATE,
    candidate_event: str = "TEST_OUTCOME",
) -> EventWindow:
    """Builder for EventWindow test objects."""
    return EventWindow(
        candidate_event_taxonomy=candidate_event,
        convergence_level=convergence,
    )

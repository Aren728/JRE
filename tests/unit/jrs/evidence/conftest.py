"""Shared test fixtures and builders for evidence unit tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from jrs.evidence.models import (
    ClassicalSource,
    EvidenceChain,
    EvidenceConfig,
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
    RuleCatalogEntry,
)

_FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "fixtures" / "evidence"


@pytest.fixture
def sample_config() -> EvidenceConfig:
    """A minimal EvidenceConfig for testing."""
    return EvidenceConfig(
        version="1.0",
        source_weights={"BPHS": 1.0, "Phaladeepika": 0.9},
        strength_multipliers={"HIGH": 0.85, "MODERATE": 0.65},
        max_chain_depth=10,
    )


@pytest.fixture
def sample_records() -> dict[str, EvidenceRecord]:
    """A set of interconnected evidence records for testing."""
    return {
        "E-1042": EvidenceRecord(
            evidence_id="E-1042",
            outcome_taxonomy="MARRIAGE_TIMELY",
            supporting_fact_type="7TH_LORD_IN_KENDRA",
            rule_id="R-7L-COND-X",
            source_id="BPHS",
            location="Chapter 7, Verse 12",
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.HIGH,
            contradicted_by=("E-1077",),
            mitigated_by=("E-1085",),
        ),
        "E-1043": EvidenceRecord(
            evidence_id="E-1043",
            outcome_taxonomy="MARRIAGE_TIMELY",
            supporting_fact_type="VENUS_ASPECTS_7TH",
            rule_id="R-VENUS-YOGA",
            source_id="BPHS",
            direction=EvidenceDirection.SUPPORT,
            strength=EvidenceStrength.MODERATE,
        ),
        "E-1077": EvidenceRecord(
            evidence_id="E-1077",
            outcome_taxonomy="MARRIAGE_DELAYED",
            supporting_fact_type="SATURN_ASPECTS_7TH_LORD",
            rule_id="R-7L-COND-X",
            source_id="Phaladeepika",
            direction=EvidenceDirection.CONTRADICT,
            strength=EvidenceStrength.MODERATE,
            mitigated_by=("E-1085",),
        ),
        "E-1085": EvidenceRecord(
            evidence_id="E-1085",
            outcome_taxonomy="MARRIAGE_NEUTRAL",
            supporting_fact_type="JUPITER_ASPECTS_7TH_LORD",
            rule_id="R-VENUS-YOGA",
            source_id="BPHS",
            direction=EvidenceDirection.MITIGATE,
            strength=EvidenceStrength.LOW,
        ),
    }


@pytest.fixture
def sample_marriage_fixture() -> dict:
    """Load the sample_marriage_evidence.json fixture."""
    path = _FIXTURES_DIR / "sample_marriage_evidence.json"
    with path.open() as f:
        return json.load(f)


def make_evidence_record(
    evidence_id: str = "E-001",
    outcome_taxonomy: str = "TEST_OUTCOME",
    direction: EvidenceDirection = EvidenceDirection.SUPPORT,
    strength: EvidenceStrength = EvidenceStrength.MODERATE,
    contradicted_by: tuple[str, ...] = (),
    mitigated_by: tuple[str, ...] = (),
) -> EvidenceRecord:
    """Builder for EvidenceRecord test objects."""
    return EvidenceRecord(
        evidence_id=evidence_id,
        outcome_taxonomy=outcome_taxonomy,
        supporting_fact_type="TEST_FACT",
        rule_id="R-TEST",
        source_id="BPHS",
        direction=direction,
        strength=strength,
        contradicted_by=contradicted_by,
        mitigated_by=mitigated_by,
    )


def make_classical_source(
    source_id: str = "BPHS",
    name: str = "Brihat Parashara Hora Shastra",
    reliability_weight: float = 1.0,
) -> ClassicalSource:
    """Builder for ClassicalSource test objects."""
    return ClassicalSource(
        source_id=source_id,
        name=name,
        reliability_weight=reliability_weight,
    )

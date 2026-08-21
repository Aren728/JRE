"""Unit tests for evidence models and graph traversal helpers."""

from __future__ import annotations

import json

import pytest

from tests.unit.jrs.evidence.conftest import make_evidence_record
from jrs.evidence.models import (
    ClassicalSource,
    EvidenceChain,
    EvidenceConfig,
    EvidenceDirection,
    EvidenceRecord,
    EvidenceStrength,
    RuleCatalogEntry,
    STRENGTH_VALUES,
    detect_circular_references,
    resolve_evidence_chain,
)


class TestEvidenceDirection:
    """Tests for the EvidenceDirection enum."""

    def test_all_directions_have_string_values(self) -> None:
        for d in EvidenceDirection:
            assert isinstance(d.value, str)
            assert d.value == d.name

    def test_direction_count(self) -> None:
        assert len(EvidenceDirection) == 4

    def test_direction_from_value(self) -> None:
        assert EvidenceDirection("SUPPORT") is EvidenceDirection.SUPPORT
        assert EvidenceDirection("CONTRADICT") is EvidenceDirection.CONTRADICT

    def test_invalid_direction(self) -> None:
        with pytest.raises(ValueError):
            EvidenceDirection("INVALID")


class TestEvidenceStrength:
    """Tests for the EvidenceStrength enum."""

    def test_all_strengths_have_string_values(self) -> None:
        for s in EvidenceStrength:
            assert isinstance(s.value, str)

    def test_strength_count(self) -> None:
        assert len(EvidenceStrength) == 5

    def test_strength_from_value(self) -> None:
        assert EvidenceStrength("HIGH") is EvidenceStrength.HIGH
        assert EvidenceStrength("VERY_LOW") is EvidenceStrength.VERY_LOW


class TestStrengthValues:
    """Tests for the STRENGTH_VALUES mapping."""

    def test_all_strengths_mapped(self) -> None:
        for s in EvidenceStrength:
            assert s in STRENGTH_VALUES

    def test_values_in_order(self) -> None:
        assert STRENGTH_VALUES[EvidenceStrength.VERY_HIGH] > STRENGTH_VALUES[EvidenceStrength.HIGH]
        assert STRENGTH_VALUES[EvidenceStrength.HIGH] > STRENGTH_VALUES[EvidenceStrength.MODERATE]
        assert STRENGTH_VALUES[EvidenceStrength.MODERATE] > STRENGTH_VALUES[EvidenceStrength.LOW]
        assert STRENGTH_VALUES[EvidenceStrength.LOW] > STRENGTH_VALUES[EvidenceStrength.VERY_LOW]

    def test_values_bounded(self) -> None:
        for v in STRENGTH_VALUES.values():
            assert 0.0 <= v <= 1.0


class TestClassicalSource:
    """Tests for the ClassicalSource model."""

    def test_creation(self) -> None:
        src = ClassicalSource(source_id="BPHS", name="Brihat Parashara Hora Shastra")
        assert src.source_id == "BPHS"
        assert src.reliability_weight == 1.0

    def test_frozen(self) -> None:
        src = ClassicalSource(source_id="BPHS", name="Test")
        with pytest.raises(AttributeError):
            src.source_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        src = ClassicalSource(
            source_id="BPHS",
            name="BPHS",
            author="Parashara",
            era="Classical",
            reliability_weight=0.95,
        )
        d = src.to_dict()
        assert d["source_id"] == "BPHS"
        assert d["reliability_weight"] == 0.95


class TestEvidenceRecord:
    """Tests for the EvidenceRecord model."""

    def test_creation(self) -> None:
        record = make_evidence_record(evidence_id="E-001")
        assert record.evidence_id == "E-001"
        assert record.direction is EvidenceDirection.SUPPORT

    def test_frozen(self) -> None:
        record = make_evidence_record()
        with pytest.raises(AttributeError):
            record.evidence_id = "changed"  # type: ignore[misc]

    def test_to_dict(self) -> None:
        record = make_evidence_record(
            evidence_id="E-100",
            direction=EvidenceDirection.CONTRADICT,
            strength=EvidenceStrength.HIGH,
            contradicted_by=("E-200",),
        )
        d = record.to_dict()
        assert d["evidence_id"] == "E-100"
        assert d["direction"] == "CONTRADICT"
        assert d["strength"] == "HIGH"
        assert d["contradicted_by"] == ["E-200"]

    def test_to_dict_deterministic(self) -> None:
        record = make_evidence_record()
        d1 = record.to_dict()
        d2 = record.to_dict()
        assert json.dumps(d1, sort_keys=True) == json.dumps(d2, sort_keys=True)

    def test_defaults(self) -> None:
        record = EvidenceRecord(
            evidence_id="E-001",
            outcome_taxonomy="TEST",
            supporting_fact_type="FACT",
            rule_id="R-001",
            source_id="BPHS",
        )
        assert record.direction is EvidenceDirection.SUPPORT
        assert record.strength is EvidenceStrength.MODERATE
        assert record.contradicted_by == ()
        assert record.mitigated_by == ()


class TestRuleCatalogEntry:
    """Tests for the RuleCatalogEntry model."""

    def test_creation(self) -> None:
        entry = RuleCatalogEntry(
            rule_id="R-001",
            description="Test rule",
            required_conditions=("cond_a", "cond_b"),
        )
        assert entry.rule_id == "R-001"
        assert len(entry.required_conditions) == 2

    def test_to_dict(self) -> None:
        entry = RuleCatalogEntry(
            rule_id="R-001",
            description="Test",
            outcome_taxonomy="TEST_OUTCOME",
        )
        d = entry.to_dict()
        assert d["rule_id"] == "R-001"
        assert d["outcome_taxonomy"] == "TEST_OUTCOME"

    def test_frozen(self) -> None:
        entry = RuleCatalogEntry(rule_id="R-001", description="Test")
        with pytest.raises(AttributeError):
            entry.rule_id = "changed"  # type: ignore[misc]


class TestDetectCircularReferences:
    """Tests for the detect_circular_references function."""

    def test_no_cycles(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", contradicted_by=("E-2",)),
            "E-2": make_evidence_record("E-2"),
        }
        cycles = detect_circular_references(records)
        assert cycles == []

    def test_simple_cycle(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", contradicted_by=("E-2",)),
            "E-2": make_evidence_record("E-2", contradicted_by=("E-1",)),
        }
        cycles = detect_circular_references(records)
        assert len(cycles) == 1

    def test_three_node_cycle(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", contradicted_by=("E-2",)),
            "E-2": make_evidence_record("E-2", contradicted_by=("E-3",)),
            "E-3": make_evidence_record("E-3", contradicted_by=("E-1",)),
        }
        cycles = detect_circular_references(records)
        assert len(cycles) == 1

    def test_mitigation_cycle(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", mitigated_by=("E-2",)),
            "E-2": make_evidence_record("E-2", mitigated_by=("E-1",)),
        }
        cycles = detect_circular_references(records)
        assert len(cycles) == 1

    def test_empty_registry(self) -> None:
        cycles = detect_circular_references({})
        assert cycles == []

    def test_self_reference(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", contradicted_by=("E-1",)),
        }
        cycles = detect_circular_references(records)
        assert len(cycles) == 1

    def test_diamond_no_cycle(self) -> None:
        """A diamond pattern (A->B, A->C, B->D, C->D) should not be a cycle."""
        records = {
            "E-1": make_evidence_record("E-1", contradicted_by=("E-2", "E-3")),
            "E-2": make_evidence_record("E-2", contradicted_by=("E-4",)),
            "E-3": make_evidence_record("E-3", contradicted_by=("E-4",)),
            "E-4": make_evidence_record("E-4"),
        }
        cycles = detect_circular_references(records)
        assert cycles == []


class TestResolveEvidenceChain:
    """Tests for the resolve_evidence_chain function."""

    def test_resolve_simple(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", contradicted_by=("E-2",)),
            "E-2": make_evidence_record("E-2"),
        }
        chain = resolve_evidence_chain("E-1", records)
        assert chain is not None
        assert chain.record.evidence_id == "E-1"
        assert len(chain.contradictions) == 1
        assert chain.contradictions[0].evidence_id == "E-2"

    def test_resolve_nonexistent(self) -> None:
        chain = resolve_evidence_chain("E-NONE", {})
        assert chain is None

    def test_resolve_with_mitigations(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", mitigated_by=("E-3",)),
            "E-3": make_evidence_record("E-3"),
        }
        chain = resolve_evidence_chain("E-1", records)
        assert chain is not None
        assert len(chain.mitigations) == 1

    def test_resolve_supporting(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1"),
            "E-2": make_evidence_record("E-2", contradicted_by=("E-1",)),
        }
        chain = resolve_evidence_chain("E-1", records)
        assert chain is not None
        assert len(chain.supporting) == 1
        assert chain.supporting[0].evidence_id == "E-2"

    def test_resolve_max_depth(self) -> None:
        records = {
            "E-1": make_evidence_record("E-1", contradicted_by=("E-2",)),
            "E-2": make_evidence_record("E-2"),
        }
        chain = resolve_evidence_chain("E-1", records, max_depth=0)
        assert chain is not None
        # With max_depth=0, links are not resolved
        assert len(chain.contradictions) == 0

    def test_resolve_full_graph(self, sample_records: dict[str, EvidenceRecord]) -> None:
        chain = resolve_evidence_chain("E-1042", sample_records)
        assert chain is not None
        assert chain.record.evidence_id == "E-1042"
        assert len(chain.contradictions) == 1  # E-1077
        assert len(chain.mitigations) == 1  # E-1085


class TestEvidenceChain:
    """Tests for the EvidenceChain model."""

    def test_creation(self) -> None:
        record = make_evidence_record("E-1")
        chain = EvidenceChain(record=record)
        assert chain.record.evidence_id == "E-1"
        assert chain.contradictions == ()

    def test_to_dict(self) -> None:
        record = make_evidence_record("E-1")
        chain = EvidenceChain(
            record=record,
            contradictions=(make_evidence_record("E-2"),),
        )
        d = chain.to_dict()
        assert d["record"]["evidence_id"] == "E-1"
        assert len(d["contradictions"]) == 1

    def test_frozen(self) -> None:
        chain = EvidenceChain(record=make_evidence_record("E-1"))
        with pytest.raises(AttributeError):
            chain.record = make_evidence_record("E-2")  # type: ignore[misc]

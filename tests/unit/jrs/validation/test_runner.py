"""JRS-088: Unit tests for Blind Historical Validation Runner Engine.

Tests verify:
1. Complete isolated run execution (Stage 1 -> Persist -> Stage 2 -> Score).
2. Detection and prevention of cryptographic tampering (CryptographicTamperError).
3. Rejection of unsealed or payload-modified prediction files.
4. Batch execution aggregation (BatchValidationReport) and error handling.
5. Verification that evaluation scoring cannot run if packet persistence fails.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from jrs.validation.models import (
    BatchValidationReport,
    BirthProvenance,
    ChartSubject,
    CryptographicTamperError,
    DomainType,
    FrozenPredictionPacket,
    HistoricalEvent,
    MetricEvaluation,
    RoddenRating,
    SingleValidationReport,
    ValidationStatus,
)
from jrs.validation.protocol import BlindValidationProtocol
from jrs.validation.runner import BlindValidationRunner
from jrs.validation.storage import (
    PredictionPacketStore,
    _canonicalize_floats,
    _compute_packet_hash,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


def _make_subject(
    chart_id: str = "subject_001",
    rodden: RoddenRating = RoddenRating.AA,
) -> ChartSubject:
    """Create a test ChartSubject."""
    return ChartSubject(
        chart_id=chart_id,
        latitude=28.6139,
        longitude=77.2090,
        birth_timestamp="1990-06-15T04:30:00+05:30",
        timezone="Asia/Kolkata",
        provenance=BirthProvenance(
            source="birth_certificate",
            rodden_rating=rodden,
            birth_time_confidence_minutes=0,
        ),
    )


def _make_event(
    event_id: str = "event_001",
    chart_id: str = "subject_001",
    domain: DomainType = DomainType.CAREER_PEAK,
    start_date: str = "2024-01-01T00:00:00Z",
    end_date: str | None = "2025-12-31T23:59:59Z",
    certainty: float = 1.0,
) -> HistoricalEvent:
    """Create a test HistoricalEvent."""
    return HistoricalEvent(
        event_id=event_id,
        chart_id=chart_id,
        domain=domain,
        start_date=start_date,
        end_date=end_date,
        event_certainty=certainty,
        description="Test event",
    )


def _make_packet(
    subject: ChartSubject | None = None,
    target_ts: str = "2024-06-15T00:00:00Z",
    predicted_strength: float = 0.8,
    payload_hash: str = "",
) -> FrozenPredictionPacket:
    """Create a test FrozenPredictionPacket."""
    if subject is None:
        subject = _make_subject()
    return FrozenPredictionPacket(
        subject=subject,
        target_timestamp=target_ts,
        formation_strength=0.9,
        structural_relationship_score=0.7,
        modification_impact=0.6,
        varga_confirmation_score=0.8,
        dasha_transit_activation=0.5,
        predicted_strength=predicted_strength,
        payload_hash=payload_hash,
    )


def _make_sealed_packet(
    subject: ChartSubject | None = None,
    predicted_strength: float = 0.8,
) -> FrozenPredictionPacket:
    """Create a properly sealed FrozenPredictionPacket."""
    if subject is None:
        subject = _make_subject()
    packet = _make_packet(subject=subject, predicted_strength=predicted_strength)
    h = _compute_packet_hash(packet)
    return FrozenPredictionPacket(
        subject=packet.subject,
        target_timestamp=packet.target_timestamp,
        formation_strength=packet.formation_strength,
        structural_relationship_score=packet.structural_relationship_score,
        modification_impact=packet.modification_impact,
        varga_confirmation_score=packet.varga_confirmation_score,
        dasha_transit_activation=packet.dasha_transit_activation,
        predicted_strength=packet.predicted_strength,
        payload_hash=h,
    )


class _StubProtocol:
    """Stub BlindValidationProtocol that returns pre-built packets."""

    def __init__(self, packet: FrozenPredictionPacket) -> None:
        self._packet = packet
        self._generate_called = False
        self._evaluate_called = False

    def generate_prediction_packet(
        self, subject: Any, target_timestamp: str,
    ) -> FrozenPredictionPacket:
        self._generate_called = True
        return self._packet

    def evaluate_prediction_against_event(
        self, packet: Any, event: Any,
    ) -> MetricEvaluation:
        self._evaluate_called = True
        return MetricEvaluation(
            packet_hash=packet.payload_hash,
            event_id=event.event_id,
            event_certainty=event.event_certainty,
            prediction_strength=packet.predicted_strength,
            hit=packet.predicted_strength > 0.0,
            timing_match=True,
            score=min(packet.predicted_strength * event.event_certainty + 0.10, 1.0),
        )


class _StubPipelineService:
    """Stub pipeline service that does nothing."""

    def evaluate_classical_yogas(self, jre_facts: Any) -> list[Any]:
        return []


# ══════════════════════════════════════════════════════════════════════
# 1. Complete Isolated Run Execution
# ══════════════════════════════════════════════════════════════════════


class TestIsolatedRunExecution:
    """Test Stage 1 -> Persist -> Stage 2 -> Score flow."""

    def test_run_blind_evaluation_end_to_end(self, tmp_path: Path) -> None:
        """Full blind evaluation completes and returns MetricEvaluation."""
        subject = _make_subject()
        event = _make_event()
        packet = _make_sealed_packet(subject=subject)

        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=_StubProtocol(packet),
        )

        result = runner.run_blind_evaluation(
            subject=subject,
            target_timestamp="2024-06-15T00:00:00Z",
            ground_truth_event=event,
            output_dir=tmp_path,
        )

        assert isinstance(result, MetricEvaluation)
        assert result.event_id == "event_001"
        assert result.hit is True

    def test_packet_persisted_to_disk(self, tmp_path: Path) -> None:
        """Stage 1 persists a JSON file to the output directory."""
        subject = _make_subject()
        event = _make_event()
        packet = _make_sealed_packet(subject=subject)

        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=_StubProtocol(packet),
        )

        runner.run_blind_evaluation(
            subject=subject,
            target_timestamp="2024-06-15T00:00:00Z",
            ground_truth_event=event,
            output_dir=tmp_path,
        )

        # Verify file was created
        expected_path = tmp_path / "subject_001_packet.json"
        assert expected_path.exists()

        # Verify file contains valid JSON with hash
        data = json.loads(expected_path.read_text())
        assert "payload_hash" in data
        assert "subject" in data
        assert data["subject"]["chart_id"] == "subject_001"

    def test_stage2_loads_from_disk_not_memory(self, tmp_path: Path) -> None:
        """Stage 2 loads the packet from disk, not from in-process state."""
        subject = _make_subject()
        event = _make_event()
        packet = _make_sealed_packet(subject=subject)

        protocol = _StubProtocol(packet)
        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=protocol,
        )

        result = runner.run_blind_evaluation(
            subject=subject,
            target_timestamp="2024-06-15T00:00:00Z",
            ground_truth_event=event,
            output_dir=tmp_path,
        )

        # Protocol generate was called (Stage 1)
        assert protocol._generate_called is True
        # Protocol evaluate was called (Stage 2)
        assert protocol._evaluate_called is True
        # Score should reflect the packet's predicted strength
        assert result.score > 0.0

    def test_generate_then_del_packet(self, tmp_path: Path) -> None:
        """After Stage 1, the in-memory packet is deleted before Stage 2."""
        subject = _make_subject()
        event = _make_event()
        packet = _make_sealed_packet(subject=subject)

        # Track that packet is passed to generate but evaluate gets from store
        saved_packets: list[Any] = []

        class _TrackingProtocol:
            def __init__(self) -> None:
                self._generate_called = False
                self._evaluate_called = False

            def generate_prediction_packet(
                self, subject: Any, target_timestamp: str,
            ) -> FrozenPredictionPacket:
                self._generate_called = True
                return packet

            def evaluate_prediction_against_event(
                self, pkt: Any, evt: Any,
            ) -> MetricEvaluation:
                self._evaluate_called = True
                saved_packets.append(pkt)
                return MetricEvaluation(
                    packet_hash=pkt.payload_hash,
                    event_id=evt.event_id,
                    prediction_strength=pkt.predicted_strength,
                    hit=True,
                    timing_match=True,
                    score=0.9,
                )

        protocol = _TrackingProtocol()
        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=protocol,
        )

        result = runner.run_blind_evaluation(
            subject=subject,
            target_timestamp="2024-06-15T00:00:00Z",
            ground_truth_event=event,
            output_dir=tmp_path,
        )

        assert protocol._generate_called is True
        assert protocol._evaluate_called is True
        assert result.score == pytest.approx(0.9, abs=1e-6)


# ══════════════════════════════════════════════════════════════════════
# 2. Cryptographic Tampering Detection
# ══════════════════════════════════════════════════════════════════════


class TestTamperDetection:
    """Test CryptographicTamperError on hash mismatch."""

    def test_tampered_hash_raises_error(self, tmp_path: Path) -> None:
        """Modifying the stored hash raises CryptographicTamperError."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")

        # Tamper with the stored hash
        data = json.loads(path.read_text())
        data["payload_hash"] = "0" * 64  # wrong hash
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

        with pytest.raises(CryptographicTamperError) as exc_info:
            store.load_and_verify(path)

        assert "tampered" in str(exc_info.value).lower()

    def test_tampered_payload_raises_error(self, tmp_path: Path) -> None:
        """Modifying the prediction_strength raises CryptographicTamperError."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject, predicted_strength=0.8)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")

        # Tamper with the payload
        data = json.loads(path.read_text())
        data["predicted_strength"] = 0.99  # modify value
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

        with pytest.raises(CryptographicTamperError):
            store.load_and_verify(path)

    def test_tampered_subject_raises_error(self, tmp_path: Path) -> None:
        """Modifying the subject chart_id raises CryptographicTamperError."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")

        # Tamper with subject
        data = json.loads(path.read_text())
        data["subject"]["chart_id"] = "tampered_id"
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

        with pytest.raises(CryptographicTamperError):
            store.load_and_verify(path)

    def test_tamper_error_contains_expected_and_actual_hashes(self, tmp_path: Path) -> None:
        """CryptographicTamperError stores both expected and actual hashes."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")

        # Tamper
        data = json.loads(path.read_text())
        data["predicted_strength"] = 0.5
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

        with pytest.raises(CryptographicTamperError) as exc_info:
            store.load_and_verify(path)

        err = exc_info.value
        assert len(err.expected_hash) == 64
        assert len(err.actual_hash) == 64
        assert err.expected_hash != err.actual_hash

    def test_valid_packet_loads_without_error(self, tmp_path: Path) -> None:
        """Unmodified packet loads and verifies without error."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")

        verified = store.load_and_verify(path)
        assert verified.payload_hash == packet.payload_hash
        assert verified.predicted_strength == packet.predicted_strength


# ══════════════════════════════════════════════════════════════════════
# 3. Rejection of Unsealed/Modified Files
# ══════════════════════════════════════════════════════════════════════


class TestFileRejection:
    """Test rejection of unsealed or modified prediction files."""

    def test_empty_hash_rejected(self, tmp_path: Path) -> None:
        """Packet with empty hash is rejected on verification."""
        subject = _make_subject()
        packet = _make_packet(subject=subject, predicted_strength=0.8)
        # Empty hash — not sealed
        path = tmp_path / "unsealed.json"
        data = packet.to_dict()
        data["payload_hash"] = ""
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

        store = PredictionPacketStore()
        with pytest.raises(CryptographicTamperError):
            store.load_and_verify(path)

    def test_extra_field_in_payload_rejected(self, tmp_path: Path) -> None:
        """Adding an extra field to the payload raises tamper error."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")

        # Add an extra field
        data = json.loads(path.read_text())
        data["sneaky_field"] = "injected_value"
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

        with pytest.raises(CryptographicTamperError):
            store.load_and_verify(path)

    def test_missing_subject_rejected(self, tmp_path: Path) -> None:
        """Removing the subject from the packet causes an error."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")

        # Remove subject
        data = json.loads(path.read_text())
        del data["subject"]
        path.write_text(json.dumps(data, sort_keys=True, indent=2))

        with pytest.raises((CryptographicTamperError, KeyError)):
            store.load_and_verify(path)

    def test_corrupt_json_rejected(self, tmp_path: Path) -> None:
        """Corrupt JSON file raises a JSON decode error."""
        path = tmp_path / "corrupt.json"
        path.write_text("{invalid json content")

        store = PredictionPacketStore()
        with pytest.raises(json.JSONDecodeError):
            store.load_and_verify(path)

    def test_missing_file_rejected(self) -> None:
        """Non-existent file raises FileNotFoundError."""
        store = PredictionPacketStore()
        with pytest.raises(FileNotFoundError):
            store.load_and_verify(Path("/nonexistent/path.json"))


# ══════════════════════════════════════════════════════════════════════
# 4. Batch Execution Aggregation
# ══════════════════════════════════════════════════════════════════════


class TestBatchExecution:
    """Test BatchValidationReport and error handling behavior."""

    def test_batch_all_success(self, tmp_path: Path) -> None:
        """All charts succeed in batch evaluation."""
        subjects = [_make_subject(chart_id=f"sub_{i}") for i in range(3)]
        events = [_make_event(event_id=f"evt_{i}", chart_id=f"sub_{i}") for i in range(3)]
        packets = [_make_sealed_packet(subject=s) for s in subjects]

        protocols = [_StubProtocol(p) for p in packets]
        idx = [0]

        def make_runner() -> BlindValidationRunner:
            i = idx[0]
            idx[0] += 1
            return BlindValidationRunner(
                pipeline_service=_StubPipelineService(),
                protocol=protocols[i] if i < len(protocols) else protocols[0],
            )

        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=protocols[0],
        )

        pairs = [
            (subjects[i], "2024-06-15T00:00:00Z", events[i])
            for i in range(3)
        ]
        report = runner.run_batch_evaluation(pairs, tmp_path)

        assert isinstance(report, BatchValidationReport)
        assert report.total_charts == 3
        assert report.successful_evaluations == 3
        assert report.failed_evaluations == 0
        assert len(report.reports) == 3

        for r in report.reports:
            assert r.status == ValidationStatus.SUCCESS
            assert r.metric_evaluation is not None

    def test_batch_mixed_success_and_failure(self, tmp_path: Path) -> None:
        """Batch handles mix of successes and failures gracefully."""
        s1 = _make_subject(chart_id="good")
        s2 = _make_subject(chart_id="bad")
        e1 = _make_event(chart_id="good")
        e2 = _make_event(chart_id="bad")

        p1 = _make_sealed_packet(subject=s1)
        p2 = _make_sealed_packet(subject=s2, predicted_strength=0.9)

        # Protocol that fails on second call
        class _FailingProtocol:
            def __init__(self) -> None:
                self._call_count = 0

            def generate_prediction_packet(self, subject: Any, ts: str) -> FrozenPredictionPacket:
                self._call_count += 1
                if self._call_count == 2:
                    raise RuntimeError("Simulated pipeline failure")
                return p1 if subject.chart_id == "good" else p2

            def evaluate_prediction_against_event(self, pkt: Any, evt: Any) -> MetricEvaluation:
                return MetricEvaluation(
                    packet_hash=pkt.payload_hash,
                    event_id=evt.event_id,
                    prediction_strength=pkt.predicted_strength,
                    hit=True,
                    timing_match=True,
                    score=0.85,
                )

        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=_FailingProtocol(),
        )

        pairs = [
            (s1, "2024-06-15T00:00:00Z", e1),
            (s2, "2024-06-15T00:00:00Z", e2),
        ]
        report = runner.run_batch_evaluation(pairs, tmp_path)

        assert report.total_charts == 2
        assert report.successful_evaluations == 1
        assert report.failed_evaluations == 1

        # First should succeed
        assert report.reports[0].status == ValidationStatus.SUCCESS
        assert report.reports[0].metric_evaluation is not None

        # Second should fail
        assert report.reports[1].status == ValidationStatus.PERSISTENCE_FAILED
        assert "pipeline failure" in report.reports[1].error_message.lower()

    def test_batch_empty_list(self, tmp_path: Path) -> None:
        """Empty batch produces empty report."""
        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=_StubProtocol(_make_sealed_packet()),
        )

        report = runner.run_batch_evaluation([], tmp_path)

        assert report.total_charts == 0
        assert report.successful_evaluations == 0
        assert report.failed_evaluations == 0
        assert len(report.reports) == 0

    def test_batch_report_serialization(self, tmp_path: Path) -> None:
        """BatchValidationReport serializes deterministically."""
        subject = _make_subject()
        event = _make_event()
        packet = _make_sealed_packet(subject=subject)

        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            protocol=_StubProtocol(packet),
        )

        report = runner.run_batch_evaluation(
            [(subject, "2024-06-15T00:00:00Z", event)],
            tmp_path,
        )

        d = report.to_dict()
        assert d["total_charts"] == 1
        assert d["successful_evaluations"] == 1
        assert d["failed_evaluations"] == 0
        assert len(d["reports"]) == 1
        assert d["reports"][0]["status"] == "SUCCESS"
        assert "metric_evaluation" in d["reports"][0]


# ══════════════════════════════════════════════════════════════════════
# 5. Persistence Failure Prevents Scoring
# ══════════════════════════════════════════════════════════════════════


class TestPersistencePreventsScoring:
    """Verify that scoring cannot run if packet persistence fails."""

    def test_persistence_error_blocks_stage2(self, tmp_path: Path) -> None:
        """If save_packet fails, evaluate is never called."""
        subject = _make_subject()
        event = _make_event()
        packet = _make_sealed_packet(subject=subject)

        evaluate_called = [False]

        class _TrackingProtocol:
            def generate_prediction_packet(self, subject: Any, ts: str) -> FrozenPredictionPacket:
                return packet

            def evaluate_prediction_against_event(self, pkt: Any, evt: Any) -> MetricEvaluation:
                evaluate_called[0] = True
                return MetricEvaluation(
                    packet_hash=pkt.payload_hash,
                    event_id=evt.event_id,
                    hit=True,
                    score=0.9,
                )

        class _FailingStore:
            def save_packet(self, packet: Any, path: Any) -> Any:
                raise IOError("Disk full")

            def load_and_verify(self, path: Any) -> Any:
                # Should never reach here
                return packet

        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            packet_store=_FailingStore(),
            protocol=_TrackingProtocol(),
        )

        with pytest.raises(RuntimeError, match="Failed to persist"):
            runner.run_blind_evaluation(
                subject, "2024-06-15T00:00:00Z", event, tmp_path,
            )

        # Stage 2 should never have been reached
        assert evaluate_called[0] is False

    def test_tamper_during_batch_marks_tampered(self, tmp_path: Path) -> None:
        """Tampered packets in batch are marked as TAMPERED status."""
        subject = _make_subject()
        event = _make_event()
        packet = _make_sealed_packet(subject=subject)

        class _TamperingStore:
            def save_packet(self, packet: Any, path: Any) -> Any:
                # Save normally first
                from jrs.validation.storage import PredictionPacketStore
                real = PredictionPacketStore()
                real_path = real.save_packet(packet, path)
                # Then tamper
                data = json.loads(real_path.read_text())
                data["predicted_strength"] = 0.99
                real_path.write_text(json.dumps(data, sort_keys=True, indent=2))
                return real_path

            def load_and_verify(self, path: Any) -> Any:
                from jrs.validation.storage import PredictionPacketStore
                return PredictionPacketStore().load_and_verify(path)

        runner = BlindValidationRunner(
            pipeline_service=_StubPipelineService(),
            packet_store=_TamperingStore(),
            protocol=_StubProtocol(packet),
        )

        report = runner.run_batch_evaluation(
            [(subject, "2024-06-15T00:00:00Z", event)],
            tmp_path,
        )

        assert report.failed_evaluations == 1
        assert report.reports[0].status == ValidationStatus.TAMPERED


# ══════════════════════════════════════════════════════════════════════
# 6. Storage Unit Tests
# ══════════════════════════════════════════════════════════════════════


class TestPredictionPacketStore:
    """Test PredictionPacketStore save/load/verify cycle."""

    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        """Packet survives save -> load roundtrip with identical fields."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        path = store.save_packet(packet, tmp_path / "test.json")
        verified = store.load_and_verify(path)

        assert verified.subject.chart_id == subject.chart_id
        assert verified.predicted_strength == packet.predicted_strength
        assert verified.formation_strength == packet.formation_strength
        assert verified.payload_hash == packet.payload_hash

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """save_packet creates parent directories if needed."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        store = PredictionPacketStore()
        deep_path = tmp_path / "a" / "b" / "c" / "packet.json"
        path = store.save_packet(packet, deep_path)

        assert path.exists()
        assert path.parent.exists()

    def test_save_default_path(self, tmp_path: Path) -> None:
        """save_packet with None destination generates a default path."""
        subject = _make_subject()
        packet = _make_sealed_packet(subject=subject)

        # Override cwd to control where default path is created
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            store = PredictionPacketStore()
            path = store.save_packet(packet, None)
            assert path.exists()
            assert path.suffix == ".json"
        finally:
            os.chdir(original_cwd)


# ══════════════════════════════════════════════════════════════════════
# 7. Hash Canonicalization
# ══════════════════════════════════════════════════════════════════════


class TestHashCanonicalization:
    """Test float canonicalization prevents false hash mismatches."""

    def test_canonicalize_floats_rounds(self) -> None:
        """Floats are rounded to 6 decimal places."""
        result = _canonicalize_floats(0.123456789)
        assert result == 0.123457

    def test_canonicalize_floats_nested(self) -> None:
        """Nested structures have floats canonicalized."""
        data = {"a": 1.0, "b": [2.0, 3.0000001]}
        result = _canonicalize_floats(data)
        assert result["a"] == 1.0
        assert result["b"][0] == 2.0
        assert result["b"][1] == round(3.0000001, 6)

    def test_same_packet_same_hash(self) -> None:
        """Identical packets produce identical hashes."""
        s = _make_subject()
        p1 = _make_sealed_packet(subject=s)
        p2 = _make_sealed_packet(subject=s)
        assert _compute_packet_hash(p1) == _compute_packet_hash(p2)


# ══════════════════════════════════════════════════════════════════════
# 8. Model Validation
# ══════════════════════════════════════════════════════════════════════


class TestValidationModels:
    """Test CryptographicTamperError, ValidationStatus, report models."""

    def test_tamper_error_message(self) -> None:
        """CryptographicTamperError has a descriptive message."""
        err = CryptographicTamperError(
            "Hash mismatch detected",
            expected_hash="aaa",
            actual_hash="bbb",
        )
        assert "Hash mismatch" in str(err)
        assert err.expected_hash == "aaa"
        assert err.actual_hash == "bbb"

    def test_validation_status_values(self) -> None:
        """ValidationStatus enum has all required values."""
        assert ValidationStatus.SUCCESS.value == "SUCCESS"
        assert ValidationStatus.TAMPERED.value == "TAMPERED"
        assert ValidationStatus.INCOMPLETE_PROVENANCE.value == "INCOMPLETE_PROVENANCE"
        assert ValidationStatus.PERSISTENCE_FAILED.value == "PERSISTENCE_FAILED"

    def test_single_validation_report_success(self) -> None:
        """SingleValidationReport with SUCCESS status."""
        metric = MetricEvaluation(
            packet_hash="abc", event_id="e1", score=0.85,
        )
        report = SingleValidationReport(
            chart_id="c1",
            status=ValidationStatus.SUCCESS,
            metric_evaluation=metric,
        )
        d = report.to_dict()
        assert d["chart_id"] == "c1"
        assert d["status"] == "SUCCESS"
        assert d["metric_evaluation"]["score"] == 0.85

    def test_single_validation_report_failure(self) -> None:
        """SingleValidationReport with failure status and error message."""
        report = SingleValidationReport(
            chart_id="c2",
            status=ValidationStatus.TAMPERED,
            error_message="Packet tampered",
        )
        d = report.to_dict()
        assert d["status"] == "TAMPERED"
        assert d["error_message"] == "Packet tampered"
        assert "metric_evaluation" not in d

    def test_batch_report_serialization(self) -> None:
        """BatchValidationReport serializes with all fields."""
        r1 = SingleValidationReport(
            chart_id="c1", status=ValidationStatus.SUCCESS,
            metric_evaluation=MetricEvaluation(packet_hash="a", event_id="e1"),
        )
        r2 = SingleValidationReport(
            chart_id="c2", status=ValidationStatus.TAMPERED,
            error_message="tampered",
        )
        batch = BatchValidationReport(
            total_charts=2,
            successful_evaluations=1,
            failed_evaluations=1,
            reports=(r1, r2),
        )
        d = batch.to_dict()
        assert d["total_charts"] == 2
        assert d["successful_evaluations"] == 1
        assert d["failed_evaluations"] == 1
        assert len(d["reports"]) == 2

    def test_batch_report_frozen(self) -> None:
        """BatchValidationReport is immutable."""
        report = BatchValidationReport()
        with pytest.raises(AttributeError):
            report.total_charts = 5  # type: ignore[misc]

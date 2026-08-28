"""JRS-087: Unit tests for Historical Dataset Specification & Blind Validation Schema.

Tests verify:
1. Strict separation of birth data (ChartSubject) vs. ground-truth events (HistoricalEvent).
2. Prediction packet SHA-256 hash generation and verification.
3. Rodden Rating constraints and event date window matching.
4. MetricEvaluation scoring logic.
5. FrozenPredictionPacket immutability and serialization.
"""

from __future__ import annotations

import hashlib
import json
import pytest

from jrs.validation.models import (
    BirthProvenance,
    ChartSubject,
    DomainType,
    FrozenPredictionPacket,
    HistoricalEvent,
    MetricEvaluation,
    RoddenRating,
)


# ══════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════


def _make_subject(
    chart_id: str = "subject_001",
    rodden: RoddenRating = RoddenRating.AA,
    confidence_minutes: int = 0,
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
            birth_time_confidence_minutes=confidence_minutes,
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
    predicted_strength: float = 0.85,
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


# ══════════════════════════════════════════════════════════════════════
# 1. Target Leakage Prevention
# ══════════════════════════════════════════════════════════════════════


class TestLeakagePrevention:
    """Ensure ChartSubject and HistoricalEvent are strictly decoupled."""

    def test_chart_subject_has_no_event_fields(self) -> None:
        """ChartSubject must not contain any event-related attributes."""
        subject = _make_subject()
        attrs = set(subject.__dataclass_fields__.keys())
        event_fields = {
            "event_id", "domain", "start_date", "end_date",
            "event_certainty", "description",
        }
        assert attrs.isdisjoint(event_fields), (
            f"ChartSubject leaks event fields: {attrs & event_fields}"
        )

    def test_historical_event_has_no_birth_fields(self) -> None:
        """HistoricalEvent must not contain birth-specific attributes."""
        event = _make_event()
        attrs = set(event.__dataclass_fields__.keys())
        birth_fields = {
            "latitude", "longitude", "birth_timestamp",
            "timezone", "provenance",
        }
        assert attrs.isdisjoint(birth_fields), (
            f"HistoricalEvent leaks birth fields: {attrs & birth_fields}"
        )

    def test_subject_serialization_has_no_event_data(self) -> None:
        """Subject serialization must not contain event information."""
        subject = _make_subject()
        d = subject.to_dict()
        serialized_keys = set(d.keys())
        assert "event_id" not in serialized_keys
        assert "domain" not in serialized_keys
        assert "start_date" not in serialized_keys

    def test_event_serialization_has_no_birth_data(self) -> None:
        """Event serialization must not contain birth information."""
        event = _make_event()
        d = event.to_dict()
        serialized_keys = set(d.keys())
        assert "latitude" not in serialized_keys
        assert "longitude" not in serialized_keys
        assert "birth_timestamp" not in serialized_keys
        assert "provenance" not in serialized_keys

    def test_subject_and_event_are_separate_types(self) -> None:
        """ChartSubject and HistoricalEvent must be distinct classes."""
        assert ChartSubject is not HistoricalEvent


# ══════════════════════════════════════════════════════════════════════
# 2. SHA-256 Hash Generation & Verification
# ══════════════════════════════════════════════════════════════════════


class TestSHA256Hashing:
    """Test FrozenPredictionPacket SHA-256 hash generation and verification."""

    def test_hash_is_valid_sha256(self) -> None:
        """Payload hash must be a valid 64-char hex SHA-256 digest."""
        subject = _make_subject()
        payload = {
            "subject": subject.to_dict(),
            "target_timestamp": "2024-06-15T00:00:00Z",
            "formation_strength": 0.9,
            "structural_relationship_score": 0.7,
            "modification_impact": 0.6,
            "varga_confirmation_score": 0.8,
            "dasha_transit_activation": 0.5,
            "predicted_strength": 0.85,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        assert len(expected_hash) == 64
        assert all(c in "0123456789abcdef" for c in expected_hash)

    def test_packet_hash_matches_computed(self) -> None:
        """Packet's payload_hash should match independently computed SHA-256."""
        from jrs.validation.protocol import BlindValidationProtocol

        subject = _make_subject()
        packet = _make_packet(subject=subject)

        # Compute expected hash
        payload = packet.to_dict()
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

        # Protocol should produce the same hash
        computed = BlindValidationProtocol._compute_hash(packet)
        assert computed == expected

    def test_different_subjects_produce_different_hashes(self) -> None:
        """Different subjects must produce different payload hashes."""
        from jrs.validation.protocol import BlindValidationProtocol

        s1 = _make_subject(chart_id="A")
        s2 = _make_subject(chart_id="B")
        p1 = _make_packet(subject=s1)
        p2 = _make_packet(subject=s2)
        assert BlindValidationProtocol._compute_hash(p1) != BlindValidationProtocol._compute_hash(p2)

    def test_same_inputs_produce_deterministic_hash(self) -> None:
        """Same inputs must always produce the same hash."""
        from jrs.validation.protocol import BlindValidationProtocol

        subject = _make_subject()
        p1 = _make_packet(subject=subject)
        p2 = _make_packet(subject=subject)
        assert BlindValidationProtocol._compute_hash(p1) == BlindValidationProtocol._compute_hash(p2)

    def test_packet_to_full_dict_includes_hash(self) -> None:
        """to_full_dict() should include the payload_hash field."""
        packet = _make_packet(payload_hash="abc123")
        d = packet.to_full_dict()
        assert "payload_hash" in d
        assert d["payload_hash"] == "abc123"

    def test_packet_to_dict_excludes_hash(self) -> None:
        """to_dict() should NOT include the payload_hash field."""
        packet = _make_packet(payload_hash="abc123")
        d = packet.to_dict()
        assert "payload_hash" not in d


# ══════════════════════════════════════════════════════════════════════
# 3. Rodden Rating Constraints
# ══════════════════════════════════════════════════════════════════════


class TestRoddenRating:
    """Test Rodden Rating classification and usage in provenance."""

    def test_rodden_rating_values(self) -> None:
        """RoddenRating enum has all required values."""
        assert RoddenRating.AA.value == "AA"
        assert RoddenRating.A.value == "A"
        assert RoddenRating.B.value == "B"
        assert RoddenRating.C.value == "C"
        assert RoddenRating.DD.value == "DD"

    def test_birth_provenance_with_rodden_a(self) -> None:
        """BirthProvenance stores RoddenRating correctly."""
        prov = BirthProvenance(
            source="birth_certificate",
            rodden_rating=RoddenRating.AA,
            birth_time_confidence_minutes=0,
        )
        assert prov.rodden_rating == RoddenRating.AA
        assert prov.birth_time_confidence_minutes == 0

    def test_birth_provenance_serialization(self) -> None:
        """BirthProvenance serializes rodden_rating as string value."""
        prov = BirthProvenance(
            source="memory",
            rodden_rating=RoddenRating.B,
            birth_time_confidence_minutes=15,
        )
        d = prov.to_dict()
        assert d["rodden_rating"] == "B"
        assert d["birth_time_confidence_minutes"] == 15

    def test_chart_subject_default_provenance(self) -> None:
        """ChartSubject default provenance uses Rodden C."""
        subject = ChartSubject(
            chart_id="x",
            latitude=0.0,
            longitude=0.0,
            birth_timestamp="2000-01-01T00:00:00Z",
        )
        assert subject.provenance.rodden_rating == RoddenRating.C


# ══════════════════════════════════════════════════════════════════════
# 4. Event Date Window Matching
# ══════════════════════════════════════════════════════════════════════


class TestEventDateWindow:
    """Test HistoricalEvent date handling and window matching."""

    def test_event_with_end_date(self) -> None:
        """Event with explicit end_date is stored correctly."""
        event = _make_event(
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-12-31T23:59:59Z",
        )
        assert event.end_date == "2024-12-31T23:59:59Z"

    def test_event_without_end_date(self) -> None:
        """Event without end_date has None end_date."""
        event = _make_event(end_date=None)
        assert event.end_date is None

    def test_timing_match_within_window(self) -> None:
        """Target within event window -> timing_match = True."""
        from jrs.validation.protocol import BlindValidationProtocol

        assert BlindValidationProtocol._check_timing(
            "2024-06-15T00:00:00Z",
            "2024-01-01T00:00:00Z",
            "2024-12-31T23:59:59Z",
        ) is True

    def test_timing_no_match_outside_window(self) -> None:
        """Target outside event window -> timing_match = False."""
        from jrs.validation.protocol import BlindValidationProtocol

        assert BlindValidationProtocol._check_timing(
            "2025-06-15T00:00:00Z",
            "2024-01-01T00:00:00Z",
            "2024-12-31T23:59:59Z",
        ) is False

    def test_timing_match_no_end_date(self) -> None:
        """No end_date: target >= start -> match."""
        from jrs.validation.protocol import BlindValidationProtocol

        assert BlindValidationProtocol._check_timing(
            "2025-06-15T00:00:00Z",
            "2024-01-01T00:00:00Z",
            None,
        ) is True

    def test_timing_no_match_before_start(self) -> None:
        """Target before event start -> no match."""
        from jrs.validation.protocol import BlindValidationProtocol

        assert BlindValidationProtocol._check_timing(
            "2023-01-01T00:00:00Z",
            "2024-01-01T00:00:00Z",
            "2024-12-31T23:59:59Z",
        ) is False

    def test_event_certainty_range(self) -> None:
        """Event certainty must be between 0.0 and 1.0."""
        event = _make_event(certainty=0.75)
        assert 0.0 <= event.event_certainty <= 1.0

    def test_domain_type_values(self) -> None:
        """DomainType enum has all required values."""
        assert DomainType.CAREER_PEAK.value == "CAREER_PEAK"
        assert DomainType.HEALTH_CRISIS.value == "HEALTH_CRISIS"
        assert DomainType.MARRIAGE.value == "MARRIAGE"
        assert DomainType.WEALTH_EVENT.value == "WEALTH_EVENT"
        assert DomainType.ACCIDENT.value == "ACCIDENT"


# ══════════════════════════════════════════════════════════════════════
# 5. MetricEvaluation Scoring
# ══════════════════════════════════════════════════════════════════════


class TestMetricEvaluation:
    """Test MetricEvaluation construction and scoring logic."""

    def test_metric_evaluation_construction(self) -> None:
        """MetricEvaluation can be constructed with required fields."""
        m = MetricEvaluation(
            packet_hash="abc123",
            event_id="e1",
            event_certainty=1.0,
            prediction_strength=0.8,
            hit=True,
            timing_match=True,
            score=0.9,
        )
        assert m.packet_hash == "abc123"
        assert m.hit is True

    def test_metric_evaluation_serialization(self) -> None:
        """MetricEvaluation serializes deterministically."""
        m = MetricEvaluation(
            packet_hash="abc123",
            event_id="e1",
            event_certainty=0.9,
            prediction_strength=0.7,
            hit=True,
            timing_match=False,
            score=0.63,
        )
        d = m.to_dict()
        assert d["packet_hash"] == "abc123"
        assert d["hit"] is True
        assert d["timing_match"] is False
        assert d["score"] == 0.63

    def test_score_formula_hit_with_timing(self) -> None:
        """Score = strength * certainty + 0.10 when hit and timing match."""
        from jrs.validation.protocol import BlindValidationProtocol

        score = BlindValidationProtocol._compute_score(
            prediction_strength=0.8,
            event_certainty=1.0,
            hit=True,
            timing_match=True,
        )
        expected = min(0.8 * 1.0 + 0.10, 1.0)
        assert score == pytest.approx(expected, abs=1e-6)

    def test_score_formula_hit_without_timing(self) -> None:
        """Score = strength * certainty when hit but no timing match."""
        from jrs.validation.protocol import BlindValidationProtocol

        score = BlindValidationProtocol._compute_score(
            prediction_strength=0.8,
            event_certainty=0.9,
            hit=True,
            timing_match=False,
        )
        expected = 0.8 * 0.9
        assert score == pytest.approx(expected, abs=1e-6)

    def test_score_formula_no_hit(self) -> None:
        """Score = 0.0 when not a hit."""
        from jrs.validation.protocol import BlindValidationProtocol

        score = BlindValidationProtocol._compute_score(
            prediction_strength=0.8,
            event_certainty=1.0,
            hit=False,
            timing_match=True,
        )
        assert score == 0.0

    def test_score_clamped_at_1_0(self) -> None:
        """Score must not exceed 1.0 even with high values."""
        from jrs.validation.protocol import BlindValidationProtocol

        score = BlindValidationProtocol._compute_score(
            prediction_strength=1.0,
            event_certainty=1.0,
            hit=True,
            timing_match=True,
        )
        assert score == pytest.approx(1.0, abs=1e-6)

    def test_score_bounded_zero_one(self) -> None:
        """Score always stays in [0.0, 1.0]."""
        from jrs.validation.protocol import BlindValidationProtocol

        for strength in [0.0, 0.3, 0.7, 1.0]:
            for certainty in [0.0, 0.5, 1.0]:
                for hit in [True, False]:
                    for timing in [True, False]:
                        s = BlindValidationProtocol._compute_score(
                            strength, certainty, hit, timing,
                        )
                        assert 0.0 <= s <= 1.0


# ══════════════════════════════════════════════════════════════════════
# 6. FrozenPredictionPacket Immutability
# ══════════════════════════════════════════════════════════════════════


class TestFrozenPredictionPacket:
    """Test FrozenPredictionPacket immutability and structure."""

    def test_packet_is_frozen(self) -> None:
        """FrozenPredictionPacket must be immutable (frozen dataclass)."""
        packet = _make_packet()
        with pytest.raises(AttributeError):
            packet.predicted_strength = 0.5  # type: ignore[misc]

    def test_packet_fields_stored(self) -> None:
        """All fields are stored correctly."""
        subject = _make_subject()
        packet = _make_packet(subject=subject, predicted_strength=0.75)
        assert packet.subject == subject
        assert packet.predicted_strength == 0.75
        assert packet.formation_strength == 0.9

    def test_packet_default_hash_empty(self) -> None:
        """Default payload_hash is empty string."""
        packet = FrozenPredictionPacket(
            subject=_make_subject(),
            target_timestamp="2024-01-01T00:00:00Z",
        )
        assert packet.payload_hash == ""

    def test_packet_subject_preserved_in_dict(self) -> None:
        """Subject data is preserved in serialization."""
        subject = _make_subject(chart_id="test_chart")
        packet = _make_packet(subject=subject)
        d = packet.to_dict()
        assert d["subject"]["chart_id"] == "test_chart"
        assert d["subject"]["latitude"] == 28.6139

    def test_packet_all_numeric_fields_bounded(self) -> None:
        """All numeric fields in packet are non-negative."""
        packet = _make_packet()
        assert packet.formation_strength >= 0.0
        assert packet.structural_relationship_score >= 0.0
        assert packet.modification_impact >= 0.0
        assert packet.varga_confirmation_score >= 0.0
        assert packet.dasha_transit_activation >= 0.0
        assert packet.predicted_strength >= 0.0


# ══════════════════════════════════════════════════════════════════════
# 7. HistoricalEvent Model
# ══════════════════════════════════════════════════════════════════════


class TestHistoricalEvent:
    """Test HistoricalEvent construction and serialization."""

    def test_event_construction(self) -> None:
        """HistoricalEvent can be constructed with required fields."""
        event = _make_event()
        assert event.event_id == "event_001"
        assert event.domain == DomainType.CAREER_PEAK

    def test_event_is_frozen(self) -> None:
        """HistoricalEvent must be immutable."""
        event = _make_event()
        with pytest.raises(AttributeError):
            event.event_certainty = 0.5  # type: ignore[misc]

    def test_event_serialization(self) -> None:
        """HistoricalEvent serializes deterministically."""
        event = _make_event(domain=DomainType.MARRIAGE, certainty=0.85)
        d = event.to_dict()
        assert d["domain"] == "MARRIAGE"
        assert d["event_certainty"] == 0.85
        assert d["chart_id"] == "subject_001"

    def test_event_all_domains(self) -> None:
        """Each DomainType value can be used in an event."""
        for domain in DomainType:
            event = _make_event(domain=domain)
            assert event.domain == domain


# ══════════════════════════════════════════════════════════════════════
# 8. BlindValidationProtocol Integration
# ══════════════════════════════════════════════════════════════════════


class TestBlindValidationProtocol:
    """Test BlindValidationProtocol end-to-end flow."""

    def test_evaluate_with_valid_packet(self) -> None:
        """evaluate_prediction_against_event with valid sealed packet."""
        from jrs.validation.protocol import BlindValidationProtocol

        protocol = BlindValidationProtocol()
        subject = _make_subject()
        # Manually compute hash
        packet = _make_packet(subject=subject, predicted_strength=0.8)
        payload_hash = protocol._compute_hash(packet)
        sealed = _make_packet(subject=subject, predicted_strength=0.8, payload_hash=payload_hash)

        event = _make_event(start_date="2024-01-01T00:00:00Z", end_date="2024-12-31T23:59:59Z")
        metric = protocol.evaluate_prediction_against_event(sealed, event)

        assert metric.hit is True
        assert metric.timing_match is True
        assert metric.score > 0.0
        assert metric.packet_hash == payload_hash

    def test_evaluate_with_tampered_hash(self) -> None:
        """evaluate_prediction_against_event detects tampered hash."""
        from jrs.validation.protocol import BlindValidationProtocol

        protocol = BlindValidationProtocol()
        subject = _make_subject()
        packet = _make_packet(subject=subject, predicted_strength=0.8)
        # Use wrong hash
        sealed = _make_packet(subject=subject, predicted_strength=0.8, payload_hash="tampered_hash")

        event = _make_event()
        metric = protocol.evaluate_prediction_against_event(sealed, event)

        assert metric.hit is False
        assert metric.score == 0.0

    def test_evaluate_outside_event_window(self) -> None:
        """Prediction outside event window -> timing_match = False."""
        from jrs.validation.protocol import BlindValidationProtocol

        protocol = BlindValidationProtocol()
        subject = _make_subject()
        packet = _make_packet(
            subject=subject,
            target_ts="2026-01-01T00:00:00Z",
            predicted_strength=0.8,
        )
        payload_hash = protocol._compute_hash(packet)
        sealed = _make_packet(
            subject=subject,
            target_ts="2026-01-01T00:00:00Z",
            predicted_strength=0.8,
            payload_hash=payload_hash,
        )

        event = _make_event(
            start_date="2024-01-01T00:00:00Z",
            end_date="2024-12-31T23:59:59Z",
        )
        metric = protocol.evaluate_prediction_against_event(sealed, event)

        assert metric.timing_match is False

    def test_evaluate_zero_strength(self) -> None:
        """Zero predicted_strength -> hit = False, score = 0.0."""
        from jrs.validation.protocol import BlindValidationProtocol

        protocol = BlindValidationProtocol()
        subject = _make_subject()
        packet = _make_packet(subject=subject, predicted_strength=0.0)
        payload_hash = protocol._compute_hash(packet)
        sealed = _make_packet(subject=subject, predicted_strength=0.0, payload_hash=payload_hash)

        event = _make_event()
        metric = protocol.evaluate_prediction_against_event(sealed, event)

        assert metric.hit is False
        assert metric.score == 0.0

    def test_evaluate_with_low_event_certainty(self) -> None:
        """Low event certainty reduces the composite score."""
        from jrs.validation.protocol import BlindValidationProtocol

        protocol = BlindValidationProtocol()
        subject = _make_subject()
        packet = _make_packet(subject=subject, predicted_strength=0.8)
        payload_hash = protocol._compute_hash(packet)
        sealed = _make_packet(subject=subject, predicted_strength=0.8, payload_hash=payload_hash)

        event_high = _make_event(certainty=1.0, start_date="2024-01-01T00:00:00Z", end_date="2024-12-31T23:59:59Z")
        event_low = _make_event(certainty=0.5, start_date="2024-01-01T00:00:00Z", end_date="2024-12-31T23:59:59Z")

        m_high = protocol.evaluate_prediction_against_event(sealed, event_high)
        m_low = protocol.evaluate_prediction_against_event(sealed, event_low)

        assert m_high.score > m_low.score

    def test_rodden_aa_packet_accepted(self) -> None:
        """Packet from AA-rated subject is accepted by protocol."""
        from jrs.validation.protocol import BlindValidationProtocol

        protocol = BlindValidationProtocol()
        subject = _make_subject(rodden=RoddenRating.AA)
        packet = _make_packet(subject=subject, predicted_strength=0.9)
        payload_hash = protocol._compute_hash(packet)
        sealed = _make_packet(subject=subject, predicted_strength=0.9, payload_hash=payload_hash)

        event = _make_event(start_date="2024-01-01T00:00:00Z", end_date="2024-12-31T23:59:59Z")
        metric = protocol.evaluate_prediction_against_event(sealed, event)

        assert metric.hit is True
        assert metric.score > 0.0

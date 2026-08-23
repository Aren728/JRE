"""Unit tests for TransitionService — deterministic transition calculation."""

from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from astronomy.models import BodyId
from jrs.transitions.errors import InvalidTransitionInputError
from jrs.transitions.models import TransitionType
from jrs.transitions.service import TransitionService
from jyotish.models import (
    EclipseClassification,
    EclipseContact,
    EclipseEvent,
    EclipseKind,
    GeographicVisibility,
    NakshatraId,
    Pada,
    RashiId,
    SearchMetadata,
    TransitEvent,
    TransitEventKind,
)
from jyotish.models import (
    RetrogradeState as JyRetrogradeState,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_dasha_period(
    start: datetime,
    end: datetime,
    mahadasha: BodyId = BodyId.SUN,
    antardasha: BodyId | None = None,
    pratyantardasha: BodyId | None = None,
) -> object:
    """Build a DashaPeriod-like object for testing."""
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class FakeDashaPeriod:
        start_utc: datetime
        end_utc: datetime
        mahadasha_lord: BodyId
        antardasha_lord: BodyId | None = None
        pratyantardasha_lord: BodyId | None = None

        @property
        def depth(self) -> int:
            if self.pratyantardasha_lord is not None:
                return 3
            if self.antardasha_lord is not None:
                return 2
            return 1

    return FakeDashaPeriod(
        start_utc=start,
        end_utc=end,
        mahadasha_lord=mahadasha,
        antardasha_lord=antardasha,
        pratyantardasha_lord=pratyantardasha,
    )


def _make_transit_event(
    body: BodyId = BodyId.SATURN,
    kind: TransitEventKind = TransitEventKind.RASHI_INGRESS,
    event_iso: str = "2025-03-01T12:00:00Z",
    boundary_deg: float | None = 0.0,
    reached: RashiId | NakshatraId | Pada | None = RashiId.MESHA,
    direction: JyRetrogradeState = JyRetrogradeState.DIRECT,
) -> TransitEvent:
    """Build a TransitEvent for testing."""
    return TransitEvent(
        body=body,
        kind=kind,
        event_julian_day_ut=2460735.0,
        event_utc_iso=event_iso,
        boundary_deg=boundary_deg,
        reached=reached,
        direction=direction,
        search_metadata=SearchMetadata(
            algorithm="bisection",
            sample_step_hours=6.0,
            tolerance_jd=1e-4,
            iterations=10,
            position_calls=20,
        ),
    )


def _make_eclipse_event(
    kind: EclipseKind = EclipseKind.SOLAR,
    classification: EclipseClassification = EclipseClassification.TOTAL,
    max_iso: str = "2025-03-29T10:00:00Z",
    magnitude: float = 1.0,
) -> EclipseEvent:
    """Build an EclipseEvent for testing."""
    return EclipseEvent(
        kind=kind,
        classification=classification,
        maximum_jd_ut=2460762.0,
        maximum_utc_iso=max_iso,
        contacts=(
            EclipseContact(phase="P1", julian_day_ut=2460761.5, utc_iso="2025-03-29T08:00:00Z"),
            EclipseContact(phase="MAX", julian_day_ut=2460762.0, utc_iso=max_iso),
            EclipseContact(phase="P4", julian_day_ut=2460762.5, utc_iso="2025-03-29T12:00:00Z"),
        ),
        magnitude=magnitude,
        node_positions=(),
        solar_lunar_positions=(),
        geographic_visibility=GeographicVisibility(
            latitude_deg=0.0, longitude_deg=0.0, description="Equatorial"
        ),
        pre_event_interval_days=1.0,
        post_event_interval_days=1.0,
        provider_id="test",
        ephemeris_version="test",
    )


# ── Initialization ───────────────────────────────────────────────────────────


class TestTransitionServiceInit:
    """Tests for TransitionService initialization."""

    def test_default_init(self) -> None:
        svc = TransitionService()
        assert svc is not None

    def test_custom_sandhi_buffer(self) -> None:
        svc = TransitionService(sandhi_buffer_days=5.0)
        assert svc is not None

    def test_invalid_sandhi_buffer(self) -> None:
        with pytest.raises(InvalidTransitionInputError, match="sandhi_buffer_days"):
            TransitionService(sandhi_buffer_days=-1.0)


# ── Dasha Boundary Tests ─────────────────────────────────────────────────────


class TestDashaBoundaryTransitions:
    """Tests for DASHA_BOUNDARY transition calculation."""

    def test_single_dasha_boundary(self) -> None:
        """One DashaPeriod produces one DASHA_BOUNDARY event."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2007, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.KETU,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        boundaries = [e for e in events if e.transition_type is TransitionType.DASHA_BOUNDARY]
        assert len(boundaries) == 1
        assert boundaries[0].exact_timestamp == "2000-01-01T00:00:00+00:00"
        assert boundaries[0].state_change.after == "KETU"

    def test_two_dasha_boundaries(self) -> None:
        """Two consecutive DashaPeriods produce two DASHA_BOUNDARY events."""
        svc = TransitionService()
        p1 = _make_dasha_period(
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2007, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.KETU,
        )
        p2 = _make_dasha_period(
            start=datetime(2007, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.VENUS,
        )
        events = svc.calculate_transitions(dasha_data=(p1, p2))
        boundaries = [e for e in events if e.transition_type is TransitionType.DASHA_BOUNDARY]
        assert len(boundaries) == 2
        # First boundary: before=KETU (from p1), after=KETU (p1 itself)
        assert boundaries[0].state_change.after == "KETU"
        # Second boundary: before=KETU (from p1), after=VENUS (p2)
        assert boundaries[1].state_change.before == "KETU"
        assert boundaries[1].state_change.after == "VENUS"

    def test_antardasha_boundary_metadata(self) -> None:
        """Antardasha period has depth=2 in metadata."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2002, 6, 1, tzinfo=UTC),
            mahadasha=BodyId.KETU,
            antardasha=BodyId.VENUS,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        boundaries = [e for e in events if e.transition_type is TransitionType.DASHA_BOUNDARY]
        assert len(boundaries) == 1
        assert boundaries[0].metadata["depth"] == "2"
        assert boundaries[0].state_change.after == "KETU-VENUS"

    def test_dasha_boundary_duration(self) -> None:
        """DASHA_BOUNDARY includes the period duration in seconds."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2001, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SUN,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        boundaries = [e for e in events if e.transition_type is TransitionType.DASHA_BOUNDARY]
        assert boundaries[0].duration_seconds is not None
        assert boundaries[0].duration_seconds == pytest.approx(365 * 86400, rel=0.01)

    def test_dasha_boundary_affected_facts(self) -> None:
        """DASHA_BOUNDARY affected_facts includes all active lords."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2002, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SATURN,
            antardasha=BodyId.MERCURY,
            pratyantardasha=BodyId.MARS,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        boundaries = [e for e in events if e.transition_type is TransitionType.DASHA_BOUNDARY]
        assert boundaries[0].affected_facts == (
            "dasha_lord", "antardasha_lord", "pratyantardasha_lord"
        )


# ── Dasha Sandhi Tests ───────────────────────────────────────────────────────


class TestDashaSandhiTransitions:
    """Tests for DASHA_SANDHI transition calculation."""

    def test_sandhi_events_produced(self) -> None:
        """Each DashaPeriod produces a DASHA_SANDHI event."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2007, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.KETU,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        sandhis = [e for e in events if e.transition_type is TransitionType.DASHA_SANDHI]
        assert len(sandhis) == 1

    def test_sandhi_window_timing(self) -> None:
        """DASHA_SANDHI timestamp is buffer_days before the boundary."""
        svc = TransitionService(sandhi_buffer_days=3.0)
        period = _make_dasha_period(
            start=datetime(2000, 1, 4, tzinfo=UTC),
            end=datetime(2007, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.KETU,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        sandhis = [e for e in events if e.transition_type is TransitionType.DASHA_SANDHI]
        assert len(sandhis) == 1
        # Sandhi starts 3 days before the boundary (Jan 4 - 3 days = Jan 1)
        assert "2000-01-01" in sandhis[0].exact_timestamp

    def test_sandhi_duration_is_double_buffer(self) -> None:
        """DASHA_SANDHI duration = 2 * buffer_days."""
        svc = TransitionService(sandhi_buffer_days=3.0)
        period = _make_dasha_period(
            start=datetime(2000, 1, 1, tzinfo=UTC),
            end=datetime(2007, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.KETU,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        sandhis = [e for e in events if e.transition_type is TransitionType.DASHA_SANDHI]
        assert sandhis[0].duration_seconds == 3.0 * 2 * 86400

    def test_sandhi_window_end_metadata(self) -> None:
        """DASHA_SANDHI metadata includes window_end timestamp."""
        svc = TransitionService(sandhi_buffer_days=3.0)
        period = _make_dasha_period(
            start=datetime(2000, 1, 4, tzinfo=UTC),
            end=datetime(2007, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.KETU,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        sandhis = [e for e in events if e.transition_type is TransitionType.DASHA_SANDHI]
        assert "sandhi_window_end" in sandhis[0].metadata


# ── Transit Event Tests ──────────────────────────────────────────────────────


class TestTransitEventTransitions:
    """Tests for transit event → transition event mapping."""

    def test_rashi_ingress(self) -> None:
        """RASHI_INGRESS transit → RASHI_INGRESS transition."""
        svc = TransitionService()
        te = _make_transit_event(
            kind=TransitEventKind.RASHI_INGRESS,
            reached=RashiId.MESHA,
        )
        events = svc.calculate_transitions(ephemeris_data=(te,))
        matches = [e for e in events if e.transition_type is TransitionType.RASHI_INGRESS]
        assert len(matches) == 1
        assert matches[0].state_change.after == "MESHA"

    def test_nakshatra_ingress(self) -> None:
        """NAKSHATRA_INGRESS transit → NAKSHATRA_INGRESS transition."""
        svc = TransitionService()
        te = _make_transit_event(
            kind=TransitEventKind.NAKSHATRA_INGRESS,
            reached=NakshatraId.ROHINI,
        )
        events = svc.calculate_transitions(ephemeris_data=(te,))
        matches = [e for e in events if e.transition_type is TransitionType.NAKSHATRA_INGRESS]
        assert len(matches) == 1
        assert matches[0].state_change.after == "ROHINI"

    def test_retrograde_station(self) -> None:
        """STATION_RETROGRADE transit → RETROGRADE_STATION transition."""
        svc = TransitionService()
        te = _make_transit_event(
            kind=TransitEventKind.STATION_RETROGRADE,
            body=BodyId.SATURN,
        )
        events = svc.calculate_transitions(ephemeris_data=(te,))
        matches = [e for e in events if e.transition_type is TransitionType.RETROGRADE_STATION]
        assert len(matches) == 1
        assert matches[0].metadata["body"] == "SATURN"

    def test_direct_station(self) -> None:
        """STATION_DIRECT transit → DIRECT_STATION transition."""
        svc = TransitionService()
        te = _make_transit_event(
            kind=TransitEventKind.STATION_DIRECT,
            body=BodyId.MARS,
        )
        events = svc.calculate_transitions(ephemeris_data=(te,))
        matches = [e for e in events if e.transition_type is TransitionType.DIRECT_STATION]
        assert len(matches) == 1
        assert matches[0].metadata["body"] == "MARS"

    def test_egress_events_ignored(self) -> None:
        """Egress events are not mapped to transition types (only ingress)."""
        svc = TransitionService()
        te = _make_transit_event(
            kind=TransitEventKind.RASHI_EGRESS,
        )
        events = svc.calculate_transitions(ephemeris_data=(te,))
        # No RASHI_EGRESS → TransitionType mapping, so no events
        assert len(events) == 0

    def test_transit_affected_facts_rashi(self) -> None:
        """RASHI_INGRESS affects rashi and degree_in_rashi."""
        svc = TransitionService()
        te = _make_transit_event(kind=TransitEventKind.RASHI_INGRESS)
        events = svc.calculate_transitions(ephemeris_data=(te,))
        matches = [e for e in events if e.transition_type is TransitionType.RASHI_INGRESS]
        assert matches[0].affected_facts == ("rashi", "degree_in_rashi")

    def test_transit_affected_facts_nakshatra(self) -> None:
        """NAKSHATRA_INGRESS affects nakshatra, pada, degree_in_nakshatra."""
        svc = TransitionService()
        te = _make_transit_event(kind=TransitEventKind.NAKSHATRA_INGRESS)
        events = svc.calculate_transitions(ephemeris_data=(te,))
        matches = [e for e in events if e.transition_type is TransitionType.NAKSHATRA_INGRESS]
        assert matches[0].affected_facts == ("nakshatra", "pada", "degree_in_nakshatra")

    def test_transit_affected_facts_station(self) -> None:
        """Station events affect retrograde and speed_longitude."""
        svc = TransitionService()
        te = _make_transit_event(kind=TransitEventKind.STATION_RETROGRADE)
        events = svc.calculate_transitions(ephemeris_data=(te,))
        matches = [e for e in events if e.transition_type is TransitionType.RETROGRADE_STATION]
        assert matches[0].affected_facts == ("retrograde", "speed_longitude")


# ── Eclipse Tests ────────────────────────────────────────────────────────────


class TestEclipseTransitions:
    """Tests for eclipse → ECLIPSE_WINDOW transition calculation."""

    def test_solar_eclipse_window(self) -> None:
        """Solar eclipse produces an ECLIPSE_WINDOW event."""
        svc = TransitionService()
        ee = _make_eclipse_event(kind=EclipseKind.SOLAR)
        events = svc.calculate_transitions(eclipse_data=(ee,))
        windows = [e for e in events if e.transition_type is TransitionType.ECLIPSE_WINDOW]
        assert len(windows) == 1
        assert windows[0].metadata["eclipse_kind"] == "SOLAR"
        assert windows[0].metadata["classification"] == "TOTAL"

    def test_lunar_eclipse_window(self) -> None:
        """Lunar eclipse produces an ECLIPSE_WINDOW event."""
        svc = TransitionService()
        ee = _make_eclipse_event(
            kind=EclipseKind.LUNAR,
            classification=EclipseClassification.PARTIAL,
            magnitude=0.5,
        )
        events = svc.calculate_transitions(eclipse_data=(ee,))
        windows = [e for e in events if e.transition_type is TransitionType.ECLIPSE_WINDOW]
        assert len(windows) == 1
        assert windows[0].metadata["eclipse_kind"] == "LUNAR"
        assert windows[0].metadata["magnitude"] == "0.5"

    def test_eclipse_state_change(self) -> None:
        """Eclipse state_change uses PRE/POST_ECLIPSE."""
        svc = TransitionService()
        ee = _make_eclipse_event(kind=EclipseKind.SOLAR)
        events = svc.calculate_transitions(eclipse_data=(ee,))
        windows = [e for e in events if e.transition_type is TransitionType.ECLIPSE_WINDOW]
        assert windows[0].state_change.before == "SOLAR_PRE_ECLIPSE"
        assert windows[0].state_change.after == "SOLAR_POST_ECLIPSE"

    def test_eclipse_duration(self) -> None:
        """Eclipse duration is sum of pre+post intervals in seconds."""
        svc = TransitionService()
        ee = _make_eclipse_event(kind=EclipseKind.SOLAR)
        events = svc.calculate_transitions(eclipse_data=(ee,))
        windows = [e for e in events if e.transition_type is TransitionType.ECLIPSE_WINDOW]
        # pre=1.0 day, post=1.0 day → 2 days = 172800 seconds
        assert windows[0].duration_seconds == pytest.approx(2 * 86400, rel=0.01)


# ── Combined Input Tests ─────────────────────────────────────────────────────


class TestCombinedInputs:
    """Tests for combined Dasha + Transit + Eclipse inputs."""

    def test_all_three_sources(self) -> None:
        """All three input sources produce events from each."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2032, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SATURN,
        )
        te = _make_transit_event(
            kind=TransitEventKind.RASHI_INGRESS,
            event_iso="2025-03-01T12:00:00Z",
        )
        ee = _make_eclipse_event(
            kind=EclipseKind.SOLAR,
            max_iso="2025-03-29T10:00:00Z",
        )
        events = svc.calculate_transitions(
            ephemeris_data=(te,),
            dasha_data=(period,),
            eclipse_data=(ee,),
        )
        types = {e.transition_type for e in events}
        assert TransitionType.DASHA_BOUNDARY in types
        assert TransitionType.DASHA_SANDHI in types
        assert TransitionType.RASHI_INGRESS in types
        assert TransitionType.ECLIPSE_WINDOW in types

    def test_sorted_by_timestamp(self) -> None:
        """Events are sorted by exact_timestamp."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2025, 6, 1, tzinfo=UTC),
            end=datetime(2032, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SATURN,
        )
        te = _make_transit_event(
            kind=TransitEventKind.RASHI_INGRESS,
            event_iso="2025-03-01T12:00:00Z",
        )
        events = svc.calculate_transitions(
            ephemeris_data=(te,),
            dasha_data=(period,),
        )
        timestamps = [e.exact_timestamp for e in events]
        assert timestamps == sorted(timestamps)

    def test_empty_inputs(self) -> None:
        """No inputs → no events."""
        svc = TransitionService()
        events = svc.calculate_transitions()
        assert events == ()

    def test_only_dasha(self) -> None:
        """Only Dasha data → Dasha events only."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2032, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SATURN,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        assert all(
            e.transition_type in (TransitionType.DASHA_BOUNDARY, TransitionType.DASHA_SANDHI)
            for e in events
        )

    def test_only_transits(self) -> None:
        """Only Transit data → Transit events only."""
        svc = TransitionService()
        te = _make_transit_event(kind=TransitEventKind.RASHI_INGRESS)
        events = svc.calculate_transitions(ephemeris_data=(te,))
        assert all(e.transition_type is TransitionType.RASHI_INGRESS for e in events)

    def test_deterministic_output(self) -> None:
        """Same inputs produce identical deterministic_ids."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2032, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SATURN,
        )
        r1 = svc.calculate_transitions(dasha_data=(period,))
        r2 = svc.calculate_transitions(dasha_data=(period,))
        ids1 = [e.deterministic_id for e in r1]
        ids2 = [e.deterministic_id for e in r2]
        assert ids1 == ids2


# ── Edge Cases ───────────────────────────────────────────────────────────────


class TestEdgeCases:
    """Edge case tests."""

    def test_invalid_dasha_data_not_tuple(self) -> None:
        svc = TransitionService()
        with pytest.raises(InvalidTransitionInputError, match="dasha_data"):
            svc.calculate_transitions(dasha_data=[_make_dasha_period(
                start=datetime(2025, 1, 1, tzinfo=UTC),
                end=datetime(2032, 1, 1, tzinfo=UTC),
            )])  # type: ignore[arg-type]

    def test_invalid_ephemeris_data_not_tuple(self) -> None:
        svc = TransitionService()
        with pytest.raises(InvalidTransitionInputError, match="ephemeris_data"):
            svc.calculate_transitions(ephemeris_data=[_make_transit_event()])  # type: ignore[arg-type]

    def test_invalid_eclipse_data_not_tuple(self) -> None:
        svc = TransitionService()
        with pytest.raises(InvalidTransitionInputError, match="eclipse_data"):
            svc.calculate_transitions(eclipse_data=[_make_eclipse_event()])  # type: ignore[arg-type]

    def test_to_dict_roundtrip(self) -> None:
        """Events serialize to valid JSON."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2032, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SATURN,
        )
        events = svc.calculate_transitions(dasha_data=(period,))
        for event in events:
            d = event.to_dict()
            json_str = json.dumps(d, sort_keys=True)
            assert len(json_str) > 0

    def test_provenance_populated(self) -> None:
        """All events have provenance set."""
        svc = TransitionService()
        period = _make_dasha_period(
            start=datetime(2025, 1, 1, tzinfo=UTC),
            end=datetime(2032, 1, 1, tzinfo=UTC),
            mahadasha=BodyId.SATURN,
        )
        te = _make_transit_event(kind=TransitEventKind.RASHI_INGRESS)
        events = svc.calculate_transitions(
            ephemeris_data=(te,),
            dasha_data=(period,),
        )
        for event in events:
            assert event.provenance != ""

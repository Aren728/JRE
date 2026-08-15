"""Shared builders for JRE-006 unit tests.

Synthetic charts/transits/events are constructed via the public
``jyotish``/``bhava`` APIs only (mirroring the JRE-005 unit conftest), so
derivation logic is testable without an ephemeris. A small
``FakeJyotishService`` substitutes for the real facade so the gochar
composition paths can be exercised deterministically.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from tests.unit.bhava.conftest import (
    make_planet_state,
    make_transit,
    make_whole_sign_chart,
)

from jyotish import (
    BodyId,
    JyotishConfig,
    PlanetState,
    RetrogradeState,
    SearchMetadata,
    TransitEvent,
    TransitEventKind,
    TransitReferencePoint,
)

ALL_BODIES: tuple[BodyId, ...] = tuple(BodyId)


def make_event(
    body: BodyId = BodyId.SUN,
    kind: TransitEventKind = TransitEventKind.RASHI_INGRESS,
    event_julian_day_ut: float = 2460462.0,
    event_utc_iso: str = "2024-06-15T00:00:00.000000Z",
    boundary_deg: float | None = 0.0,
    reached=None,
    direction: RetrogradeState = RetrogradeState.DIRECT,
) -> TransitEvent:
    """Build one synthetic ``TransitEvent`` (public API, JRE-003 type)."""
    return TransitEvent(
        body=body,
        kind=kind,
        event_julian_day_ut=event_julian_day_ut,
        event_utc_iso=event_utc_iso,
        boundary_deg=boundary_deg,
        reached=reached,
        direction=direction,
        search_metadata=SearchMetadata(
            algorithm="fake.linear",
            sample_step_hours=6.0,
            tolerance_jd=1e-4,
            iterations=3,
            position_calls=4,
        ),
    )


class FakeJyotishService:
    """Deterministic stand-in for ``JyotishService`` (public API only).

    ``planetary_state`` returns synthetic canonical states for the
    requested bodies; ``chart`` returns a whole-sign synthetic chart;
    ``transit_through_houses`` builds entries against that chart;
    ``events_between`` returns a configurable synthetic stream; and
    ``state_series`` returns one state per requested body per sample JD.
    """

    def __init__(
        self,
        events: tuple[TransitEvent, ...] = (),
        sample_step_days: float = 1.0,
        chart=None,
    ) -> None:
        self._events = events
        self._sample_step_days = sample_step_days
        self._chart = chart if chart is not None else make_whole_sign_chart()
        self.calls: list[str] = []

    def planetary_state(self, date, time, timezone, latitude, longitude, bodies=None, config=None):
        self.calls.append("planetary_state")
        requested = bodies or ALL_BODIES
        base = {
            BodyId.SUN: 5.0,
            BodyId.MOON: 35.0,
            BodyId.MARS: 65.0,
            BodyId.MERCURY: 95.0,
            BodyId.JUPITER: 125.0,
            BodyId.VENUS: 155.0,
            BodyId.SATURN: 185.0,
            BodyId.RAHU: 215.0,
            BodyId.KETU: 245.0,
        }
        return tuple(
            make_planet_state(body, base[body])
            for body in ALL_BODIES
            if body in requested
        )

    def chart(self, birth, config=None):
        self.calls.append("chart")
        return self._chart

    def transit_through_houses(
        self, birth, transit_date, transit_time, transit_timezone,
        reference=TransitReferencePoint.LAGNA, config=None,
    ):
        self.calls.append("transit_through_houses")
        transiting = [(body, 60.0 + idx * 30.0) for idx, body in enumerate(ALL_BODIES)]
        transit = make_transit(self._chart, transiting)
        return replace(
            transit,
            reference=reference,
            config=config if config is not None else JyotishConfig(),
        )

    def events_between(self, start_utc_iso, end_utc_iso, bodies, kinds=None, config=None):
        self.calls.append("events_between")
        return self._events

    def state_series(self, start_utc_iso, end_utc_iso, step_days, bodies, config=None):
        self.calls.append("state_series")
        import jyotish

        start_jd = jyotish.iso_utc_to_jd(start_utc_iso)
        end_jd = jyotish.iso_utc_to_jd(end_utc_iso)
        n = max(1, int((end_jd - start_jd) / step_days) + 1)
        samples: list[PlanetState] = []
        for i in range(n):
            jd = min(start_jd + i * step_days, end_jd)
            for body in ALL_BODIES:
                if body in bodies:
                    samples.append(
                        replace(
                            make_planet_state(body, 5.0 + (jd % 30.0)),
                            julian_day_ut=jd,
                            timestamp_utc_iso=jyotish.jd_to_iso_utc(jd),
                        )
                    )
        return tuple(samples)


@pytest.fixture
def fake_service() -> FakeJyotishService:
    return FakeJyotishService()

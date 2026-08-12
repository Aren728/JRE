"""QA requirement 12: retrograde/direct determination.

Windows verified empirically against the pinned ephemeris during QA:
- Mars retrograde 2018-07-15 (window Jun 26 - Aug 27 2018)
- Mercury retrograde 2019-03-15 (window Mar 5 - 28 2019)
- Jupiter retrograde 2023-11-01 (window Sep - Dec 2023)
- Saturn retrograde 1990-08-15 (window Jun 6 - Oct 24 1990)
Station dates (speed sign changes) are scanned around known stations.
"""

from __future__ import annotations

import datetime as dt

import pytest
from tests.integration.astronomy.conftest import make_request

from astronomy.models import BodyId, CalculationConfig, EphemerisMode, RetrogradeState

RETRO_WINDOWS = [
    (BodyId.MARS, dt.date(2018, 7, 15)),
    (BodyId.MERCURY, dt.date(2019, 3, 15)),
    (BodyId.JUPITER, dt.date(2023, 11, 1)),
    (BodyId.SATURN, dt.date(1990, 8, 15)),
]

DIRECT_WINDOWS = [
    (BodyId.MARS, dt.date(2020, 11, 15)),
    (BodyId.MERCURY, dt.date(2019, 5, 15)),
    (BodyId.JUPITER, dt.date(2024, 2, 1)),
    (BodyId.SATURN, dt.date(1990, 12, 15)),
]


@pytest.mark.parametrize("body,date", RETRO_WINDOWS)
def test_known_retrograde_windows(service, body, date):
    result = service.compute(make_request(date=date, timezone="UTC"))
    pos = next(p for p in result.positions if p.body is body)
    assert pos.retrograde is RetrogradeState.RETROGRADE, (
        f"{body.value} on {date}: speed={pos.speed_longitude}"
    )
    assert pos.speed_longitude < 0.0


@pytest.mark.parametrize("body,date", DIRECT_WINDOWS)
def test_known_direct_windows(service, body, date):
    result = service.compute(make_request(date=date, timezone="UTC"))
    pos = next(p for p in result.positions if p.body is body)
    assert pos.retrograde is RetrogradeState.DIRECT, (
        f"{body.value} on {date}: speed={pos.speed_longitude}"
    )
    assert pos.speed_longitude > 0.0


def test_retrograde_state_consistent_with_speed_sign(service):
    result = service.compute(make_request())
    for pos in result.positions:
        if pos.retrograde is RetrogradeState.RETROGRADE:
            assert pos.speed_longitude < 0.0
        elif pos.retrograde is RetrogradeState.DIRECT:
            assert pos.speed_longitude > 0.0


def test_speed_sign_flips_across_known_station(service):
    """Mercury station ~2019-03-06 (retrograde->direct reversal window)."""
    before = service.compute(
        make_request(date=dt.date(2019, 3, 5), timezone="UTC")
    )
    after = service.compute(
        make_request(date=dt.date(2019, 3, 7), timezone="UTC")
    )
    b = next(p for p in before.positions if p.body is BodyId.MERCURY)
    a = next(p for p in after.positions if p.body is BodyId.MERCURY)
    # One side is retrograde and the other direct around a station.
    assert b.retrograde is not a.retrograde


def test_stationary_requires_near_zero_speed(service):
    """STATIONARY is only reachable when |speed| is below the epsilon."""
    result = service.compute(make_request())
    for pos in result.positions:
        if pos.retrograde is RetrogradeState.STATIONARY:
            assert abs(pos.speed_longitude) < 1e-9


def test_retrograde_classification_consistent_in_moseph(service):
    config = CalculationConfig(ephemeris_mode=EphemerisMode.MOSEPH)
    result = service.compute(
        make_request(date=dt.date(2018, 7, 15), timezone="UTC", config=config)
    )
    mars = next(p for p in result.positions if p.body is BodyId.MARS)
    assert mars.retrograde is RetrogradeState.RETROGRADE

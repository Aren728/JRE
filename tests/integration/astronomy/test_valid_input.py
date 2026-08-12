"""QA requirement 4/9: valid datetime/location input; all nine bodies correct.

Asserts the full output envelope: canonical ordering, finite floats, angular
and distance ranges, enum echoes of the configuration.
"""

from __future__ import annotations

import math

from tests.integration.astronomy.conftest import make_request

from astronomy.models import (
    CANONICAL_BODIES,
    BodyId,
    PositionType,
    RetrogradeState,
)


def test_valid_request_returns_nine_bodies_in_canonical_order(service):
    result = service.compute(make_request())
    assert [p.body for p in result.positions] == list(CANONICAL_BODIES)
    assert len(result.positions) == 9


def test_all_floats_finite(service):
    result = service.compute(make_request())
    for pos in result.positions:
        for value in (
            pos.longitude_tropical,
            pos.latitude,
            pos.distance_au,
            pos.speed_longitude,
            pos.speed_latitude,
            pos.speed_distance,
        ):
            assert math.isfinite(value), f"{pos.body.value} has non-finite {value!r}"


def test_longitude_and_latitude_ranges(service):
    result = service.compute(make_request())
    for pos in result.positions:
        assert 0.0 <= pos.longitude_tropical < 360.0
        assert -90.0 <= pos.latitude <= 90.0
        assert pos.distance_au > 0.0


def test_position_type_echoes_config(service):
    result = service.compute(make_request())
    assert all(p.position_type is PositionType.APPARENT for p in result.positions)

    from astronomy.models import CalculationConfig

    true_result = service.compute(
        make_request(config=CalculationConfig(position_type=PositionType.TRUE))
    )
    assert all(p.position_type is PositionType.TRUE for p in true_result.positions)
    # True vs apparent longitudes differ only slightly (light-time etc.).
    for app, tru in zip(result.positions, true_result.positions, strict=True):
        delta = abs(app.longitude_tropical - tru.longitude_tropical) % 360.0
        assert delta < 0.5, f"{app.body.value} apparent/true differ too much: {delta}"


def test_retrograde_state_is_enum(service):
    result = service.compute(make_request())
    for pos in result.positions:
        assert isinstance(pos.retrograde, RetrogradeState)


def test_sun_and_moon_plausible_values(service):
    """Known approximate values: Sun ~1 AU, Moon ~0.0025 AU (geocentric)."""
    result = service.compute(make_request())
    sun = next(p for p in result.positions if p.body is BodyId.SUN)
    moon = next(p for p in result.positions if p.body is BodyId.MOON)
    assert 0.98 < sun.distance_au < 1.02
    assert 0.0024 < moon.distance_au < 0.0028
    assert sun.speed_longitude > 0.5  # Sun ~0.98 deg/day


def test_subset_request_returns_only_requested_bodies(service):
    result = service.compute(
        make_request(bodies=(BodyId.MARS, BodyId.VENUS, BodyId.SUN))
    )
    assert [p.body for p in result.positions] == [BodyId.SUN, BodyId.MARS, BodyId.VENUS]


def test_julian_day_and_timestamps_are_consistent(service):
    result = service.compute(make_request())
    assert result.timestamp_utc_iso == "1990-06-15T04:30:00Z"
    assert result.timestamp_local_iso == "1990-06-15T10:00:00+05:30"
    assert result.julian_day_ut == 2448057.6875

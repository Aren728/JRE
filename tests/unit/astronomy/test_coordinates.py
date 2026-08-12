"""Unit tests for geographic coordinate validation and longitude normalization."""

import math

import pytest

from astronomy.coordinates import normalize_longitude, validate_coordinates
from astronomy.errors import InvalidCoordinatesError


@pytest.mark.parametrize(
    "lat,lon",
    [
        (0.0, 0.0),
        (90.0, 180.0),
        (-90.0, -180.0),
        (28.6139, 77.2090),
        (0.0, -0.0),
    ],
)
def test_valid_coordinates(lat, lon):
    validate_coordinates(lat, lon)  # must not raise


@pytest.mark.parametrize(
    "lat,lon",
    [
        (91.0, 0.0),
        (-90.1, 0.0),
        (0.0, 181.0),
        (0.0, -180.5),
        (math.nan, 0.0),
        (0.0, math.nan),
        (math.inf, 0.0),
        (0.0, -math.inf),
    ],
)
def test_invalid_coordinates(lat, lon):
    with pytest.raises(InvalidCoordinatesError):
        validate_coordinates(lat, lon)


def test_error_message_contains_offending_value():
    with pytest.raises(InvalidCoordinatesError) as excinfo:
        validate_coordinates(91.0, 0.0)
    assert "91.0" in str(excinfo.value)


def test_normalize_longitude():
    assert normalize_longitude(0.0) == 0.0
    assert normalize_longitude(-0.0) == 0.0
    assert normalize_longitude(360.0) == 0.0
    assert normalize_longitude(-360.0) == 0.0
    assert normalize_longitude(280.5) == 280.5
    assert normalize_longitude(725.0) == pytest.approx(5.0)
    assert normalize_longitude(-5.0) == pytest.approx(355.0)
    assert normalize_longitude(359.999999) == pytest.approx(359.999999)

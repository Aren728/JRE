"""Geographic coordinate validation and angular normalization (pure functions).

All functions are deterministic and have no I/O or provider coupling.
"""

from __future__ import annotations

import math

from .errors import InvalidCoordinatesError

LATITUDE_MIN: float = -90.0
LATITUDE_MAX: float = 90.0
LONGITUDE_MIN: float = -180.0
LONGITUDE_MAX: float = 180.0


def validate_coordinates(latitude: float, longitude: float) -> None:
    """Validate latitude/longitude (degrees, geodetic). Raises on violation."""
    if not math.isfinite(latitude) or not (LATITUDE_MIN <= latitude <= LATITUDE_MAX):
        raise InvalidCoordinatesError(f"latitude must be in [-90, 90] degrees, got {latitude!r}")
    if not math.isfinite(longitude) or not (LONGITUDE_MIN <= longitude <= LONGITUDE_MAX):
        msg = f"longitude must be in [-180, 180] degrees, got {longitude!r}"
        raise InvalidCoordinatesError(msg)


def normalize_longitude(degrees: float) -> float:
    """Normalize to ``[0, 360)``; ``-0.0`` becomes ``0.0``."""
    if degrees == 0.0:
        return 0.0
    result = math.fmod(degrees, 360.0)
    if result < 0.0:
        result += 360.0
    return 0.0 if result == 360.0 else result

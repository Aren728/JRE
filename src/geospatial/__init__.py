"""Geospatial coordinate transforms and declination math.

Pure-python (stdlib only) geodesy:

- ``coordinates`` — WGS-84 geodetic <-> ECEF, ENU frames, topocentric look angles
- ``declination`` — ecliptic <-> equatorial declination, horizon declination

No ephemeris dependency: everything is exact analytic spherical/geodetic
arithmetic, fully unit-testable without pysweph (mirrors the JRE-011
synthetic-state test strategy).
"""

from __future__ import annotations

from .coordinates import (
    ECEFVector,
    GeodeticPosition,
    ecef_to_geodetic,
    enu_basis,
    enu_from_ecef,
    geodetic_to_ecef,
    look_angles,
    wgs84_params,
)
from .declination import (
    DEFAULT_OBLIQUITY_DEG,
    declination_from_ecliptic,
    ecliptic_longitude_crossing,
    horizon_declination,
    max_visible_declination,
    right_ascension_from_ecliptic,
    solar_declination,
)

__all__ = [
    "DEFAULT_OBLIQUITY_DEG",
    "ECEFVector",
    "GeodeticPosition",
    "declination_from_ecliptic",
    "ecliptic_longitude_crossing",
    "ecef_to_geodetic",
    "enu_basis",
    "enu_from_ecef",
    "geodetic_to_ecef",
    "horizon_declination",
    "look_angles",
    "max_visible_declination",
    "right_ascension_from_ecliptic",
    "solar_declination",
    "wgs84_params",
]

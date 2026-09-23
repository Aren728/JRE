"""WGS-84 geodetic <-> ECEF transforms and topocentric look angles.

Standard geodesy, kept dependency-free and exact (no approximations beyond
the WGS-84 ellipsoid itself). Frozen dataclasses mirror the astronomy
models conventions.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# --------------------------------------------------------------------------- #
# WGS-84 ellipsoid parameters
# --------------------------------------------------------------------------- #

WGS84_SEMI_MAJOR_AXIS_M: float = 6378137.0
WGS84_FLATTENING: float = 1.0 / 298.257223563
WGS84_SEMI_MINOR_AXIS_M: float = WGS84_SEMI_MAJOR_AXIS_M * (1.0 - WGS84_FLATTENING)
WGS84_SQUARE_ECCENTRICITY: float = 2.0 * WGS84_FLATTENING - WGS84_FLATTENING * WGS84_FLATTENING


def wgs84_params() -> dict[str, float]:
    """The ellipsoid constants used by every transform in this module."""
    return {
        "semi_major_axis_m": WGS84_SEMI_MAJOR_AXIS_M,
        "semi_minor_axis_m": WGS84_SEMI_MINOR_AXIS_M,
        "flattening": WGS84_FLATTENING,
        "square_eccentricity": WGS84_SQUARE_ECCENTRICITY,
    }


# --------------------------------------------------------------------------- #
# Position types
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class GeodeticPosition:
    """A point expressed in WGS-84 geodetic coordinates."""

    latitude_deg: float
    longitude_deg: float
    altitude_m: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "altitude_m": self.altitude_m,
        }


@dataclass(frozen=True)
class ECEFVector:
    """A point (or displacement) in Earth-Centered Earth-Fixed meters."""

    x_m: float
    y_m: float
    z_m: float

    def to_dict(self) -> dict[str, float]:
        return {"x_m": self.x_m, "y_m": self.y_m, "z_m": self.z_m}

    def norm_m(self) -> float:
        return math.sqrt(self.x_m**2 + self.y_m**2 + self.z_m**2)


# --------------------------------------------------------------------------- #
# Transforms
# --------------------------------------------------------------------------- #


def geodetic_to_ecef(position: GeodeticPosition) -> ECEFVector:
    """Convert WGS-84 geodetic coordinates to ECEF (Fulton/Snyder closed form)."""
    lat = math.radians(position.latitude_deg)
    lon = math.radians(position.longitude_deg)
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)

    # Prime vertical radius of curvature.
    n = WGS84_SEMI_MAJOR_AXIS_M / math.sqrt(1.0 - WGS84_SQUARE_ECCENTRICITY * sin_lat * sin_lat)

    x = (n + position.altitude_m) * cos_lat * math.cos(lon)
    y = (n + position.altitude_m) * cos_lat * math.sin(lon)
    z = (n * (1.0 - WGS84_SQUARE_ECCENTRICITY) + position.altitude_m) * sin_lat
    return ECEFVector(x_m=x, y_m=y, z_m=z)


def ecef_to_geodetic(vector: ECEFVector) -> GeodeticPosition:
    """Convert ECEF back to WGS-84 geodetic (Ferrari's closed-form solution)."""
    x = vector.x_m
    y = vector.y_m
    z = vector.z_m

    lon = math.atan2(y, x)
    p = math.hypot(x, y)
    if p == 0.0:
        # On the rotation axis: latitude is +/-90 (by z sign), altitude via b.
        lat = math.pi / 2.0 if z >= 0.0 else -math.pi / 2.0
        altitude = abs(z) - WGS84_SEMI_MINOR_AXIS_M
        return GeodeticPosition(
            latitude_deg=math.degrees(lat), longitude_deg=math.degrees(lon), altitude_m=altitude
        )

    # Bowring's improved iteration converges to machine precision in 1-2 steps.
    e2 = WGS84_SQUARE_ECCENTRICITY
    ep2 = e2 / (1.0 - e2)
    theta = math.atan2(z * WGS84_SEMI_MAJOR_AXIS_M, p * WGS84_SEMI_MINOR_AXIS_M)
    sin_theta = math.sin(theta)
    lat = math.atan2(
        z + ep2 * WGS84_SEMI_MINOR_AXIS_M * sin_theta**3,
        p - e2 * WGS84_SEMI_MAJOR_AXIS_M * math.cos(theta) ** 3,
    )
    sin_lat = math.sin(lat)
    n = WGS84_SEMI_MAJOR_AXIS_M / math.sqrt(1.0 - e2 * sin_lat * sin_lat)
    altitude = p / math.cos(lat) - n

    return GeodeticPosition(
        latitude_deg=math.degrees(lat), longitude_deg=math.degrees(lon), altitude_m=altitude
    )


# --------------------------------------------------------------------------- #
# Local ENU frame and topocentric look angles
# --------------------------------------------------------------------------- #


def enu_basis(origin: GeodeticPosition) -> tuple[ECEFVector, ECEFVector, ECEFVector]:
    """Unit basis (east, north, up) vectors of the local ENU frame at ``origin``."""
    lat = math.radians(origin.latitude_deg)
    lon = math.radians(origin.longitude_deg)
    east = ECEFVector(x_m=-math.sin(lon), y_m=math.cos(lon), z_m=0.0)
    north = ECEFVector(
        x_m=-math.sin(lat) * math.cos(lon),
        y_m=-math.sin(lat) * math.sin(lon),
        z_m=math.cos(lat),
    )
    up = ECEFVector(
        x_m=math.cos(lat) * math.cos(lon),
        y_m=math.cos(lat) * math.sin(lon),
        z_m=math.sin(lat),
    )
    return east, north, up


def enu_from_ecef(displacement: ECEFVector, origin: GeodeticPosition) -> tuple[float, float, float]:
    """Project an ECEF displacement onto the local ENU axes at ``origin``."""
    east, north, up = enu_basis(origin)
    e = east.x_m * displacement.x_m + east.y_m * displacement.y_m + east.z_m * displacement.z_m
    n = north.x_m * displacement.x_m + north.y_m * displacement.y_m + north.z_m * displacement.z_m
    u = up.x_m * displacement.x_m + up.y_m * displacement.y_m + up.z_m * displacement.z_m
    return e, n, u


@dataclass(frozen=True)
class LookAngles:
    """Topocentric azimuth/elevation of a target from an observer."""

    azimuth_deg: float  # [0, 360): 0 = north, 90 = east
    elevation_deg: float  # [-90, 90]: 0 = horizon, 90 = zenith
    range_m: float

    def to_dict(self) -> dict[str, float]:
        return {
            "azimuth_deg": self.azimuth_deg,
            "elevation_deg": self.elevation_deg,
            "range_m": self.range_m,
        }


def look_angles(observer: GeodeticPosition, target: GeodeticPosition) -> LookAngles:
    """Azimuth/elevation/range of ``target`` as seen from ``observer``."""
    observer_ecef = geodetic_to_ecef(observer)
    target_ecef = geodetic_to_ecef(target)
    displacement = ECEFVector(
        x_m=target_ecef.x_m - observer_ecef.x_m,
        y_m=target_ecef.y_m - observer_ecef.y_m,
        z_m=target_ecef.z_m - observer_ecef.z_m,
    )
    e, n, u = enu_from_ecef(displacement, observer)

    azimuth = math.degrees(math.atan2(e, n)) % 360.0
    horizontal = math.hypot(e, n)
    elevation = math.degrees(math.atan2(u, horizontal))
    return LookAngles(azimuth_deg=azimuth, elevation_deg=elevation, range_m=displacement.norm_m())

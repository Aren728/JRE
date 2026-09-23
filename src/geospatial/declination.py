"""Declination math: ecliptic <-> equatorial conversion and horizon visibility.

Pure spherical astronomy, independent of any ephemeris:

- ``declination_from_ecliptic`` — the exact spherical identity linking a body's
  ecliptic longitude/latitude to its equatorial declination (obliquity model).
- ``solar_declination`` — declination from the solar ecliptic longitude.
- ``horizon_declination`` / ``max_visible_declination`` — which declinations
  ever rise above the horizon at a given latitude (circumpolar / never-rising
  regimes), the classical kranti (declination) notion used by Ayana Bala.

All functions are exact trigonometry with no side effects, so tests can pin
them to closed-form expectations without an ephemeris.
"""

from __future__ import annotations

import math

#: Mean obliquity of the ecliptic (J2000, degrees). Callers needing epoch-
#: precise values (Laskar/IAU polynomials) can pass ``obliquity_deg`` explicitly.
DEFAULT_OBLIQUITY_DEG: float = 23.4392911


def declination_from_ecliptic(
    ecliptic_longitude_deg: float,
    ecliptic_latitude_deg: float = 0.0,
    obliquity_deg: float = DEFAULT_OBLIQUITY_DEG,
) -> float:
    """Equatorial declination (deg, [-90, 90]) of a point on/ near the ecliptic.

    Exact spherical identity::

        sin(delta) = sin(beta)·cos(eps) + cos(beta)·sin(eps)·sin(lambda)

    with ``lambda`` ecliptic longitude, ``beta`` ecliptic latitude and ``eps``
    the obliquity. Longitudes wrap modulo 360; inputs need no pre-normalization.
    """
    lam = math.radians(ecliptic_longitude_deg)
    beta = math.radians(ecliptic_latitude_deg)
    eps = math.radians(obliquity_deg)

    sin_delta = math.sin(beta) * math.cos(eps) + math.cos(beta) * math.sin(eps) * math.sin(lam)
    sin_delta = min(1.0, max(-1.0, sin_delta))
    return math.degrees(math.asin(sin_delta))


def right_ascension_from_ecliptic(
    ecliptic_longitude_deg: float,
    ecliptic_latitude_deg: float = 0.0,
    obliquity_deg: float = DEFAULT_OBLIQUITY_DEG,
) -> float:
    """Equatorial right ascension (deg, [0, 360)) for the same ecliptic point."""

    lam = math.radians(ecliptic_longitude_deg)
    beta = math.radians(ecliptic_latitude_deg)
    eps = math.radians(obliquity_deg)

    y = math.sin(lam) * math.cos(eps) - math.tan(beta) * math.sin(eps)
    x = math.cos(lam)
    return math.degrees(math.atan2(y, x)) % 360.0


def solar_declination(
    solar_ecliptic_longitude_deg: float, obliquity_deg: float = DEFAULT_OBLIQUITY_DEG
) -> float:
    """Sun's declination (deg) for its ecliptic longitude (solar latitude is 0)."""
    return declination_from_ecliptic(solar_ecliptic_longitude_deg, 0.0, obliquity_deg)


def ecliptic_longitude_crossing(
    target_declination_deg: float, obliquity_deg: float = DEFAULT_OBLIQUITY_DEG
) -> float:
    """First ascending ecliptic longitude (deg, [0, 360)) reaching a declination.

    Inverse of ``declination_from_ecliptic`` on the ascending branch: the
    returned longitude satisfies ``declination_from_ecliptic(lon) == target``.
    Raises ``ValueError`` for declinations the ecliptic never reaches
    (|target| > obliquity), which is the classical tropical limit (kranti).
    """
    sin_eps = math.sin(math.radians(obliquity_deg))
    if abs(target_declination_deg) > obliquity_deg:
        raise ValueError(
            f"declination {target_declination_deg} deg unreachable on the ecliptic "
            f"(tropical limit +/-{obliquity_deg} deg)"
        )
    sin_lambda = min(1.0, max(-1.0, math.sin(math.radians(target_declination_deg)) / sin_eps))
    return math.degrees(math.asin(sin_lambda)) % 360.0


def horizon_declination(latitude_deg: float, refraction_deg: float = 0.0) -> float:
    """Circumpolar threshold magnitude at ``latitude_deg`` (the kranti limit).

    Returns ``T = 90 - |latitude|`` (reduced by ``refraction_deg``): bodies
    with ``|declination| > T`` are circumpolar (never set, on the observer's
    hemisphere side) or never rise (opposite side); bodies with
    ``|declination| < T`` rise and set daily. T is 90 at the equator (no
    declination is circumpolar) and 0 at the poles (every nonzero
    declination is circumpolar or never rises). Hemisphere semantics belong
    to the caller — the magnitude is hemispherically symmetric.
    """
    if not -90.0 <= latitude_deg <= 90.0:
        raise ValueError(f"latitude {latitude_deg} out of range [-90, 90]")
    magnitude = 90.0 - abs(latitude_deg) - refraction_deg
    return min(90.0, max(0.0, magnitude))


def max_visible_declination(latitude_deg: float, refraction_deg: float = 0.0) -> float:
    """Largest |declination| that can still rise above the horizon at a latitude.

    Identical to ``horizon_declination`` (kept as a named counterpart for
    readability at call sites asking the visibility question).
    """
    return horizon_declination(latitude_deg, refraction_deg)

"""Degrees -> DMS conversion with the explicit rounding policy (Specialist §8).

DMS is presentational only — calculations never use it. Rounding is
round-half-even (Python's ``round``) at ``coordinate_precision`` decimal
seconds, with rollover of seconds -> minutes -> degrees at 60.
"""

from __future__ import annotations

from .models import DmsValue


def from_degrees(value_deg: float, precision: int) -> DmsValue:
    """Convert a signed longitude/latitude in degrees to a ``DmsValue``.

    ``precision`` is the number of decimal places kept in the seconds field
    (0–3; validated by the config layer). Negative values keep a ``sign`` of
    -1; the absolute magnitude is decomposed.
    """
    sign = -1 if value_deg < 0 else 1
    abs_value = abs(value_deg)

    total_seconds = abs_value * 3600.0
    degrees = int(total_seconds // 3600)
    remainder = total_seconds - degrees * 3600.0
    minutes = int(remainder // 60)
    seconds = remainder - minutes * 60.0

    # Round-half-even at the requested precision, then roll over at 60.
    seconds = round(seconds, precision)
    if seconds >= 60.0:
        seconds = 0.0
        minutes += 1
    if minutes >= 60:
        minutes = 0
        degrees += 1

    # Keep degrees in [0, 360) for longitudes (360° -> 0°).
    degrees %= 360
    return DmsValue(degrees=degrees, minutes=minutes, seconds=seconds, sign=sign)

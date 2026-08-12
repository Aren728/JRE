"""Time handling for the astronomical core: local -> UTC, fold policy, pure JD.

Design (Specialist spec v0.3.0 §7–§9):

- IANA timezone names only. Abbreviations (``"IST"``, ``"PST"`` ...) and
  unknown names raise ``InvalidTimestampError``.
- Ambiguous local times (DST fall-back) resolve with ``fold=0`` (first
  occurrence). Nonexistent local times (DST spring-forward gap) raise
  ``InvalidTimestampError``.
- The Julian Day is computed by a pure, provider-independent proleptic
  Gregorian algorithm (Fliegel–Van Flandern form of the standard Gregorian
  JDN, equivalent to Meeus *Astronomical Algorithms* ch. 7). It is verified
  bit-exact against ``swe.julday(..., GREG_CAL)`` across 1583–3000 AD in the
  integration tests (deviation 0.0 days) and within ~4e-6 days of
  ``swe.utc_to_jd``'s UT output (the residual is the UT1-vs-UTC offset, not
  an error). QA found and fixed the earlier variant of this formula, which
  silently deviated by 1–3 days for accepted dates before 1900 and by up to
  +7 days by 3000 AD.
- Accepted civil dates are >= 1582-10-15 (proleptic Gregorian); earlier
  Julian-era dates are rejected to avoid an ~11-day calendar ambiguity.
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .errors import InvalidTimestampError

#: Proleptic-Gregorian support starts at the Gregorian calendar reform.
MIN_GREGORIAN_DATE: dt.date = dt.date(1582, 10, 15)

#: Single-word IANA names that are unambiguous enough to accept.
_ACCEPTED_SINGLE_WORD_ZONES = frozenset({"UTC", "GMT"})

UTC = dt.UTC


def _resolve_zone(timezone: str) -> ZoneInfo:
    """Resolve an IANA zone name, rejecting abbreviations and unknown names."""
    if "/" not in timezone and timezone not in _ACCEPTED_SINGLE_WORD_ZONES:
        raise InvalidTimestampError(
            f"timezone must be an IANA zone name (e.g. 'Asia/Kolkata'), got {timezone!r}"
        )
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        raise InvalidTimestampError(f"unknown IANA timezone {timezone!r}") from None


def validate_civil_date(date: dt.date) -> None:
    if date < MIN_GREGORIAN_DATE:
        raise InvalidTimestampError(
            "dates before 1582-10-15 (Julian calendar era) are not supported; "
            f"got {date.isoformat()}"
        )


def local_time_to_utc(date: dt.date, time: dt.time, timezone: str) -> tuple[dt.datetime, str, str]:
    """Convert local civil (date, time, IANA zone) to an exact UTC instant.

    Returns ``(utc_datetime, local_iso, utc_iso)``. Raises
    ``InvalidTimestampError`` for unsupported zones, nonexistent local times,
    or out-of-range civil dates.
    """
    validate_civil_date(date)
    zone = _resolve_zone(timezone)
    naive = dt.datetime(
        date.year, date.month, date.day,
        time.hour, time.minute, time.second, time.microsecond,
    )
    local = naive.replace(tzinfo=zone, fold=0)
    utc_dt = local.astimezone(UTC)

    # Nonexistent local time detection: converting back must reproduce the
    # exact wall-clock fields (fold=0 interpretation).
    back = utc_dt.astimezone(zone).replace(fold=0)

    def _wall_clock(d: dt.datetime) -> tuple[int, int, int, int, int, int, int]:
        return (d.year, d.month, d.day, d.hour, d.minute, d.second, d.microsecond)

    if _wall_clock(back) != _wall_clock(naive):
        raise InvalidTimestampError(
            f"local time {naive.isoformat(sep=' ')} does not exist in zone {timezone!r} "
            "(DST spring-forward gap)"
        )
    return utc_dt, local.isoformat(), _utc_iso(utc_dt)


def _utc_iso(utc_dt: dt.datetime) -> str:
    iso = utc_dt.isoformat()
    return iso.replace("+00:00", "Z")


def julian_day_ut(utc_dt: dt.datetime) -> float:
    """Pure proleptic-Gregorian Julian Day of a UTC-aware datetime.

    Canonical Gregorian JDN algorithm (Fliegel–Van Flandern form): verified
    bit-exact against ``swe.julday(..., GREG_CAL)`` over 1583–3000 AD in the
    integration suite (deviation 0.0 days). ``swe.calc_ut`` interprets the JD
    as UT and applies its own Delta-T internally, so no leap-second table is
    needed here.
    """
    if utc_dt.tzinfo is None or utc_dt.utcoffset() is None:
        raise InvalidTimestampError("julian_day_ut requires a timezone-aware UTC datetime")
    utc_dt = utc_dt.astimezone(UTC)
    y, m = utc_dt.year, utc_dt.month
    d = utc_dt.day
    seconds = utc_dt.hour * 3600 + utc_dt.minute * 60 + utc_dt.second + utc_dt.microsecond / 1e6
    day_fraction = seconds / 86400.0

    # Proleptic Gregorian Julian Day Number (valid for all proleptic dates;
    # the service additionally gates civil dates at >= 1582-10-15).
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    jdn = (
        d
        + (153 * mm + 2) // 5
        + 365 * yy
        + yy // 4
        - yy // 100
        + yy // 400
        - 32045
    )
    return float(jdn) - 0.5 + day_fraction

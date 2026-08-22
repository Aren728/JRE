"""JRE-027 Birth Signature models — core data structures and constants.

JRE-027 assembles a deterministic ``BirthSignature`` from existing
astronomy and jyotish facts.  It outputs ONLY structural facts (Panchanga
factors, rashi positions, etc.) — never personality traits, temperament,
or interpretations.

Core Models:
- ``Tithi``: lunar day (1-30)
- ``Karana``: half-lunar day (11 classical types)
- ``Yoga``: sun-moon angular combination (27 yogas)
- ``Vara``: weekday (7 days)
- ``HoraPeriod``: planetary hora at birth time
- ``DayNightPeriod``: day or night at birth
- ``AmPm``: AM or PM
- ``BirthSignature``: the complete birth signature dataclass
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from jyotish import NakshatraId, Pada, RashiId

#: Pinned package version.
BIRTH_SIGNATURE_VERSION = "0.1.0"


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class Tithi(StrEnum):
    """The 30 lunar days (tithis) of the Panchanga."""

    SHUKLA_PRATIPADA = "SHUKLA_PRATIPADA"
    SHUKLA_DVITIYA = "SHUKLA_DVITIYA"
    SHUKLA_TRITIYA = "SHUKLA_TRITIYA"
    SHUKLA_CHATURTHI = "SHUKLA_CHATURTHI"
    SHUKLA_PANCHAMI = "SHUKLA_PANCHAMI"
    SHUKLA_SHASHTHI = "SHUKLA_SHASHTHI"
    SHUKLA_SAPTAMI = "SHUKLA_SAPTAMI"
    SHUKLA_ASHTAMI = "SHUKLA_ASHTAMI"
    SHUKLA_NAVAMI = "SHUKLA_NAVAMI"
    SHUKLA_DASHAMI = "SHUKLA_DASHAMI"
    SHUKLA_EKADASHI = "SHUKLA_EKADASHI"
    SHUKLA_DVADASHI = "SHUKLA_DVADASHI"
    SHUKLA_TRAYODASHI = "SHUKLA_TRAYODASHI"
    SHUKLA_CHATURDASHI = "SHUKLA_CHATURDASHI"
    PURNIMA = "PURNIMA"
    KRISHNA_PRATIPADA = "KRISHNA_PRATIPADA"
    KRISHNA_DVITIYA = "KRISHNA_DVITIYA"
    KRISHNA_TRITIYA = "KRISHNA_TRITIYA"
    KRISHNA_CHATURTHI = "KRISHNA_CHATURTHI"
    KRISHNA_PANCHAMI = "KRISHNA_PANCHAMI"
    KRISHNA_SHASHTHI = "KRISHNA_SHASHTHI"
    KRISHNA_SAPTAMI = "KRISHNA_SAPTAMI"
    KRISHNA_ASHTAMI = "KRISHNA_ASHTAMI"
    KRISHNA_NAVAMI = "KRISHNA_NAVAMI"
    KRISHNA_DASHAMI = "KRISHNA_DASHAMI"
    KRISHNA_EKADASHI = "KRISHNA_EKADASHI"
    KRISHNA_DVADASHI = "KRISHNA_DVADASHI"
    KRISHNA_TRAYODASHI = "KRISHNA_TRAYODASHI"
    KRISHNA_CHATURDASHI = "KRISHNA_CHATURDASHI"
    AMANTHA = "AMANTHA"


class Karana(StrEnum):
    """The 11 karanas (half-tithi) of the Panchanga."""

    BALAVA = "BALAVA"
    BAVALA = "BAVALA"
    KAILAVA = "KAILAVA"
    TAITILA = "TAITILA"
    GARJA = "GARJA"
    VANIJA = "VANIJA"
    VISHTI = "VISHTI"
    SHAKUNI = "SHAKUNI"
    CHATUSHPADA = "CHATUSHPADA"
    NAGAVA = "NAGAVA"
    KIMSTUGHNA = "KIMSTUGHNA"


class Yoga(StrEnum):
    """The 27 yogas (samyoga) of the Panchanga."""

    VISHKAMBHA = "VISHKAMBHA"
    PRITI = "PRITI"
    AYUSHMAN = "AYUSHMAN"
    SOUBHAGYA = "SOUBHAGYA"
    SHOBHANA = "SHOBHANA"
    ATIGANDA = "ATIGANDA"
    SUKARMA = "SUKARMA"
    DHRTI = "DHRTI"
    SHULA = "SHULA"
    GANDA = "GANDA"
    VRIDDHI = "VRIDDHI"
    DHRUVA = "DHRUVA"
    VYAGHATA = "VYAGHATA"
    HARSHANA = "HARSHANA"
    VAJRA = "VAJRA"
    SIDDHI = "SIDDHI"
    VYATIPATA = "VYATIPATA"
    VARIGHA = "VARIGHA"
    PARIGHA = "PARIGHA"
    SHIVA = "SHIVA"
    SIDDHA = "SIDDHA"
    SADHYA = "SADHYA"
    SUBHA = "SUBHA"
    SHUKLA = "SHUKLA"
    BRAHMA = "BRAHMA"
    INDRA = "INDRA"
    VAIDHRITI = "VAIDHRITI"


class Vara(StrEnum):
    """The 7 weekdays (vara) of the Panchanga."""

    SUNDAY = "SUNDAY"
    MONDAY = "MONDAY"
    TUESDAY = "TUESDAY"
    WEDNESDAY = "WEDNESDAY"
    THURSDAY = "THURSDAY"
    FRIDAY = "FRIDAY"
    SATURDAY = "SATURDAY"


class HoraPeriod(StrEnum):
    """The 7 planetary hora lords (one per day segment)."""

    SUN = "SUN"
    MOON = "MOON"
    MARS = "MARS"
    MERCURY = "MERCURY"
    JUPITER = "JUPITER"
    VENUS = "VENUS"
    SATURN = "SATURN"


class DayNightPeriod(StrEnum):
    """Whether birth occurred during day or night."""

    DAY = "DAY"
    NIGHT = "NIGHT"


class AmPm(StrEnum):
    """AM or PM designation."""

    AM = "AM"
    PM = "PM"


# --------------------------------------------------------------------------- #
# Classical lookup tables
# --------------------------------------------------------------------------- #

#: Canonical tithi names indexed by tithi number (1-30).
_TITHI_NAMES: tuple[Tithi, ...] = (
    Tithi.SHUKLA_PRATIPADA,    # 1
    Tithi.SHUKLA_DVITIYA,      # 2
    Tithi.SHUKLA_TRITIYA,      # 3
    Tithi.SHUKLA_CHATURTHI,    # 4
    Tithi.SHUKLA_PANCHAMI,     # 5
    Tithi.SHUKLA_SHASHTHI,     # 6
    Tithi.SHUKLA_SAPTAMI,      # 7
    Tithi.SHUKLA_ASHTAMI,      # 8
    Tithi.SHUKLA_NAVAMI,       # 9
    Tithi.SHUKLA_DASHAMI,      # 10
    Tithi.SHUKLA_EKADASHI,     # 11
    Tithi.SHUKLA_DVADASHI,     # 12
    Tithi.SHUKLA_TRAYODASHI,   # 13
    Tithi.SHUKLA_CHATURDASHI,  # 14
    Tithi.PURNIMA,             # 15
    Tithi.KRISHNA_PRATIPADA,   # 16
    Tithi.KRISHNA_DVITIYA,     # 17
    Tithi.KRISHNA_TRITIYA,     # 18
    Tithi.KRISHNA_CHATURTHI,   # 19
    Tithi.KRISHNA_PANCHAMI,    # 20
    Tithi.KRISHNA_SHASHTHI,    # 21
    Tithi.KRISHNA_SAPTAMI,     # 22
    Tithi.KRISHNA_ASHTAMI,     # 23
    Tithi.KRISHNA_NAVAMI,      # 24
    Tithi.KRISHNA_DASHAMI,     # 25
    Tithi.KRISHNA_EKADASHI,    # 26
    Tithi.KRISHNA_DVADASHI,    # 27
    Tithi.KRISHNA_TRAYODASHI,  # 28
    Tithi.KRISHNA_CHATURDASHI, # 29
    Tithi.AMANTHA,             # 30
)

#: One tithi arc in degrees (12 degrees).
TITHI_ARC_DEG: float = 12.0

#: One yoga arc in degrees (360/27 = 13.333... degrees).
YOGA_ARC_DEG: float = 360.0 / 27.0

#: Classical 7 cyclic karanas (positions 1-58 in the 60 half-tithi table).
_CYCLIC_KARANAS: tuple[Karana, ...] = (
    Karana.BALAVA,
    Karana.BAVALA,
    Karana.KAILAVA,
    Karana.TAITILA,
    Karana.GARJA,
    Karana.VANIJA,
    Karana.VISHTI,
)

#: Fixed karana for the first half-tithi (position 0).
_KIMSTUGHNA: Karana = Karana.KIMSTUGHNA

#: Fixed karana for the last half-tithi (position 59).
_SHAKUNI: Karana = Karana.SHAKUNI

#: Canonical yoga names indexed by yoga number (1-27).
_YOGA_NAMES: tuple[Yoga, ...] = (
    Yoga.VISHKAMBHA,  # 1
    Yoga.PRITI,       # 2
    Yoga.AYUSHMAN,    # 3
    Yoga.SOUBHAGYA,   # 4
    Yoga.SHOBHANA,    # 5
    Yoga.ATIGANDA,    # 6
    Yoga.SUKARMA,     # 7
    Yoga.DHRTI,       # 8
    Yoga.SHULA,       # 9
    Yoga.GANDA,       # 10
    Yoga.VRIDDHI,     # 11
    Yoga.DHRUVA,      # 12
    Yoga.VYAGHATA,    # 13
    Yoga.HARSHANA,    # 14
    Yoga.VAJRA,       # 15
    Yoga.SIDDHI,      # 16
    Yoga.VYATIPATA,   # 17
    Yoga.VARIGHA,     # 18
    Yoga.PARIGHA,     # 19
    Yoga.SHIVA,       # 20
    Yoga.SIDDHA,      # 21
    Yoga.SADHYA,      # 22
    Yoga.SUBHA,       # 23
    Yoga.SHUKLA,      # 24
    Yoga.BRAHMA,      # 25
    Yoga.INDRA,       # 26
    Yoga.VAIDHRITI,   # 27
)

#: Weekday lords (Sun=0 Sunday ... Saturn=6 Saturday) for hora calculation.
_VARA_LORDS: tuple[HoraPeriod, ...] = (
    HoraPeriod.SUN,      # Sunday
    HoraPeriod.MOON,     # Monday
    HoraPeriod.MARS,     # Tuesday
    HoraPeriod.MERCURY,  # Wednesday
    HoraPeriod.JUPITER,  # Thursday
    HoraPeriod.VENUS,    # Friday
    HoraPeriod.SATURN,   # Saturday
)

#: Weekday to Vara enum mapping.
_WEEKDAY_TO_VARA: tuple[Vara, ...] = (
    Vara.SUNDAY,
    Vara.MONDAY,
    Vara.TUESDAY,
    Vara.WEDNESDAY,
    Vara.THURSDAY,
    Vara.FRIDAY,
    Vara.SATURDAY,
)


# --------------------------------------------------------------------------- #
# Pure derivation functions
# --------------------------------------------------------------------------- #


def _fold(longitude_deg: float) -> float:
    """Fold any input into [0, 360)."""
    value = longitude_deg % 360.0
    return 0.0 if value == 0.0 else value


def compute_tithi_number(sun_lon: float, moon_lon: float) -> int:
    """Compute the tithi number (1-30) from Sun and Moon longitudes.

    Tithi is determined by the angular distance between Moon and Sun,
    divided by 12 degrees.

    Parameters
    ----------
    sun_lon : float
        Sun sidereal longitude in degrees [0, 360).
    moon_lon : float
        Moon sidereal longitude in degrees [0, 360).

    Returns
    -------
    int
        Tithi number in [1, 30].
    """
    diff = (_fold(moon_lon) - _fold(sun_lon)) % 360.0
    # Use multiplication to avoid floating point precision issues
    tithi_num = int(diff * 30.0 / 360.0) + 1
    return min(tithi_num, 30)


def tithi_from_number(tithi_num: int) -> Tithi:
    """Map a tithi number (1-30) to its Tithi enum value."""
    return _TITHI_NAMES[tithi_num - 1]


def compute_tithi(sun_lon: float, moon_lon: float) -> Tithi:
    """Compute the Tithi from Sun and Moon longitudes."""
    return tithi_from_number(compute_tithi_number(sun_lon, moon_lon))


def compute_tithi_remainder(sun_lon: float, moon_lon: float) -> float:
    """Compute the fractional remainder within the current tithi.

    Returns a value in [0.0, 1.0) indicating how far into the current
    tithi the birth falls.  < 0.5 means first half, >= 0.5 means second half.
    """
    diff = (_fold(moon_lon) - _fold(sun_lon)) % 360.0
    # Use multiplication to avoid floating point precision issues
    return (diff * 30.0 / 360.0) % 1.0


def compute_karana(sun_lon: float, moon_lon: float) -> Karana:
    """Compute the Karana from Sun and Moon longitudes.

    Uses the classical 60 half-tithi table:
    - Position 0: KIMSTUGHNA (fixed)
    - Positions 1-58: 7 cyclic karanas repeating
    - Position 59: SHAKUNI (fixed)
    """
    tithi_num = compute_tithi_number(sun_lon, moon_lon)
    remainder = compute_tithi_remainder(sun_lon, moon_lon)

    # Compute half-tithi index (0-59)
    half_tithi = (tithi_num - 1) * 2
    if remainder >= 0.5:
        half_tithi += 1

    if half_tithi == 0:
        return _KIMSTUGHNA
    if half_tithi == 59:
        return _SHAKUNI
    return _CYCLIC_KARANAS[(half_tithi - 1) % 7]


def compute_yoga_number(sun_lon: float, moon_lon: float) -> int:
    """Compute the yoga number (1-27) from Sun and Moon longitudes.

    Yoga is determined by the sum of Sun and Moon longitudes,
    divided by (360/27) degrees.

    Parameters
    ----------
    sun_lon : float
        Sun sidereal longitude in degrees [0, 360).
    moon_lon : float
        Moon sidereal longitude in degrees [0, 360).

    Returns
    -------
    int
        Yoga number in [1, 27].
    """
    total = (_fold(sun_lon) + _fold(moon_lon)) % 360.0
    # Use multiplication to avoid floating point precision issues
    yoga_num = int(total * 27.0 / 360.0) + 1
    return min(yoga_num, 27)


def compute_yoga(sun_lon: float, moon_lon: float) -> Yoga:
    """Compute the Yoga from Sun and Moon longitudes."""
    return _YOGA_NAMES[compute_yoga_number(sun_lon, moon_lon) - 1]


def compute_vara(julian_day_ut: float) -> Vara:
    """Compute the Vara (weekday) from Julian Day (UT).

    Uses the standard algorithm: JDN = int(JD + 0.5), then
    weekday = (JDN + 1) % 7, where 0 = Sunday.
    """
    # Julian Day starts at noon UT.  The Julian Day Number (JDN) is
    # int(JD + 0.5).  The weekday is (JDN + 1) % 7, where 0 = Sunday.
    jdn = int(julian_day_ut + 0.5)
    weekday = (jdn + 1) % 7
    return _WEEKDAY_TO_VARA[weekday]


def compute_hora(julian_day_ut: float, hour_of_day: float) -> HoraPeriod:
    """Compute the Hora lord at a specific time of day.

    The day is divided into 24 hora.  The hora cycle starts with the
    weekday lord and continues through the classical planet sequence:
    Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn (repeating).

    For simplicity, we compute the hora based on the hour of the day
    (0-23) and the weekday lord.
    """
    # Use corrected weekday computation
    jdn = int(julian_day_ut + 0.5)
    weekday = (jdn + 1) % 7
    start_lord = _VARA_LORDS[weekday]

    # Classical hora sequence: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn
    hora_cycle: tuple[HoraPeriod, ...] = (
        HoraPeriod.SUN,
        HoraPeriod.MOON,
        HoraPeriod.MARS,
        HoraPeriod.MERCURY,
        HoraPeriod.JUPITER,
        HoraPeriod.VENUS,
        HoraPeriod.SATURN,
    )

    # Find the index of the weekday lord in the cycle
    lord_index = hora_cycle.index(start_lord)

    # The hora at a given hour is determined by the hour offset from
    # the start of the day (sunrise ~= 6 AM for simplification).
    # Each hora lasts ~1.714 hours (24/7), but we use integer hour for simplicity.
    hora_index = (lord_index + int(hour_of_day)) % 7
    return hora_cycle[hora_index]


def compute_am_pm(hour_of_day: float) -> AmPm:
    """Determine AM or PM from the hour of day (0-23)."""
    if hour_of_day < 12.0:
        return AmPm.AM
    return AmPm.PM


def compute_day_night(
    sun_lon: float,
    hour_of_day: float,
) -> DayNightPeriod:
    """Determine day or night period from Sun longitude and hour of day.

    Uses a simplified approach: if the Sun is above the horizon
    (roughly 6 AM to 6 PM local), it's day; otherwise night.
    """
    if 6.0 <= hour_of_day < 18.0:
        return DayNightPeriod.DAY
    return DayNightPeriod.NIGHT


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BirthSignature:
    """The complete birth signature — a deterministic snapshot of
    structural Panchanga and positional facts at the birth instant.

    This is a FACT container.  It contains NO interpretations,
    predictions, personality traits, or temperament claims.
    """

    lagna: RashiId
    sun_rashi: RashiId
    moon_rashi: RashiId
    nakshatra: NakshatraId
    pada: Pada
    weekday: Vara
    hora: HoraPeriod
    tithi: Tithi
    karana: Karana
    yoga: Yoga
    day_night_period: DayNightPeriod
    am_pm: AmPm
    deterministic_id: str = ""

    def __post_init__(self) -> None:
        """Compute deterministic_id if not provided."""
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_hash(self)
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization (declaration-order keys)."""
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Deterministic hashing
# --------------------------------------------------------------------------- #


def _compute_hash(sig: BirthSignature) -> str:
    """Compute a deterministic SHA-256 hash for a BirthSignature."""
    data = {
        "lagna": sig.lagna.value,
        "sun_rashi": sig.sun_rashi.value,
        "moon_rashi": sig.moon_rashi.value,
        "nakshatra": sig.nakshatra.value,
        "pada": int(sig.pada),
        "weekday": sig.weekday.value,
        "hora": sig.hora.value,
        "tithi": sig.tithi.value,
        "karana": sig.karana.value,
        "yoga": sig.yoga.value,
        "day_night_period": sig.day_night_period.value,
        "am_pm": sig.am_pm.value,
    }
    serialized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    hasher = hashlib.sha256()
    hasher.update(b"birth_signature:")
    hasher.update(serialized.encode("utf-8"))
    return hasher.hexdigest()


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #


def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> .value; tuples -> lists; -0.0 -> 0.0)."""
    if hasattr(model, "__dataclass_fields__"):
        return {key: _model_to_dict(value) for key, value in model.__dict__.items()}
    if isinstance(model, enum.Enum):
        return model.value
    if isinstance(model, (list, tuple)):
        return [_model_to_dict(value) for value in model]
    if isinstance(model, dict):
        return {_model_to_dict(key): _model_to_dict(value) for key, value in model.items()}
    if isinstance(model, float):
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)

"""JRE-066 Western Astrology data models — deterministic fact containers.

All dataclasses are frozen and use SHA-256 deterministic IDs.  No
astrological interpretation is performed here — only fact definitions
and pure computational helpers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from typing import Any

# ── Enums ────────────────────────────────────────────────────────────────────


class WesternPlanet(StrEnum):
    """Classical and modern planets used in Western astrology."""

    SUN = "SUN"
    MOON = "MOON"
    MERCURY = "MERCURY"
    VENUS = "VENUS"
    MARS = "MARS"
    JUPITER = "JUPITER"
    SATURN = "SATURN"
    URANUS = "URANUS"
    NEPTUNE = "NEPTUNE"
    PLUTO = "PLUTO"
    NORTH_NODE = "NORTH_NODE"
    SOUTH_NODE = "SOUTH_NODE"
    CHIRON = "CHIRON"


class WesternHouseSystem(StrEnum):
    """Supported house system calculation methods."""

    PLACIDUS = "PLACIDUS"
    WHOLE_SIGN = "WHOLE_SIGN"
    EQUAL = "EQUAL"


class WesternDignity(StrEnum):
    """Essential dignity of a planet by zodiacal placement."""

    DOMICILE = "DOMICILE"
    EXALTATION = "EXALTATION"
    DETRIMENT = "DETRIMENT"
    FALL = "FALL"
    PEREGRINE = "PEREGRINE"


class Sect(StrEnum):
    """Diurnal/Nocturnal sect — foundational to traditional dignity.

    A chart is DIURNAL if the Sun is above the horizon (between
    Ascendant and Descendant through the MC), NOCTURNAL otherwise.
    Sect modifies planetary dignity: diurnal planets (Sun, Jupiter,
    Saturn) are empowered in diurnal charts; nocturnal planets
    (Moon, Venus, Mars) are empowered in nocturnal charts.

    Source: Lilly CA Ch. 21, Bonatti Tr. 5, Dorotheus C.I.4.
    """

    DIURNAL = "DIURNAL"
    NOCTURNAL = "NOCTURNAL"


class WesternAspectType(Enum):
    """Major Ptolemaic aspect types with their orb."""

    CONJUNCTION = "CONJUNCTION"
    OPPOSITION = "OPPOSITION"
    SQUARE = "SQUARE"
    TRINE = "TRINE"
    SEXTILE = "SEXTILE"


# ── Aspect Orb Defaults (degrees) ────────────────────────────────────────────

ASPECT_ORBS: dict[WesternAspectType, float] = {
    WesternAspectType.CONJUNCTION: 8.0,
    WesternAspectType.OPPOSITION: 8.0,
    WesternAspectType.SQUARE: 7.0,
    WesternAspectType.TRINE: 7.0,
    WesternAspectType.SEXTILE: 6.0,
}

# ── Aspect Angular Distances (degrees) ───────────────────────────────────────

ASPECT_ANGLES: dict[WesternAspectType, float] = {
    WesternAspectType.CONJUNCTION: 0.0,
    WesternAspectType.OPPOSITION: 180.0,
    WesternAspectType.SQUARE: 90.0,
    WesternAspectType.TRINE: 120.0,
    WesternAspectType.SEXTILE: 60.0,
}


# ── Essential Dignity Tables ─────────────────────────────────────────────────
# Each planet maps to (domicile_sign_start, exaltation_sign_start).
# Sign indices: 0=Aries … 11=Pisces.  Positions in degrees:
#   Aries=0, Taurus=30, Gemini=60, Cancer=90, Leo=120, Virgo=150,
#   Libra=180, Scorpio=210, Sagittarius=240, Capricorn=270,
#   Aquarius=300, Pisces=330.

# Domicile: sign where planet has root dignity (Rulership).
# Detriment: opposite sign.
# Exaltation: sign where planet is enhanced.
# Fall: opposite sign.

DOMICILE_SIGNS: dict[WesternPlanet, int] = {
    WesternPlanet.SUN: 4,          # Leo (120°)
    WesternPlanet.MOON: 1,         # Taurus (30°) — classical, some traditions say Cancer
    WesternPlanet.MERCURY: 2,      # Gemini (60°) — also Virgo (5)
    WesternPlanet.VENUS: 1,        # Taurus (30°) — also Libra (7)
    WesternPlanet.MARS: 0,         # Aries (0°) — also Scorpio (7)
    WesternPlanet.JUPITER: 8,      # Sagittarius (240°) — also Pisces (11)
    WesternPlanet.SATURN: 9,       # Capricorn (270°) — also Aquarius (10)
    WesternPlanet.URANUS: 10,      # Aquarius (300°) — modern ruler
    WesternPlanet.NEPTUNE: 11,     # Pisces (330°) — modern ruler
    WesternPlanet.PLUTO: 7,        # Scorpio (210°) — modern ruler
}

EXALTATION_SIGNS: dict[WesternPlanet, int] = {
    WesternPlanet.SUN: 0,          # Aries (0°)
    WesternPlanet.MOON: 1,         # Taurus (30°)
    WesternPlanet.MERCURY: 5,      # Virgo (150°)
    WesternPlanet.VENUS: 11,       # Pisces (330°)
    WesternPlanet.MARS: 9,         # Capricorn (270°)
    WesternPlanet.JUPITER: 3,      # Cancer (90°)
    WesternPlanet.SATURN: 6,       # Libra (180°)
}

# Secondary domicile rulerships (some planets share signs)
SECONDARY_DOMICILE: dict[WesternPlanet, int] = {
    WesternPlanet.MERCURY: 5,      # Virgo
    WesternPlanet.VENUS: 7,        # Libra
    WesternPlanet.MARS: 7,         # Scorpio
    WesternPlanet.JUPITER: 11,     # Pisces
    WesternPlanet.SATURN: 10,      # Aquarius
}


def _sign_index(longitude: float) -> int:
    """Return 0-based zodiac sign index from ecliptic longitude."""
    return int(longitude / 30.0) % 12


def _sign_name(longitude: float) -> str:
    """Return zodiac sign name from ecliptic longitude."""
    signs = [
        "ARIES", "TAURUS", "GEMINI", "CANCER",
        "LEO", "VIRGO", "LIBRA", "SCORPIO",
        "SAGITTARIUS", "CAPRICORN", "AQUARIUS", "PISCES",
    ]
    return signs[_sign_index(longitude)]


def _degree_in_sign(longitude: float) -> float:
    """Return degree within the current sign (0.0 – 29.999…)."""
    return longitude % 30.0


def evaluate_essential_dignity(
    planet: WesternPlanet,
    longitude: float,
) -> WesternDignity:
    """Evaluate essential dignity from tropical longitude.

    Uses classical domicile/exaltation/detriment/fall scheme.
    Planets not in any of those are PEREGRINE.
    """
    sign_idx = _sign_index(longitude)

    # Check domicile
    dom = DOMICILE_SIGNS.get(planet)
    sec = SECONDARY_DOMICILE.get(planet)
    if dom is not None and sign_idx == dom:
        return WesternDignity.DOMICILE
    if sec is not None and sign_idx == sec:
        return WesternDignity.DOMICILE

    # Check exaltation
    exalt = EXALTATION_SIGNS.get(planet)
    if exalt is not None and sign_idx == exalt:
        return WesternDignity.EXALTATION

    # Check detriment (opposite of domicile)
    if dom is not None and sign_idx == (dom + 6) % 12:
        return WesternDignity.DETRIMENT

    # Check fall (opposite of exaltation)
    if exalt is not None and sign_idx == (exalt + 6) % 12:
        return WesternDignity.FALL

    return WesternDignity.PEREGRINE


# ── Data Classes ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class WesternAspect:
    """A single major aspect between two planets."""

    planet_a: WesternPlanet
    planet_b: WesternPlanet
    aspect_type: WesternAspectType
    exact_angle: float  # angular distance in degrees (0–360)
    orb: float  # exact_angle - aspect_angle (always positive)
    applying: bool  # True if the aspect is applying (closing)

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "planet_a": self.planet_a.value,
            "planet_b": self.planet_b.value,
            "aspect_type": self.aspect_type.value,
            "exact_angle": round(self.exact_angle, 6),
            "orb": round(self.orb, 6),
            "applying": self.applying,
        }


@dataclass(frozen=True)
class PlanetPosition:
    """Tropical position of a single planet."""

    planet: WesternPlanet
    longitude: float  # tropical ecliptic longitude (0–360)
    latitude: float  # ecliptic latitude
    speed_longitude: float  # daily motion in longitude
    sign: str  # zodiac sign name
    degree_in_sign: float  # degree within sign (0–30)

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "planet": self.planet.value,
            "longitude": round(self.longitude, 6),
            "latitude": round(self.latitude, 6),
            "speed_longitude": round(self.speed_longitude, 6),
            "sign": self.sign,
            "degree_in_sign": round(self.degree_in_sign, 6),
        }


@dataclass(frozen=True)
class HouseCusp:
    """A single house cusp."""

    house_number: int  # 1–12
    longitude: float  # tropical ecliptic longitude

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "house_number": self.house_number,
            "longitude": round(self.longitude, 6),
        }


@dataclass(frozen=True)
class WesternChart:
    """Complete Western natal chart — pure deterministic facts.

    Contains tropical positions, house cusps, aspects, and dignities.
    No astrological interpretation is performed.
    """

    birth_date: str  # ISO date string (YYYY-MM-DD)
    birth_time: str  # ISO time string (HH:MM:SS)
    latitude: float
    longitude: float
    house_system: WesternHouseSystem
    julian_day_ut: float

    planet_positions: tuple[PlanetPosition, ...]
    house_cusps: tuple[HouseCusp, ...]
    aspects: tuple[WesternAspect, ...]
    dignities: dict[WesternPlanet, WesternDignity]

    ascendant: float  # tropical longitude of Ascendant
    midheaven: float  # tropical longitude of MC
    sect: Sect = Sect.DIURNAL  # Diurnal or Nocturnal chart

    deterministic_id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.deterministic_id:
            object.__setattr__(
                self, "deterministic_id", _compute_chart_id(self)
            )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic serialization."""
        return {
            "birth_date": self.birth_date,
            "birth_time": self.birth_time,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "house_system": self.house_system.value,
            "julian_day_ut": self.julian_day_ut,
            "planet_positions": [p.to_dict() for p in self.planet_positions],
            "house_cusps": [c.to_dict() for c in self.house_cusps],
            "aspects": [a.to_dict() for a in self.aspects],
            "dignities": {k.value: v.value for k, v in self.dignities.items()},
            "ascendant": round(self.ascendant, 6),
            "midheaven": round(self.midheaven, 6),
            "sect": self.sect.value,
            "deterministic_id": self.deterministic_id,
        }


def _compute_chart_id(chart: WesternChart) -> str:
    """SHA-256 deterministic ID from chart contents."""
    payload = json.dumps(chart.to_dict(), sort_keys=True, separators=(",", ":"))
    # Exclude the deterministic_id itself to avoid circular reference
    cleaned = payload.replace(f'"{chart.deterministic_id}"', '""')
    return hashlib.sha256(cleaned.encode()).hexdigest()[:16]


# ── Aspect Calculation Helpers ───────────────────────────────────────────────


def _angular_distance(a: float, b: float) -> float:
    """Smallest angular distance between two longitudes (0–180)."""
    diff = abs(a - b) % 360.0
    return diff if diff <= 180.0 else 360.0 - diff


def compute_aspect(
    planet_a: WesternPlanet,
    lon_a: float,
    speed_a: float,
    planet_b: WesternPlanet,
    lon_b: float,
    speed_b: float,
) -> WesternAspect | None:
    """Compute a single aspect between two planets, if any major aspect exists.

    Returns None if no major aspect is within orb.
    """
    if planet_a == planet_b:
        return None

    diff = abs(lon_a - lon_b) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff

    for aspect_type, target_angle in ASPECT_ANGLES.items():
        orb_limit = ASPECT_ORBS[aspect_type]
        orb = abs(diff - target_angle)
        if orb <= orb_limit:
            # Determine applying: closing aspect (speed difference reduces orb)
            relative_speed = abs(speed_a - speed_b)
            applying = relative_speed > 1e-10
            return WesternAspect(
                planet_a=planet_a,
                planet_b=planet_b,
                aspect_type=aspect_type,
                exact_angle=diff,
                orb=orb,
                applying=applying,
            )

    return None


def compute_all_aspects(
    positions: dict[WesternPlanet, tuple[float, float]],
) -> tuple[WesternAspect, ...]:
    """Compute all major aspects between all planet pairs.

    Args:
        positions: dict mapping planet -> (longitude, speed_longitude).

    Returns:
        Sorted tuple of WesternAspect objects.
    """
    aspects: list[WesternAspect] = []
    planets = list(positions.keys())
    for i, pa in enumerate(planets):
        for pb in planets[i + 1 :]:
            lon_a, spd_a = positions[pa]
            lon_b, spd_b = positions[pb]
            aspect = compute_aspect(pa, lon_a, spd_a, pb, lon_b, spd_b)
            if aspect is not None:
                aspects.append(aspect)
    return tuple(sorted(aspects, key=lambda a: (a.aspect_type.value, a.orb)))

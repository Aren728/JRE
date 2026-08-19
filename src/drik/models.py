"""JRE-012 Drik (Aspect) models — core data structures and constants.

JRE-012 computes the classical Jyotish aspect graph from natal planet
positions.  It applies standard and special aspects (Mars 4/8, Jupiter
5/9, Saturn 3/10) and outputs a structured aspect graph without
predictive interpretation.

Core Models:
- ``AspectType``: enum of standard and special aspect kinds
- ``AspectRule``: one aspect rule (source, target offset, type)
- ``AspectApplication``: one computed aspect between two planets
- ``DrikResult``: complete aspect graph for the chart
- ``DrikConfig``: immutable configuration
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId

from .errors import InvalidDrikConfigError

#: Pinned package version.
DRIK_VERSION = "0.1.0"

#: House offsets for each planet's aspects (1-indexed from planet's sign).
#: House 7 (180 degrees) is the standard aspect for all planets.
DEFAULT_ASPECT_HOUSES: dict[BodyId, tuple[int, ...]] = {
    BodyId.SUN: (7,),
    BodyId.MOON: (7,),
    BodyId.MARS: (4, 7, 8),
    BodyId.MERCURY: (7,),
    BodyId.JUPITER: (5, 7, 9),
    BodyId.VENUS: (7,),
    BodyId.SATURN: (3, 7, 10),
    BodyId.RAHU: (7,),
    BodyId.KETU: (7,),
}

#: Angular distance in degrees for each house offset.
HOUSE_OFFSET_DEGREES: dict[int, float] = {
    1: 0.0,
    2: 30.0,
    3: 60.0,
    4: 90.0,
    5: 120.0,
    6: 150.0,
    7: 180.0,
    8: 210.0,
    9: 240.0,
    10: 270.0,
    11: 300.0,
    12: 330.0,
}

#: Default orb for aspect detection in degrees.
DEFAULT_ORB_DEG: float = 6.0


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class AspectType(StrEnum):
    """Classical Jyotish aspect types."""

    STANDARD = "STANDARD"           # 7th house (all planets)
    MARS_SPECIAL = "MARS_SPECIAL"   # 4th and 8th house
    JUPITER_SPECIAL = "JUPITER_SPECIAL"  # 5th and 9th house
    SATURN_SPECIAL = "SATURN_SPECIAL"    # 3rd and 10th house


class AspectDirection(StrEnum):
    """Whether the aspect is applying (closing) or separating (opening)."""

    APPLYING = "APPLYING"
    SEPARATING = "SEPARATING"
    EXACT = "EXACT"


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class AspectRule:
    """One aspect rule: a source planet may aspect targets at given offsets."""

    source_planet: BodyId
    target_house_offset: int
    aspect_type: AspectType

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class AspectApplication:
    """One computed aspect between two planets.

    ``source_planet`` is the planet casting the aspect.
    ``target_planet`` is the planet receiving the aspect.
    ``angular_distance_deg`` is the forward zodiacal distance from
    source to target.
    ``orb_deg`` is the absolute difference between the ideal angle and
    the actual angular distance.
    ``direction`` indicates whether the aspect is applying, separating,
    or exact.
    """

    source_planet: BodyId
    target_planet: BodyId
    aspect_type: AspectType
    ideal_angle_deg: float
    angular_distance_deg: float
    orb_deg: float
    direction: AspectDirection
    house_offset: int

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class DrikResult:
    """Complete aspect graph for the chart."""

    aspects: tuple[AspectApplication, ...]
    version: str = DRIK_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def aspects_for(self, planet: BodyId) -> tuple[AspectApplication, ...]:
        """Return all aspects where *planet* is the source."""
        return tuple(a for a in self.aspects if a.source_planet == planet)

    def aspects_involving(self, planet: BodyId) -> tuple[AspectApplication, ...]:
        """Return all aspects where *planet* is source or target."""
        return tuple(
            a for a in self.aspects
            if a.source_planet == planet or a.target_planet == planet
        )


@dataclass(frozen=True)
class DrikConfig:
    """Immutable JRE-012 configuration.  TOML is authoritative; every
    default is declared in ``config/drik.toml`` (no hidden defaults).
    """

    version: str = DRIK_VERSION
    default_orb_deg: float = DEFAULT_ORB_DEG
    aspect_houses: dict[str, tuple[int, ...]] = field(
        default_factory=lambda: {
            k.value: v for k, v in DEFAULT_ASPECT_HOUSES.items()
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DrikConfig:
        version = data.get("version", DRIK_VERSION)
        orb = float(data.get("default_orb_deg", DEFAULT_ORB_DEG))
        houses_raw = data.get("aspect_houses")
        aspect_houses: dict[str, tuple[int, ...]]
        if isinstance(houses_raw, dict) and houses_raw:
            aspect_houses = {
                str(k): tuple(int(vi) for vi in v) if isinstance(v, list) else (int(v),)
                for k, v in houses_raw.items()
            }
        else:
            aspect_houses = {
                k.value: v for k, v in DEFAULT_ASPECT_HOUSES.items()
            }
        return cls(
            version=str(version),
            default_orb_deg=orb,
            aspect_houses=aspect_houses,
        )


def validate(config: DrikConfig) -> DrikConfig:
    """Validate a ``DrikConfig``; raises ``InvalidDrikConfigError``."""
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidDrikConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    if not isinstance(config.default_orb_deg, (int, float)) or config.default_orb_deg < 0:
        raise InvalidDrikConfigError(
            f"default_orb_deg must be a non-negative number, got {config.default_orb_deg!r}"
        )
    if not isinstance(config.aspect_houses, dict) or not config.aspect_houses:
        raise InvalidDrikConfigError(
            f"aspect_houses must be a non-empty dict, got {config.aspect_houses!r}"
        )
    for planet_str, houses in config.aspect_houses.items():
        if not isinstance(houses, (list, tuple)):
            raise InvalidDrikConfigError(
                f"aspect_houses[{planet_str!r}] must be a list of ints"
            )
        for h in houses:
            if not isinstance(h, int) or h < 1 or h > 12:
                raise InvalidDrikConfigError(
                    f"aspect_houses[{planet_str!r}] contains invalid house {h!r}"
                )
    return config


# --------------------------------------------------------------------------- #
# Generic serialization helpers
# --------------------------------------------------------------------------- #

def _model_to_dict(model: Any) -> Any:
    """Generic dataclass serializer (deterministic key order = declaration
    order; enums -> ``.value``; tuples -> lists; ``-0.0`` -> ``0.0``)."""
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

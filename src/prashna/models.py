"""JRE-019 Prashna (Horary) models — core data structures.

JRE-019 computes the Query Ascendant (Prashna Lagna) and maps the
relevant houses for a specific inquiry based on the exact time of
the query, strictly as structural data points without predictive
interpretation.

Core Models:
- ``QueryLocation``: latitude, longitude
- ``PrashnaChart``: query_time_utc, query_location, prashna_lagna, query_moon_rashi
- ``PrashnaHouseMapping``: query_category, primary_house, secondary_house
- ``PrashnaReport``: chart, house_mapping
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, PlanetState, RashiId

#: Pinned package version.
PRASHNA_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class PrashnaCategory(StrEnum):
    """Standard Prashna query categories."""

    WEALTH = "WEALTH"
    CAREER = "CAREER"
    MARRIAGE = "MARRIAGE"
    HEALTH = "HEALTH"
    EDUCATION = "EDUCATION"
    PROPERTY = "PROPERTY"
    LITIGATION = "LITIGATION"
    TRAVEL = "TRAVEL"
    CHILDREN = "CHILDREN"
    GENERAL = "GENERAL"


# --------------------------------------------------------------------------- #
# Nakshatra-to-Rashi mapping for Prashna Lagna
# --------------------------------------------------------------------------- #

# Classical rule: the Prashna Lagna is the rashi ruled by the Nakshatra
# lord of the Moon at query time.  Each Nakshatra lord (BodyId) maps to
# the rashi they naturally rule.
_NAKSHATRA_LORD_RASHI: dict[BodyId, RashiId] = {
    BodyId.SUN: RashiId.SIMHA,        # Sun rules Leo
    BodyId.MOON: RashiId.KARKA,       # Moon rules Cancer
    BodyId.MARS: RashiId.MESHA,       # Mars rules Aries
    BodyId.MERCURY: RashiId.KANYA,    # Mercury rules Virgo
    BodyId.JUPITER: RashiId.DHANUSHA, # Jupiter rules Sagittarius
    BodyId.VENUS: RashiId.VRISHABHA,  # Venus rules Taurus
    BodyId.SATURN: RashiId.MAKARA,    # Saturn rules Capricorn
}


# --------------------------------------------------------------------------- #
# Classical house mapping defaults
# --------------------------------------------------------------------------- #

DEFAULT_HOUSE_MAPPINGS: dict[str, tuple[int, int]] = {
    "WEALTH": (2, 11),
    "CAREER": (10, 6),
    "MARRIAGE": (7, 2),
    "HEALTH": (1, 8),
    "EDUCATION": (4, 9),
    "PROPERTY": (4, 11),
    "LITIGATION": (6, 7),
    "TRAVEL": (3, 12),
    "CHILDREN": (5, 11),
    "GENERAL": (1, 7),
}


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class QueryLocation:
    """Geographic location of the querent at the time of the query."""

    latitude: float
    longitude: float

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class PrashnaChart:
    """The Prashna (horary) chart cast at the exact query time."""

    query_time_utc: str  # ISO-UTC string
    query_location: QueryLocation
    prashna_lagna: RashiId
    query_moon_rashi: RashiId

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class PrashnaHouseMapping:
    """House mapping for a specific query category relative to the Prashna Lagna."""

    query_category: PrashnaCategory
    primary_house: int  # 1-12
    secondary_house: int  # 1-12

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class PrashnaReport:
    """Complete Prashna (Horary) report."""

    chart: PrashnaChart
    house_mapping: PrashnaHouseMapping
    version: str = PRASHNA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class PrashnaConfig:
    """Immutable JRE-019 configuration."""

    version: str = PRASHNA_VERSION
    default_category: str = "GENERAL"
    house_mappings: dict[str, tuple[int, int]] = field(
        default_factory=lambda: dict(DEFAULT_HOUSE_MAPPINGS)
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #


def compute_prashna_lagna(moon_nakshatra_lord: BodyId) -> RashiId:
    """Determine the Prashna Lagna (Query Ascendant) from the Moon's Nakshatra lord.

    The classical rule: the Prashna Lagna is the rashi naturally ruled
    by the Nakshatra lord of the Moon at the time of the query.

    Parameters
    ----------
    moon_nakshatra_lord : BodyId
        The Nakshatra lord of the Moon at query time.

    Returns
    -------
    RashiId
        The Prashna Lagna rashi.
    """
    rashi = _NAKSHATRA_LORD_RASHI.get(moon_nakshatra_lord)
    if rashi is None:
        # Fallback: use the Sun's sign (Leo) for unknown lords
        return RashiId.SIMHA
    return rashi


def resolve_house_mapping(
    category: PrashnaCategory,
    house_mappings: dict[str, tuple[int, int]],
) -> PrashnaHouseMapping:
    """Resolve the house mapping for a query category from the config.

    Parameters
    ----------
    category : PrashnaCategory
        The query category.
    house_mappings : dict
        Mapping from category name to (primary_house, secondary_house).

    Returns
    -------
    PrashnaHouseMapping
        The house mapping for the category.
    """
    key = category.value
    houses = house_mappings.get(key)
    if houses is None:
        # Fallback to GENERAL
        houses = house_mappings.get("GENERAL", (1, 7))
    return PrashnaHouseMapping(
        query_category=category,
        primary_house=houses[0],
        secondary_house=houses[1],
    )


def lookup_moon_nakshatra_lord(
    planet_states: tuple[PlanetState, ...],
) -> BodyId:
    """Find the Nakshatra lord of the Moon from the planet states.

    Parameters
    ----------
    planet_states : tuple of PlanetState
        Planet positions at the query time.

    Returns
    -------
    BodyId
        The Nakshatra lord of the Moon.

    Raises
    ------
    ValueError
        If the Moon is not found in the planet states.
    """
    for state in planet_states:
        if state.body == BodyId.MOON:
            return state.nakshatra_lord
    raise ValueError("Moon not found in planet_states")


def rashi_at_distance(from_rashi: RashiId, distance: int) -> RashiId:
    """Return the rashi that is *distance* signs forward from *from_rashi*.

    Distance is counted in zodiacal (forward) order.
    """
    rashi_list = list(RashiId)
    idx = rashi_list.index(from_rashi)
    return rashi_list[(idx + distance) % 12]


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

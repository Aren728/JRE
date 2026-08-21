"""JRE-018 Jaimini (Chara Dasha / Argala) models — core data structures.

JRE-018 computes the Chara Dasha sequence (sign-based periods) and
Argala (planetary interventions) for a given natal chart, strictly
as structural data points without predictive interpretation.

Core Models:
- ``CharaDashaPeriod``: rashi, start_utc, end_utc, lord
- ``ArgalaResult``: target_rashi, intervening_planets, obstructing_planets
- ``JaiminiReport``: chara_dasha, argala
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, PlanetState, RashiId, sign_lord_of

from .errors import InvalidJaiminiConfigError

#: Pinned package version.
JAIMINI_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class LagnaNature(StrEnum):
    """Classification of Lagna (ascendant) sign nature."""

    MOVABLE = "MOVABLE"  # Chara: Aries, Cancer, Libra, Capricorn
    FIXED = "FIXED"      # Sthira: Taurus, Leo, Scorpio, Aquarius
    DUAL = "DUAL"        # Dvisvabhava: Gemini, Virgo, Sagittarius, Pisces


# --------------------------------------------------------------------------- #
# Lagna nature classification
# --------------------------------------------------------------------------- #

_MOVABLE_RASHIS: frozenset[RashiId] = frozenset({
    RashiId.MESHA, RashiId.KARKA, RashiId.TULA, RashiId.MAKARA,
})

_FIXED_RASHIS: frozenset[RashiId] = frozenset({
    RashiId.VRISHABHA, RashiId.SIMHA, RashiId.VRISHCHIKA, RashiId.KUMBHA,
})

_DUAL_RASHIS: frozenset[RashiId] = frozenset({
    RashiId.MITHUNA, RashiId.KANYA, RashiId.DHANUSHA, RashiId.MEENA,
})


def classify_lagna_nature(rashi: RashiId) -> LagnaNature:
    """Classify a rashi as MOVABLE, FIXED, or DUAL."""
    if rashi in _MOVABLE_RASHIS:
        return LagnaNature.MOVABLE
    if rashi in _FIXED_RASHIS:
        return LagnaNature.FIXED
    if rashi in _DUAL_RASHIS:
        return LagnaNature.DUAL
    raise InvalidJaiminiConfigError(f"unknown rashi for classification: {rashi!r}")


# --------------------------------------------------------------------------- #
# Rashi helpers
# --------------------------------------------------------------------------- #

RASHI_LIST: list[RashiId] = list(RashiId)


def rashi_at_distance(from_rashi: RashiId, distance: int) -> RashiId:
    """Return the rashi that is *distance* signs forward from *from_rashi*.

    Distance is counted in zodiacal (forward) order.  Negative distances
    are wrapped correctly.
    """
    idx = RASHI_LIST.index(from_rashi)
    return RASHI_LIST[(idx + distance) % 12]


def get_planets_in_rashi(
    planet_states: tuple[PlanetState, ...],
    target_rashi: RashiId,
) -> tuple[BodyId, ...]:
    """Return the BodyIds of planets whose natal rashi is *target_rashi*."""
    return tuple(
        state.body for state in planet_states if state.rashi == target_rashi
    )


# --------------------------------------------------------------------------- #
# Classical Argala house offsets
# --------------------------------------------------------------------------- #

ARGALA_INTERVENING_HOUSES: tuple[int, ...] = (2, 4, 5, 11)
ARGALA_OBSTRUCTING_HOUSES: tuple[int, ...] = (12, 10, 9, 3)


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class CharaDashaPeriod:
    """One Chara Dasha (sign-based) period."""

    rashi: RashiId
    start_utc: str  # ISO-UTC string
    end_utc: str  # ISO-UTC string
    lord: BodyId  # classical lord of the rashi

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class ArgalaResult:
    """Argala (intervention) analysis for one target rashi."""

    target_rashi: RashiId
    intervening_planets: tuple[BodyId, ...]
    obstructing_planets: tuple[BodyId, ...]

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class JaiminiReport:
    """Complete Jaimini (Chara Dasha / Argala) report."""

    chara_dasha: tuple[CharaDashaPeriod, ...]
    argala: tuple[ArgalaResult, ...]
    version: str = JAIMINI_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class JaiminiConfig:
    """Immutable JRE-018 configuration."""

    version: str = JAIMINI_VERSION
    default_period_years: int = 7
    chara_dasha_start_sign: dict[str, int] = field(
        default_factory=lambda: {"MOVABLE": 9, "FIXED": 10, "DUAL": 11}
    )
    argala_intervening_houses: tuple[int, ...] = field(
        default_factory=lambda: ARGALA_INTERVENING_HOUSES
    )
    argala_obstructing_houses: tuple[int, ...] = field(
        default_factory=lambda: ARGALA_OBSTRUCTING_HOUSES
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #


def compute_starting_sign(
    lagna_rashi: RashiId,
    lagna_nature: LagnaNature,
    planet_states: tuple[PlanetState, ...],
    start_house_offset: int,
) -> RashiId:
    """Determine the Chara Dasha starting sign.

    The starting sign is the sign occupied by the lord of the
    ``start_house_offset``-th house from the Lagna.

    Parameters
    ----------
    lagna_rashi : RashiId
        The ascendant rashi.
    lagna_nature : LagnaNature
        Classification of the Lagna sign.
    planet_states : tuple of PlanetState
        Natal planet positions (needed to find which sign the lord occupies).
    start_house_offset : int
        9 for MOVABLE, 10 for FIXED, 11 for DUAL.

    Returns
    -------
    RashiId
        The starting sign of the Chara Dasha.
    """
    # 1. Find the target house sign (house numbers are 1-indexed)
    target_house_rashi = rashi_at_distance(lagna_rashi, start_house_offset - 1)

    # 2. Find the lord of that target house sign
    target_lord = sign_lord_of(target_house_rashi)

    # 3. Find which sign that lord occupies in the natal chart
    for state in planet_states:
        if state.body == target_lord:
            return state.rashi

    # Fallback: if the lord planet is not in planet_states, use its natural sign
    return target_house_rashi


def compute_chara_dasha_sequence(
    starting_sign: RashiId,
    period_years: int,
    natal_moon_rashi: RashiId,
) -> tuple[CharaDashaPeriod, ...]:
    """Generate the Chara Dasha sequence starting from *starting_sign*.

    The sequence progresses through all 12 signs in zodiacal (forward)
    order.  Each period has an equal duration of *period_years* years.

    The reference epoch is arbitrary (2000-01-01T00:00:00Z) since the
    structure (sign order, lord) is deterministic regardless of absolute
    dates.

    Parameters
    ----------
    starting_sign : RashiId
        The first sign of the Chara Dasha.
    period_years : int
        Years per sign period.
    natal_moon_rashi : RashiId
        Natal Moon rashi (used for reference epoch; kept for future use).

    Returns
    -------
    tuple of CharaDashaPeriod
        The 12 Chara Dasha periods in sequence.
    """
    periods: list[CharaDashaPeriod] = []
    total_months = period_years * 12
    month_offset = 0
    start_idx = RASHI_LIST.index(starting_sign)

    for i in range(12):
        rashi = RASHI_LIST[(start_idx + i) % 12]
        lord = sign_lord_of(rashi)
        start_month = month_offset
        end_month = month_offset + total_months
        start_utc = _month_to_iso(start_month)
        end_utc = _month_to_iso(end_month)
        periods.append(CharaDashaPeriod(
            rashi=rashi,
            start_utc=start_utc,
            end_utc=end_utc,
            lord=lord,
        ))
        month_offset = end_month

    return tuple(periods)


def compute_argala(
    target_rashi: RashiId,
    planet_states: tuple[PlanetState, ...],
    intervening_houses: tuple[int, ...] = ARGALA_INTERVENING_HOUSES,
    obstructing_houses: tuple[int, ...] = ARGALA_OBSTRUCTING_HOUSES,
) -> ArgalaResult:
    """Compute Argala (intervention) for a single target rashi.

    Parameters
    ----------
    target_rashi : RashiId
        The rashi being analyzed.
    planet_states : tuple of PlanetState
        Natal planet positions.
    intervening_houses : tuple of int
        House offsets for Argala (default: 2, 4, 5, 11).
    obstructing_houses : tuple of int
        House offsets for Virodha Argala (default: 12, 10, 9, 3).

    Returns
    -------
    ArgalaResult
        The intervening and obstructing planets for *target_rashi*.
    """
    intervening: list[BodyId] = []
    for house_offset in intervening_houses:
        house_rashi = rashi_at_distance(target_rashi, house_offset - 1)
        intervening.extend(get_planets_in_rashi(planet_states, house_rashi))

    obstructing: list[BodyId] = []
    for house_offset in obstructing_houses:
        house_rashi = rashi_at_distance(target_rashi, house_offset - 1)
        obstructing.extend(get_planets_in_rashi(planet_states, house_rashi))

    return ArgalaResult(
        target_rashi=target_rashi,
        intervening_planets=tuple(intervening),
        obstructing_planets=tuple(obstructing),
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _month_to_iso(months_from_epoch: int) -> str:
    """Convert a month offset from the reference epoch to an ISO-UTC string.

    Reference epoch: 2000-01-01T00:00:00Z.
    """
    year = 2000 + months_from_epoch // 12
    month = 1 + months_from_epoch % 12
    return f"{year:04d}-{month:02d}-01T00:00:00Z"


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

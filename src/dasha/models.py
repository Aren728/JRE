"""JRE-010 Dasha models (core data structures and Vimshottari constants).

JRE-010 defines a deterministic Dasha (planetary period) computation engine.
It produces a hierarchical timeline of Mahadasha → Antardasha → Pratyantardasha
periods from the Moon's natal Nakshatra/Pada, without predictive interpretation.

Core Models:
- ``DashaSystem``: enum of supported Dasha systems (V1: VIMSHOTTARI only)
- ``DashaPeriod``: one period with start/end UTC and lord hierarchy
- ``DashaTimeline``: the full hierarchical timeline
- ``DashaConfig``: immutable configuration
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, NakshatraId, Pada, PlanetState

from .errors import InvalidDashaConfigError

#: Pinned package version.
DASHA_VERSION = "0.1.0"

#: Vimshottari total cycle length in years.
VIMSHOTTARI_CYCLE_YEARS: int = 120

#: Nakshatra span in degrees (360 / 27).
NAKSHATRA_SPAN_DEG: float = 360.0 / 27.0  # 13.333...


# --------------------------------------------------------------------------- #
# Vimshottari constants
# --------------------------------------------------------------------------- #

#: Canonical Vimshottari period order (starting from KETU).
VIMSHOTTARI_ORDER: tuple[BodyId, ...] = (
    BodyId.KETU,
    BodyId.VENUS,
    BodyId.SUN,
    BodyId.MOON,
    BodyId.MARS,
    BodyId.RAHU,
    BodyId.JUPITER,
    BodyId.SATURN,
    BodyId.MERCURY,
)

#: Vimshottari period lengths keyed by BodyId (years).
VIMSHOTTARI_YEARS: dict[BodyId, int] = {
    BodyId.KETU: 7,
    BodyId.VENUS: 20,
    BodyId.SUN: 6,
    BodyId.MOON: 10,
    BodyId.MARS: 7,
    BodyId.RAHU: 18,
    BodyId.JUPITER: 16,
    BodyId.SATURN: 19,
    BodyId.MERCURY: 17,
}

assert sum(VIMSHOTTARI_YEARS.values()) == VIMSHOTTARI_CYCLE_YEARS, (
    f"Vimshottari years must sum to {VIMSHOTTARI_CYCLE_YEARS}, "
    f"got {sum(VIMSHOTTARI_YEARS.values())}"
)

#: Mapping from NakshatraId to its Vimshottari lord (BodyId).
NAKSHATRA_LORDS: dict[NakshatraId, BodyId] = {
    NakshatraId.ASHWINI: BodyId.KETU,
    NakshatraId.BHARANI: BodyId.VENUS,
    NakshatraId.KRITTIKA: BodyId.SUN,
    NakshatraId.ROHINI: BodyId.MOON,
    NakshatraId.MRIGASHIRA: BodyId.MARS,
    NakshatraId.ARDRA: BodyId.RAHU,
    NakshatraId.PUNARVASU: BodyId.JUPITER,
    NakshatraId.PUSHYA: BodyId.SATURN,
    NakshatraId.ASHLESHA: BodyId.MERCURY,
    NakshatraId.MAGHA: BodyId.KETU,
    NakshatraId.PURVA_PHALGUNI: BodyId.VENUS,
    NakshatraId.UTTARA_PHALGUNI: BodyId.SUN,
    NakshatraId.HASTA: BodyId.MOON,
    NakshatraId.CHITRA: BodyId.MARS,
    NakshatraId.SWATI: BodyId.RAHU,
    NakshatraId.VISHAKHA: BodyId.JUPITER,
    NakshatraId.ANURADHA: BodyId.SATURN,
    NakshatraId.JYESHTHA: BodyId.MERCURY,
    NakshatraId.MULA: BodyId.KETU,
    NakshatraId.PURVA_ASHADHA: BodyId.VENUS,
    NakshatraId.UTTARA_ASHADHA: BodyId.SUN,
    NakshatraId.SHRAVANA: BodyId.MOON,
    NakshatraId.DHANISHTHA: BodyId.MARS,
    NakshatraId.SHATABHISHA: BodyId.RAHU,
    NakshatraId.PURVA_BHADRAPADA: BodyId.JUPITER,
    NakshatraId.UTTARA_BHADRAPADA: BodyId.SATURN,
    NakshatraId.REVATI: BodyId.MERCURY,
}

assert len(NAKSHATRA_LORDS) == 27, "Every NakshatraId must have a Vimshottari lord"


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class DashaSystem(StrEnum):
    """Supported Dasha systems (V1: VIMSHOTTARI only)."""

    VIMSHOTTARI = "VIMSHOTTARI"


# --------------------------------------------------------------------------- #
# Pure derivation helpers (public, unit-testable)
# --------------------------------------------------------------------------- #


def _vismottari_lord_index(lord: BodyId) -> int:
    """Return the index of *lord* in ``VIMSHOTTARI_ORDER``."""
    return VIMSHOTTARI_ORDER.index(lord)


def compute_balance_at_birth(
    nakshatra: NakshatraId,
    pada: Pada,
    degree_in_nakshatra: float,
) -> float:
    """Compute the Vimshottari balance at birth in years.

    The balance is the *remaining* portion of the Moon's nakshatra lord's
    Vimshottari period, given the Moon's exact degree within the nakshatra.

    Each nakshatra spans ``NAKSHATRA_SPAN_DEG`` degrees.  The Moon's
    ``degree_in_nakshatra`` is in [0, NAKSHATRA_SPAN_DEG).  Within a
    nakshatra there are 4 padas of equal span.

    The elapsed fraction of the nakshatra is:
        ``(pada - 1) / 4  +  degree_in_nakshatra_within_pada / pada_span``

    The balance is:
        ``lord_years * (1 - elapsed_fraction)``
    """
    lord = NAKSHATRA_LORDS[nakshatra]
    lord_years = VIMSHOTTARI_YEARS[lord]

    pada_span = NAKSHATRA_SPAN_DEG / 4.0
    pada_start = (int(pada) - 1) * pada_span
    degree_within_pada = degree_in_nakshatra - pada_start

    # Clamp to [0, pada_span) for safety
    degree_within_pada = max(0.0, min(degree_within_pada, pada_span))

    elapsed_fraction = ((int(pada) - 1) + degree_within_pada / pada_span) / 4.0
    # Clamp to [0, 1)
    elapsed_fraction = max(0.0, min(elapsed_fraction, 1.0 - 1e-15))

    return lord_years * (1.0 - elapsed_fraction)


def compute_balance_at_birth_from_state(moon_state: PlanetState) -> float:
    """Compute the Vimshottari balance at birth from a Moon ``PlanetState``."""
    return compute_balance_at_birth(
        nakshatra=moon_state.nakshatra,
        pada=moon_state.pada,
        degree_in_nakshatra=moon_state.degree_in_nakshatra,
    )


def _next_lord(lord: BodyId) -> BodyId:
    """Return the next Vimshottari lord in cycle order."""
    idx = _vismottari_lord_index(lord)
    return VIMSHOTTARI_ORDER[(idx + 1) % len(VIMSHOTTARI_ORDER)]


def _antardasha_duration(mahadasha_lord: BodyId, antardasha_lord: BodyId) -> float:
    """Compute the duration in years of an Antardasha within a Mahadasha.

    Formula: ``mahadasha_years * antardasha_years / VIMSHOTTARI_CYCLE_YEARS``
    """
    return (
        VIMSHOTTARI_YEARS[mahadasha_lord]
        * VIMSHOTTARI_YEARS[antardasha_lord]
        / VIMSHOTTARI_CYCLE_YEARS
    )


def _pratyantardasha_duration(
    mahadasha_lord: BodyId,
    antardasha_lord: BodyId,
    pratyantardasha_lord: BodyId,
) -> float:
    """Compute the duration in years of a Pratyantardasha.

    Formula: ``antardasha_duration * pratyantardasha_years / VIMSHOTTARI_CYCLE_YEARS``
    """
    adasha_years = _antardasha_duration(mahadasha_lord, antardasha_lord)
    return adasha_years * VIMSHOTTARI_YEARS[pratyantardasha_lord] / VIMSHOTTARI_CYCLE_YEARS


def compute_antardasha_order(mahadasha_lord: BodyId) -> tuple[BodyId, ...]:
    """Return the Antardasha lords in order starting from *mahadasha_lord*.

    The Antardasha sequence starts from the Mahadasha lord and cycles
    through all 9 Vimshottari planets in order.
    """
    start_idx = _vismottari_lord_index(mahadasha_lord)
    return tuple(
        VIMSHOTTARI_ORDER[(start_idx + i) % len(VIMSHOTTARI_ORDER)]
        for i in range(len(VIMSHOTTARI_ORDER))
    )


def compute_pratyantardasha_order(antardasha_lord: BodyId) -> tuple[BodyId, ...]:
    """Return the Pratyantardasha lords in order starting from *antardasha_lord*."""
    return compute_antardasha_order(antardasha_lord)


# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DashaConfig:
    """Immutable JRE-010 configuration.  TOML is authoritative; every default
    is declared in ``config/dasha.toml`` (no hidden defaults).
    """

    version: str = DASHA_VERSION
    default_system: DashaSystem = DashaSystem.VIMSHOTTARI
    max_depth: int = 3
    vimshottari_years: dict[str, int] = field(
        default_factory=lambda: {k.value: v for k, v in VIMSHOTTARI_YEARS.items()}
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DashaConfig:
        version = data.get("version", DASHA_VERSION)
        system_raw = data.get("default_system", DashaSystem.VIMSHOTTARI.value)
        max_depth = int(data.get("max_depth", 3))
        vy_raw = data.get("vimshottari_years")
        vy: dict[str, int]
        if vy_raw is not None and isinstance(vy_raw, dict):
            vy = {str(k): int(v) for k, v in vy_raw.items()}
        else:
            vy = {k.value: v for k, v in VIMSHOTTARI_YEARS.items()}
        return cls(
            version=str(version),
            default_system=DashaSystem(system_raw),
            max_depth=max_depth,
            vimshottari_years=vy,
        )


def validate(config: DashaConfig) -> DashaConfig:
    """Validate a ``DashaConfig``; raises ``InvalidDashaConfigError``."""
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidDashaConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    if not isinstance(config.default_system, DashaSystem):
        raise InvalidDashaConfigError(
            f"unknown default_system value {config.default_system!r}"
        )
    if not isinstance(config.max_depth, int) or config.max_depth < 1 or config.max_depth > 3:
        raise InvalidDashaConfigError(
            f"max_depth must be 1, 2, or 3, got {config.max_depth}"
        )
    if not isinstance(config.vimshottari_years, dict) or not config.vimshottari_years:
        raise InvalidDashaConfigError(
            f"vimshottari_years must be a non-empty dict, got {config.vimshottari_years!r}"
        )
    total = sum(config.vimshottari_years.values())
    if total != VIMSHOTTARI_CYCLE_YEARS:
        raise InvalidDashaConfigError(
            f"vimshottari_years must sum to {VIMSHOTTARI_CYCLE_YEARS}, got {total}"
        )
    return config


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class DashaPeriod:
    """One period in the Dasha hierarchy.

    ``mahadasha_lord`` is always set.  ``antardasha_lord`` is set when
    ``depth >= 2``.  ``pratyantardasha_lord`` is set when ``depth == 3``.
    """

    start_utc: datetime
    end_utc: datetime
    mahadasha_lord: BodyId
    antardasha_lord: BodyId | None = None
    pratyantardasha_lord: BodyId | None = None

    @property
    def duration(self) -> timedelta:
        """Duration of this period."""
        return self.end_utc - self.start_utc

    @property
    def depth(self) -> int:
        """Hierarchy depth (1 = Mahadasha, 2 = Antardasha, 3 = Pratyantardasha)."""
        if self.pratyantardasha_lord is not None:
            return 3
        if self.antardasha_lord is not None:
            return 2
        return 1

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class DashaTimeline:
    """The full hierarchical Dasha timeline computed for a birth chart.

    ``periods`` contains the most granular periods (Pratyantardasha at
    depth=3, Antardasha at depth=2, or Mahadasha at depth=1).
    """

    birth_nakshatra: NakshatraId
    birth_pada: Pada
    balance_at_birth: float  # years remaining in first Mahadasha
    system: DashaSystem
    periods: tuple[DashaPeriod, ...]

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


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
    if isinstance(model, datetime):
        return model.isoformat()
    if isinstance(model, timedelta):
        return model.total_seconds()
    if isinstance(model, float):
        return 0.0 if model == 0.0 else model  # -0.0 -> 0.0
    return model


def to_dict_value(model: Any) -> Any:
    """Public wrapper around the generic dataclass serializer."""
    return _model_to_dict(model)

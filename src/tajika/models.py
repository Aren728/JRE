"""JRE-017 Tajika (Varshaphala / annual chart) models — core data structures.

JRE-017 computes the Muntha, Varsheshwar, and classical Sahams for
a given Solar Return chart, strictly as structural data points without
predictive interpretation.

Core Models:
- ``MunthaResult``: rashi, house, lord
- ``VarsheshwarResult``: planet, basis
- ``SahamResult``: saham_name, rashi, degree
- ``TajikaReport``: muntha, varsheshwar, sahams
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, RashiId

#: Pinned package version.
TAJIKA_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #


class VarsheshwarBasis(StrEnum):
    """Basis for determining the Varsheshwar (Lord of the Year)."""

    LORD_OF_YEAR = "LORD_OF_YEAR"
    LORD_OF_MUNTHA = "LORD_OF_MUNTHA"
    LORD_OF_LAGNA = "LORD_OF_LAGNA"


class SahamType(StrEnum):
    """Classical Saham types with their standard formulas.

    Each Saham is computed as: Lagna + PlanetA - PlanetB (mod 360).
    """

    PUNYA = "PUNYA"          # Lagna + Jupiter - Sun
    VIDYA = "VIDYA"          # Lagna + Jupiter - Moon
    ARTHA = "ARTHA"          # Lagna + Jupiter - Mars
    KARMA = "KARMA"          # Lagna + Jupiter - Mercury
    PUTRA = "PUTRA"          # Lagna + Jupiter - Jupiter
    GNA = "GNA"              # Lagna + Jupiter - Venus
    SAMPAT = "SAMPAT"        # Lagna + Jupiter - Saturn
    RAJA = "RAJA"            # Lagna + Sun - Moon
    DEHA = "DEHA"            # Lagna + Sun - Mars
    JEEVA = "JEEVA"          # Lagna + Moon - Sun


# --------------------------------------------------------------------------- #
# Classical Saham formulas: (planet_a, planet_b)
# Saham longitude = (lagna + planet_a - planet_b) mod 360
# --------------------------------------------------------------------------- #

SAHAM_FORMULAS: dict[SahamType, tuple[BodyId, BodyId]] = {
    SahamType.PUNYA:  (BodyId.JUPITER, BodyId.SUN),
    SahamType.VIDYA:  (BodyId.JUPITER, BodyId.MOON),
    SahamType.ARTHA:  (BodyId.JUPITER, BodyId.MARS),
    SahamType.KARMA:  (BodyId.JUPITER, BodyId.MERCURY),
    SahamType.PUTRA:  (BodyId.JUPITER, BodyId.JUPITER),
    SahamType.GNA:    (BodyId.JUPITER, BodyId.VENUS),
    SahamType.SAMPAT: (BodyId.JUPITER, BodyId.SATURN),
    SahamType.RAJA:   (BodyId.SUN, BodyId.MOON),
    SahamType.DEHA:   (BodyId.SUN, BodyId.MARS),
    SahamType.JEEVA:  (BodyId.MOON, BodyId.SUN),
}

# --------------------------------------------------------------------------- #
# Classical Varsheshwar hierarchy rules
# --------------------------------------------------------------------------- #

# Benefic planets that qualify as Varsheshwar when Muntha lord
CLASSICAL_BENEFICS: frozenset[BodyId] = frozenset({
    BodyId.JUPITER, BodyId.VENUS, BodyId.MOON, BodyId.MERCURY,
})


# --------------------------------------------------------------------------- #
# Rashi lords (classical Vimshottari-style for each rashi)
# --------------------------------------------------------------------------- #

RASHI_LORDS: dict[RashiId, BodyId] = {
    RashiId.MESHA:      BodyId.MARS,
    RashiId.VRISHABHA:  BodyId.VENUS,
    RashiId.MITHUNA:    BodyId.MERCURY,
    RashiId.KARKA:      BodyId.MOON,
    RashiId.SIMHA:      BodyId.SUN,
    RashiId.KANYA:      BodyId.MERCURY,
    RashiId.TULA:       BodyId.VENUS,
    RashiId.VRISHCHIKA: BodyId.MARS,
    RashiId.DHANUSHA:   BodyId.JUPITER,
    RashiId.MAKARA:     BodyId.SATURN,
    RashiId.KUMBHA:     BodyId.SATURN,
    RashiId.MEENA:      BodyId.JUPITER,
}


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class MunthaResult:
    """Muntha position in the annual chart."""

    rashi: RashiId
    house: int  # 1-12, house number from Lagna
    lord: BodyId

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class VarsheshwarResult:
    """Varsheshwar (Lord of the Year) determination."""

    planet: BodyId
    basis: VarsheshwarBasis

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class SahamResult:
    """One Saham (longitudinal point) in the annual chart."""

    saham_name: SahamType
    rashi: RashiId
    degree: float  # degree within rashi [0, 30)

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class TajikaReport:
    """Complete Tajika (Varshaphala) report."""

    muntha: MunthaResult
    varsheshwar: VarsheshwarResult
    sahams: tuple[SahamResult, ...]
    version: str = TAJIKA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def saham_for(self, saham_type: SahamType) -> SahamResult | None:
        """Return the result for a specific Saham, or None."""
        for s in self.sahams:
            if s.saham_name == saham_type:
                return s
        return None


@dataclass(frozen=True)
class TajikaConfig:
    """Immutable JRE-017 configuration."""

    version: str = TAJIKA_VERSION
    enabled_sahams: tuple[SahamType, ...] = tuple(SahamType)

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #


def compute_muntha_rashi(
    natal_moon_rashi: RashiId,
    elapsed_years: int,
) -> RashiId:
    """Compute the Muntha rashi after a given number of elapsed years.

    The Muntha starts at the natal Moon's rashi at birth and progresses
    one rashi per year. After 12 years, it returns to the natal Moon's rashi.

    Parameters
    ----------
    natal_moon_rashi : RashiId
        The Moon's rashi at birth.
    elapsed_years : int
        Number of completed years since birth.

    Returns
    -------
    RashiId
        The Muntha rashi for the given year.
    """
    if elapsed_years < 0:
        raise ValueError("elapsed_years must be non-negative")
    rashi_list = list(RashiId)
    natal_idx = rashi_list.index(natal_moon_rashi)
    muntha_idx = (natal_idx + elapsed_years) % 12
    return rashi_list[muntha_idx]


def compute_muntha_lord(
    muntha_rashi: RashiId,
) -> BodyId:
    """Return the classical lord of a rashi."""
    return RASHI_LORDS[muntha_rashi]


def compute_varsheshwar(
    muntha_lord: BodyId,
    year_lord: BodyId,
    lagna_lord: BodyId,
) -> VarsheshwarResult:
    """Determine the Varsheshwar based on classical hierarchy.

    The hierarchy is:
    1. If Muntha lord is a benefic → Muntha lord is Varsheshwar
    2. Otherwise → Year lord is Varsheshwar
    3. If Year lord is also not a benefic → Lagna lord is Varsheshwar

    Parameters
    ----------
    muntha_lord : BodyId
        Lord of the Muntha rashi.
    year_lord : BodyId
        Lord of the year (Vimshottari from natal Moon).
    lagna_lord : BodyId
        Lord of the Lagna (ascendant).

    Returns
    -------
    VarsheshwarResult
        The determined Varsheshwar with its basis.
    """
    if muntha_lord in CLASSICAL_BENEFICS:
        return VarsheshwarResult(
            planet=muntha_lord,
            basis=VarsheshwarBasis.LORD_OF_MUNTHA,
        )
    if year_lord in CLASSICAL_BENEFICS:
        return VarsheshwarResult(
            planet=year_lord,
            basis=VarsheshwarBasis.LORD_OF_YEAR,
        )
    return VarsheshwarResult(
        planet=lagna_lord,
        basis=VarsheshwarBasis.LORD_OF_LAGNA,
    )


def compute_saham_longitude(
    lagna_longitude: float,
    planet_a_longitude: float,
    planet_b_longitude: float,
) -> float:
    """Compute a Saham longitude using the classical formula.

    Saham = (Lagna + PlanetA - PlanetB) mod 360

    Parameters
    ----------
    lagna_longitude : float
        Longitude of the Lagna in degrees.
    planet_a_longitude : float
        Longitude of the first planet in the formula.
    planet_b_longitude : float
        Longitude of the second planet in the formula.

    Returns
    -------
    float
        Saham longitude in degrees [0, 360).
    """
    return (lagna_longitude + planet_a_longitude - planet_b_longitude) % 360.0


def longitude_to_rashi(longitude: float) -> RashiId:
    """Convert a longitude in degrees to its RashiId."""
    rashi_list = list(RashiId)
    idx = int(longitude / 30.0) % 12
    return rashi_list[idx]


def longitude_to_degree_in_rashi(longitude: float) -> float:
    """Extract the degree within a rashi [0, 30) from a longitude."""
    return longitude % 30.0


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

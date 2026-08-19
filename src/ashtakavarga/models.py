"""JRE-016 Ashtakavarga (eight-fold strength) models — core data structures.

JRE-016 computes the Bhinnashtakavarga (individual planet points) and
Sarvashtakavarga (total points) for all 12 Rashis, strictly without
predictive interpretation.

Core Models:
- ``PlanetAshtakavarga``: per-planet bindu scores for each rashi
- ``Sarvashtakavarga``: total bindu scores for each rashi
- ``AshtakavargaReport``: complete report for all computed planets
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Any, cast

from jyotish import BodyId

#: Pinned package version.
ASHTAKAVARGA_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Classical bindu rules — which houses (from the planet's own rashi) receive
# 4 bindus from each planet.  1-indexed house positions.
# --------------------------------------------------------------------------- #

CLASSICAL_BINDU_RULES: dict[BodyId, tuple[int, ...]] = {
    BodyId.SUN:     (1, 2, 4, 7, 8, 9, 10, 11),
    BodyId.MOON:    (1, 3, 6, 7, 8, 10, 11, 12),
    BodyId.MARS:    (1, 2, 4, 7, 8, 10, 11),
    BodyId.MERCURY: (1, 2, 4, 6, 8, 9, 10, 11),
    BodyId.JUPITER: (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11),
    BodyId.VENUS:   (1, 2, 3, 4, 5, 7, 8, 9, 10, 11),
    BodyId.SATURN:  (1, 3, 4, 5, 6, 7, 8, 9, 10, 11),
}

#: Each contributing house receives this many bindus.
BINDUS_PER_CONTRIBUTION: int = 4

# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class PlanetAshtakavarga:
    """One planet's bindu scores for each rashi (Mesha=0 .. Meena=11)."""

    planet: BodyId
    bindus: tuple[int, ...]  # length 12

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class Sarvashtakavarga:
    """Total bindu scores for each rashi (Mesha=0 .. Meena=11)."""

    bindus: tuple[int, ...]  # length 12

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class AshtakavargaReport:
    """Complete Ashtakavarga report for all computed planets."""

    bhinnashtakavarga: tuple[PlanetAshtakavarga, ...]
    sarvashtakavarga: Sarvashtakavarga
    version: str = ASHTAKAVARGA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def result_for(self, planet: BodyId) -> PlanetAshtakavarga | None:
        """Return the result for a specific planet, or None."""
        for r in self.bhinnashtakavarga:
            if r.planet == planet:
                return r
        return None


@dataclass(frozen=True)
class AshtakavargaConfig:
    """Immutable JRE-016 configuration."""

    version: str = ASHTAKAVARGA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #


def compute_planet_bindus(
    planet: BodyId,
    planet_rashi_idx: int,
) -> tuple[int, ...]:
    """Compute bindu scores for one planet across all 12 rashis.

    Parameters
    ----------
    planet : BodyId
        The contributing planet.
    planet_rashi_idx : int
        0-based index of the planet's rashi (Mesha=0, ..., Meena=11).

    Returns
    -------
    tuple of 12 ints
        Bindu count for each rashi (Mesha=0 .. Meena=11).
    """
    rules = CLASSICAL_BINDU_RULES.get(planet, ())
    bindus = [0] * 12
    for house_from_planet in rules:
        target_idx = (planet_rashi_idx + house_from_planet - 1) % 12
        bindus[target_idx] += BINDUS_PER_CONTRIBUTION
    return tuple(bindus)


def compute_sarvashtakavarga(
    planet_scores: tuple[PlanetAshtakavarga, ...],
) -> Sarvashtakavarga:
    """Sum all planet bindus to produce the Sarvashtakavarga."""
    totals = [0] * 12
    for pa in planet_scores:
        for i in range(12):
            totals[i] += pa.bindus[i]
    return Sarvashtakavarga(bindus=tuple(totals))


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

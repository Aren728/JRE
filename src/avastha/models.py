"""JRE-015 Avastha (Planetary States) models — core data structures.

JRE-015 assigns classical states to planets based on their position:
- Jagradadi: awake/dream/deep-sleep based on degree within rashi
- Deeptadi: exalted/own/friendly/neutral/enemy/debilitated based on rashi
- Baladi: infant/youth/adult/old/dead based on varga placement (optional)

It performs NO predictive interpretation.

Core Models:
- ``JagradadiState``: JAGRAT, SWAPNA, SUSHUPTI
- ``DeeptadiState``: DEEPTA, SWASTHA, PRASANTA, DEENA, KSHUDHITA, KSHOBHITA
- ``BaladiState``: BALA, KUMARA, YUVA, VRIDDHA, MRITA
- ``AvasthaResult``: per-planet state result with multiplier
- ``AvasthaReport``: complete report for all computed planets
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, RashiId

from .errors import InvalidAvasthaConfigError

#: Pinned package version.
AVASTHA_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class JagradadiState(StrEnum):
    """Awake/Dream/Deep-Sleep states based on degree within rashi."""

    JAGRAT = "JAGRAT"       # Awake (0-6 degrees)
    SWAPNA = "SWAPNA"       # Dream (6-18 degrees)
    SUSHUPTI = "SUSHUPTI"   # Deep Sleep (18-30 degrees)


class DeeptadiState(StrEnum):
    """Exaltation-based dignity states."""

    DEEPTA = "DEEPTA"           # Exalted
    SWASTHA = "SWASTHA"         # Own sign
    PRASANTA = "PRASANTA"       # Friendly sign
    DEENA = "DEENA"             # Neutral sign
    KSHUDHITA = "KSHUDHITA"     # Enemy sign
    KSHOBHITA = "KSHOBHITA"     # Debilitated sign


class BaladiState(StrEnum):
    """Age-based states from varga placements."""

    BALA = "BALA"           # Infant (D-1)
    KUMARA = "KUMARA"       # Youth (D-7)
    YUVA = "YUVA"           # Adult (D-9)
    VRIDDHA = "VRIDDHA"     # Old (D-12)
    MRITA = "MRITA"         # Dead (D-16 or D-30)


# --------------------------------------------------------------------------- #
# Default degree ranges for Jagradadi
# --------------------------------------------------------------------------- #

DEFAULT_JAGRAT_RANGE: tuple[float, float] = (0.0, 6.0)
DEFAULT_SWAPNA_RANGE: tuple[float, float] = (6.0, 18.0)
DEFAULT_SUSHUPTI_RANGE: tuple[float, float] = (18.0, 30.0)

# --------------------------------------------------------------------------- #
# Default multipliers
# --------------------------------------------------------------------------- #

DEFAULT_JAGRADI_MULTIPLIERS: dict[JagradadiState, float] = {
    JagradadiState.JAGRAT: 1.0,
    JagradadiState.SWAPNA: 0.75,
    JagradadiState.SUSHUPTI: 0.5,
}

DEFAULT_DEEPTADI_MULTIPLIERS: dict[DeeptadiState, float] = {
    DeeptadiState.DEEPTA: 1.0,
    DeeptadiState.SWASTHA: 0.875,
    DeeptadiState.PRASANTA: 0.75,
    DeeptadiState.DEENA: 0.5,
    DeeptadiState.KSHUDHITA: 0.375,
    DeeptadiState.KSHOBHITA: 0.25,
}

# --------------------------------------------------------------------------- #
# Default dignity mappings
# --------------------------------------------------------------------------- #

DEFAULT_EXALTATION_SIGNS: dict[BodyId, RashiId] = {
    BodyId.SUN: RashiId.MESHA,
    BodyId.MOON: RashiId.VRISHABHA,
    BodyId.MARS: RashiId.MAKARA,
    BodyId.MERCURY: RashiId.KANYA,
    BodyId.JUPITER: RashiId.KARKA,
    BodyId.VENUS: RashiId.MEENA,
    BodyId.SATURN: RashiId.TULA,
}

DEFAULT_DEBILITATION_SIGNS: dict[BodyId, RashiId] = {
    BodyId.SUN: RashiId.TULA,
    BodyId.MOON: RashiId.VRISHCHIKA,
    BodyId.MARS: RashiId.KARKA,
    BodyId.MERCURY: RashiId.MEENA,
    BodyId.JUPITER: RashiId.MAKARA,
    BodyId.VENUS: RashiId.KANYA,
    BodyId.SATURN: RashiId.MESHA,
}

DEFAULT_OWN_SIGNS: dict[BodyId, tuple[RashiId, ...]] = {
    BodyId.SUN: (RashiId.SIMHA,),
    BodyId.MOON: (RashiId.KARKA,),
    BodyId.MARS: (RashiId.MESHA, RashiId.VRISHCHIKA),
    BodyId.MERCURY: (RashiId.MITHUNA, RashiId.KANYA),
    BodyId.JUPITER: (RashiId.DHANUSHA, RashiId.MEENA),
    BodyId.VENUS: (RashiId.VRISHABHA, RashiId.TULA),
    BodyId.SATURN: (RashiId.MAKARA, RashiId.KUMBHA),
}

DEFAULT_FRIENDLY_SIGNS: dict[BodyId, tuple[RashiId, ...]] = {
    BodyId.SUN: (RashiId.MESHA, RashiId.VRISHABHA, RashiId.DHANUSHA),
    BodyId.MOON: (RashiId.MESHA, RashiId.VRISHABHA),
    BodyId.MARS: (RashiId.MESHA, RashiId.VRISHABHA, RashiId.DHANUSHA),
    BodyId.MERCURY: (RashiId.VRISHABHA, RashiId.KANYA),
    BodyId.JUPITER: (RashiId.MESHA, RashiId.VRISHABHA, RashiId.KARKA),
    BodyId.VENUS: (RashiId.MITHUNA, RashiId.KANYA),
    BodyId.SATURN: (RashiId.MITHUNA, RashiId.KANYA),
}

DEFAULT_ENEMY_SIGNS: dict[BodyId, tuple[RashiId, ...]] = {
    BodyId.SUN: (RashiId.TULA, RashiId.VRISHABHA),
    BodyId.MOON: (RashiId.TULA,),
    BodyId.MARS: (RashiId.TULA, RashiId.KARKA),
    BodyId.MERCURY: (RashiId.KARKA, RashiId.SIMHA),
    BodyId.JUPITER: (RashiId.MITHUNA, RashiId.KANYA),
    BodyId.VENUS: (RashiId.MESHA, RashiId.VRISHCHIKA),
    BodyId.SATURN: (RashiId.MESHA, RashiId.VRISHABHA),
}

# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class AvasthaResult:
    """One planet's Avastha computation result."""

    planet: BodyId
    jagradadi: JagradadiState
    deeptadi: DeeptadiState
    baladi: BaladiState | None
    multiplier: float

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class AvasthaReport:
    """Complete Avastha report for all computed planets."""

    results: tuple[AvasthaResult, ...]
    version: str = AVASTHA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def result_for(self, planet: BodyId) -> AvasthaResult | None:
        """Return the result for a specific planet, or None."""
        for r in self.results:
            if r.planet == planet:
                return r
        return None


@dataclass(frozen=True)
class AvasthaConfig:
    """Immutable JRE-015 configuration.  TOML is authoritative; every
    default is declared in ``config/avastha.toml`` (no hidden defaults).
    """

    version: str = AVASTHA_VERSION
    jagradadi_multipliers: dict[str, float] = field(
        default_factory=lambda: {k.value: v for k, v in DEFAULT_JAGRADI_MULTIPLIERS.items()}
    )
    deeptadi_multipliers: dict[str, float] = field(
        default_factory=lambda: {k.value: v for k, v in DEFAULT_DEEPTADI_MULTIPLIERS.items()}
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AvasthaConfig:
        version = data.get("version", AVASTHA_VERSION)
        jag_raw = data.get("jagradadi_multipliers")
        jag: dict[str, float]
        if isinstance(jag_raw, dict) and jag_raw:
            jag = {str(k): float(v) for k, v in jag_raw.items()}
        else:
            jag = {k.value: v for k, v in DEFAULT_JAGRADI_MULTIPLIERS.items()}
        deep_raw = data.get("deeptadi_multipliers")
        deep: dict[str, float]
        if isinstance(deep_raw, dict) and deep_raw:
            deep = {str(k): float(v) for k, v in deep_raw.items()}
        else:
            deep = {k.value: v for k, v in DEFAULT_DEEPTADI_MULTIPLIERS.items()}
        return cls(
            version=str(version),
            jagradadi_multipliers=jag,
            deeptadi_multipliers=deep,
        )


def validate(config: AvasthaConfig) -> AvasthaConfig:
    """Validate an ``AvasthaConfig``; raises ``InvalidAvasthaConfigError``."""
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidAvasthaConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    if not isinstance(config.jagradadi_multipliers, dict) or not config.jagradadi_multipliers:
        raise InvalidAvasthaConfigError(
            f"jagradadi_multipliers must be a non-empty dict, "
            f"got {config.jagradadi_multipliers!r}"
        )
    if not isinstance(config.deeptadi_multipliers, dict) or not config.deeptadi_multipliers:
        raise InvalidAvasthaConfigError(
            f"deeptadi_multipliers must be a non-empty dict, "
            f"got {config.deeptadi_multipliers!r}"
        )
    return config


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #

def compute_jagradadi(degree_in_rashi: float) -> JagradadiState:
    """Determine Jagradadi state from degree within rashi (0-30)."""
    deg = degree_in_rashi % 30.0
    if deg < DEFAULT_JAGRAT_RANGE[1]:
        return JagradadiState.JAGRAT
    if deg < DEFAULT_SWAPNA_RANGE[1]:
        return JagradadiState.SWAPNA
    return JagradadiState.SUSHUPTI


def compute_deeptadi(
    planet: BodyId,
    rashi: RashiId,
) -> DeeptadiState:
    """Determine Deeptadi state from planet and its rashi placement."""
    if rashi == DEFAULT_EXALTATION_SIGNS.get(planet):
        return DeeptadiState.DEEPTA
    if rashi == DEFAULT_DEBILITATION_SIGNS.get(planet):
        return DeeptadiState.KSHOBHITA
    if rashi in DEFAULT_OWN_SIGNS.get(planet, ()):
        return DeeptadiState.SWASTHA
    if rashi in DEFAULT_FRIENDLY_SIGNS.get(planet, ()):
        return DeeptadiState.PRASANTA
    if rashi in DEFAULT_ENEMY_SIGNS.get(planet, ()):
        return DeeptadiState.KSHUDHITA
    return DeeptadiState.DEENA


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

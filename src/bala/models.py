"""JRE-011 Bala (Shadbala) models — core data structures and constants.

JRE-011 computes the Shadbala (six-fold planetary strength) from
positional, temporal, directional, motional, natural, and aspectual
factors.  It produces deterministic numerical strength values without
any predictive interpretation.

Core Models:
- ``BalaConfig``: immutable configuration with minimum requirements
- ``ShadbalaComponents``: the six balas and their sub-components
- ``IshtaKashtaPhala``: ishta/kashta phala values
- ``ShadbalaResult``: per-planet strength result
- ``ShadbalaReport``: full report for all classical planets + Rahu/Ketu
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId

from .errors import InvalidBalaConfigError

#: Pinned package version.
BALA_VERSION = "0.1.0"

#: Virupas per Rupa.
VIRUPAS_PER_RUPA: int = 60

#: The seven classical planets + Rahu/Ketu (all 9 Vimshottari planets).
BALA_PLANETS: tuple[BodyId, ...] = (
    BodyId.SUN,
    BodyId.MOON,
    BodyId.MARS,
    BodyId.MERCURY,
    BodyId.JUPITER,
    BodyId.VENUS,
    BodyId.SATURN,
    BodyId.RAHU,
    BodyId.KETU,
)


# --------------------------------------------------------------------------- #
# Exaltation / Debilitation longitudes (sidereal degrees from 0° Aries)
# --------------------------------------------------------------------------- #

EXALTATION_DEGREES: dict[BodyId, float] = {
    BodyId.SUN: 10.0,       # Aries 10°
    BodyId.MOON: 33.0,      # Taurus 3°
    BodyId.MARS: 298.0,     # Capricorn 28°
    BodyId.MERCURY: 165.0,  # Virgo 15°
    BodyId.JUPITER: 95.0,   # Cancer 5°
    BodyId.VENUS: 357.0,    # Pisces 27°
    BodyId.SATURN: 200.0,   # Libra 20°
    BodyId.RAHU: 33.0,      # Taurus 3° (some traditions)
    BodyId.KETU: 213.0,     # Scorpio 3° (some traditions)
}

DEBILITATION_DEGREES: dict[BodyId, float] = {
    BodyId.SUN: 190.0,      # Libra 10°
    BodyId.MOON: 213.0,     # Scorpio 3°
    BodyId.MARS: 118.0,     # Cancer 28°
    BodyId.MERCURY: 345.0,  # Pisces 15°
    BodyId.JUPITER: 275.0,  # Capricorn 5°
    BodyId.VENUS: 177.0,    # Virgo 27°
    BodyId.SATURN: 20.0,    # Aries 20°
    BodyId.RAHU: 213.0,     # Scorpio 3° (some traditions)
    BodyId.KETU: 33.0,      # Taurus 3° (some traditions)
}

# Moolatrikona longitudes — used for Saptavargaja dignity scoring.
# Planet is in moolatrikona when within these degree ranges.
MOOLATRIKONA_RANGES: dict[BodyId, tuple[float, float]] = {
    BodyId.SUN: (13.33, 20.0),      # Leo 13°20' – 20°
    BodyId.MOON: (3.33, 20.0),      # Taurus 3°20' – 20°
    BodyId.MARS: (0.0, 13.33),      # Aries 0° – 13°20'
    BodyId.MERCURY: (15.0, 20.0),   # Virgo 15° – 20°
    BodyId.JUPITER: (0.0, 10.0),    # Sagittarius 0° – 10°
    BodyId.VENUS: (0.0, 15.0),      # Libra 0° – 15°
    BodyId.SATURN: (20.0, 26.67),   # Aquarius 20° – 26°40'
}

# Planet friendships: FRIEND, NEUTRAL, ENEMY
# Key = planet, Value = dict of (other_planet -> relationship)
FRIENDSHIP_MAP: dict[BodyId, dict[BodyId, str]] = {
    BodyId.SUN: {
        BodyId.MOON: "FRIEND",
        BodyId.MARS: "FRIEND",
        BodyId.JUPITER: "FRIEND",
        BodyId.VENUS: "ENEMY",
        BodyId.MERCURY: "ENEMY",
    },
    BodyId.MOON: {
        BodyId.SUN: "FRIEND",
        BodyId.MERCURY: "FRIEND",
    },
    BodyId.MARS: {
        BodyId.SUN: "FRIEND",
        BodyId.MOON: "FRIEND",
        BodyId.JUPITER: "FRIEND",
        BodyId.VENUS: "ENEMY",
        BodyId.SATURN: "ENEMY",
    },
    BodyId.MERCURY: {
        BodyId.SUN: "ENEMY",
        BodyId.VENUS: "FRIEND",
    },
    BodyId.JUPITER: {
        BodyId.SUN: "FRIEND",
        BodyId.MOON: "FRIEND",
        BodyId.MARS: "FRIEND",
        BodyId.MERCURY: "ENEMY",
    },
    BodyId.VENUS: {
        BodyId.MERCURY: "FRIEND",
        BodyId.SATURN: "FRIEND",
        BodyId.MARS: "ENEMY",
        BodyId.JUPITER: "ENEMY",
    },
    BodyId.SATURN: {
        BodyId.MERCURY: "FRIEND",
        BodyId.VENUS: "FRIEND",
        BodyId.JUPITER: "ENEMY",
        BodyId.MARS: "ENEMY",
        BodyId.SUN: "ENEMY",
        BodyId.MOON: "ENEMY",
    },
    BodyId.RAHU: {
        BodyId.VENUS: "FRIEND",
        BodyId.SATURN: "FRIEND",
        BodyId.JUPITER: "ENEMY",
    },
    BodyId.KETU: {
        BodyId.MARS: "FRIEND",
        BodyId.JUPITER: "FRIEND",
        BodyId.VENUS: "ENEMY",
    },
}

# Self is always considered own-sign for dignity purposes.
# Intermediary friendship (friend of friend = friend, enemy of friend = neutral).
_INTERMEDIARY_FRIENDS: dict[BodyId, set[BodyId]] = {}


def _build_intermediary() -> None:
    """Build the intermediary friendship map from the direct map."""
    for planet, friends_map in FRIENDSHIP_MAP.items():
        direct: set[BodyId] = set()
        enemies: set[BodyId] = set()
        for other, rel in friends_map.items():
            if rel == "FRIEND":
                direct.add(other)
            elif rel == "ENEMY":
                enemies.add(other)
        # Friends of friends are intermediary friends
        intermediary: set[BodyId] = set()
        for f in direct:
            for other, rel in FRIENDSHIP_MAP.get(f, {}).items():
                if rel == "FRIEND" and other != planet and other not in enemies:
                    intermediary.add(other)
        _INTERMEDIARY_FRIENDS[planet] = intermediary


_build_intermediary()


def get_dignity(planet: BodyId, sign_lord: BodyId) -> str:
    """Return the dignity relationship of *planet* in a sign owned by *sign_lord*.

    Returns one of: ``"OWN"``, ``"Moolatrikona"``, ``"FRIEND"``,
    ``"NEUTRAL"``, ``"ENEMY"``, ``"DEBILITATED"``.
    """
    if planet == sign_lord:
        return "OWN"
    rel = FRIENDSHIP_MAP.get(planet, {}).get(sign_lord)
    if rel == "FRIEND":
        return "FRIEND"
    if rel == "ENEMY":
        return "ENEMY"
    # Check intermediary friendship
    if sign_lord in _INTERMEDIARY_FRIENDS.get(planet, set()):
        return "FRIEND"
    return "NEUTRAL"


# --------------------------------------------------------------------------- #
# Dignity scoring for Saptavargaja Bala
# --------------------------------------------------------------------------- #

DIGNITY_SCORES: dict[str, int] = {
    "Moolatrikona": 5,
    "OWN": 4,
    "FRIEND": 3,
    "NEUTRAL": 2,
    "ENEMY": 1,
    "DEBILITATED": 0,
}


# --------------------------------------------------------------------------- #
# Natural (Naisargika) Strength default values in Virupas
# --------------------------------------------------------------------------- #

DEFAULT_NAISARGIKA_VIRUPAS: dict[BodyId, float] = {
    BodyId.SUN: 60.0,
    BodyId.MOON: 51.43,
    BodyId.VENUS: 42.86,
    BodyId.MARS: 34.29,
    BodyId.JUPITER: 25.71,
    BodyId.MERCURY: 17.14,
    BodyId.SATURN: 8.57,
    BodyId.RAHU: 4.29,
    BodyId.KETU: 4.29,
}

# --------------------------------------------------------------------------- #
# Dig Bala peak house for each planet
# --------------------------------------------------------------------------- #

# Peak house number (1-indexed) where planet gets maximum Dig Bala.
DIG_BALA_PEAK_HOUSE: dict[BodyId, int] = {
    BodyId.SUN: 10,       # East
    BodyId.MOON: 4,       # West
    BodyId.MARS: 7,       # South
    BodyId.MERCURY: 1,    # North (Ascendant)
    BodyId.JUPITER: 10,   # East
    BodyId.VENUS: 4,      # West
    BodyId.SATURN: 1,     # North
    BodyId.RAHU: 1,       # North
    BodyId.KETU: 7,       # South
}


# --------------------------------------------------------------------------- #
# Vimshottari sign lords (which planet owns which sign, sidereal)
# --------------------------------------------------------------------------- #

# Standard Vimshottari sign ownership (1-indexed rashi):1=Aries..12=Pisces
SIGN_LORDS_VIMSHOTTARI: dict[int, BodyId] = {
    1: BodyId.MARS,      # Aries
    2: BodyId.VENUS,     # Taurus
    3: BodyId.MERCURY,   # Gemini
    4: BodyId.MOON,      # Cancer
    5: BodyId.SUN,       # Leo
    6: BodyId.MERCURY,   # Virgo
    7: BodyId.VENUS,     # Libra
    8: BodyId.MARS,      # Scorpio (traditional; some say Ketu)
    9: BodyId.JUPITER,   # Sagittarius
    10: BodyId.SATURN,    # Capricorn
    11: BodyId.SATURN,    # Aquarius
    12: BodyId.JUPITER,   # Pisces
}


# --------------------------------------------------------------------------- #
# Kendra / Panaphara / Apoklima house classification
# --------------------------------------------------------------------------- #

KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})
PANAPHARA_HOUSES: frozenset[int] = frozenset({2, 5, 8, 11})
APOKLIMA_HOUSES: frozenset[int] = frozenset({3, 6, 9, 12})


def _kendradi_virupas(house_number: int) -> float:
    """Return Kendradi Bala in virupas for a planet in *house_number*."""
    if house_number in KENDRA_HOUSES:
        return 60.0
    if house_number in PANAPHARA_HOUSES:
        return 30.0
    if house_number in APOKLIMA_HOUSES:
        return 15.0
    return 0.0


# --------------------------------------------------------------------------- #
# Minimum required Shadbala in Rupas (default values)
# --------------------------------------------------------------------------- #

DEFAULT_MINIMUM_RUPAS: dict[BodyId, float] = {
    BodyId.SUN: 5.0,
    BodyId.MOON: 6.0,
    BodyId.MARS: 5.0,
    BodyId.MERCURY: 7.0,
    BodyId.JUPITER: 6.5,
    BodyId.VENUS: 5.5,
    BodyId.SATURN: 5.0,
    BodyId.RAHU: 5.0,
    BodyId.KETU: 5.0,
}


# --------------------------------------------------------------------------- #
# Planet numbering for Ojhayugma Bala
# --------------------------------------------------------------------------- #

PLANET_NUMBER: dict[BodyId, int] = {
    BodyId.SUN: 1,
    BodyId.MOON: 2,
    BodyId.MARS: 3,
    BodyId.MERCURY: 4,
    BodyId.JUPITER: 5,
    BodyId.VENUS: 6,
    BodyId.SATURN: 7,
    BodyId.RAHU: 8,
    BodyId.KETU: 9,
}


# --------------------------------------------------------------------------- #
# Benefic / Malefic classification
# --------------------------------------------------------------------------- #

NATURAL_BENEFICS: frozenset[BodyId] = frozenset({
    BodyId.JUPITER, BodyId.VENUS, BodyId.MOON,
})

NATURAL_MALEFICS: frozenset[BodyId] = frozenset({
    BodyId.SUN, BodyId.MARS, BodyId.SATURN, BodyId.RAHU, BodyId.KETU,
})

NATURAL_NEUTRAL: frozenset[BodyId] = frozenset({BodyId.MERCURY})


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class BalaSystem(StrEnum):
    """Supported Bala systems (V1: SHADBALA only)."""

    SHADBALA = "SHADBALA"


# --------------------------------------------------------------------------- #
# Sub-component data classes
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class SthanaBalaComponents:
    """Sub-components of Sthana Bala (Positional Strength) in virupas."""

    uchcha_bala: float = 0.0
    saptavargaja_bala: float = 0.0
    ojhayugma_bala: float = 0.0
    kendradi_bala: float = 0.0
    drekkana_bala: float = 0.0

    @property
    def total(self) -> float:
        """Total Sthana Bala in virupas."""
        return (
            self.uchcha_bala
            + self.saptavargaja_bala
            + self.ojhayugma_bala
            + self.kendradi_bala
            + self.drekkana_bala
        )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class KalaBalaComponents:
    """Sub-components of Kala Bala (Temporal Strength) in virupas."""

    nathonnatha_bala: float = 0.0
    paksha_bala: float = 0.0
    tribhaga_bala: float = 0.0
    ayana_bala: float = 0.0
    yudhdha_bala: float = 0.0

    @property
    def total(self) -> float:
        """Total Kala Bala in virupas."""
        return (
            self.nathonnatha_bala
            + self.paksha_bala
            + self.tribhaga_bala
            + self.ayana_bala
            + self.yudhdha_bala
        )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# ShadbalaComponents — the six main balas and their sub-components
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ShadbalaComponents:
    """All six Shadbala components and their sub-components (in virupas).

    The six balas are:
    1. Sthana Bala (Positional Strength)
    2. Dig Bala (Directional Strength)
    3. Kala Bala (Temporal Strength)
    4. Cheshta Bala (Motional/Effective Strength)
    5. Naisargika Bala (Natural Strength)
    6. Drik Bala (Aspectual Strength)
    """

    sthana_bala: SthanaBalaComponents = field(default_factory=SthanaBalaComponents)
    dig_bala: float = 0.0
    kala_bala: KalaBalaComponents = field(default_factory=KalaBalaComponents)
    cheshta_bala: float = 0.0
    naisargika_bala: float = 0.0
    drik_bala: float = 0.0

    @property
    def total_sthana(self) -> float:
        """Total Sthana Bala in virupas."""
        return self.sthana_bala.total

    @property
    def total_kala(self) -> float:
        """Total Kala Bala in virupas."""
        return self.kala_bala.total

    @property
    def total_virupas(self) -> float:
        """Total Shadbala in virupas (sum of all six balas)."""
        return (
            self.total_sthana
            + self.dig_bala
            + self.total_kala
            + self.cheshta_bala
            + self.naisargika_bala
            + self.drik_bala
        )

    @property
    def total_rupas(self) -> float:
        """Total Shadbala in rupas (1 rupa = 60 virupas)."""
        return self.total_virupas / VIRUPAS_PER_RUPA

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# IshtaKashtaPhala
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class IshtaKashtaPhala:
    """Ishta and Kashta phala values in virupas."""

    ishta_phala: float = 0.0
    kashta_phala: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# ShadbalaResult — per-planet strength result
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ShadbalaResult:
    """One planet's Shadbala computation result."""

    planet: BodyId
    components: ShadbalaComponents
    total_virupas: float
    total_rupas: float
    minimum_required: float
    ratio: float
    ishta_kashta: IshtaKashtaPhala

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


# --------------------------------------------------------------------------- #
# ShadbalaReport — full report for all computed planets
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ShadbalaReport:
    """Complete Shadbala report for all computed planets."""

    results: tuple[ShadbalaResult, ...]
    system: BalaSystem = BalaSystem.SHADBALA
    version: str = BALA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def result_for(self, planet: BodyId) -> ShadbalaResult | None:
        """Return the result for a specific planet, or None."""
        for r in self.results:
            if r.planet == planet:
                return r
        return None


# --------------------------------------------------------------------------- #
# BalaConfig
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class BalaConfig:
    """Immutable JRE-011 configuration.  TOML is authoritative; every
    default is declared in ``config/bala.toml`` (no hidden defaults).
    """

    version: str = BALA_VERSION
    max_depth: int = 1
    minimum_rupas: dict[str, float] = field(
        default_factory=lambda: {k.value: v for k, v in DEFAULT_MINIMUM_RUPAS.items()}
    )
    naisargika_virupas: dict[str, float] = field(
        default_factory=lambda: {k.value: v for k, v in DEFAULT_NAISARGIKA_VIRUPAS.items()}
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BalaConfig:
        version = data.get("version", BALA_VERSION)
        max_depth = int(data.get("max_depth", 1))
        min_raw = data.get("minimum_rupas")
        min_rupas: dict[str, float]
        if isinstance(min_raw, dict) and min_raw:
            min_rupas = {str(k): float(v) for k, v in min_raw.items()}
        else:
            min_rupas = {k.value: v for k, v in DEFAULT_MINIMUM_RUPAS.items()}
        nais_raw = data.get("naisargika_virupas")
        nais_virupas: dict[str, float]
        if isinstance(nais_raw, dict) and nais_raw:
            nais_virupas = {str(k): float(v) for k, v in nais_raw.items()}
        else:
            nais_virupas = {k.value: v for k, v in DEFAULT_NAISARGIKA_VIRUPAS.items()}
        return cls(
            version=str(version),
            max_depth=max_depth,
            minimum_rupas=min_rupas,
            naisargika_virupas=nais_virupas,
        )


def validate(config: BalaConfig) -> BalaConfig:
    """Validate a ``BalaConfig``; raises ``InvalidBalaConfigError``."""
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidBalaConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    if not isinstance(config.max_depth, int) or config.max_depth < 1:
        raise InvalidBalaConfigError(
            f"max_depth must be a positive integer, got {config.max_depth}"
        )
    if not isinstance(config.minimum_rupas, dict) or not config.minimum_rupas:
        raise InvalidBalaConfigError(
            f"minimum_rupas must be a non-empty dict, got {config.minimum_rupas!r}"
        )
    if not isinstance(config.naisargika_virupas, dict) or not config.naisargika_virupas:
        raise InvalidBalaConfigError(
            f"naisargika_virupas must be a non-empty dict, "
            f"got {config.naisargika_virupas!r}"
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

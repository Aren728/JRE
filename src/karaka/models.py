"""JRE-014 Karaka (Significator) models — core data structures and constants.

JRE-014 assigns and ranks Naisargika (Natural), Sthira (Permanent),
Chara (Temporary), and Vishesha (Special) significators for classical
life categories.  It performs NO predictive interpretation.

Core Models:
- ``KarakaCategory``: enum of life categories
- ``KarakaType``: enum of significator types
- ``KarakaAssignment``: one significator mapping
- ``KarakaReport``: complete significator report
- ``KarakaConfig``: immutable configuration
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, PlanetState

from .errors import InvalidKarakaConfigError

#: Pinned package version.
KARAKA_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class KarakaCategory(StrEnum):
    """Classical life categories (Jaimini Karaka scheme)."""

    ATMA = "ATMA"           # Soul / Self
    MANAS = "MANAS"         # Mind / Emotions
    PUTRA = "PUTRA"         # Children / Progeny
    DHANA = "DHANA"         # Financial assets
    DARA = "DARA"           # Spouse / Marriage
    SANTANA = "SANTANA"     # Progeny (broader)
    BHRATRU = "BHRATRU"     # Siblings
    MATRU = "MATRU"         # Mother
    SHATRU = "SHATRU"       # Enemies
    VYAYA = "VYAYA"         # Loss / Expenditure
    AYUR = "AYUR"           # Longevity
    RIKTA = "RIKTA"         # Wastage / Loss
    LABHA = "LABHA"         # Gains / Profit
    BANDHU = "BANDHU"       # Relatives / Kinsmen
    VAK = "VAK"             # Speech / Communication


class KarakaType(StrEnum):
    """Types of significators."""

    NAISARGIKA = "NAISARGIKA"   # Natural significator
    STHIRA = "STHIRA"          # Permanent significator
    CHARA = "CHARA"            # Temporary / Jaimini significator
    VISHESHA = "VISHESHA"      # Special significator


# --------------------------------------------------------------------------- #
# Default Naisargika mappings (planet -> category)
# --------------------------------------------------------------------------- #

DEFAULT_NAISARGIKA: dict[BodyId, KarakaCategory] = {
    BodyId.SUN: KarakaCategory.ATMA,
    BodyId.MOON: KarakaCategory.MANAS,
    BodyId.MARS: KarakaCategory.BHRATRU,
    BodyId.MERCURY: KarakaCategory.VAK,
    BodyId.JUPITER: KarakaCategory.PUTRA,
    BodyId.VENUS: KarakaCategory.DARA,
    BodyId.SATURN: KarakaCategory.SHATRU,
}

# --------------------------------------------------------------------------- #
# Default Sthira mappings (category -> planet)
# --------------------------------------------------------------------------- #

DEFAULT_STHIRA: dict[KarakaCategory, BodyId] = {
    KarakaCategory.ATMA: BodyId.SUN,
    KarakaCategory.MANAS: BodyId.MOON,
    KarakaCategory.PUTRA: BodyId.JUPITER,
    KarakaCategory.DHANA: BodyId.JUPITER,
    KarakaCategory.DARA: BodyId.VENUS,
    KarakaCategory.SANTANA: BodyId.JUPITER,
    KarakaCategory.BHRATRU: BodyId.MARS,
    KarakaCategory.MATRU: BodyId.MOON,
    KarakaCategory.SHATRU: BodyId.SATURN,
    KarakaCategory.VYAYA: BodyId.SATURN,
    KarakaCategory.AYUR: BodyId.SATURN,
    KarakaCategory.RIKTA: BodyId.SATURN,
    KarakaCategory.LABHA: BodyId.SATURN,
    KarakaCategory.BANDHU: BodyId.SUN,
}

# --------------------------------------------------------------------------- #
# Chara Karaka categories (Jaimini scheme, 7 ranks)
# --------------------------------------------------------------------------- #

CHARA_KARAKA_RANKS: tuple[KarakaCategory, ...] = (
    KarakaCategory.ATMA,      # Atmakaraka (rank 1)
    KarakaCategory.MANAS,     # Amatyakaraka (rank 2)
    KarakaCategory.BHRATRU,   # Bhratrukaraka (rank 3)
    KarakaCategory.MATRU,     # Matrukaraka (rank 4)
    KarakaCategory.PUTRA,     # Putrakaraka (rank 5)
    KarakaCategory.SHATRU,    # Gnatikaraka (rank 6)
    KarakaCategory.DARA,      # Darakaraka (rank 7)
)

# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class KarakaAssignment:
    """One significator mapping."""

    category: KarakaCategory
    planet: BodyId
    karaka_type: KarakaType
    rank: int
    strength_modifier: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class KarakaReport:
    """Complete significator report for the chart."""

    assignments: tuple[KarakaAssignment, ...]
    version: str = KARAKA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def karakas_for_category(
        self, category: KarakaCategory
    ) -> tuple[KarakaAssignment, ...]:
        """Return all significators for a given category."""
        return tuple(a for a in self.assignments if a.category == category)

    def karakas_for_planet(
        self, planet: BodyId
    ) -> tuple[KarakaAssignment, ...]:
        """Return all categories a planet signifies."""
        return tuple(a for a in self.assignments if a.planet == planet)

    def karakas_by_type(
        self, karaka_type: KarakaType
    ) -> tuple[KarakaAssignment, ...]:
        """Return all assignments of a given type."""
        return tuple(a for a in self.assignments if a.karaka_type == karaka_type)


@dataclass(frozen=True)
class KarakaConfig:
    """Immutable JRE-014 configuration.  TOML is authoritative; every
    default is declared in ``config/karaka.toml`` (no hidden defaults).
    """

    version: str = KARAKA_VERSION
    chara_planet_count: int = 7
    naisargika: dict[str, str] = field(
        default_factory=lambda: {k.value: v.value for k, v in DEFAULT_NAISARGIKA.items()}
    )
    sthira: dict[str, str] = field(
        default_factory=lambda: {k.value: v.value for k, v in DEFAULT_STHIRA.items()}
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KarakaConfig:
        version = data.get("version", KARAKA_VERSION)
        chara_count = int(data.get("chara_planet_count", 7))
        nais_raw = data.get("naisargika")
        nais: dict[str, str]
        if isinstance(nais_raw, dict) and nais_raw:
            nais = {str(k): str(v) for k, v in nais_raw.items()}
        else:
            nais = {k.value: v.value for k, v in DEFAULT_NAISARGIKA.items()}
        sthi_raw = data.get("sthira")
        sthi: dict[str, str]
        if isinstance(sthi_raw, dict) and sthi_raw:
            sthi = {str(k): str(v) for k, v in sthi_raw.items()}
        else:
            sthi = {k.value: v.value for k, v in DEFAULT_STHIRA.items()}
        return cls(
            version=str(version),
            chara_planet_count=chara_count,
            naisargika=nais,
            sthira=sthi,
        )


def validate(config: KarakaConfig) -> KarakaConfig:
    """Validate a ``KarakaConfig``; raises ``InvalidKarakaConfigError``."""
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidKarakaConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    if not isinstance(config.chara_planet_count, int) or config.chara_planet_count < 1:
        raise InvalidKarakaConfigError(
            f"chara_planet_count must be a positive integer, "
            f"got {config.chara_planet_count!r}"
        )
    if not isinstance(config.naisargika, dict) or not config.naisargika:
        raise InvalidKarakaConfigError(
            f"naisargika must be a non-empty dict, got {config.naisargika!r}"
        )
    if not isinstance(config.sthira, dict) or not config.sthira:
        raise InvalidKarakaConfigError(
            f"sthira must be a non-empty dict, got {config.sthira!r}"
        )
    return config


# --------------------------------------------------------------------------- #
# Pure derivation helpers
# --------------------------------------------------------------------------- #

def _degree_in_sign(longitude: float) -> float:
    """Degrees within the sign, in [0, 30)."""
    return longitude % 30.0


def compute_chara_karakas(
    planet_states: tuple[PlanetState, ...],
    count: int = 7,
) -> tuple[tuple[KarakaCategory, BodyId], ...]:
    """Compute Jaimini Chara Karakas from planetary longitudes.

    The planet with the highest degree-in-sign becomes Atmakaraka (rank 1),
    the second becomes Amatyakaraka (rank 2), and so on.

    Parameters
    ----------
    planet_states : tuple of PlanetState
        The natal planet states (typically Sun through Saturn).
    count : int
        Number of karaka ranks to assign (default 7).

    Returns
    -------
    tuple of (KarakaCategory, BodyId)
        Ordered by rank (rank 1 = Atmakaraka first).
    """
    # Filter to classical planets (Sun through Saturn)
    classical = [
        s for s in planet_states
        if s.body in {BodyId.SUN, BodyId.MOON, BodyId.MARS, BodyId.MERCURY,
                      BodyId.JUPITER, BodyId.VENUS, BodyId.SATURN}
    ]

    # Sort by degree-in-sign descending (highest = rank 1)
    ranked = sorted(
        classical,
        key=lambda s: _degree_in_sign(s.longitude_used),
        reverse=True,
    )

    result: list[tuple[KarakaCategory, BodyId]] = []
    for i, state in enumerate(ranked[:count]):
        category = CHARA_KARAKA_RANKS[i] if i < len(CHARA_KARAKA_RANKS) else KarakaCategory.ATMA
        result.append((category, state.body))

    return tuple(result)


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

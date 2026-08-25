"""JRE-013 Yoga models — core data structures and constants.

JRE-013 identifies structural planetary combinations (classical Yogas)
from natal chart facts, Shadbala strengths, and Drik aspect graphs.
It performs NO predictive interpretation (e.g., "this yoga causes
wealth").

Core Models:
- ``YogaId``: enum of supported classical yogas
- ``YogaCondition``: the specific rule met
- ``YogaResult``: one yoga evaluation result
- ``YogaReport``: complete yoga report for the chart
- ``YogaConfig``: immutable configuration
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, cast

from jyotish import BodyId, RashiId

from .errors import InvalidYogaConfigError

#: Pinned package version.
YOGA_VERSION = "0.1.0"

# --------------------------------------------------------------------------- #
# Sign ownership (Vimshottari) — 1-indexed rashi -> owning planet
# --------------------------------------------------------------------------- #

SIGN_LORDS: dict[int, BodyId] = {
    1: BodyId.MARS,      # Aries (Mesha)
    2: BodyId.VENUS,     # Taurus (Vrishabha)
    3: BodyId.MERCURY,   # Gemini (Mithuna)
    4: BodyId.MOON,      # Cancer (Karka)
    5: BodyId.SUN,       # Leo (Simha)
    6: BodyId.MERCURY,   # Virgo (Kanya)
    7: BodyId.VENUS,     # Libra (Tula)
    8: BodyId.MARS,      # Scorpio (Vrishchika)
    9: BodyId.JUPITER,   # Sagittarius (Dhanusha)
    10: BodyId.SATURN,    # Capricorn (Makara)
    11: BodyId.SATURN,    # Aquarius (Kumbha)
    12: BodyId.JUPITER,   # Pisces (Meena)
}

# RashiId value -> 1-indexed number
_RASHI_ORDER: list[str] = [
    "MESHA", "VRISHABHA", "MITHUNA", "KARKA", "SIMHA", "KANYA",
    "TULA", "VRISHCHIKA", "DHANUSHA", "MAKARA", "KUMBHA", "MEENA",
]


def rashi_number(rashi: RashiId | str) -> int:
    """Convert RashiId or string to 1-indexed number (1=Aries, ...12=Pisces)."""
    name = rashi.value if hasattr(rashi, "value") else str(rashi)
    try:
        return _RASHI_ORDER.index(name) + 1
    except ValueError:
        return 1


# --------------------------------------------------------------------------- #
# House classification
# --------------------------------------------------------------------------- #

KENDRA_HOUSES: frozenset[int] = frozenset({1, 4, 7, 10})
TRIKONA_HOUSES: frozenset[int] = frozenset({1, 5, 9})
DHANA_HOUSES: frozenset[int] = frozenset({2, 11})
DUSTHANA_HOUSES: frozenset[int] = frozenset({6, 8, 12})
UPACHAYA_HOUSES: frozenset[int] = frozenset({3, 6, 10, 11})


def house_from_lagna(lagna_sign: int, planet_sign: int) -> int:
    """Compute the 1-indexed house number from Lagna to a planet's sign."""
    return (planet_sign - lagna_sign) % 12 + 1


def signs_away(from_sign: int, to_sign: int) -> int:
    """Number of signs from *from_sign* to *to_sign* (1-12)."""
    return (to_sign - from_sign) % 12 + 1


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #

class YogaId(StrEnum):
    """Supported classical yogas (V1 subset)."""

    GAJAKESARI_YOGA = "GAJAKESARI_YOGA"
    RAJA_YOGA = "RAJA_YOGA"
    DHANA_YOGA = "DHANA_YOGA"
    VIPARITA_RAJA_YOGA = "VIPARITA_RAJA_YOGA"
    PANCHA_MAHAPURUSHA_YOGA = "PANCHA_MAHAPURUSHA_YOGA"
    KENDRADHIPATI_DOSHA = "KENDRADHIPATI_DOSHA"


class YogaRuleType(StrEnum):
    """Types of structural yoga rules."""

    KENDRA_FROM = "KENDRA_FROM"
    KENDRA_TRIKONA_CONNECTION = "KENDRA_TRIKONA_CONNECTION"
    DHANA_CONNECTION = "DHANA_CONNECTION"
    VIPARITA_CONNECTION = "VIPARITA_CONNECTION"


class ConnectionType(StrEnum):
    """How two planets are connected."""

    CONJUNCTION = "CONJUNCTION"
    ASPECT = "ASPECT"
    EXCHANGE = "EXCHANGE"
    NONE = "NONE"


class ParivartanaType(StrEnum):
    """Classification of sign exchanges (BPHS Ch.26)."""

    MAHA = "MAHA"          # Kendra-Trikona exchange
    KAHALA = "KAHALA"      # Exchange between functional-positive houses (2/5/9/11)
    DAINYA = "DAINYA"      # Exchange involving Dusthana lords (6/8/12)
    NONE = "NONE"          # Not an exchange or unclassifiable


# --------------------------------------------------------------------------- #
# Dignity strength weights (BPHS Ch.3)
# --------------------------------------------------------------------------- #

#: Classical dignity strength weights for yoga evaluation.
#: Higher value = stronger planet contribution to yoga.
DIGNITY_STRENGTH: dict[str, float] = {
    "EXALTED": 1.0,
    "MULATRIKONA": 0.9,
    "OWN": 0.8,
    "FRIEND": 0.6,
    "NEUTRAL": 0.5,
    "ENEMY": 0.3,
    "DEBILITATED": 0.1,
}

#: Connection type strength hierarchy (COMMENTARY_DEPENDENT).
#: Conjunction/Exchange > Mutual Aspect > One-way Aspect.
CONNECTION_STRENGTH: dict[ConnectionType, float] = {
    ConnectionType.CONJUNCTION: 1.0,
    ConnectionType.EXCHANGE: 1.0,
    ConnectionType.ASPECT: 0.7,
    ConnectionType.NONE: 0.0,
}


# --------------------------------------------------------------------------- #
# Data models
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class YogaCondition:
    """Describes the specific structural rule met for a yoga."""

    condition_type: str
    planets_involved: tuple[BodyId, ...]
    houses_involved: tuple[int, ...]
    connection_type: ConnectionType = ConnectionType.NONE
    details: str = ""

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class YogaResult:
    """One yoga evaluation result."""

    yoga_id: YogaId
    is_present: bool
    strength_modifier: float
    evidence: tuple[str, ...]
    conditions: tuple[YogaCondition, ...] = ()
    is_cancelled: bool = False
    cancellation_reasons: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))


@dataclass(frozen=True)
class YogaReport:
    """Complete yoga report for the chart."""

    results: tuple[YogaResult, ...]
    version: str = YOGA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    def result_for(self, yoga_id: YogaId) -> YogaResult | None:
        """Return the result for a specific yoga, or None."""
        for r in self.results:
            if r.yoga_id == yoga_id:
                return r
        return None

    @property
    def active_yogas(self) -> tuple[YogaResult, ...]:
        """Return only the yogas that are present."""
        return tuple(r for r in self.results if r.is_present)


@dataclass(frozen=True)
class YogaConfig:
    """Immutable JRE-013 configuration.  TOML is authoritative; every
    default is declared in ``config/yoga.toml`` (no hidden defaults).
    """

    version: str = YOGA_VERSION
    min_bala_ratio: float = 0.5
    enabled_yogas: tuple[YogaId, ...] = field(
        default_factory=lambda: tuple(YogaId)
    )

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], _model_to_dict(self))

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> YogaConfig:
        version = data.get("version", YOGA_VERSION)
        min_bala = float(data.get("min_bala_ratio", 0.5))
        enabled_raw = data.get("enabled_yogas")
        if isinstance(enabled_raw, list) and enabled_raw:
            enabled = tuple(YogaId(str(v)) for v in enabled_raw)
        else:
            enabled = tuple(YogaId)
        return cls(
            version=str(version),
            min_bala_ratio=min_bala,
            enabled_yogas=enabled,
        )


def validate(config: YogaConfig) -> YogaConfig:
    """Validate a ``YogaConfig``; raises ``InvalidYogaConfigError``."""
    if not isinstance(config.version, str) or config.version == "":
        raise InvalidYogaConfigError(
            f"version must be a non-empty string, got {config.version!r}"
        )
    if not isinstance(config.min_bala_ratio, (int, float)) or config.min_bala_ratio < 0:
        raise InvalidYogaConfigError(
            f"min_bala_ratio must be a non-negative number, got {config.min_bala_ratio!r}"
        )
    if not isinstance(config.enabled_yogas, tuple):
        raise InvalidYogaConfigError(
            f"enabled_yogas must be a tuple, got {type(config.enabled_yogas).__name__}"
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

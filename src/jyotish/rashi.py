"""Complete 12-Rashi catalog — pure data + pure functions (ADR-003).

Boundaries are derived from the arc constant (30°) and the index, never
hard-coded per sign. Rulers follow the classical Parasari assignment
(Brihat Parashara Hora Shastra ch. 4; same scheme in Varahamihira's Brihat
Jataka ch. 1). Any catalog change is a versioned decision (RASHI_CATALOG_VERSION).
"""

from __future__ import annotations

from astronomy.models import BodyId

from .models import RashiId

#: Catalog version (part of the calculation identity; ADR-003).
RASHI_CATALOG_VERSION = "1.0.0"

RASHI_SOURCE = (
    "Classical Parasari rashi lords (Brihat Parashara Hora Shastra ch. 4; "
    "Varahamihira, Brihat Jataka ch. 1). Romanization: common Sanskrit "
    "transliteration (IAST-lite)."
)

#: 30-degree arc constant (degrees).
RASHI_ARC_DEG = 30.0

#: Canonical zodiacal order of the 12 rashis.
RASHI_ORDER: tuple[RashiId, ...] = (
    RashiId.MESHA,
    RashiId.VRISHABHA,
    RashiId.MITHUNA,
    RashiId.KARKA,
    RashiId.SIMHA,
    RashiId.KANYA,
    RashiId.TULA,
    RashiId.VRISHCHIKA,
    RashiId.DHANUSHA,
    RashiId.MAKARA,
    RashiId.KUMBHA,
    RashiId.MEENA,
)

#: Classical lords by rashi (index-aligned with RASHI_ORDER).
RASHI_LORDS: tuple[BodyId, ...] = (
    BodyId.MARS,  # MESHA
    BodyId.VENUS,  # VRISHABHA
    BodyId.MERCURY,  # MITHUNA
    BodyId.MOON,  # KARKA
    BodyId.SUN,  # SIMHA
    BodyId.MERCURY,  # KANYA
    BodyId.VENUS,  # TULA
    BodyId.MARS,  # VRISHCHIKA
    BodyId.JUPITER,  # DHANUSHA
    BodyId.SATURN,  # MAKARA
    BodyId.SATURN,  # KUMBHA
    BodyId.JUPITER,  # MEENA
)

_RASHI_INDEX: dict[RashiId, int] = {rashi: i for i, rashi in enumerate(RASHI_ORDER)}


def rashi_index_of(longitude_deg: float) -> int:
    """Rashi index (0 = MESHA) for a longitude in [0, 360). Pure floor semantics."""
    return int(longitude_deg // RASHI_ARC_DEG) % 12


def rashi_of(longitude_deg: float) -> RashiId:
    """Rashi containing ``longitude_deg`` (0.0 -> MESHA; 30.0 -> VRISHABHA)."""
    return RASHI_ORDER[rashi_index_of(longitude_deg)]


def degree_in_rashi(longitude_deg: float) -> float:
    """Degrees within the rashi, in [0, 30)."""
    return longitude_deg % RASHI_ARC_DEG


def rashi_span(rashi: RashiId) -> tuple[float, float]:
    """Start/end longitude of a rashi in [0, 360)."""
    index = _RASHI_INDEX[rashi]
    return index * RASHI_ARC_DEG, (index + 1) * RASHI_ARC_DEG


def lord_of(rashi: RashiId) -> BodyId:
    """Classical lord of a rashi."""
    return RASHI_LORDS[_RASHI_INDEX[rashi]]

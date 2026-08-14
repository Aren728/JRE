"""Complete 27-Nakshatra catalog — pure data + pure functions (ADR-003).

Every nakshatra spans exactly ``NAKSHATRA_ARC = 360/27`` (13°20′), divided
into four padas of ``PADA_ARC = NAKSHATRA_ARC/4`` (3°20′). Boundaries are
derived from the arc constants, never hard-coded per nakshatra. Rulers follow
the classical Vimshottari 9-planet cycle repeated three times (Brihat
Parashara Hora Shastra ch. 46). Any catalog change is a versioned decision.
"""

from __future__ import annotations

from astronomy.models import BodyId

from .models import NakshatraId, Pada

#: Catalog version (part of the calculation identity; ADR-003).
NAKSHATRA_CATALOG_VERSION = "1.0.0"

NAKSHATRA_SOURCE = (
    "27 nakshatras with classical Vimshottari rulers (Brihat Parashara Hora "
    "Shastra ch. 46). Romanization: common Sanskrit transliteration "
    "(IAST-lite: ASHWINI, KRITTIKA, JYESHTHA, SHATABHISHA, ...)."
)

#: One nakshatra arc in degrees (13°20′).
NAKSHATRA_ARC = 360.0 / 27.0

#: One pada arc in degrees (3°20′).
PADA_ARC = NAKSHATRA_ARC / 4.0

#: Canonical zodiacal order of the 27 nakshatras from 0° sidereal.
NAKSHATRA_ORDER: tuple[NakshatraId, ...] = (
    NakshatraId.ASHWINI,
    NakshatraId.BHARANI,
    NakshatraId.KRITTIKA,
    NakshatraId.ROHINI,
    NakshatraId.MRIGASHIRA,
    NakshatraId.ARDRA,
    NakshatraId.PUNARVASU,
    NakshatraId.PUSHYA,
    NakshatraId.ASHLESHA,
    NakshatraId.MAGHA,
    NakshatraId.PURVA_PHALGUNI,
    NakshatraId.UTTARA_PHALGUNI,
    NakshatraId.HASTA,
    NakshatraId.CHITRA,
    NakshatraId.SWATI,
    NakshatraId.VISHAKHA,
    NakshatraId.ANURADHA,
    NakshatraId.JYESHTHA,
    NakshatraId.MULA,
    NakshatraId.PURVA_ASHADHA,
    NakshatraId.UTTARA_ASHADHA,
    NakshatraId.SHRAVANA,
    NakshatraId.DHANISHTHA,
    NakshatraId.SHATABHISHA,
    NakshatraId.PURVA_BHADRAPADA,
    NakshatraId.UTTARA_BHADRAPADA,
    NakshatraId.REVATI,
)

#: Classical Vimshottari lord cycle (9 rulers, repeated 3x over 27).
NAKSHATRA_LORD_CYCLE: tuple[BodyId, ...] = (
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

_NAKSHATRA_INDEX: dict[NakshatraId, int] = {
    nak: i for i, nak in enumerate(NAKSHATRA_ORDER)
}


def _fold(longitude_deg: float) -> float:
    """Fold any input into [0, 360) (360.0 -> 0.0; negatives wrap)."""
    value = longitude_deg % 360.0
    return 0.0 if value == 0.0 else value


def nakshatra_index_of(longitude_deg: float) -> int:
    """Nakshatra index (0 = ASHWINI) for a longitude in [0, 360). Floor semantics.

    Computed as ``floor(lon * 27 / 360)`` rather than ``floor(lon / (360/27))``
    to keep exact boundaries deterministic: the double ``360/27`` is slightly
    larger than the true 13°20′ arc, so dividing a boundary value (e.g. 40.0)
    by it can round to one bucket early. The multiplication form is exact for
    every boundary multiple (Specialist §18 boundary rules).
    """
    value = _fold(longitude_deg)
    return int((value * 27.0) // 360.0) % 27


def nakshatra_of(longitude_deg: float) -> NakshatraId:
    """Nakshatra containing ``longitude_deg`` (0.0 -> ASHWINI)."""
    return NAKSHATRA_ORDER[nakshatra_index_of(longitude_deg)]


def degree_in_nakshatra(longitude_deg: float) -> float:
    """Degrees within the nakshatra, in [0, 13°20′)."""
    value = _fold(longitude_deg)
    return ((value * 27.0) % 360.0) / 27.0


def pada_of(longitude_deg: float) -> Pada:
    """Pada (1–4) for a longitude within its nakshatra.

    Same exact-boundary arithmetic as ``nakshatra_index_of``: a longitude at
    a pada boundary (multiple of 3°20′) begins the next pada.
    """
    value = _fold(longitude_deg)
    index = int((value * 108.0) // 360.0) % 108
    return Pada(index % 4 + 1)


def lord_of(nakshatra: NakshatraId) -> BodyId:
    """Classical ruler of a nakshatra."""
    return NAKSHATRA_LORD_CYCLE[_NAKSHATRA_INDEX[nakshatra] % 9]


def nakshatra_span(nakshatra: NakshatraId) -> tuple[float, float]:
    """Start/end longitude of a nakshatra in [0, 360)."""
    index = _NAKSHATRA_INDEX[nakshatra]
    return index * NAKSHATRA_ARC, (index + 1) * NAKSHATRA_ARC


def pada_span(nakshatra: NakshatraId, pada: Pada) -> tuple[float, float]:
    """Start/end longitude of one pada within its nakshatra."""
    start = _NAKSHATRA_INDEX[nakshatra] * NAKSHATRA_ARC + (int(pada) - 1) * PADA_ARC
    return start, start + PADA_ARC

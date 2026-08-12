"""Centralized Swiss Ephemeris constant mappings for the adapter.

NOTE (pysweph 2.10.3.x): this binding exposes the C-style flag names
``FLG_*`` (e.g. ``FLG_SWIEPH``) instead of the legacy ``SEFLG_*`` aliases of
the unmaintained ``pyswisseph`` package, and ``calc_ut`` returns
``(xx, retflag, errmsg)`` while ``utc_to_jd`` returns ``(jd_et, jd_ut)``.
These are documented breaking changes of the continuation fork (see
https://github.com/sailorfe/pysweph). Numeric flag values are defined by the
binding — never hardcode them; always use these named constants.
"""

from __future__ import annotations

import swisseph as swe

from ..models import Ayanamsa, BodyId, EphemerisMode, NodeType, PositionType

#: Body mapping for bodies computed directly from the ephemeris.
BODY_TO_SWE: dict[BodyId, int] = {
    BodyId.SUN: swe.SUN,
    BodyId.MOON: swe.MOON,
    BodyId.MARS: swe.MARS,
    BodyId.MERCURY: swe.MERCURY,
    BodyId.JUPITER: swe.JUPITER,
    BodyId.VENUS: swe.VENUS,
    BodyId.SATURN: swe.SATURN,
}

#: Rahu/Ketu are derived from the lunar node (never mixed silently — the
#: node model is an explicit ``CalculationConfig.node_type``).
NODE_TO_SWE: dict[NodeType, int] = {
    NodeType.MEAN: swe.MEAN_NODE,
    NodeType.TRUE: swe.TRUE_NODE,
}

#: Ayanamsa modes -> ``swe.set_sid_mode`` constants.
AYANAMSA_TO_SIDM: dict[Ayanamsa, int] = {
    Ayanamsa.LAHIRI: swe.SIDM_LAHIRI,
    Ayanamsa.RAMAN: swe.SIDM_RAMAN,
    Ayanamsa.FAGAN_BRADLEY: swe.SIDM_FAGAN_BRADLEY,
}

#: Swiss Ephemeris data set version (pinned; see datasets/ephemeris/README.md).
EPHEMERIS_VERSION = "18"

#: Library/binding identity for ProviderMetadata.
LIBRARY_NAME = "pysweph"


def calculation_flags(mode: EphemerisMode, position_type: PositionType) -> int:
    """Deterministic flag set for a (mode, position_type) pair (§21)."""
    base = swe.FLG_SWIEPH if mode is EphemerisMode.SWIEPH else swe.FLG_MOSEPH
    flags = int(base) | int(swe.FLG_SPEED)
    if position_type is PositionType.TRUE:
        flags |= int(swe.FLG_TRUEPOS)
    return flags


def mode_flag(mode: EphemerisMode) -> int:
    """The flag bit that proves a mode actually engaged (retflag check)."""
    return int(swe.FLG_SWIEPH) if mode is EphemerisMode.SWIEPH else int(swe.FLG_MOSEPH)

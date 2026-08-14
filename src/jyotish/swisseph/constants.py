"""Swiss Ephemeris constants for the Jyotish adapters (Specialist §22).

No magic numbers in adapter code. Values verified empirically against the
pinned binding (pysweph 2.10.03) on 2026-08-12; the ``ECL_*`` named constants
are exposed by the binding (superseding ADR-006's raw-hex premise — the raw
values are recorded beside each name for auditability).
"""

from __future__ import annotations

import swisseph as swe  # noqa: PLC0415 — confined to the adapter subpackage

#: Ephemeris data version of the bundled .se1 files (matches astronomy's
#: pinned data; ADR-001).
EPHEMERIS_VERSION = "18"

# House system codes passed to ``swe.houses_ex`` (hsys byte). 'W' is never
# requested: whole-sign bhavas are derived in pure code (ADR-002).
HSYS_BY_SYSTEM = {
    "EQUAL": b"E",
    "PLACIDUS": b"P",
    "KOCH": b"K",
    "REGIOMONTANUS": b"R",
    "CAMPANUS": b"C",
}

# --- Eclipse type constants (named on the binding; raw values for reference) -
ECL_CENTRAL = swe.ECL_CENTRAL  # 0x00000001
ECL_NONCENTRAL = swe.ECL_NONCENTRAL  # 0x00000002
ECL_TOTAL = swe.ECL_TOTAL  # 0x00000004
ECL_ANNULAR = swe.ECL_ANNULAR  # 0x00000008
ECL_PARTIAL = swe.ECL_PARTIAL  # 0x00000010
ECL_ANNULAR_TOTAL = swe.ECL_ANNULAR_TOTAL  # 0x00000020 (hybrid)
ECL_PENUMBRAL = swe.ECL_PENUMBRAL  # 0x00000040
ECL_ALLTYPES_SOLAR = swe.ECL_ALLTYPES_SOLAR  # 0x0000003F
ECL_ALLTYPES_LUNAR = swe.ECL_ALLTYPES_LUNAR  # 0x00000054

# Solar/Lunar ephemeris flag for the global eclipse search.
FLAG_SWIEPH = swe.FLG_SWIEPH

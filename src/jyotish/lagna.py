"""Lagna (ascendant) classification (Specialist spec §11).

The ascendant is computed by the house-cusp provider; this module classifies
the ascendant longitude exactly like a planet (rashi, degree, nakshatra, lord,
pada, degree in nakshatra, DMS) and binds the Bhava-1 relationship.
"""

from __future__ import annotations

from . import dms as _dms
from . import nakshatra as _nakshatra
from . import rashi as _rashi
from .models import Bhava, HouseSystem, JyotishConfig, LagnaState


def derive_lagna(
    ascendant_longitude_deg: float,
    config: JyotishConfig,
    house_system: HouseSystem,
    bhava_one: Bhava | None = None,
) -> LagnaState:
    """Classify an ascendant longitude (already in the ``longitude_used`` frame)."""
    lon = ascendant_longitude_deg % 360.0
    nakshatra = _nakshatra.nakshatra_of(lon)
    return LagnaState(
        ascendant_longitude_deg=0.0 if lon == 0.0 else lon,
        dms=_dms.from_degrees(lon, config.coordinate_precision),
        rashi=_rashi.rashi_of(lon),
        degree_in_rashi=_rashi.degree_in_rashi(lon),
        nakshatra=nakshatra,
        nakshatra_lord=_nakshatra.lord_of(nakshatra),
        pada=_nakshatra.pada_of(lon),
        degree_in_nakshatra=_nakshatra.degree_in_nakshatra(lon),
        bhava_relationship=bhava_one,
        house_system=house_system,
    )

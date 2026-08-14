"""``BodyPosition`` -> ``PlanetState`` derivation (Specialist spec §9).

Classification (rashi/nakshatra/pada) is a pure function of the unrounded
``longitude_used`` double — rounding is presentation-only (DMS) and never
feeds classification.
"""

from __future__ import annotations

from astronomy.models import BodyId, BodyPosition, RetrogradeState

from . import dms as _dms
from . import nakshatra as _nakshatra
from . import rashi as _rashi
from .models import JyotishConfig, PlanetState


def derive_planet_state(
    body_pos: BodyPosition,
    config: JyotishConfig,
    timestamp_utc_iso: str,
    julian_day_ut: float,
    provider_id: str,
    ephemeris_version: str,
) -> PlanetState:
    """Derive the full Jyotish state of one body from its raw astronomy state."""
    if config.zodiac_mode.value == "SIDEREAL":
        if body_pos.longitude_sidereal is None:
            raise ValueError(
                "longitude_sidereal is None for a body under SIDEREAL mode; "
                "the service boundary must reject ayanamsa=None with SIDEREAL"
            )
        longitude_used = body_pos.longitude_sidereal
    else:
        longitude_used = body_pos.longitude_tropical

    longitude_used = _normalize(longitude_used)

    rashi = _rashi.rashi_of(longitude_used)
    nakshatra = _nakshatra.nakshatra_of(longitude_used)

    return PlanetState(
        body=body_pos.body,
        longitude_tropical=_normalize(body_pos.longitude_tropical),
        longitude_sidereal=(
            None if body_pos.longitude_sidereal is None else _normalize(body_pos.longitude_sidereal)
        ),
        longitude_used=longitude_used,
        dms=_dms.from_degrees(longitude_used, config.coordinate_precision),
        rashi=rashi,
        degree_in_rashi=_rashi.degree_in_rashi(longitude_used),
        nakshatra=nakshatra,
        nakshatra_lord=_nakshatra.lord_of(nakshatra),
        pada=_nakshatra.pada_of(longitude_used),
        degree_in_nakshatra=_nakshatra.degree_in_nakshatra(longitude_used),
        latitude=body_pos.latitude,
        speed_longitude=body_pos.speed_longitude,
        retrograde=body_pos.retrograde,
        timestamp_utc_iso=timestamp_utc_iso,
        julian_day_ut=julian_day_ut,
        provider_id=provider_id,
        ephemeris_version=ephemeris_version,
    )


def classify_longitude(longitude_deg: float, config: JyotishConfig) -> PlanetState:
    """Classify a bare longitude (used for the ascendant point and tests).

    Returns a ``PlanetState``-shaped result with body ``SUN`` as a placeholder
    and zero motion — callers that need a real body should use
    ``derive_planet_state`` instead.
    """

    def _clamp(value: float) -> float:
        return max(-90.0, min(90.0, value))

    return PlanetState(
        body=BodyId.SUN,
        longitude_tropical=_normalize(longitude_deg),
        longitude_sidereal=None,
        longitude_used=_normalize(longitude_deg),
        dms=_dms.from_degrees(longitude_deg, config.coordinate_precision),
        rashi=_rashi.rashi_of(longitude_deg),
        degree_in_rashi=_rashi.degree_in_rashi(longitude_deg),
        nakshatra=_nakshatra.nakshatra_of(longitude_deg),
        nakshatra_lord=_nakshatra.lord_of(_nakshatra.nakshatra_of(longitude_deg)),
        pada=_nakshatra.pada_of(longitude_deg),
        degree_in_nakshatra=_nakshatra.degree_in_nakshatra(longitude_deg),
        latitude=0.0,
        speed_longitude=0.0,
        retrograde=RetrogradeState.STATIONARY,
        timestamp_utc_iso="",
        julian_day_ut=0.0,
        provider_id="",
        ephemeris_version="",
    )


def _normalize(longitude_deg: float) -> float:
    """Normalize to [0, 360) with ``-0.0 -> 0.0``."""
    value = longitude_deg % 360.0
    return 0.0 if value == 0.0 else value

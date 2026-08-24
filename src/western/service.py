"""JRE-066 Western Astrology calculation service — deterministic fact engine.

``WesternCalculationService`` takes birth data (date, time, latitude,
longitude, house system) and produces a ``WesternChart`` containing ONLY
deterministic facts: tropical longitudes, house cusps, aspects, and
essential dignities.  No astrological interpretation is performed.
"""

from __future__ import annotations

import datetime as dt

import swisseph as swe

from .errors import WesternCalculationError, WesternInputError
from .models import (
    HouseCusp,
    PlanetPosition,
    Sect,
    WesternChart,
    WesternDignity,
    WesternHouseSystem,
    WesternPlanet,
    _degree_in_sign,
    _sign_name,
    compute_all_aspects,
    evaluate_essential_dignity,
)

# ── Swiss Ephemeris body mapping ─────────────────────────────────────────────

# Core bodies always computed (SWIEPH or MOSEPH)
_SWE_BODY_MAP: dict[WesternPlanet, int] = {
    WesternPlanet.SUN: swe.SUN,
    WesternPlanet.MOON: swe.MOON,
    WesternPlanet.MERCURY: swe.MERCURY,
    WesternPlanet.VENUS: swe.VENUS,
    WesternPlanet.MARS: swe.MARS,
    WesternPlanet.JUPITER: swe.JUPITER,
    WesternPlanet.SATURN: swe.SATURN,
    WesternPlanet.URANUS: swe.URANUS,
    WesternPlanet.NEPTUNE: swe.NEPTUNE,
    WesternPlanet.PLUTO: swe.PLUTO,
    WesternPlanet.NORTH_NODE: swe.TRUE_NODE,
}

# Bodies requiring asteroid ephemeris files (seas_18.se1).
# Skipped gracefully when the file is not present.
_SWE_BODY_MAP_EXTENDED: dict[WesternPlanet, int] = {
    WesternPlanet.CHIRON: swe.CHIRON,
}

# ── House system byte codes ──────────────────────────────────────────────────

_HOUSE_SYSTEM_BYTES: dict[WesternHouseSystem, bytes] = {
    WesternHouseSystem.PLACIDUS: b"P",
    WesternHouseSystem.WHOLE_SIGN: b"W",
    WesternHouseSystem.EQUAL: b"E",
}

# South Node is always North Node + 180°
_SOUTH_NODE_OFFSET = 180.0

# Default ephemeris path
_DEFAULT_EPHE_PATH = "datasets/ephemeris"

# Flags for apparent geocentric ecliptic-of-date positions with speed
_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

# MOSEPH fallback flags (no data files needed)
_FLAGS_MOSEPH = swe.FLG_MOSEPH | swe.FLG_SPEED


class WesternCalculationService:
    """Deterministic Western astrological calculation service.

    Takes birth data and produces a WesternChart fact object.  Uses the
    Swiss Ephemeris (pysweph) for high-precision tropical positions.

    Usage::

        svc = WesternCalculationService()
        chart = svc.calculate(
            birth_date=datetime.date(1985, 7, 15),
            birth_time=datetime.time(14, 30, 0),
            latitude=40.7128,
            longitude=-74.0060,
            house_system=WesternHouseSystem.PLACIDUS,
        )
    """

    def __init__(self, ephe_path: str | None = None) -> None:
        self._ephe_path = ephe_path or _DEFAULT_EPHE_PATH

    def calculate(
        self,
        birth_date: dt.date,
        birth_time: dt.time,
        latitude: float,
        longitude: float,
        house_system: WesternHouseSystem = WesternHouseSystem.PLACIDUS,
    ) -> WesternChart:
        """Calculate the complete Western natal chart.

        Args:
            birth_date: Date of birth.
            birth_time: Time of birth (local civil time, UTC assumed).
            latitude: Geographic latitude (degrees, N positive).
            longitude: Geographic longitude (degrees, E positive).
            house_system: House system to use.

        Returns:
            A WesternChart containing all deterministic facts.

        Raises:
            WesternInputError: If input data is invalid.
            WesternCalculationError: If calculation fails.
        """
        self._validate_input(birth_date, birth_time, latitude, longitude)

        jd_ut = self._compute_julian_day(birth_date, birth_time)

        swe.set_ephe_path(self._ephe_path)

        # Calculate tropical positions
        planet_positions = self._calculate_tropical_positions(jd_ut)

        # Calculate house cusps
        house_cusps, ascendant, midheaven = self._calculate_house_cusps(
            jd_ut, latitude, longitude, house_system
        )

        # Build position lookup for aspect calculation
        pos_lookup: dict[WesternPlanet, tuple[float, float]] = {}
        for pp in planet_positions:
            pos_lookup[pp.planet] = (pp.longitude, pp.speed_longitude)

        # Compute all major aspects
        aspects = compute_all_aspects(pos_lookup)

        # Evaluate essential dignities
        dignities: dict[WesternPlanet, WesternDignity] = {}
        for pp in planet_positions:
            dignities[pp.planet] = evaluate_essential_dignity(
                pp.planet, pp.longitude
            )

        # Determine sect (diurnal or nocturnal)
        sect = self._calculate_sect(
            planet_positions=planet_positions,
            ascendant=ascendant,
            midheaven=midheaven,
        )

        return WesternChart(
            birth_date=birth_date.isoformat(),
            birth_time=birth_time.isoformat(),
            latitude=latitude,
            longitude=longitude,
            house_system=house_system,
            julian_day_ut=jd_ut,
            planet_positions=tuple(planet_positions),
            house_cusps=tuple(house_cusps),
            aspects=aspects,
            dignities=dignities,
            ascendant=ascendant,
            midheaven=midheaven,
            sect=sect,
        )

    # ── Private helpers ──────────────────────────────────────────────────

    def _validate_input(
        self,
        birth_date: dt.date,
        birth_time: dt.time,
        latitude: float,
        longitude: float,
    ) -> None:
        """Validate all input parameters."""
        if not isinstance(birth_date, dt.date):
            raise WesternInputError(
                f"birth_date must be a datetime.date, got {type(birth_date).__name__}"
            )
        if not isinstance(birth_time, dt.time):
            raise WesternInputError(
                f"birth_time must be a datetime.time, got {type(birth_time).__name__}"
            )
        if not (-90.0 <= latitude <= 90.0):
            raise WesternInputError(
                f"latitude must be in [-90, 90], got {latitude}"
            )
        if not (-180.0 <= longitude <= 180.0):
            raise WesternInputError(
                f"longitude must be in [-180, 180], got {longitude}"
            )
        if birth_date.year < 1582:
            raise WesternInputError(
                "dates before 1582 (Julian calendar era) are not supported"
            )

    def _compute_julian_day(
        self, birth_date: dt.date, birth_time: dt.time
    ) -> float:
        """Compute Julian Day in UT from birth data.

        Assumes UTC input.  For production use, timezone conversion
        should be applied before calling this method.
        """
        hour_decimal = (
            birth_time.hour
            + birth_time.minute / 60.0
            + birth_time.second / 3600.0
            + birth_time.microsecond / 3_600_000_000.0
        )
        jd: float = swe.julday(
            birth_date.year,
            birth_date.month,
            birth_date.day,
            hour_decimal,
        )
        return jd

    def _calc_single_body(
        self, jd_ut: float, swe_id: int
    ) -> tuple[float, float, float] | None:
        """Calculate a single body, falling back to MOSEPH if needed.

        Returns:
            (longitude, latitude, speed_longitude) or None if the
            body cannot be computed in any mode.
        """
        try:
            xx, _retflag, _errmsg = swe.calc_ut(jd_ut, swe_id, _FLAGS)
            return (xx[0], xx[1], xx[3])
        except (swe.Error, ValueError):
            pass
        try:
            xx, _retflag, _errmsg = swe.calc_ut(jd_ut, swe_id, _FLAGS_MOSEPH)
            return (xx[0], xx[1], xx[3])
        except (swe.Error, ValueError):
            return None

    def _calculate_tropical_positions(
        self, jd_ut: float
    ) -> list[PlanetPosition]:
        """Calculate tropical ecliptic positions for all planets.

        Uses SWIEPH by default.  Falls back to MOSEPH for individual
        bodies whose ephemeris files are unavailable.  Extended bodies
        (e.g. Chiron) are skipped when their ephemeris files are missing.
        """
        positions: list[PlanetPosition] = []

        # Core planets (always available)
        all_bodies: dict[WesternPlanet, int] = dict(_SWE_BODY_MAP)
        all_bodies.update(_SWE_BODY_MAP_EXTENDED)

        for planet, swe_id in all_bodies.items():
            result = self._calc_single_body(jd_ut, swe_id)
            if result is None:
                continue  # Skip bodies with unavailable ephemeris
            longitude, latitude_val, speed_lon = result

            positions.append(
                PlanetPosition(
                    planet=planet,
                    longitude=longitude,
                    latitude=latitude_val,
                    speed_longitude=speed_lon,
                    sign=_sign_name(longitude),
                    degree_in_sign=_degree_in_sign(longitude),
                )
            )

        # Derive South Node from North Node
        north_node = next(
            (p for p in positions if p.planet == WesternPlanet.NORTH_NODE),
            None,
        )
        if north_node is not None:
            sn_lon = (north_node.longitude + _SOUTH_NODE_OFFSET) % 360.0
            positions.append(
                PlanetPosition(
                    planet=WesternPlanet.SOUTH_NODE,
                    longitude=sn_lon,
                    latitude=0.0,
                    speed_longitude=-north_node.speed_longitude,
                    sign=_sign_name(sn_lon),
                    degree_in_sign=_degree_in_sign(sn_lon),
                )
            )

        return positions

    def _calculate_house_cusps(
        self,
        jd_ut: float,
        latitude: float,
        longitude: float,
        house_system: WesternHouseSystem,
    ) -> tuple[list[HouseCusp], float, float]:
        """Calculate house cusps and angles.

        Returns:
            (house_cusps, ascendant_longitude, midheaven_longitude)
        """
        hsys_byte = _HOUSE_SYSTEM_BYTES[house_system]

        try:
            cusps_tuple, ascmc_tuple = swe.houses(
                jd_ut, latitude, longitude, hsys_byte
            )
        except (swe.Error, ValueError) as exc:
            raise WesternCalculationError(
                f"Failed to calculate houses: {exc}"
            ) from exc

        ascendant = ascmc_tuple[0]  # Ascendant
        midheaven = ascmc_tuple[1]  # MC

        # pysweph returns 13 elements: cusps[0] is unused (0.0),
        # cusps[1]..cusps[12] are houses 1..12.
        house_cusps = [
            HouseCusp(house_number=i, longitude=cusps_tuple[i])
            for i in range(1, 13)
        ]

        return house_cusps, ascendant, midheaven

    def _calculate_sect(
        self,
        planet_positions: list[PlanetPosition],
        ascendant: float,
        midheaven: float,
    ) -> Sect:
        """Determine diurnal or nocturnal sect.

        The chart is DIURNAL if the Sun is above the horizon (between
        Ascendant and Descendant going through the MC), NOCTURNAL
        otherwise.

        Algorithm (Lilly CA Ch. 21, Bonatti Tr. 5, Dorotheus C.I.4):
          1. Compute offsets of MC and Sun relative to Ascendant.
          2. The diurnal arc is the 180° semicircle containing the MC.
          3. The Sun is above the horizon if it falls in this semicircle.

        Returns:
            Sect.DIURNAL or Sect.NOCTURNAL.
        """
        sun = next(
            (pp for pp in planet_positions if pp.planet == WesternPlanet.SUN),
            None,
        )
        if sun is None:
            return Sect.DIURNAL  # Default if Sun is unavailable

        asc = ascendant % 360.0
        mc = midheaven % 360.0
        sun_lon = sun.longitude % 360.0

        # Normalize positions relative to Ascendant (Asc = 0)
        sun_offset = (sun_lon - asc) % 360.0
        mc_offset = (mc - asc) % 360.0

        # The diurnal arc (above horizon) is the 180° semicircle
        # containing the MC.  Determine which semicircle that is.
        if mc_offset <= 180.0:
            # MC is in the forward semicircle (0-180° from Asc)
            # Diurnal = Sun offset < 180
            return Sect.DIURNAL if sun_offset < 180.0 else Sect.NOCTURNAL
        else:
            # MC is in the backward semicircle (180-360° from Asc)
            # Diurnal = Sun offset >= 180
            return Sect.DIURNAL if sun_offset >= 180.0 else Sect.NOCTURNAL

"""JRE-027 BirthSignatureService facade.

``BirthSignatureService.create_signature`` is the canonical entry point:
it takes existing astronomy/jyotish facts (PlanetStates, LagnaState)
and deterministically assembles the ``BirthSignature`` object.

It produces NO qualitative output — no personality traits,
no temperament, no predictions.
"""

from __future__ import annotations

from jyotish import BodyId, LagnaState, PlanetState

from .errors import InvalidSignatureRequestError, SignatureComputationError
from .models import (
    BirthSignature,
    compute_am_pm,
    compute_day_night,
    compute_hora,
    compute_karana,
    compute_tithi,
    compute_vara,
    compute_yoga,
)


class BirthSignatureService:
    """Deterministic Birth Signature computation facade."""

    def __init__(self) -> None:
        pass

    def create_signature(
        self,
        planet_states: tuple[PlanetState, ...],
        lagna: LagnaState,
        local_hour: float | None = None,
        local_minute: float | None = None,
        timezone_offset_hours: float = 0.0,
    ) -> BirthSignature:
        """Create a BirthSignature from existing jyotish facts.

        Parameters
        ----------
        planet_states : tuple of PlanetState
            The natal planet states from JRE-003.
        lagna : LagnaState
            The ascendant state from JRE-003.
        local_hour : float or None
            Hour of day in local time (0-23).  Used for hora, AM/PM,
            and day/night determination.
        local_minute : float or None
            Minute of hour in local time (0-59).  Used for refined
            day/night determination.
        timezone_offset_hours : float
            UTC offset in hours for the birth location.

        Returns
        -------
        BirthSignature
            The deterministic birth signature with all Panchanga factors.
        """
        self._validate_request(planet_states, lagna)

        sun_state = self._find_planet(planet_states, BodyId.SUN)
        moon_state = self._find_planet(planet_states, BodyId.MOON)

        sun_lon = sun_state.longitude_used
        moon_lon = moon_state.longitude_used

        # Compute Panchanga factors from Sun/Moon longitudes
        tithi = compute_tithi(sun_lon, moon_lon)
        karana = compute_karana(sun_lon, moon_lon)
        yoga = compute_yoga(sun_lon, moon_lon)

        # Compute weekday from Julian Day (UT)
        weekday = compute_vara(moon_state.julian_day_ut)

        # Determine hour of day for hora and other time-based facts
        hour_of_day = self._compute_hour_of_day(
            local_hour, local_minute, moon_state.julian_day_ut, timezone_offset_hours
        )

        hora = compute_hora(moon_state.julian_day_ut, hour_of_day)
        am_pm = compute_am_pm(hour_of_day)
        day_night = compute_day_night(sun_lon, hour_of_day)

        # Extract positional facts from existing PlanetStates
        sun_rashi = sun_state.rashi
        moon_rashi = moon_state.rashi
        nakshatra = moon_state.nakshatra
        pada = moon_state.pada

        return BirthSignature(
            lagna=lagna.rashi,
            sun_rashi=sun_rashi,
            moon_rashi=moon_rashi,
            nakshatra=nakshatra,
            pada=pada,
            weekday=weekday,
            hora=hora,
            tithi=tithi,
            karana=karana,
            yoga=yoga,
            day_night_period=day_night,
            am_pm=am_pm,
        )

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #

    def _validate_request(
        self,
        planet_states: tuple[PlanetState, ...],
        lagna: LagnaState,
    ) -> None:
        """Validate the BirthSignature request."""
        if not isinstance(planet_states, tuple) or not planet_states:
            raise InvalidSignatureRequestError(
                "planet_states must be a non-empty tuple of PlanetState values"
            )
        for state in planet_states:
            if not isinstance(state, PlanetState):
                raise InvalidSignatureRequestError(
                    "planet_states must contain PlanetState values, "
                    f"got {type(state).__name__}"
                )
        if not isinstance(lagna, LagnaState):
            raise InvalidSignatureRequestError(
                f"lagna must be a LagnaState, got {type(lagna).__name__}"
            )
        # Ensure required planets are present
        bodies_present = {s.body for s in planet_states}
        if BodyId.SUN not in bodies_present:
            raise InvalidSignatureRequestError(
                "planet_states must contain SUN"
            )
        if BodyId.MOON not in bodies_present:
            raise InvalidSignatureRequestError(
                "planet_states must contain MOON"
            )

    def _find_planet(
        self, planet_states: tuple[PlanetState, ...], body: BodyId
    ) -> PlanetState:
        """Find a specific planet in the states tuple."""
        for state in planet_states:
            if state.body == body:
                return state
        raise SignatureComputationError(
            f"planet {body.value} not found in planet_states"
        )

    def _compute_hour_of_day(
        self,
        local_hour: float | None,
        local_minute: float | None,
        julian_day_ut: float,
        timezone_offset_hours: float,
    ) -> float:
        """Compute the hour of day (0-23) in local time.

        If local_hour is provided, use it directly.  Otherwise,
        derive from Julian Day and timezone offset.
        """
        if local_hour is not None:
            hour = local_hour
            if local_minute is not None:
                hour += local_minute / 60.0
            return hour % 24.0

        # Derive from Julian Day: the UT hour + timezone offset
        # JD starts at noon UT, so we need to account for that
        ut_hour = ((julian_day_ut + 0.5) % 1.0) * 24.0
        local_hour_computed = (ut_hour + timezone_offset_hours) % 24.0
        return local_hour_computed
